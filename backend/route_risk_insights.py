"""Route Risk Insights Service
Analyzes route risk using unresolved reports, active alerts, and operational load.
"""

from datetime import datetime, timedelta
from models import Database


class RouteRiskInsightsService:
    """Service class for route risk scoring and recommendations."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_risk_overview(self, days=30):
        """Return overall route risk snapshot."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_routes,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_routes,
                    SUM(CASE WHEN status IN ('planned', 'in-progress') THEN 1 ELSE 0 END) AS active_routes,
                    AVG(COALESCE(actual_distance, estimated_distance, 0)) AS avg_distance
                FROM routes
                WHERE route_date >= %s
                """,
                (start_date,)
            )
            route_stats = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS unresolved_reports,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) AS urgent_reports
                FROM waste_reports
                WHERE status IN ('pending', 'acknowledged')
                  AND reported_at >= %s
                """,
                (start_date,)
            )
            report_stats = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS active_alerts,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_alerts
                FROM alerts
                WHERE status = 'active'
                """
            )
            alert_stats = cursor.fetchone() or {}

            total_routes = route_stats.get('total_routes', 0) or 0
            urgent_reports = report_stats.get('urgent_reports', 0) or 0
            critical_alerts = alert_stats.get('critical_alerts', 0) or 0
            active_routes = route_stats.get('active_routes', 0) or 0

            # Weighted risk score from 0 to 100.
            risk_score = min(100, round((urgent_reports * 2.5) + (critical_alerts * 5) + (active_routes * 0.7), 1))
            risk_status = 'High' if risk_score >= 70 else 'Medium' if risk_score >= 40 else 'Low'

            return {
                'success': True,
                'period_days': days,
                'risk_score': risk_score,
                'risk_status': risk_status,
                'total_routes': total_routes,
                'completed_routes': route_stats.get('completed_routes', 0) or 0,
                'active_routes': active_routes,
                'avg_route_distance_km': round(route_stats.get('avg_distance', 0) or 0, 2),
                'unresolved_reports': report_stats.get('unresolved_reports', 0) or 0,
                'urgent_reports': urgent_reports,
                'active_alerts': alert_stats.get('active_alerts', 0) or 0,
                'critical_alerts': critical_alerts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_high_risk_routes(self, days=30):
        """Return routes prioritized by current risk indicators."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    r.route_id,
                    r.route_name,
                    r.vehicle_id,
                    r.status,
                    r.route_date,
                    r.total_bins,
                    r.bins_collected,
                    COALESCE(r.actual_distance, r.estimated_distance, 0) AS distance_km,
                    COUNT(CASE WHEN wr.status IN ('pending', 'acknowledged') THEN 1 END) AS open_reports,
                    COUNT(CASE WHEN wr.priority IN ('high', 'critical') AND wr.status IN ('pending', 'acknowledged') THEN 1 END) AS urgent_open_reports
                FROM routes r
                LEFT JOIN route_bins rb ON rb.route_id = r.route_id
                LEFT JOIN waste_reports wr ON wr.bin_id = rb.bin_id AND wr.reported_at >= %s
                WHERE r.route_date >= %s
                GROUP BY r.route_id, r.route_name, r.vehicle_id, r.status, r.route_date, r.total_bins, r.bins_collected, distance_km
                ORDER BY urgent_open_reports DESC, open_reports DESC, distance_km DESC
                LIMIT 15
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            routes = []
            for row in rows:
                risk_points = (row.get('urgent_open_reports', 0) or 0) * 8 + (row.get('open_reports', 0) or 0) * 3
                if row.get('status') != 'completed':
                    risk_points += 5
                risk_level = 'High' if risk_points >= 30 else 'Medium' if risk_points >= 15 else 'Low'
                routes.append({
                    'route_id': row.get('route_id'),
                    'route_name': row.get('route_name'),
                    'vehicle_id': row.get('vehicle_id'),
                    'route_date': str(row.get('route_date')),
                    'status': row.get('status'),
                    'distance_km': round(row.get('distance_km', 0) or 0, 2),
                    'open_reports': row.get('open_reports', 0) or 0,
                    'urgent_open_reports': row.get('urgent_open_reports', 0) or 0,
                    'risk_points': risk_points,
                    'risk_level': risk_level
                })

            return {'success': True, 'period_days': days, 'routes': routes}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_zone_risk_profile(self, days=30):
        """Return zone-level risk profile from bins, reports, and route load."""
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
                    AVG(b.waste_level) AS avg_waste_level,
                    COUNT(DISTINCT CASE WHEN wr.status IN ('pending', 'acknowledged') THEN wr.report_id END) AS open_reports,
                    COUNT(DISTINCT CASE WHEN wr.priority IN ('high', 'critical') AND wr.status IN ('pending', 'acknowledged') THEN wr.report_id END) AS urgent_reports,
                    COUNT(DISTINCT r.route_id) AS scheduled_routes
                FROM bins b
                LEFT JOIN waste_reports wr ON wr.bin_id = b.bin_id AND wr.reported_at >= %s
                LEFT JOIN route_bins rb ON rb.bin_id = b.bin_id
                LEFT JOIN routes r ON r.route_id = rb.route_id AND r.route_date >= %s
                WHERE b.zone IS NOT NULL AND b.zone <> ''
                GROUP BY b.zone
                ORDER BY urgent_reports DESC, open_reports DESC, avg_waste_level DESC
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                risk_points = (row.get('urgent_reports', 0) or 0) * 6 + (row.get('open_reports', 0) or 0) * 2
                risk_points += int((row.get('avg_waste_level', 0) or 0) / 10)
                risk_level = 'High' if risk_points >= 35 else 'Medium' if risk_points >= 18 else 'Low'
                zones.append({
                    'zone': row.get('zone'),
                    'total_bins': row.get('total_bins', 0) or 0,
                    'avg_waste_level': round(row.get('avg_waste_level', 0) or 0, 1),
                    'open_reports': row.get('open_reports', 0) or 0,
                    'urgent_reports': row.get('urgent_reports', 0) or 0,
                    'scheduled_routes': row.get('scheduled_routes', 0) or 0,
                    'risk_points': risk_points,
                    'risk_level': risk_level
                })

            return {'success': True, 'period_days': days, 'zones': zones}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_risk_recommendations(self, days=30):
        """Return operational recommendations from risk profile."""
        try:
            overview = self.get_risk_overview(days)
            zones = self.get_zone_risk_profile(days)
            high_routes = self.get_high_risk_routes(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('risk_score', 0) >= 70:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'System Risk',
                    'recommendation': f"Overall route risk score is {overview.get('risk_score')}. Deploy rapid response crew for backlog reduction.",
                    'action': 'Increase short-cycle collections in high-risk zones'
                })

            if zones.get('success'):
                high_zone = next((z for z in zones.get('zones', []) if z.get('risk_level') == 'High'), None)
                if high_zone:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': f"Zone {high_zone.get('zone')}",
                        'recommendation': f"Zone risk points reached {high_zone.get('risk_points')} with {high_zone.get('urgent_reports')} urgent reports.",
                        'action': 'Rebalance vehicles and prioritize this zone next shift'
                    })

            if high_routes.get('success'):
                route = next((r for r in high_routes.get('routes', []) if r.get('risk_level') == 'High'), None)
                if route:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': f"Route {route.get('route_id')}",
                        'recommendation': f"Route has {route.get('urgent_open_reports')} urgent open reports and risk points {route.get('risk_points')}.",
                        'action': 'Inspect route bins and clear pending alerts before next cycle'
                    })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Stability',
                    'recommendation': 'Current route risk indicators are within normal limits.',
                    'action': 'Continue standard monitoring cadence'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
