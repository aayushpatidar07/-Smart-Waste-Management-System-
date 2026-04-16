"""
Cost analytics service for waste management system.
Tracks operational costs, vehicle costs, labor costs, and financial efficiency.
"""
from database import Database
from datetime import datetime, timedelta


class CostAnalyticsService:
    """Provides cost analytics and financial insights."""
    
    def __init__(self):
        self.db = Database()
    
    def get_cost_summary(self, days=30):
        """Get overall cost summary for a period."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                COUNT(*) as total_collections,
                SUM(weight_kg) as total_waste_kg,
                COUNT(DISTINCT vehicle_id) as vehicles_used,
                COUNT(DISTINCT staff_id) as staff_deployed
            FROM collection_logs
            WHERE collection_date >= %s AND status = 'completed'
            """
            
            self.db.cursor.execute(query, (start_date,))
            row = self.db.cursor.fetchone()
            
            total_collections = row[0] or 0
            total_waste = row[1] or 0
            vehicles_used = row[2] or 1
            staff_used = row[3] or 1
            
            # Cost estimates (adjust based on actual rates)
            vehicle_cost_per_km = 5  # $5 per km
            labor_cost_per_hour = 25  # $25 per hour
            fuel_cost_per_liter = 3.5  # $3.50 per liter
            maintenance_cost_percent = 0.10  # 10% of vehicle costs
            
            avg_distance = (total_collections * 15) / max(total_collections, 1)
            total_vehicle_distance = avg_distance * total_collections
            
            vehicle_ops_cost = total_vehicle_distance * vehicle_cost_per_km
            fuel_cost = (total_vehicle_distance / 7) * fuel_cost_per_liter  # 7 km/liter avg
            maintenance_cost = vehicle_ops_cost * maintenance_cost_percent
            
            labor_hours = total_collections * 1.5  # 1.5 hours per collection
            labor_cost = labor_hours * labor_cost_per_hour
            
            total_cost = vehicle_ops_cost + fuel_cost + maintenance_cost + labor_cost
            cost_per_collection = total_cost / max(total_collections, 1)
            cost_per_kg = total_cost / max(total_waste, 1)
            
            return {
                'success': True,
                'total_collections': total_collections,
                'total_waste_kg': round(total_waste, 2),
                'vehicles_used': vehicles_used,
                'staff_deployed': staff_used,
                'vehicle_operations_cost': round(vehicle_ops_cost, 2),
                'fuel_cost': round(fuel_cost, 2),
                'maintenance_cost': round(maintenance_cost, 2),
                'labor_cost': round(labor_cost, 2),
                'total_operational_cost': round(total_cost, 2),
                'cost_per_collection': round(cost_per_collection, 2),
                'cost_per_kg_waste': round(cost_per_kg, 4)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_cost_by_vehicle(self, days=30):
        """Get cost breakdown by vehicle."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                v.id,
                v.vehicle_name,
                v.vehicle_type,
                COUNT(cl.id) as collections,
                SUM(cl.vehicle_distance_km) as total_distance,
                AVG(cl.vehicle_distance_km) as avg_distance
            FROM collection_logs cl
            JOIN vehicles v ON cl.vehicle_id = v.id
            WHERE cl.collection_date >= %s AND cl.status = 'completed'
            GROUP BY v.id, v.vehicle_name, v.vehicle_type
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            # Cost multipliers by vehicle type
            cost_multipliers = {
                'Electric': 0.8,
                'Hybrid': 0.9,
                'Diesel': 1.0,
                'Gasoline': 1.1
            }
            
            breakdown = []
            for row in rows:
                vehicle_id, name, vehicle_type, collections, total_distance, avg_distance = row
                total_distance = total_distance or 0
                
                multiplier = cost_multipliers.get(vehicle_type, 1.0)
                vehicle_cost = total_distance * 5 * multiplier  # Base $5/km
                fuel_cost = (total_distance / 7) * 3.5 * multiplier
                maintenance_cost = vehicle_cost * 0.10
                total_vehicle_cost = vehicle_cost + fuel_cost + maintenance_cost
                
                breakdown.append({
                    'vehicle_id': vehicle_id,
                    'vehicle_name': name,
                    'vehicle_type': vehicle_type,
                    'collections': collections,
                    'total_distance_km': round(total_distance, 2),
                    'avg_distance_km': round(avg_distance or 0, 2),
                    'operations_cost': round(vehicle_cost, 2),
                    'fuel_cost': round(fuel_cost, 2),
                    'maintenance_cost': round(maintenance_cost, 2),
                    'total_cost': round(total_vehicle_cost, 2),
                    'cost_per_collection': round(total_vehicle_cost / max(collections, 1), 2)
                })
            
            return {
                'success': True,
                'breakdown': sorted(breakdown, key=lambda x: x['total_cost'], reverse=True)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_cost_by_zone(self, days=30):
        """Get cost analysis by zone."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                b.zone,
                COUNT(cl.id) as collections,
                SUM(cl.weight_kg) as waste_kg,
                AVG(cl.vehicle_distance_km) as avg_distance,
                COUNT(DISTINCT cl.vehicle_id) as vehicles
            FROM collection_logs cl
            JOIN bins b ON cl.bin_id = b.id
            WHERE cl.collection_date >= %s AND cl.status = 'completed'
            GROUP BY b.zone
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            breakdown = []
            for row in rows:
                zone, collections, waste_kg, avg_distance, vehicles = row
                avg_distance = avg_distance or 0
                waste_kg = waste_kg or 0
                
                total_distance = avg_distance * collections
                zone_cost = total_distance * 5 + (total_distance / 7) * 3.5
                cost_per_collection = zone_cost / max(collections, 1)
                cost_per_kg = zone_cost / max(waste_kg, 1)
                
                breakdown.append({
                    'zone': zone,
                    'collections': collections,
                    'waste_kg': round(waste_kg, 2),
                    'avg_distance_km': round(avg_distance, 2),
                    'vehicles_deployed': vehicles,
                    'total_zone_cost': round(zone_cost, 2),
                    'cost_per_collection': round(cost_per_collection, 2),
                    'cost_per_kg': round(cost_per_kg, 4)
                })
            
            return {
                'success': True,
                'breakdown': sorted(breakdown, key=lambda x: x['total_zone_cost'], reverse=True)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_cost_trends(self, days=30):
        """Get daily cost trends."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                DATE(collection_date) as date,
                COUNT(*) as collections,
                SUM(vehicle_distance_km) as total_distance,
                COUNT(DISTINCT staff_id) as staff_count
            FROM collection_logs
            WHERE collection_date >= %s AND status = 'completed'
            GROUP BY DATE(collection_date)
            ORDER BY date DESC
            LIMIT 14
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            trends = []
            for row in rows:
                date, collections, total_distance, staff_count = row
                total_distance = total_distance or 0
                staff_count = staff_count or 1
                
                vehicle_cost = total_distance * 5
                fuel_cost = (total_distance / 7) * 3.5
                labor_cost = collections * 1.5 * 25
                daily_cost = vehicle_cost + fuel_cost + labor_cost
                
                trends.append({
                    'date': str(date),
                    'collections': collections,
                    'distance_km': round(total_distance, 2),
                    'staff_deployed': staff_count,
                    'daily_cost': round(daily_cost, 2),
                    'cost_per_collection': round(daily_cost / max(collections, 1), 2)
                })
            
            return {
                'success': True,
                'trends': trends
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_cost_efficiency_recommendations(self, days=30):
        """Get cost optimization recommendations."""
        try:
            summary = self.get_cost_summary(days)
            if not summary.get('success'):
                return summary
            
            vehicle_breakdown = self.get_cost_by_vehicle(days)
            zone_breakdown = self.get_cost_by_zone(days)
            
            recommendations = []
            
            # Check vehicle utilization
            cost_per_collection = summary.get('cost_per_collection', 0)
            if cost_per_collection > 120:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Vehicle Efficiency',
                    'recommendation': f'High cost per collection (${cost_per_collection}). Optimize route planning or vehicle utilization.',
                    'potential_savings': f'${cost_per_collection * 0.2:.2f} per collection',
                    'action': 'Review route optimizer settings'
                })
            
            # Check fuel costs
            fuel_percent = (summary.get('fuel_cost', 0) / max(summary.get('total_operational_cost', 1), 1)) * 100
            if fuel_percent > 35:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Fuel Management',
                    'recommendation': f'Fuel costs are {fuel_percent:.1f}% of total. Consider electric vehicle expansion.',
                    'potential_savings': f'${summary.get("fuel_cost", 0) * 0.25:.2f} per period',
                    'action': 'Increase electric vehicle fleet'
                })
            
            # Check labor efficiency
            labor_to_total = (summary.get('labor_cost', 0) / max(summary.get('total_operational_cost', 1), 1)) * 100
            if labor_to_total > 40:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Labor Optimization',
                    'recommendation': f'Labor costs are {labor_to_total:.1f}% of total. Improve scheduling efficiency.',
                    'potential_savings': f'${summary.get("labor_cost", 0) * 0.15:.2f} per period',
                    'action': 'Review staff scheduling'
                })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
