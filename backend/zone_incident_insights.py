"""Zone Incident Insights Service
Analyzes incident volume, severity, and resolution pressure by zone.
"""

from datetime import datetime, timedelta
from models import Database


class ZoneIncidentInsightsService:
    """Service for zone-level incident analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_incident_overview(self, days=30):
        """Get overall incident pressure metrics."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN status IN ('pending', 'acknowledged') THEN 1 ELSE 0 END) AS open_reports,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) AS urgent_reports
                FROM waste_reports
                WHERE reported_at >= %s
                """,
                (start_date,)
            )
            reports = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_alerts,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN severity = 'critical' AND status = 'active' THEN 1 ELSE 0 END) AS critical_active_alerts
                FROM alerts
                WHERE created_at >= %s
                """,
                (start_date,)
            )
            alerts = cursor.fetchone() or {}

            total_reports = reports.get('total_reports', 0) or 0
            resolved_reports = reports.get('resolved_reports', 0) or 0
            resolution_rate = round((resolved_reports / total_reports) * 100, 1) if total_reports else 0

            incident_score = min(100, round((reports.get('open_reports', 0) or 0) * 2.5 + (alerts.get('critical_active_alerts', 0) or 0) * 6, 1))
            incident_status = 'High' if incident_score >= 70 else 'Medium' if incident_score >= 40 else 'Low'

            return {
                'success': True,
                'period_days': days,
                'incident_score': incident_score,
                'incident_status': incident_status,
                'total_reports': total_reports,
                'open_reports': reports.get('open_reports', 0) or 0,
                'resolved_reports': resolved_reports,
                'urgent_reports': reports.get('urgent_reports', 0) or 0,
                'resolution_rate': resolution_rate,
                'total_alerts': alerts.get('total_alerts', 0) or 0,
                'active_alerts': alerts.get('active_alerts', 0) or 0,
                'critical_active_alerts': alerts.get('critical_active_alerts', 0) or 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_zone_incident_ranking(self, days=30):
        """Get per-zone incident ranking."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    b.zone,
                    COUNT(DISTINCT b.bin_id) AS total_bins,
                    COUNT(DISTINCT CASE WHEN wr.report_id IS NOT NULL THEN wr.report_id END) AS reports,
                    COUNT(DISTINCT CASE WHEN wr.status IN ('pending', 'acknowledged') THEN wr.report_id END) AS open_reports,
                    COUNT(DISTINCT CASE WHEN wr.priority IN ('high', 'critical') THEN wr.report_id END) AS urgent_reports,
                    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.alert_id END) AS active_alerts,
                    COUNT(DISTINCT CASE WHEN a.severity = 'critical' AND a.status = 'active' THEN a.alert_id END) AS critical_alerts
                FROM bins b
                LEFT JOIN waste_reports wr ON wr.bin_id = b.bin_id AND wr.reported_at >= %s
                LEFT JOIN alerts a ON a.bin_id = b.bin_id AND a.created_at >= %s
                WHERE b.zone IS NOT NULL AND b.zone <> ''
                GROUP BY b.zone
                ORDER BY urgent_reports DESC, open_reports DESC, critical_alerts DESC
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                points = (row.get('urgent_reports', 0) or 0) * 5 + (row.get('open_reports', 0) or 0) * 2 + (row.get('critical_alerts', 0) or 0) * 6
                risk = 'High' if points >= 35 else 'Medium' if points >= 15 else 'Low'
                zones.append({
                    'zone': row.get('zone'),
                    'total_bins': row.get('total_bins', 0) or 0,
                    'reports': row.get('reports', 0) or 0,
                    'open_reports': row.get('open_reports', 0) or 0,
                    'urgent_reports': row.get('urgent_reports', 0) or 0,
                    'active_alerts': row.get('active_alerts', 0) or 0,
                    'critical_alerts': row.get('critical_alerts', 0) or 0,
                    'incident_points': points,
                    'risk_level': risk
                })

            return {'success': True, 'period_days': days, 'zones': zones}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_incident_trends(self, days=30):
        """Get daily incident trends."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    DATE(reported_at) AS day,
                    COUNT(*) AS reports,
                    SUM(CASE WHEN status IN ('pending', 'acknowledged') THEN 1 ELSE 0 END) AS open_reports,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) AS urgent_reports
                FROM waste_reports
                WHERE reported_at >= %s
                GROUP BY DATE(reported_at)
                ORDER BY day DESC
                LIMIT 14
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            trends = []
            for row in rows:
                reports = row.get('reports', 0) or 0
                open_reports = row.get('open_reports', 0) or 0
                trends.append({
                    'day': str(row.get('day')),
                    'reports': reports,
                    'open_reports': open_reports,
                    'urgent_reports': row.get('urgent_reports', 0) or 0,
                    'open_rate': round((open_reports / reports) * 100, 1) if reports else 0
                })

            return {'success': True, 'period_days': days, 'trends': trends}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_incident_recommendations(self, days=30):
        """Get recommendations based on incident pressure."""
        try:
            overview = self.get_incident_overview(days)
            zones = self.get_zone_incident_ranking(days)
            trends = self.get_incident_trends(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('incident_score', 0) >= 60:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Incident Backlog',
                    'recommendation': f"Incident score is {overview.get('incident_score')} with {overview.get('open_reports')} open reports.",
                    'action': 'Run focused backlog-clearance shifts in top-risk zones'
                })

            if zones.get('success'):
                hot_zone = next((z for z in zones.get('zones', []) if z.get('risk_level') == 'High'), None)
                if hot_zone:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': f"Zone {hot_zone.get('zone')}",
                        'recommendation': f"Zone has {hot_zone.get('urgent_reports')} urgent reports and {hot_zone.get('critical_alerts')} critical alerts.",
                        'action': 'Increase collection pass frequency and enforce rapid alert triage'
                    })

            if trends.get('success') and trends.get('trends'):
                latest = trends.get('trends')[0]
                if latest.get('open_rate', 0) > 50:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': 'Recent Trend',
                        'recommendation': f"Latest open-rate is {latest.get('open_rate')}%.",
                        'action': 'Improve same-day acknowledgment and closure workflow'
                    })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Stability',
                    'recommendation': 'Zone incident profile is stable in the selected period.',
                    'action': 'Continue weekly monitoring and preventive maintenance'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
