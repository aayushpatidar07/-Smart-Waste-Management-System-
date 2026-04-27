"""Alert Aging Insights Service
Tracks how long alerts stay open and where backlog pressure is building.
"""

from datetime import datetime, timedelta
from models import Database


class AlertAgingInsightsService:
    """Service for alert aging analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        connection = self.db.connect()
        if not connection:
            raise Exception('Unable to connect to database')
        return connection

    def get_aging_overview(self, days=30):
        """Get overall alert aging snapshot."""
        connection = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_alerts,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_alerts,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts,
                    AVG(CASE WHEN status <> 'resolved' THEN TIMESTAMPDIFF(HOUR, created_at, NOW()) END) AS avg_open_hours
                FROM alerts
                WHERE created_at >= %s
                """,
                (start_date,)
            )
            row = cursor.fetchone() or {}

            total_alerts = row.get('total_alerts', 0) or 0
            active_alerts = row.get('active_alerts', 0) or 0
            resolved_alerts = row.get('resolved_alerts', 0) or 0
            open_rate = round(((active_alerts + (row.get('acknowledged_alerts', 0) or 0)) / total_alerts) * 100, 1) if total_alerts else 0
            avg_open_hours = round(row.get('avg_open_hours', 0) or 0, 1)
            aging_score = min(100, round(open_rate * 0.6 + min(avg_open_hours, 168) / 1.68 * 0.4, 1))
            aging_status = 'Healthy' if aging_score < 40 else 'Watch' if aging_score < 70 else 'Critical'

            return {
                'success': True,
                'period_days': days,
                'aging_score': aging_score,
                'aging_status': aging_status,
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'acknowledged_alerts': row.get('acknowledged_alerts', 0) or 0,
                'resolved_alerts': resolved_alerts,
                'critical_alerts': row.get('critical_alerts', 0) or 0,
                'open_rate': open_rate,
                'avg_open_hours': avg_open_hours
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_age_buckets(self, days=30):
        """Get alerts grouped by age buckets."""
        connection = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    CASE
                        WHEN TIMESTAMPDIFF(HOUR, created_at, NOW()) < 6 THEN '0-6 hrs'
                        WHEN TIMESTAMPDIFF(HOUR, created_at, NOW()) < 24 THEN '6-24 hrs'
                        WHEN TIMESTAMPDIFF(HOUR, created_at, NOW()) < 72 THEN '1-3 days'
                        WHEN TIMESTAMPDIFF(HOUR, created_at, NOW()) < 168 THEN '3-7 days'
                        ELSE '7+ days'
                    END AS age_bucket,
                    COUNT(*) AS alert_count,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts
                FROM alerts
                WHERE created_at >= %s
                GROUP BY age_bucket
                ORDER BY FIELD(age_bucket, '0-6 hrs', '6-24 hrs', '1-3 days', '3-7 days', '7+ days')
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            buckets = []
            for row in rows:
                alert_count = row.get('alert_count', 0) or 0
                buckets.append({
                    'age_bucket': row.get('age_bucket'),
                    'alert_count': alert_count,
                    'active_alerts': row.get('active_alerts', 0) or 0,
                    'critical_alerts': row.get('critical_alerts', 0) or 0,
                    'bucket_share': round(alert_count / max(1, sum(r.get('alert_count', 0) or 0 for r in rows)) * 100, 1)
                })

            return {'success': True, 'period_days': days, 'age_buckets': buckets}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_old_active_alerts(self, days=30):
        """Get alerts that have remained active for a long time."""
        connection = None
        cursor = None
        try:
            connection = self._connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    a.alert_id,
                    a.alert_type,
                    a.severity,
                    a.status,
                    a.created_at,
                    TIMESTAMPDIFF(HOUR, a.created_at, NOW()) AS age_hours,
                    b.bin_code,
                    b.location,
                    b.zone,
                    u.full_name AS acknowledged_by_name
                FROM alerts a
                LEFT JOIN bins b ON b.bin_id = a.bin_id
                LEFT JOIN users u ON u.user_id = a.acknowledged_by
                WHERE a.status IN ('active', 'acknowledged')
                  AND a.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY age_hours DESC, a.severity DESC, a.created_at ASC
                LIMIT 15
                """,
                (days,)
            )
            rows = cursor.fetchall()

            alerts = []
            for row in rows:
                alerts.append({
                    'alert_id': row.get('alert_id'),
                    'alert_type': row.get('alert_type'),
                    'severity': row.get('severity'),
                    'status': row.get('status'),
                    'age_hours': row.get('age_hours', 0) or 0,
                    'bin_code': row.get('bin_code'),
                    'location': row.get('location'),
                    'zone': row.get('zone'),
                    'acknowledged_by_name': row.get('acknowledged_by_name')
                })

            return {'success': True, 'period_days': days, 'alerts': alerts}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_aging_recommendations(self, days=30):
        """Get recommendations to reduce alert aging."""
        try:
            overview = self.get_aging_overview(days)
            buckets = self.get_age_buckets(days)
            old_alerts = self.get_old_active_alerts(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('aging_score', 0) >= 70:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Backlog Pressure',
                    'recommendation': f"Alert aging score is {overview.get('aging_score')} with {overview.get('active_alerts')} active alerts.",
                    'action': 'Prioritize oldest active alerts in the next response cycle'
                })

            if buckets.get('success'):
                old_bucket = next((b for b in buckets.get('age_buckets', []) if b.get('age_bucket') in ['3-7 days', '7+ days']), None)
                if old_bucket and old_bucket.get('alert_count', 0) > 0:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': 'Aging Alerts',
                        'recommendation': f"{old_bucket.get('alert_count')} alerts fall in the {old_bucket.get('age_bucket')} bucket.",
                        'action': 'Escalate long-pending alerts and assign closure ownership'
                    })

            if old_alerts.get('success') and old_alerts.get('alerts'):
                top = old_alerts.get('alerts')[0]
                recommendations.append({
                    'priority': 'HIGH',
                    'category': f"Alert {top.get('alert_id')}",
                    'recommendation': f"Longest open alert is {top.get('age_hours')} hours old at {top.get('zone') or 'unknown zone'}.",
                    'action': 'Inspect bin and close or reclassify the alert immediately'
                })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Operations',
                    'recommendation': 'Alert aging metrics are under control for the selected period.',
                    'action': 'Continue standard monitoring and closure cadence'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
