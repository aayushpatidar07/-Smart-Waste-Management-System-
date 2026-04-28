"""Maintenance Alert Insights Service
Tracks maintenance-related alerts, their aging, and resolution pressure.
"""

from datetime import datetime, timedelta
from models import Database


class MaintenanceAlertInsightsService:
    """Service for maintenance alert analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_alert_overview(self, days=30):
        """Return overall maintenance alert metrics."""
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
                WHERE alert_type = 'maintenance_required'
                  AND created_at >= %s
                """,
                (start_date,)
            )
            row = cursor.fetchone() or {}

            total = row.get('total_alerts', 0) or 0
            resolved = row.get('resolved_alerts', 0) or 0
            open_alerts = (row.get('active_alerts', 0) or 0) + (row.get('acknowledged_alerts', 0) or 0)
            resolution_rate = round((resolved / total) * 100, 1) if total else 0
            avg_open_hours = round(row.get('avg_open_hours', 0) or 0, 1)
            pressure_score = min(100, round(open_alerts * 4 + avg_open_hours / 2 + (row.get('critical_alerts', 0) or 0) * 10, 1))
            pressure_status = 'Low' if pressure_score < 35 else 'Medium' if pressure_score < 70 else 'High'

            return {
                'success': True,
                'period_days': days,
                'pressure_score': pressure_score,
                'pressure_status': pressure_status,
                'total_alerts': total,
                'active_alerts': row.get('active_alerts', 0) or 0,
                'acknowledged_alerts': row.get('acknowledged_alerts', 0) or 0,
                'resolved_alerts': resolved,
                'critical_alerts': row.get('critical_alerts', 0) or 0,
                'resolution_rate': resolution_rate,
                'avg_open_hours': avg_open_hours
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_aging_bins(self, days=30):
        """Get bins with the oldest maintenance alerts."""
        connection = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    b.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    COUNT(a.alert_id) AS alert_count,
                    SUM(CASE WHEN a.status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN a.status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_alerts,
                    SUM(CASE WHEN a.severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts,
                    AVG(CASE WHEN a.status <> 'resolved' THEN TIMESTAMPDIFF(HOUR, a.created_at, NOW()) END) AS avg_open_hours
                FROM alerts a
                LEFT JOIN bins b ON b.bin_id = a.bin_id
                WHERE a.alert_type = 'maintenance_required'
                  AND a.created_at >= %s
                GROUP BY b.bin_id, b.bin_code, b.location, b.zone
                ORDER BY active_alerts DESC, critical_alerts DESC, avg_open_hours DESC
                LIMIT 15
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            bins = []
            for row in rows:
                bins.append({
                    'bin_id': row.get('bin_id'),
                    'bin_code': row.get('bin_code'),
                    'location': row.get('location'),
                    'zone': row.get('zone'),
                    'alert_count': row.get('alert_count', 0) or 0,
                    'active_alerts': row.get('active_alerts', 0) or 0,
                    'acknowledged_alerts': row.get('acknowledged_alerts', 0) or 0,
                    'critical_alerts': row.get('critical_alerts', 0) or 0,
                    'avg_open_hours': round(row.get('avg_open_hours', 0) or 0, 1)
                })

            return {'success': True, 'period_days': days, 'bins': bins}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_zone_alert_profile(self, days=30):
        """Get maintenance alert profile by zone."""
        connection = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    b.zone,
                    COUNT(a.alert_id) AS total_alerts,
                    SUM(CASE WHEN a.status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN a.status = 'acknowledged' THEN 1 ELSE 0 END) AS acknowledged_alerts,
                    SUM(CASE WHEN a.severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts,
                    AVG(CASE WHEN a.status <> 'resolved' THEN TIMESTAMPDIFF(HOUR, a.created_at, NOW()) END) AS avg_open_hours
                FROM alerts a
                LEFT JOIN bins b ON b.bin_id = a.bin_id
                WHERE a.alert_type = 'maintenance_required'
                  AND a.created_at >= %s
                  AND b.zone IS NOT NULL
                  AND b.zone <> ''
                GROUP BY b.zone
                ORDER BY total_alerts DESC, critical_alerts DESC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                total = row.get('total_alerts', 0) or 0
                zones.append({
                    'zone': row.get('zone'),
                    'total_alerts': total,
                    'active_alerts': row.get('active_alerts', 0) or 0,
                    'acknowledged_alerts': row.get('acknowledged_alerts', 0) or 0,
                    'critical_alerts': row.get('critical_alerts', 0) or 0,
                    'avg_open_hours': round(row.get('avg_open_hours', 0) or 0, 1),
                    'open_rate': round(((row.get('active_alerts', 0) or 0) + (row.get('acknowledged_alerts', 0) or 0)) / total * 100, 1) if total else 0
                })

            return {'success': True, 'period_days': days, 'zones': zones}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_maintenance_alert_recommendations(self, days=30):
        """Get recommendations for maintenance alert management."""
        try:
            overview = self.get_alert_overview(days)
            bins = self.get_aging_bins(days)
            zones = self.get_zone_alert_profile(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('pressure_score', 0) >= 70:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Alert Pressure',
                    'recommendation': f"Maintenance alert pressure score is {overview.get('pressure_score')}.",
                    'action': 'Clear the oldest active maintenance alerts first'
                })

            if bins.get('success') and bins.get('bins'):
                top_bin = bins.get('bins')[0]
                recommendations.append({
                    'priority': 'HIGH',
                    'category': f"Bin {top_bin.get('bin_code')}",
                    'recommendation': f"Bin has {top_bin.get('alert_count')} maintenance alerts with {top_bin.get('avg_open_hours')} avg open hours.",
                    'action': 'Inspect the bin hardware and maintenance logs immediately'
                })

            if zones.get('success'):
                high_zone = next((z for z in zones.get('zones', []) if z.get('critical_alerts', 0) > 0), None)
                if high_zone:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': f"Zone {high_zone.get('zone')}",
                        'recommendation': f"Zone has {high_zone.get('critical_alerts')} critical maintenance alerts.",
                        'action': 'Assign an urgent maintenance sweep to this zone'
                    })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Operations',
                    'recommendation': 'Maintenance alert pressure is under control.',
                    'action': 'Continue routine inspection and closure workflow'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
