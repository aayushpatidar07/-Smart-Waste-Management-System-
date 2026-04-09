"""Real-time Monitoring and Alert Management Service
Handles real-time event detection, alert generation, notification routing,
and severity-based prioritization for the waste management system.
"""

from datetime import datetime, timedelta
import json
from models import Database

class RealTimeAlertsService:
    """Service for managing real-time alerts and monitoring critical events"""
    
    def __init__(self):
        self.db = Database()
    
    def create_alert(self, alert_type, severity, message, related_entity_id=None, related_entity_type=None):
        """
        Create a new alert in the system
        
        Args:
            alert_type: Type of alert (bin_overflow, vehicle_breakdown, missed_collection, data_anomaly)
            severity: Alert severity level (Critical, High, Medium, Low)
            message: Alert message
            related_entity_id: ID of related entity (bin, vehicle, route, etc.)
            related_entity_type: Type of related entity
        
        Returns:
            Created alert ID or error message
        """
        try:
            cursor = self.db.get_connection().cursor()
            
            timestamp = datetime.now()
            status = 'Active'
            
            query = """
                INSERT INTO alerts 
                (alert_type, severity, message, status, created_at, related_entity_id, related_entity_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                alert_type, severity, message, status, timestamp, 
                related_entity_id, related_entity_type
            ))
            self.db.get_connection().commit()
            
            alert_id = cursor.lastrowid
            cursor.close()
            
            return {
                'success': True,
                'alert_id': alert_id,
                'message': f'Alert created successfully with ID {alert_id}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_active_alerts(self, severity=None, alert_type=None, limit=100):
        """
        Retrieve active alerts with optional filtering
        
        Args:
            severity: Filter by severity level
            alert_type: Filter by alert type
            limit: Maximum number of alerts to return
        
        Returns:
            List of active alerts with details
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            query = "SELECT * FROM alerts WHERE status = 'Active'"
            params = []
            
            if severity:
                query += " AND severity = %s"
                params.append(severity)
            
            if alert_type:
                query += " AND alert_type = %s"
                params.append(alert_type)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            alerts = cursor.fetchall()
            
            # Format timestamps
            for alert in alerts:
                if alert['created_at']:
                    alert['created_at'] = alert['created_at'].isoformat()
                if alert['acknowledged_at']:
                    alert['acknowledged_at'] = alert['acknowledged_at'].isoformat()
            
            cursor.close()
            
            return {
                'success': True,
                'alert_count': len(alerts),
                'alerts': alerts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_alert_summary(self):
        """
        Get summary statistics of current alerts
        
        Returns:
            Alert counts by severity and type
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Count by severity
            severity_query = """
                SELECT severity, COUNT(*) as count 
                FROM alerts 
                WHERE status = 'Active'
                GROUP BY severity
            """
            cursor.execute(severity_query)
            severity_counts = cursor.fetchall()
            
            severity_stats = {}
            total_active = 0
            for row in severity_counts:
                severity_stats[row['severity']] = row['count']
                total_active += row['count']
            
            # Count by type
            type_query = """
                SELECT alert_type, COUNT(*) as count 
                FROM alerts 
                WHERE status = 'Active'
                GROUP BY alert_type
            """
            cursor.execute(type_query)
            type_counts = cursor.fetchall()
            
            type_stats = {}
            for row in type_counts:
                type_stats[row['alert_type']] = row['count']
            
            cursor.close()
            
            return {
                'success': True,
                'total_active_alerts': total_active,
                'by_severity': severity_stats,
                'by_type': type_stats,
                'requires_attention': severity_stats.get('Critical', 0) + severity_stats.get('High', 0)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def acknowledge_alert(self, alert_id, notes=None):
        """
        Acknowledge an alert (mark as being addressed)
        
        Args:
            alert_id: ID of alert to acknowledge
            notes: Optional acknowledgment notes
        
        Returns:
            Success status
        """
        try:
            cursor = self.db.get_connection().cursor()
            
            acknowledged_at = datetime.now()
            
            query = """
                UPDATE alerts 
                SET status = 'Acknowledged', acknowledged_at = %s, notes = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (acknowledged_at, notes, alert_id))
            self.db.get_connection().commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                return {'success': False, 'error': 'Alert not found'}
            
            cursor.close()
            
            return {
                'success': True,
                'message': f'Alert {alert_id} acknowledged'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def resolve_alert(self, alert_id, resolution_notes=None):
        """
        Resolve an alert (close it)
        
        Args:
            alert_id: ID of alert to resolve
            resolution_notes: Notes on how alert was resolved
        
        Returns:
            Success status
        """
        try:
            cursor = self.db.get_connection().cursor()
            
            resolved_at = datetime.now()
            
            query = """
                UPDATE alerts 
                SET status = 'Resolved', resolved_at = %s, resolution_notes = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (resolved_at, resolution_notes, alert_id))
            self.db.get_connection().commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                return {'success': False, 'error': 'Alert not found'}
            
            cursor.close()
            
            return {
                'success': True,
                'message': f'Alert {alert_id} resolved'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_alert_history(self, days=30, limit=200):
        """
        Retrieve historical alerts from the past N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of alerts to return
        
        Returns:
            Historical alerts with status and resolution info
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT * FROM alerts 
                WHERE created_at >= %s
                ORDER BY created_at DESC 
                LIMIT %s
            """
            
            cursor.execute(query, (cutoff_date, limit))
            alerts = cursor.fetchall()
            
            # Format timestamps
            for alert in alerts:
                if alert['created_at']:
                    alert['created_at'] = alert['created_at'].isoformat()
                if alert['acknowledged_at']:
                    alert['acknowledged_at'] = alert['acknowledged_at'].isoformat()
                if alert['resolved_at']:
                    alert['resolved_at'] = alert['resolved_at'].isoformat()
            
            cursor.close()
            
            return {
                'success': True,
                'alert_count': len(alerts),
                'period_days': days,
                'alerts': alerts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_alerts_by_entity(self, entity_type, entity_id, status='Active', limit=50):
        """
        Get all alerts related to a specific entity
        
        Args:
            entity_type: Type of entity (bin, vehicle, route, user)
            entity_id: ID of the entity
            status: Status filter (Active, Acknowledged, Resolved, all)
            limit: Maximum alerts to return
        
        Returns:
            Alerts related to the entity
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            if status == 'all':
                query = """
                    SELECT * FROM alerts 
                    WHERE related_entity_type = %s AND related_entity_id = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                """
                cursor.execute(query, (entity_type, entity_id, limit))
            else:
                query = """
                    SELECT * FROM alerts 
                    WHERE related_entity_type = %s AND related_entity_id = %s AND status = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                """
                cursor.execute(query, (entity_type, entity_id, status, limit))
            
            alerts = cursor.fetchall()
            
            # Format timestamps
            for alert in alerts:
                if alert['created_at']:
                    alert['created_at'] = alert['created_at'].isoformat()
                if alert['acknowledged_at']:
                    alert['acknowledged_at'] = alert['acknowledged_at'].isoformat()
            
            cursor.close()
            
            return {
                'success': True,
                'alert_count': len(alerts),
                'entity_type': entity_type,
                'entity_id': entity_id,
                'alerts': alerts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_critical_events(self, hours=24):
        """
        Get critical and high-priority events from the past N hours
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Critical/High severity alerts requiring immediate attention
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = """
                SELECT * FROM alerts 
                WHERE created_at >= %s 
                AND severity IN ('Critical', 'High')
                ORDER BY created_at DESC 
                LIMIT 100
            """
            
            cursor.execute(query, (cutoff_time,))
            alerts = cursor.fetchall()
            
            # Format timestamps and categorize
            critical_count = 0
            high_count = 0
            for alert in alerts:
                if alert['created_at']:
                    alert['created_at'] = alert['created_at'].isoformat()
                if alert['severity'] == 'Critical':
                    critical_count += 1
                else:
                    high_count += 1
            
            cursor.close()
            
            return {
                'success': True,
                'critical_count': critical_count,
                'high_count': high_count,
                'total_urgent': critical_count + high_count,
                'period_hours': hours,
                'alerts': alerts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Initialize service
real_time_alerts_service = RealTimeAlertsService()
