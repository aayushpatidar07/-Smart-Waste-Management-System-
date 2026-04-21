"""Alert Response Insights Service
Analyzes alert lifecycles, severity response patterns, and hotspot bins.
"""

from datetime import datetime, timedelta
from models import Database


class AlertResponseInsightsService:
    """Service class for alert response analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_response_overview(self, days=30):
        """Get high-level alert response overview."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_alerts,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_alerts,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts,
                    AVG(CASE
                        WHEN resolved_at IS NOT NULL THEN TIMESTAMPDIFF(HOUR, created_at, resolved_at)
                        ELSE NULL
                    END) AS avg_resolution_hours
                FROM alerts
                WHERE created_at >= %s
                """,
                (start_date,)
            )
            row = cursor.fetchone() or {}

            total = row.get('total_alerts', 0) or 0
            resolved = row.get('resolved_alerts', 0) or 0
            resolution_rate = round((resolved / total) * 100, 1) if total else 0
            avg_resolution = round(row.get('avg_resolution_hours', 0) or 0, 1)

            return {
                'success': True,
                'period_days': days,
                'total_alerts': total,
                'active_alerts': row.get('active_alerts', 0) or 0,
                'acknowledged_alerts': row.get('acknowledged_alerts', 0) or 0,
                'resolved_alerts': resolved,
                'critical_alerts': row.get('critical_alerts', 0) or 0,
                'resolution_rate': resolution_rate,
                'avg_resolution_hours': avg_resolution,
                'response_status': 'Strong' if resolution_rate >= 80 else 'Watch' if resolution_rate >= 60 else 'Needs Improvement'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_severity_response(self, days=30):
        """Get response metrics by severity."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    severity,
                    COUNT(*) AS total_alerts,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
                    AVG(CASE
                        WHEN acknowledged_at IS NOT NULL THEN TIMESTAMPDIFF(MINUTE, created_at, acknowledged_at)
                        ELSE NULL
                    END) AS avg_ack_mins,
                    AVG(CASE
                        WHEN resolved_at IS NOT NULL THEN TIMESTAMPDIFF(HOUR, created_at, resolved_at)
                        ELSE NULL
                    END) AS avg_resolve_hours
                FROM alerts
                WHERE created_at >= %s
                GROUP BY severity
                ORDER BY FIELD(severity, 'critical', 'warning', 'info')
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            severities = []
            for row in rows:
                total = row.get('total_alerts', 0) or 0
                resolved = row.get('resolved_alerts', 0) or 0
                severities.append({
                    'severity': row.get('severity'),
                    'total_alerts': total,
                    'resolved_alerts': resolved,
                    'resolution_rate': round((resolved / total) * 100, 1) if total else 0,
                    'avg_ack_mins': round(row.get('avg_ack_mins', 0) or 0, 1),
                    'avg_resolve_hours': round(row.get('avg_resolve_hours', 0) or 0, 1)
                })

            return {'success': True, 'period_days': days, 'severity_metrics': severities}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_alert_hotspots(self, days=30):
        """Get bins with highest alert concentration."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    b.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    COUNT(a.alert_id) AS total_alerts,
                    SUM(CASE WHEN a.status <> 'resolved' THEN 1 ELSE 0 END) AS open_alerts,
                    SUM(CASE WHEN a.severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts
                FROM bins b
                JOIN alerts a ON a.bin_id = b.bin_id
                WHERE a.created_at >= %s
                GROUP BY b.bin_id, b.bin_code, b.location, b.zone
                ORDER BY critical_alerts DESC, open_alerts DESC, total_alerts DESC
                LIMIT 12
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            hotspots = []
            for row in rows:
                risk_score = (row.get('critical_alerts', 0) or 0) * 10 + (row.get('open_alerts', 0) or 0) * 4
                hotspots.append({
                    'bin_id': row.get('bin_id'),
                    'bin_code': row.get('bin_code'),
                    'location': row.get('location'),
                    'zone': row.get('zone'),
                    'total_alerts': row.get('total_alerts', 0) or 0,
                    'open_alerts': row.get('open_alerts', 0) or 0,
                    'critical_alerts': row.get('critical_alerts', 0) or 0,
                    'risk_score': risk_score
                })

            return {'success': True, 'period_days': days, 'hotspots': hotspots}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_response_recommendations(self, days=30):
        """Get recommendations to improve response quality."""
        try:
            overview = self.get_response_overview(days)
            severity = self.get_severity_response(days)
            hotspots = self.get_alert_hotspots(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('resolution_rate', 0) < 70:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Resolution Throughput',
                    'recommendation': f"Resolution rate is {overview.get('resolution_rate')}%. Increase closure throughput for active alerts.",
                    'action': 'Assign daily triage and closure targets per shift'
                })

            if overview.get('avg_resolution_hours', 0) > 24:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Response Time',
                    'recommendation': f"Average resolution time is {overview.get('avg_resolution_hours')} hours.",
                    'action': 'Escalate unresolved critical alerts after 12 hours'
                })

            if severity.get('success'):
                critical = next((s for s in severity.get('severity_metrics', []) if s.get('severity') == 'critical'), None)
                if critical and critical.get('resolution_rate', 0) < 80:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': 'Critical Alert Handling',
                        'recommendation': f"Critical alert resolution is {critical.get('resolution_rate')}%.",
                        'action': 'Reserve emergency response capacity for critical alerts'
                    })

            if hotspots.get('success') and hotspots.get('hotspots'):
                top = hotspots.get('hotspots')[0]
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': f"Hotspot Bin {top.get('bin_code')}",
                    'recommendation': f"{top.get('total_alerts')} alerts logged with risk score {top.get('risk_score')}.",
                    'action': 'Inspect sensor health and collection schedule at this location'
                })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Operations',
                    'recommendation': 'Alert response metrics are stable for the selected period.',
                    'action': 'Continue current response process and monitor weekly'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
