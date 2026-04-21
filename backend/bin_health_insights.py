"""Bin Health Insights Service
Provides health, anomaly, and maintenance-risk analytics for smart bins.
"""

from datetime import datetime, timedelta
from models import Database


class BinHealthInsightsService:
    """Service class for bin health analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_health_overview(self, days=14):
        """Get system-level bin health overview."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_bins,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_bins,
                    SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) AS maintenance_bins,
                    AVG(waste_level) AS avg_fill_level,
                    SUM(CASE WHEN waste_level >= 80 THEN 1 ELSE 0 END) AS high_fill_bins
                FROM bins
                """
            )
            bins = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS sensor_events,
                    SUM(CASE WHEN sensor_status = 'warning' THEN 1 ELSE 0 END) AS warning_events,
                    SUM(CASE WHEN sensor_status = 'error' THEN 1 ELSE 0 END) AS error_events,
                    AVG(temperature) AS avg_temp,
                    AVG(humidity) AS avg_humidity
                FROM sensor_logs
                WHERE timestamp >= %s
                """,
                (start_date,)
            )
            sensors = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS active_alerts,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts
                FROM alerts
                WHERE status = 'active'
                """
            )
            alerts = cursor.fetchone() or {}

            total_bins = bins.get('total_bins', 0) or 0
            maintenance_bins = bins.get('maintenance_bins', 0) or 0
            high_fill_bins = bins.get('high_fill_bins', 0) or 0
            error_events = sensors.get('error_events', 0) or 0
            critical_alerts = alerts.get('critical_alerts', 0) or 0

            # Health score from 0 to 100.
            health_score = 100
            health_score -= min(30, maintenance_bins * 4)
            health_score -= min(25, high_fill_bins * 2)
            health_score -= min(20, error_events * 3)
            health_score -= min(25, critical_alerts * 5)
            health_score = max(0, round(health_score, 1))
            health_status = 'Healthy' if health_score >= 75 else 'Watch' if health_score >= 50 else 'At Risk'

            return {
                'success': True,
                'period_days': days,
                'health_score': health_score,
                'health_status': health_status,
                'total_bins': total_bins,
                'active_bins': bins.get('active_bins', 0) or 0,
                'maintenance_bins': maintenance_bins,
                'avg_fill_level': round(bins.get('avg_fill_level', 0) or 0, 1),
                'high_fill_bins': high_fill_bins,
                'sensor_events': sensors.get('sensor_events', 0) or 0,
                'warning_events': sensors.get('warning_events', 0) or 0,
                'error_events': error_events,
                'avg_temperature': round(sensors.get('avg_temp', 0) or 0, 1),
                'avg_humidity': round(sensors.get('avg_humidity', 0) or 0, 1),
                'active_alerts': alerts.get('active_alerts', 0) or 0,
                'critical_alerts': critical_alerts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_bin_health_ranking(self, days=14):
        """Get bins ranked by health risk."""
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
                    b.status,
                    b.waste_level,
                    COUNT(CASE WHEN s.sensor_status = 'error' THEN 1 END) AS sensor_errors,
                    COUNT(CASE WHEN s.sensor_status = 'warning' THEN 1 END) AS sensor_warnings,
                    COUNT(CASE WHEN a.status = 'active' THEN 1 END) AS active_alerts,
                    COUNT(CASE WHEN a.severity = 'critical' AND a.status = 'active' THEN 1 END) AS critical_alerts
                FROM bins b
                LEFT JOIN sensor_logs s ON s.bin_id = b.bin_id AND s.timestamp >= %s
                LEFT JOIN alerts a ON a.bin_id = b.bin_id AND a.created_at >= %s
                GROUP BY b.bin_id, b.bin_code, b.location, b.zone, b.status, b.waste_level
                ORDER BY b.waste_level DESC
                LIMIT 25
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            bins = []
            for row in rows:
                risk_points = int((row.get('waste_level', 0) or 0) / 5)
                risk_points += (row.get('sensor_errors', 0) or 0) * 6
                risk_points += (row.get('sensor_warnings', 0) or 0) * 2
                risk_points += (row.get('critical_alerts', 0) or 0) * 8
                risk_points += (row.get('active_alerts', 0) or 0) * 3
                if row.get('status') == 'maintenance':
                    risk_points += 10

                health_level = 'At Risk' if risk_points >= 45 else 'Watch' if risk_points >= 20 else 'Healthy'
                bins.append({
                    'bin_id': row.get('bin_id'),
                    'bin_code': row.get('bin_code'),
                    'location': row.get('location'),
                    'zone': row.get('zone'),
                    'status': row.get('status'),
                    'waste_level': round(row.get('waste_level', 0) or 0, 1),
                    'sensor_errors': row.get('sensor_errors', 0) or 0,
                    'sensor_warnings': row.get('sensor_warnings', 0) or 0,
                    'active_alerts': row.get('active_alerts', 0) or 0,
                    'critical_alerts': row.get('critical_alerts', 0) or 0,
                    'risk_points': risk_points,
                    'health_level': health_level
                })

            bins.sort(key=lambda x: x['risk_points'], reverse=True)
            return {'success': True, 'period_days': days, 'bins': bins[:15]}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_sensor_anomaly_summary(self, days=14):
        """Get anomaly summary by sensor status and zone."""
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
                    COUNT(*) AS total_events,
                    SUM(CASE WHEN s.sensor_status = 'warning' THEN 1 ELSE 0 END) AS warnings,
                    SUM(CASE WHEN s.sensor_status = 'error' THEN 1 ELSE 0 END) AS errors,
                    AVG(s.temperature) AS avg_temp,
                    AVG(s.humidity) AS avg_humidity
                FROM sensor_logs s
                JOIN bins b ON b.bin_id = s.bin_id
                WHERE s.timestamp >= %s
                  AND b.zone IS NOT NULL
                  AND b.zone <> ''
                GROUP BY b.zone
                ORDER BY errors DESC, warnings DESC, total_events DESC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                anomaly_rate = round(((row.get('warnings', 0) or 0) + (row.get('errors', 0) or 0)) / max(1, row.get('total_events', 0) or 1) * 100, 1)
                zones.append({
                    'zone': row.get('zone'),
                    'total_events': row.get('total_events', 0) or 0,
                    'warnings': row.get('warnings', 0) or 0,
                    'errors': row.get('errors', 0) or 0,
                    'anomaly_rate': anomaly_rate,
                    'avg_temperature': round(row.get('avg_temp', 0) or 0, 1),
                    'avg_humidity': round(row.get('avg_humidity', 0) or 0, 1)
                })

            return {'success': True, 'period_days': days, 'zones': zones}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_health_recommendations(self, days=14):
        """Get recommendations to improve bin health operations."""
        try:
            overview = self.get_health_overview(days)
            ranking = self.get_bin_health_ranking(days)
            anomalies = self.get_sensor_anomaly_summary(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('health_score', 0) < 60:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'System Health',
                    'recommendation': f"Overall bin health score is {overview.get('health_score')}.",
                    'action': 'Launch focused maintenance and overflow reduction sprint'
                })

            if overview.get('high_fill_bins', 0) > 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Overflow Risk',
                    'recommendation': f"{overview.get('high_fill_bins')} bins are above 80% fill.",
                    'action': 'Increase pickup frequency in affected zones'
                })

            if ranking.get('success') and ranking.get('bins'):
                top = ranking.get('bins')[0]
                recommendations.append({
                    'priority': 'HIGH',
                    'category': f"Bin {top.get('bin_code')}",
                    'recommendation': f"Top risk bin with score {top.get('risk_points')} and {top.get('critical_alerts')} critical alerts.",
                    'action': 'Schedule immediate field inspection and sensor recalibration'
                })

            if anomalies.get('success'):
                bad_zone = next((z for z in anomalies.get('zones', []) if z.get('errors', 0) > 0), None)
                if bad_zone:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': f"Zone {bad_zone.get('zone')}",
                        'recommendation': f"Zone reports {bad_zone.get('errors')} sensor errors.",
                        'action': 'Audit gateway connectivity and sensor firmware for this zone'
                    })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Stability',
                    'recommendation': 'Bin health indicators are stable in the selected period.',
                    'action': 'Continue routine preventive maintenance and monitoring'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
