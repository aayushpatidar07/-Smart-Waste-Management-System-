"""Incident Response Metrics Service
Provides operational metrics for incident response speed, SLA compliance,
and response workload distribution.
"""

from models import Database


class IncidentResponseMetricsService:
    """Service for incident response and SLA analytics."""

    def __init__(self):
        self.db = Database()

    def get_response_summary(self, days=30):
        """Return response summary for the selected period."""
        try:
            alert_query = """
                SELECT
                    COUNT(*) AS total_alerts,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_alerts,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
                    ROUND(AVG(CASE WHEN acknowledged_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, created_at, acknowledged_at) END), 1)
                        AS avg_ack_minutes,
                    ROUND(AVG(CASE WHEN resolved_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, created_at, resolved_at) END), 1)
                        AS avg_resolution_minutes
                FROM alerts
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            alert_stats = self.db.execute_query(alert_query, (days,))
            alert_stats = alert_stats[0] if alert_stats else {}

            report_query = """
                SELECT
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_reports,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports
                FROM waste_reports
                WHERE reported_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            report_stats = self.db.execute_query(report_query, (days,))
            report_stats = report_stats[0] if report_stats else {}

            total_alerts = int(alert_stats.get('total_alerts') or 0)
            resolved_alerts = int(alert_stats.get('resolved_alerts') or 0)
            closure_rate = round((resolved_alerts * 100.0 / total_alerts), 1) if total_alerts else 0.0

            return {
                'success': True,
                'period_days': days,
                'alerts': {
                    'total': total_alerts,
                    'active': int(alert_stats.get('active_alerts') or 0),
                    'acknowledged': int(alert_stats.get('acknowledged_alerts') or 0),
                    'resolved': resolved_alerts,
                    'closure_rate_percent': closure_rate,
                    'avg_ack_minutes': float(alert_stats.get('avg_ack_minutes') or 0),
                    'avg_resolution_minutes': float(alert_stats.get('avg_resolution_minutes') or 0),
                },
                'waste_reports': {
                    'total': int(report_stats.get('total_reports') or 0),
                    'pending': int(report_stats.get('pending_reports') or 0),
                    'resolved': int(report_stats.get('resolved_reports') or 0),
                },
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_severity_breakdown(self, days=30):
        """Return alert severity distribution and active backlog."""
        try:
            query = """
                SELECT
                    severity,
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_count,
                    ROUND(AVG(CASE WHEN acknowledged_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, created_at, acknowledged_at) END), 1)
                        AS avg_ack_minutes
                FROM alerts
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY severity
                ORDER BY FIELD(severity, 'critical', 'warning', 'info')
            """
            rows = self.db.execute_query(query, (days,)) or []

            total_alerts = sum(int(row.get('total') or 0) for row in rows)
            for row in rows:
                row['share_percent'] = round((int(row.get('total') or 0) * 100.0 / total_alerts), 1) if total_alerts else 0.0

            return {
                'success': True,
                'period_days': days,
                'total_alerts': total_alerts,
                'severity_breakdown': rows,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_sla_compliance(self, days=30):
        """Return SLA compliance against severity-based acknowledgment thresholds."""
        try:
            query = """
                SELECT
                    severity,
                    COUNT(*) AS total,
                    SUM(
                        CASE
                            WHEN acknowledged_at IS NOT NULL AND TIMESTAMPDIFF(MINUTE, created_at, acknowledged_at) <=
                                CASE
                                    WHEN severity = 'critical' THEN 30
                                    WHEN severity = 'warning' THEN 120
                                    ELSE 240
                                END
                            THEN 1
                            ELSE 0
                        END
                    ) AS within_sla,
                    ROUND(AVG(CASE WHEN acknowledged_at IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, created_at, acknowledged_at) END), 1)
                        AS avg_ack_minutes
                FROM alerts
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY severity
                ORDER BY FIELD(severity, 'critical', 'warning', 'info')
            """
            rows = self.db.execute_query(query, (days,)) or []

            total = 0
            within = 0
            for row in rows:
                row_total = int(row.get('total') or 0)
                row_within = int(row.get('within_sla') or 0)
                row['sla_percent'] = round((row_within * 100.0 / row_total), 1) if row_total else 0.0
                row['target_minutes'] = 30 if row.get('severity') == 'critical' else (120 if row.get('severity') == 'warning' else 240)
                total += row_total
                within += row_within

            overall = round((within * 100.0 / total), 1) if total else 0.0
            return {
                'success': True,
                'period_days': days,
                'overall_sla_percent': overall,
                'tracked_alerts': total,
                'within_sla': within,
                'by_severity': rows,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_response_trend(self, days=14):
        """Return day-wise incident creation and closure trend."""
        try:
            query = """
                SELECT
                    DATE(created_at) AS day,
                    COUNT(*) AS created_count,
                    SUM(CASE WHEN status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_count,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_count,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_count
                FROM alerts
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            """
            trend = self.db.execute_query(query, (days,)) or []
            return {
                'success': True,
                'period_days': days,
                'trend': trend,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_response_workload(self, days=30):
        """Return top responders by acknowledgments and report resolutions."""
        try:
            ack_query = """
                SELECT
                    acknowledged_by AS user_id,
                    COUNT(*) AS acknowledged_count
                FROM alerts
                WHERE acknowledged_by IS NOT NULL
                  AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY acknowledged_by
            """
            ack_rows = self.db.execute_query(ack_query, (days,)) or []

            resolved_query = """
                SELECT
                    resolved_by AS user_id,
                    COUNT(*) AS resolved_reports
                FROM waste_reports
                WHERE resolved_by IS NOT NULL
                  AND reported_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY resolved_by
            """
            resolved_rows = self.db.execute_query(resolved_query, (days,)) or []

            users_query = """
                SELECT user_id, full_name, role
                FROM users
                WHERE role IN ('admin', 'staff')
            """
            users = self.db.execute_query(users_query) or []
            users_map = {int(user['user_id']): user for user in users}

            workload = {}
            for row in ack_rows:
                user_id = int(row['user_id'])
                workload[user_id] = workload.get(user_id, {'acknowledged_count': 0, 'resolved_reports': 0})
                workload[user_id]['acknowledged_count'] = int(row.get('acknowledged_count') or 0)

            for row in resolved_rows:
                user_id = int(row['user_id'])
                workload[user_id] = workload.get(user_id, {'acknowledged_count': 0, 'resolved_reports': 0})
                workload[user_id]['resolved_reports'] = int(row.get('resolved_reports') or 0)

            leaderboard = []
            for user_id, metrics in workload.items():
                if user_id not in users_map:
                    continue
                user = users_map[user_id]
                total_actions = metrics['acknowledged_count'] + metrics['resolved_reports']
                leaderboard.append({
                    'user_id': user_id,
                    'name': user['full_name'],
                    'role': user['role'],
                    'acknowledged_count': metrics['acknowledged_count'],
                    'resolved_reports': metrics['resolved_reports'],
                    'total_actions': total_actions,
                })

            leaderboard.sort(key=lambda item: item['total_actions'], reverse=True)

            return {
                'success': True,
                'period_days': days,
                'workload': leaderboard[:10],
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_response_health_score(self, days=30):
        """Return a single response health score from SLA and closure metrics."""
        try:
            summary = self.get_response_summary(days)
            sla = self.get_sla_compliance(days)

            if not summary.get('success') or not sla.get('success'):
                return {'success': False, 'error': 'Unable to calculate incident health score'}

            closure = float(summary['alerts'].get('closure_rate_percent') or 0)
            avg_ack = float(summary['alerts'].get('avg_ack_minutes') or 0)
            sla_percent = float(sla.get('overall_sla_percent') or 0)

            ack_component = max(0.0, 100.0 - min(avg_ack, 300.0) / 3.0)
            score = round((closure * 0.45) + (sla_percent * 0.40) + (ack_component * 0.15), 1)

            if score >= 85:
                status = 'Healthy'
            elif score >= 70:
                status = 'Watch'
            else:
                status = 'At Risk'

            return {
                'success': True,
                'period_days': days,
                'health_score': score,
                'status': status,
                'components': {
                    'closure_rate_percent': round(closure, 1),
                    'sla_percent': round(sla_percent, 1),
                    'ack_speed_component': round(ack_component, 1),
                },
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
