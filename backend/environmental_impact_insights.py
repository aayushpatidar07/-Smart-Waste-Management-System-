"""
Environmental impact insights service for waste management system.
Tracks CO2 emissions, environmental impact metrics, and sustainability progress.
"""
from database import Database
from datetime import datetime, timedelta


class EnvironmentalImpactService:
    """Provides environmental impact analytics and insights."""
    
    def __init__(self):
        self.db = Database()
    
    def get_impact_summary(self, days=30):
        """Get overall environmental impact summary metrics."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                COUNT(*) as total_collections,
                SUM(weight_kg) as total_waste_kg,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_collections,
                AVG(vehicle_distance_km) as avg_route_distance,
                COUNT(DISTINCT vehicle_id) as vehicles_used
            FROM collection_logs
            WHERE collection_date >= %s
            """
            
            self.db.cursor.execute(query, (start_date,))
            row = self.db.cursor.fetchone()
            
            # Calculate carbon footprint (approx 2.5 kg CO2 per liter diesel, ~7L per 100km)
            total_waste = row[1] or 0
            avg_distance = row[3] or 0
            num_collections = row[0] or 1
            
            total_distance = avg_distance * num_collections
            co2_kg = (total_distance / 100) * 7 * 2.5
            
            # Landfill diversion (assume 60% recycled/composted)
            landfill_kg = total_waste * 0.4
            diverted_kg = total_waste * 0.6
            
            return {
                'success': True,
                'total_collections': row[0],
                'total_waste_kg': round(total_waste, 2),
                'successful_collections': row[2],
                'vehicles_deployed': row[4],
                'total_route_distance_km': round(total_distance, 2),
                'co2_emissions_kg': round(co2_kg, 2),
                'landfill_sent_kg': round(landfill_kg, 2),
                'diverted_from_landfill_kg': round(diverted_kg, 2),
                'diversion_rate_percent': 60,
                'avg_collection_distance_km': round(avg_distance, 2)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_co2_breakdown(self, days=30):
        """Get CO2 emissions breakdown by vehicle type and zone."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                v.vehicle_type,
                COUNT(cl.id) as collections,
                AVG(cl.vehicle_distance_km) as avg_distance,
                SUM(cl.vehicle_distance_km) as total_distance
            FROM collection_logs cl
            JOIN vehicles v ON cl.vehicle_id = v.id
            WHERE cl.collection_date >= %s AND cl.status = 'completed'
            GROUP BY v.vehicle_type
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            breakdown = []
            for row in rows:
                vehicle_type = row[0]
                total_distance = row[3] or 0
                
                # CO2 per km varies by vehicle type
                co2_per_km = 0.25 if vehicle_type == 'Electric' else 0.35 if vehicle_type == 'Hybrid' else 0.50
                co2_kg = total_distance * co2_per_km
                
                breakdown.append({
                    'vehicle_type': vehicle_type,
                    'collections': row[1],
                    'total_distance_km': round(total_distance, 2),
                    'co2_emissions_kg': round(co2_kg, 2),
                    'co2_per_km': co2_per_km
                })
            
            return {
                'success': True,
                'breakdown': breakdown
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_waste_composition_impact(self, days=30):
        """Get environmental impact breakdown by waste type."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                report_type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN priority >= 'HIGH' THEN 1 ELSE 0 END) as high_impact
            FROM waste_reports
            WHERE created_at >= %s
            GROUP BY report_type
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            # Environmental impact scores (1-10, higher = worse impact)
            impact_map = {
                'Hazardous': 9,
                'E-Waste': 8,
                'Organic': 3,
                'Plastic': 7,
                'Metal': 5,
                'Paper': 2
            }
            
            composition = []
            total_score = 0
            total_reports = 0
            
            for row in rows:
                waste_type = row[0]
                count = row[1]
                impact = impact_map.get(waste_type, 5)
                weighted_impact = impact * count
                
                composition.append({
                    'waste_type': waste_type,
                    'total_reports': count,
                    'resolved_reports': row[2],
                    'high_impact_reports': row[3],
                    'environmental_impact_score': impact,
                    'weighted_impact': weighted_impact
                })
                
                total_score += weighted_impact
                total_reports += count
            
            avg_impact = round(total_score / max(total_reports, 1), 2)
            
            return {
                'success': True,
                'composition': composition,
                'average_impact_score': avg_impact,
                'total_reports': total_reports
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_sustainability_trends(self, days=30):
        """Get sustainability improvement trends over time."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                DATE(collection_date) as date,
                COUNT(*) as collections,
                SUM(weight_kg) as waste_kg,
                AVG(vehicle_distance_km) as avg_distance,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
            FROM collection_logs
            WHERE collection_date >= %s
            GROUP BY DATE(collection_date)
            ORDER BY date DESC
            LIMIT 14
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            trends = []
            for row in rows:
                distance = row[3] or 0
                co2 = (distance / 100) * 7 * 2.5
                
                trends.append({
                    'date': str(row[0]),
                    'collections': row[1],
                    'waste_kg': round(row[2] or 0, 2),
                    'avg_distance_km': round(distance, 2),
                    'co2_kg': round(co2, 2),
                    'efficiency_rate_percent': round((row[4] / max(row[1], 1)) * 100, 1)
                })
            
            return {
                'success': True,
                'trends': trends
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_sustainability_recommendations(self, days=30):
        """Get AI-driven recommendations for improving environmental impact."""
        try:
            # Get current metrics
            summary = self.get_impact_summary(days)
            if not summary.get('success'):
                return summary
            
            breakdown = self.get_co2_breakdown(days)
            composition = self.get_waste_composition_impact(days)
            
            recommendations = []
            
            # Check for optimization opportunities
            co2_kg = summary.get('co2_emissions_kg', 0)
            if co2_kg > 500:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Fleet Optimization',
                    'recommendation': 'High CO2 emissions detected. Consider expanding electric vehicle fleet.',
                    'expected_impact': 'Reduce CO2 by 30-40%',
                    'action': 'Review vehicle deployment strategy'
                })
            
            # Route optimization
            if summary.get('avg_collection_distance_km', 0) > 15:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Route Optimization',
                    'recommendation': 'Average collection distance exceeds 15 km. Optimize route planning.',
                    'expected_impact': 'Reduce distance by 15-20%',
                    'action': 'Use AI route optimizer'
                })
            
            # Waste composition
            if composition.get('success') and composition.get('average_impact_score', 0) > 5:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Waste Management',
                    'recommendation': 'High-impact waste types dominate. Increase recycling/composting.',
                    'expected_impact': 'Increase diversion rate to 75%',
                    'action': 'Education & infrastructure'
                })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
