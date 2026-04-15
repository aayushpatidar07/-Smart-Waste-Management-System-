"""Waste Audit Insights Service
Provides audit and compliance visibility for waste reports and resolution patterns.
"""

from models import Database


class WasteAuditInsightsService:
    """Service for waste audit dashboards and trend analysis."""

    def __init__(self):
        self.db = Database()

    def get_audit_summary(self, days=30):
        """Return high-level audit summary for the selected period."""
        try:
            query = """
                SELECT
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_reports,
                    SUM(CASE WHEN status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_reports,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN priority = 'critical' THEN 1 ELSE 0 END) AS critical_reports,
                    SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS high_reports,
                    ROUND(AVG(CASE WHEN resolved_at IS NOT NULL
                        THEN TIMESTAMPDIFF(HOUR, reported_at, resolved_at) END), 1) AS avg_resolution_hours
                FROM waste_reports
                WHERE reported_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            rows = self.db.execute_query(query, (days,)) or []
            stats = rows[0] if rows else {}

            total = int(stats.get('total_reports') or 0)
            resolved = int(stats.get('resolved_reports') or 0)
            pending = int(stats.get('pending_reports') or 0)
            acknowledged = int(stats.get('acknowledged_reports') or 0)
            critical = int(stats.get('critical_reports') or 0)
            high = int(stats.get('high_reports') or 0)

            resolution_rate = round((resolved * 100.0 / total), 1) if total else 0.0
            backlog_pressure = pending + acknowledged + (critical * 2) + high
            audit_score = max(0.0, min(100.0, round((resolution_rate * 0.7) + (max(0.0, 100.0 - backlog_pressure * 3.0) * 0.3), 1)))

            if audit_score >= 85:
                status = 'PASS'
            elif audit_score >= 70:
                status = 'WATCH'
            else:
                status = 'FAIL'

            return {
                'success': True,
                'period_days': days,
                'total_reports': total,
                'pending_reports': pending,
                'acknowledged_reports': acknowledged,
                'resolved_reports': resolved,
                'critical_reports': critical,
                'high_reports': high,
                'resolution_rate_percent': resolution_rate,
                'avg_resolution_hours': float(stats.get('avg_resolution_hours') or 0),
                'audit_score': audit_score,
                'status': status,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_zone_audit_ranking(self, days=30, limit=10):
        """Return zone-level audit ranking based on unresolved waste reports."""
        try:
            query = """
                SELECT
                    COALESCE(b.zone, 'Unassigned') AS zone,
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN wr.status = 'pending' THEN 1 ELSE 0 END) AS pending_reports,
                    SUM(CASE WHEN wr.status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_reports,
                    SUM(CASE WHEN wr.status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN wr.priority = 'critical' THEN 1 ELSE 0 END) AS critical_reports,
                    ROUND(AVG(CASE WHEN wr.resolved_at IS NOT NULL
                        THEN TIMESTAMPDIFF(HOUR, wr.reported_at, wr.resolved_at) END), 1) AS avg_resolution_hours
                FROM waste_reports wr
                LEFT JOIN bins b ON wr.bin_id = b.bin_id
                WHERE wr.reported_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY COALESCE(b.zone, 'Unassigned')
                ORDER BY pending_reports DESC, critical_reports DESC, total_reports DESC
                LIMIT %s
            """
            zones = self.db.execute_query(query, (days, limit)) or []

            for zone in zones:
                total = int(zone.get('total_reports') or 0)
                resolved = int(zone.get('resolved_reports') or 0)
                pending = int(zone.get('pending_reports') or 0)
                critical = int(zone.get('critical_reports') or 0)
                resolution_rate = round((resolved * 100.0 / total), 1) if total else 0.0
                risk_score = round(min(100.0, (pending * 10.0) + (critical * 15.0) + (100.0 - resolution_rate)), 1)
                zone['resolution_rate_percent'] = resolution_rate
                zone['risk_score'] = risk_score

            return {
                'success': True,
                'period_days': days,
                'zones': zones,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_resolution_timeline(self, days=30):
        """Return daily resolution timeline for waste reports."""
        try:
            query = """
                SELECT
                    DATE(reported_at) AS report_day,
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN status IN ('pending', 'acknowledged') THEN 1 ELSE 0 END) AS open_reports
                FROM waste_reports
                WHERE reported_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(reported_at)
                ORDER BY report_day ASC
            """
            timeline = self.db.execute_query(query, (days,)) or []
            return {
                'success': True,
                'period_days': days,
                'timeline': timeline,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_backlog_items(self, days=30, limit=10):
        """Return the most important unresolved audit items."""
        try:
            query = """
                SELECT
                    wr.report_id,
                    wr.report_type,
                    wr.priority,
                    wr.status,
                    wr.location,
                    wr.description,
                    wr.reported_at,
                    COALESCE(b.zone, 'Unassigned') AS zone
                FROM waste_reports wr
                LEFT JOIN bins b ON wr.bin_id = b.bin_id
                WHERE wr.reported_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  AND wr.status IN ('pending', 'acknowledged')
                ORDER BY FIELD(wr.priority, 'critical', 'high', 'medium', 'low'), wr.reported_at ASC
                LIMIT %s
            """
            backlog = self.db.execute_query(query, (days, limit)) or []
            return {
                'success': True,
                'period_days': days,
                'backlog': backlog,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_audit_recommendations(self, days=30):
        """Return audit improvement recommendations."""
        try:
            summary = self.get_audit_summary(days)
            zones = self.get_zone_audit_ranking(days, 5)
            backlog = self.get_backlog_items(days, 5)

            if not summary.get('success'):
                return {'success': False, 'error': 'Unable to build recommendations'}

            recs = []
            score = float(summary.get('audit_score') or 0)
            if score < 75:
                recs.append({'priority': 'High', 'title': 'Reduce Audit Backlog', 'message': 'Audit score is below target. Focus on pending and acknowledged waste reports.'})
            if int(summary.get('critical_reports') or 0) > 0:
                recs.append({'priority': 'High', 'title': 'Escalate Critical Reports', 'message': 'Critical reports remain open. Assign them immediately to the response team.'})
            if float(summary.get('avg_resolution_hours') or 0) > 24:
                recs.append({'priority': 'Medium', 'title': 'Improve Resolution Time', 'message': 'Average resolution time exceeds 24 hours. Review the escalation workflow.'})

            if zones.get('zones'):
                worst_zone = zones['zones'][0]
                if float(worst_zone.get('risk_score') or 0) >= 60:
                    recs.append({'priority': 'High', 'title': 'Fix Highest-Risk Zone', 'message': f"{worst_zone.get('zone')} has the highest unresolved backlog and should be audited first."})

            if backlog.get('backlog'):
                top_item = backlog['backlog'][0]
                recs.append({'priority': 'Low', 'title': 'Triage Oldest Open Item', 'message': f"Oldest open item: {top_item.get('report_type')} in {top_item.get('zone')} reported on {top_item.get('reported_at')}"})

            return {
                'success': True,
                'period_days': days,
                'recommendations': recs,
                'total_recommendations': len(recs),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
