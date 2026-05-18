"""
Vehicle maintenance tracking and analytics service.
Tracks scheduled maintenance, maintenance history, and vehicle health.
"""
from models import Database
from datetime import datetime, timedelta


class VehicleMaintenanceService:
    """Provides vehicle maintenance tracking and insights."""
    
    def __init__(self):
        self.db = Database()
    
    def get_maintenance_overview(self):
        """Get overall vehicle maintenance status overview."""
        try:
            query = """
            SELECT 
                COUNT(*) as total_vehicles,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_vehicles,
                SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as in_maintenance,
                SUM(CASE WHEN status = 'Retired' THEN 1 ELSE 0 END) as retired_vehicles
            FROM vehicles
            """
            
            self.db.cursor.execute(query)
            row = self.db.cursor.fetchone()
            
            # Get upcoming maintenance
            upcoming_query = """
            SELECT COUNT(*) FROM vehicles
            WHERE status = 'Active' AND (mileage_km / 5000) >= 0.8
            """
            
            self.db.cursor.execute(upcoming_query)
            upcoming = self.db.cursor.fetchone()[0]
            
            return {
                'success': True,
                'total_vehicles': row[0],
                'active_vehicles': row[1] or 0,
                'in_maintenance': row[2] or 0,
                'retired_vehicles': row[3] or 0,
                'upcoming_maintenance_count': upcoming
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_schedule(self):
        """Get vehicles requiring maintenance or with upcoming schedules."""
        try:
            query = """
            SELECT 
                id,
                vehicle_name,
                vehicle_type,
                mileage_km,
                status,
                last_maintenance_date,
                purchase_date
            FROM vehicles
            ORDER BY mileage_km DESC
            LIMIT 20
            """
            
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
            
            schedule = []
            for row in rows:
                vehicle_id, name, v_type, mileage, status, last_maint, purchase = row
                mileage = mileage or 0
                
                # Maintenance intervals: 10,000 km or 6 months
                maintenance_interval_km = 10000
                maint_percentage = (mileage % maintenance_interval_km) / maintenance_interval_km * 100
                
                # Estimate next maintenance
                next_maint_km = ((mileage // maintenance_interval_km) + 1) * maintenance_interval_km
                km_until_maintenance = max(0, next_maint_km - mileage)
                
                # Priority based on percentage
                if maint_percentage >= 90:
                    priority = 'CRITICAL'
                elif maint_percentage >= 70:
                    priority = 'HIGH'
                elif maint_percentage >= 50:
                    priority = 'MEDIUM'
                else:
                    priority = 'LOW'
                
                schedule.append({
                    'vehicle_id': vehicle_id,
                    'vehicle_name': name,
                    'vehicle_type': v_type,
                    'current_mileage_km': round(mileage, 1),
                    'status': status,
                    'maintenance_percentage': round(maint_percentage, 1),
                    'km_until_maintenance': round(km_until_maintenance, 1),
                    'priority': priority,
                    'last_maintenance': str(last_maint) if last_maint else 'Never'
                })
            
            return {
                'success': True,
                'schedule': schedule
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_history(self, days=90):
        """Get vehicle maintenance history."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                v.vehicle_name,
                v.vehicle_type,
                COUNT(*) as maintenance_count,
                SUM(CASE WHEN m.maintenance_type = 'Oil Change' THEN 1 ELSE 0 END) as oil_changes,
                SUM(CASE WHEN m.maintenance_type = 'Tire Rotation' THEN 1 ELSE 0 END) as tire_rotations,
                SUM(CASE WHEN m.maintenance_type = 'Inspection' THEN 1 ELSE 0 END) as inspections,
                SUM(m.cost) as total_cost
            FROM vehicle_maintenance_logs m
            JOIN vehicles v ON m.vehicle_id = v.id
            WHERE m.maintenance_date >= %s
            GROUP BY v.vehicle_name, v.vehicle_type
            ORDER BY maintenance_count DESC
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'vehicle_name': row[0],
                    'vehicle_type': row[1],
                    'total_maintenance': row[2],
                    'oil_changes': row[3] or 0,
                    'tire_rotations': row[4] or 0,
                    'inspections': row[5] or 0,
                    'total_cost': round(row[6] or 0, 2)
                })
            
            return {
                'success': True,
                'history': history,
                'period_days': days
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_fleet_health(self):
        """Get overall fleet health metrics."""
        try:
            query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN mileage_km < 100000 THEN 1 ELSE 0 END) as low_mileage,
                SUM(CASE WHEN mileage_km >= 100000 AND mileage_km < 250000 THEN 1 ELSE 0 END) as medium_mileage,
                SUM(CASE WHEN mileage_km >= 250000 THEN 1 ELSE 0 END) as high_mileage,
                AVG(mileage_km) as avg_mileage,
                MAX(mileage_km) as max_mileage
            FROM vehicles
            WHERE status = 'Active'
            """
            
            self.db.cursor.execute(query)
            row = self.db.cursor.fetchone()
            
            total = row[0] or 1
            avg_mileage = row[4] or 0
            max_mileage = row[5] or 0
            
            # Health score: lower average mileage = better health
            health_score = max(0, 100 - (avg_mileage / 1000))
            
            return {
                'success': True,
                'total_active_vehicles': total,
                'low_mileage_vehicles': row[1] or 0,
                'medium_mileage_vehicles': row[2] or 0,
                'high_mileage_vehicles': row[3] or 0,
                'average_mileage_km': round(avg_mileage, 1),
                'max_mileage_km': round(max_mileage, 1),
                'fleet_health_score': round(health_score, 1),
                'health_status': 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair' if health_score >= 40 else 'Poor'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_costs(self, days=90):
        """Get maintenance cost analysis."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                v.vehicle_type,
                COUNT(*) as maintenance_events,
                SUM(m.cost) as total_cost,
                AVG(m.cost) as avg_cost,
                MAX(m.cost) as max_cost,
                MIN(m.cost) as min_cost
            FROM vehicle_maintenance_logs m
            JOIN vehicles v ON m.vehicle_id = v.id
            WHERE m.maintenance_date >= %s
            GROUP BY v.vehicle_type
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            costs = []
            total_cost = 0
            total_events = 0
            
            for row in rows:
                event_cost = row[2] or 0
                total_cost += event_cost
                total_events += (row[1] or 0)
                
                costs.append({
                    'vehicle_type': row[0],
                    'maintenance_events': row[1],
                    'total_cost': round(event_cost, 2),
                    'average_cost': round(row[3] or 0, 2),
                    'max_cost': round(row[4] or 0, 2),
                    'min_cost': round(row[5] or 0, 2)
                })
            
            return {
                'success': True,
                'costs_by_type': costs,
                'total_maintenance_cost': round(total_cost, 2),
                'total_events': total_events,
                'average_event_cost': round(total_cost / max(total_events, 1), 2),
                'period_days': days
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_recommendations(self):
        """Get maintenance recommendations."""
        try:
            overview = self.get_maintenance_overview()
            if not overview.get('success'):
                return overview
            
            schedule = self.get_maintenance_schedule()
            health = self.get_fleet_health()
            
            recommendations = []
            
            # Check for vehicles needing immediate maintenance
            critical_count = sum(1 for item in schedule.get('schedule', []) if item.get('priority') == 'CRITICAL')
            if critical_count > 0:
                recommendations.append({
                    'priority': 'CRITICAL',
                    'category': 'Immediate Maintenance',
                    'recommendation': f'{critical_count} vehicles require immediate maintenance.',
                    'action': 'Schedule maintenance appointments immediately'
                })
            
            # Check fleet health
            if health.get('health_score', 0) < 50:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Fleet Rejuvenation',
                    'recommendation': f'Fleet health score is {health.get("health_score")}. Consider vehicle replacement.',
                    'action': 'Plan vehicle replacement strategy'
                })
            
            # Check for high-mileage vehicles
            high_mileage = health.get('high_mileage_vehicles', 0)
            if high_mileage > 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'High Mileage Management',
                    'recommendation': f'{high_mileage} vehicles have high mileage. Increase maintenance frequency.',
                    'action': 'Schedule preventive maintenance for high-mileage vehicles'
                })
            
            # Check for upcoming maintenance
            upcoming = overview.get('upcoming_maintenance_count', 0)
            if upcoming > 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Scheduled Maintenance',
                    'recommendation': f'{upcoming} vehicles have upcoming maintenance within 20% of interval.',
                    'action': 'Plan maintenance schedule'
                })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
