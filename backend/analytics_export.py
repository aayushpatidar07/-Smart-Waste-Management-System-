"""Analytics Export & Mobile API Service
Provides comprehensive data export capabilities (CSV, JSON, PDF) and
RESTful APIs optimized for mobile applications with minimal bandwidth.
"""

from datetime import datetime, timedelta
from models import Database
import json

class AnalyticsExportService:
    """Service for exporting analytics and providing mobile-optimized APIs"""
    
    def __init__(self):
        self.db = Database()
    
    def export_bin_data_json(self, days=30):
        """Export bin analytics as JSON"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT 
                    id, zone_id, latitude, longitude, fill_level,
                    last_collection_date, status, created_at
                FROM bins
                WHERE created_at >= %s
                ORDER BY zone_id, id
                LIMIT 10000
            """
            
            cursor.execute(query, (cutoff_date,))
            bins = cursor.fetchall()
            
            # Format for export
            exported_data = []
            for bin_data in bins:
                exported_data.append({
                    'bin_id': bin_data['id'],
                    'zone_id': bin_data['zone_id'],
                    'location': {'lat': bin_data['latitude'], 'lon': bin_data['longitude']},
                    'fill_level_percent': bin_data['fill_level'],
                    'status': bin_data['status'],
                    'last_collection': bin_data['last_collection_date'].isoformat() if bin_data['last_collection_date'] else None
                })
            
            cursor.close()
            
            return {
                'success': True,
                'export_type': 'JSON',
                'timestamp': datetime.now().isoformat(),
                'total_records': len(exported_data),
                'data': exported_data
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_collection_statistics_csv(self, start_date, end_date):
        """Export collection statistics as CSV format"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            query = """
                SELECT 
                    DATE(created_at) as collection_date,
                    COUNT(id) as total_collections,
                    SUM(waste_quantity) as total_waste,
                    AVG(waste_quantity) as avg_waste,
                    COUNT(DISTINCT bin_id) as bins_collected,
                    COUNT(DISTINCT reported_by) as citizens
                FROM waste_reports
                WHERE created_at BETWEEN %s AND %s
                GROUP BY DATE(created_at)
                ORDER BY collection_date
            """
            
            cursor.execute(query, (start_date, end_date))
            stats = cursor.fetchall()
            
            # Format as CSV
            csv_lines = ['Date,Collections,Total Waste (kg),Avg Waste (kg),Bins Collected,Citizens']
            for stat in stats:
                csv_lines.append(
                    f"{stat['collection_date']},"
                    f"{stat['total_collections']},"
                    f"{stat['total_waste']},"
                    f"{stat['avg_waste']},"
                    f"{stat['bins_collected']},"
                    f"{stat['citizens']}"
                )
            
            cursor.close()
            
            return {
                'success': True,
                'export_type': 'CSV',
                'timestamp': datetime.now().isoformat(),
                'total_records': len(stats),
                'csv_content': '\n'.join(csv_lines)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_mobile_dashboard_summary(self):
        """Get lightweight dashboard summary for mobile apps"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get minimal data for mobile
            bins_query = "SELECT COUNT(id) as total, SUM(CASE WHEN fill_level > 90 THEN 1 ELSE 0 END) as critical FROM bins"
            cursor.execute(bins_query)
            bins_data = cursor.fetchone()
            
            vehicles_query = "SELECT COUNT(id) as active FROM vehicles WHERE status = 'active'"
            cursor.execute(vehicles_query)
            vehicles_data = cursor.fetchone()
            
            collections_query = "SELECT COUNT(id) as today FROM waste_reports WHERE DATE(created_at) = CURDATE()"
            cursor.execute(collections_query)
            collections_today = cursor.fetchone()
            
            cursor.close()
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'bins': {
                    'total': bins_data['total'],
                    'critical': bins_data['critical']
                },
                'vehicles': {
                    'active': vehicles_data['active']
                },
                'collections_today': collections_today['today'],
                'last_sync': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_mobile_nearby_bins(self, latitude, longitude, radius_km=5):
        """Get nearby bins for mobile users (location-based)"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Simplified proximity search
            query = """
                SELECT 
                    id, zone_id, latitude, longitude, fill_level, status,
                    (6371 * ACOS(COS(RADIANS(%s)) * COS(RADIANS(latitude)) * 
                    COS(RADIANS(%s) - RADIANS(longitude)) + SIN(RADIANS(%s)) * 
                    SIN(RADIANS(latitude)))) as distance_km
                FROM bins
                HAVING distance_km <= %s
                ORDER BY distance_km
                LIMIT 50
            """
            
            cursor.execute(query, (latitude, longitude, longitude, radius_km))
            bins = cursor.fetchall()
            
            mobile_bins = []
            for bin_data in bins:
                mobile_bins.append({
                    'id': bin_data['id'],
                    'zone': bin_data['zone_id'],
                    'location': {
                        'lat': float(bin_data['latitude']),
                        'lon': float(bin_data['longitude'])
                    },
                    'fill': bin_data['fill_level'],
                    'status': bin_data['status'],
                    'distance_km': round(bin_data['distance_km'], 2)
                })
            
            cursor.close()
            
            return {
                'success': True,
                'nearby_bins': mobile_bins,
                'search_radius_km': radius_km,
                'results_count': len(mobile_bins),
                'search_location': {'lat': latitude, 'lon': longitude}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_mobile_citizen_profile(self, citizen_id):
        """Get citizen profile data for mobile apps"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            user_query = "SELECT id, name, email, role FROM users WHERE id = %s"
            cursor.execute(user_query, (citizen_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                return {'success': False, 'message': 'User not found'}
            
            # Get recent activity
            activity_query = """
                SELECT COUNT(id) as reports, COALESCE(SUM(waste_quantity), 0) as total_waste
                FROM waste_reports
                WHERE reported_by = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            cursor.execute(activity_query, (citizen_id,))
            activity = cursor.fetchone()
            
            cursor.close()
            
            return {
                'success': True,
                'profile': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role']
                },
                'stats': {
                    'reports_month': activity['reports'],
                    'waste_reported_kg': round(activity['total_waste'], 2)
                },
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_system_health_status(self):
        """Get system health metrics for mobile status page"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Quick health checks
            bins_query = "SELECT COUNT(id) as total, AVG(fill_level) as avg_fill FROM bins"
            cursor.execute(bins_query)
            bins_health = cursor.fetchone()
            
            vehicles_query = "SELECT COUNT(id) as total, SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) as active FROM vehicles"
            cursor.execute(vehicles_query)
            vehicles_health = cursor.fetchone()
            
            alerts_query = "SELECT COUNT(id) as active FROM alerts WHERE status='Active'"
            cursor.execute(alerts_query)
            alerts_count = cursor.fetchone()
            
            cursor.close()
            
            # Calculate health percentage
            health_score = 100
            warnings = []
            
            if bins_health['avg_fill'] > 85:
                health_score -= 10
                warnings.append('High average bin fill levels')
            
            if vehicles_health['active'] < vehicles_health['total'] * 0.8:
                health_score -= 15
                warnings.append('Vehicle availability below threshold')
            
            if alerts_count['active'] > 10:
                health_score -= 20
                warnings.append('Multiple active alerts')
            
            return {
                'success': True,
                'health_score': max(0, health_score),
                'status': 'HEALTHY' if health_score >= 80 else 'WARNING' if health_score >= 60 else 'CRITICAL',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'bins': {'total': bins_health['total'], 'avg_fill': round(bins_health['avg_fill'], 1)},
                    'vehicles': {'total': vehicles_health['total'], 'active': vehicles_health['active']},
                    'alerts': {'active': alerts_count['active']}
                },
                'warnings': warnings
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Initialize service
analytics_export_service = AnalyticsExportService()
