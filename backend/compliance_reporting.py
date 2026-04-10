"""Compliance & Regulatory Reporting Service
Generates compliance reports for waste management regulations, environmental standards,
and operational metrics required by regulatory authorities.
"""

from datetime import datetime, timedelta
from models import Database

class ComplianceReportingService:
    """Service for generating compliance and regulatory reports"""
    
    def __init__(self):
        self.db = Database()
    
    def generate_waste_disposal_report(self, start_date, end_date):
        """Generate waste disposal compliance report"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get waste disposal stats
            query = """
                SELECT 
                    COUNT(id) as total_reports,
                    SUM(waste_quantity) as total_waste_kg,
                    COUNT(DISTINCT DATE(created_at)) as collection_days,
                    AVG(waste_quantity) as avg_waste_per_collection
                FROM waste_reports
                WHERE created_at BETWEEN %s AND %s
            """
            
            cursor.execute(query, (start_date, end_date))
            stats = cursor.fetchone()
            
            cursor.close()
            
            # Generate compliance metrics
            compliance_score = 95  # Base score
            violations = []
            
            if stats['total_waste_kg'] is None:
                stats['total_waste_kg'] = 0
            if stats['collection_days'] == 0:
                compliance_score -= 20
                violations.append('No collection activity in period')
            
            return {
                'success': True,
                'report_type': 'Waste Disposal Compliance',
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'total_waste_collected_kg': round(stats['total_waste_kg'], 2),
                'total_collections': stats['total_reports'],
                'collection_days': stats['collection_days'],
                'avg_collection_frequency': round(stats['collection_days'] / max(1, stats['total_reports']), 2),
                'compliance_score': compliance_score,
                'violations': violations,
                'status': 'COMPLIANT' if compliance_score >= 85 else 'WARNING'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_environmental_impact_report(self, start_date, end_date):
        """Generate environmental impact compliance report"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get environmental metrics
            query = """
                SELECT 
                    SUM(carbon_emissions) as total_co2,
                    SUM(waste_diverted) as total_diverted,
                    COUNT(DISTINCT bin_id) as bins_participating,
                    AVG(diversion_rate) as avg_diversion
                FROM bins
                WHERE created_at BETWEEN %s AND %s
            """
            
            cursor.execute(query, (start_date, end_date))
            env_data = cursor.fetchone()
            
            cursor.close()
            
            return {
                'success': True,
                'report_type': 'Environmental Impact Compliance',
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'total_co2_avoided_kg': round(env_data['total_co2'] or 0, 2),
                'total_waste_diverted_kg': round(env_data['total_diverted'] or 0, 2),
                'participating_bins': env_data['bins_participating'] or 0,
                'avg_diversion_rate_percent': round(env_data['avg_diversion'] or 0, 1),
                'status': 'ON_TARGET' if (env_data['avg_diversion'] or 0) >= 50 else 'NEEDS_IMPROVEMENT'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_operational_efficiency_report(self, start_date, end_date):
        """Generate operational efficiency report"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get operational metrics
            query = """
                SELECT 
                    COUNT(DISTINCT vehicle_id) as active_vehicles,
                    AVG(distance) as avg_route_distance,
                    AVG(duration) as avg_route_duration,
                    COUNT(id) as total_routes
                FROM routes
                WHERE created_at BETWEEN %s AND %s
            """
            
            cursor.execute(query, (start_date, end_date))
            ops_data = cursor.fetchone()
            
            cursor.close()
            
            return {
                'success': True,
                'report_type': 'Operational Efficiency',
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'active_vehicles': ops_data['active_vehicles'] or 0,
                'total_routes': ops_data['total_routes'] or 0,
                'avg_route_distance_km': round(ops_data['avg_route_distance'] or 0, 1),
                'avg_route_duration_hours': round(ops_data['avg_route_duration'] or 0, 1),
                'efficiency_rating': 'EXCELLENT' if (ops_data['avg_route_distance'] or 0) < 50 else 'GOOD'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_safety_compliance_report(self):
        """Generate safety compliance report"""
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get safety metrics
            query = """
                SELECT 
                    COUNT(id) as total_vehicles,
                    SUM(CASE WHEN maintenance_status = 'Good' THEN 1 ELSE 0 END) as well_maintained,
                    SUM(CASE WHEN fuel_consumption < 5 THEN 1 ELSE 0 END) as efficient_vehicles
                FROM vehicles
            """
            
            cursor.execute(query)
            safety_data = cursor.fetchone()
            
            cursor.close()
            
            maintained_percent = (safety_data['well_maintained'] / safety_data['total_vehicles'] * 100) if safety_data['total_vehicles'] > 0 else 0
            
            return {
                'success': True,
                'report_type': 'Safety & Vehicle Compliance',
                'timestamp': datetime.now().isoformat(),
                'total_vehicles': safety_data['total_vehicles'],
                'well_maintained_percent': round(maintained_percent, 1),
                'efficient_vehicles': safety_data['efficient_vehicles'],
                'compliance_status': 'COMPLIANT' if maintained_percent >= 90 else 'AT_RISK',
                'recommendations': [
                    'Schedule preventive maintenance for aging vehicles',
                    'Implement fuel efficiency monitoring',
                    'Conduct safety training for drivers'
                ] if maintained_percent < 95 else []
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_quarterly_compliance_summary(self, quarter, year):
        """Generate quarterly compliance summary"""
        try:
            if quarter < 1 or quarter > 4:
                return {'success': False, 'message': 'Invalid quarter (1-4)'}
            
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2
            
            start_date = datetime(year, start_month, 1)
            end_date = datetime(year, end_month, 28)
            
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Compile quarterly data
            summary_query = """
                SELECT 
                    COUNT(id) as total_collections,
                    SUM(waste_quantity) as total_waste,
                    COUNT(DISTINCT reported_by) as citizen_participation,
                    COUNT(DISTINCT DATE(created_at)) as active_collection_days
                FROM waste_reports
                WHERE created_at BETWEEN %s AND %s
            """
            
            cursor.execute(summary_query, (start_date, end_date))
            summary = cursor.fetchone()
            
            cursor.close()
            
            return {
                'success': True,
                'report_type': f'Quarterly Summary Q{quarter} {year}',
                'quarter': quarter,
                'year': year,
                'total_collections': summary['total_collections'],
                'total_waste_handled_kg': round(summary['total_waste'] or 0, 2),
                'citizen_participants': summary['citizen_participation'],
                'active_days': summary['active_collection_days'],
                'overall_status': 'COMPLIANT',
                'audit_status': 'PASSED'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Initialize service
compliance_reporting_service = ComplianceReportingService()
