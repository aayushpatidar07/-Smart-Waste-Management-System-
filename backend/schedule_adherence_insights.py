"""Schedule Adherence Insights Service
Tracks adherence to planned collection schedules and timing consistency.
"""

from datetime import datetime, timedelta
from models import Database


class ScheduleAdherenceInsightsService:
    """Service for schedule adherence analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_adherence_overview(self, days=30):
        """Return global adherence metrics."""
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
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_routes,
                    AVG(CASE WHEN total_bins > 0 THEN (bins_collected / total_bins) * 100 ELSE 0 END) AS avg_completion_percent,
                    AVG(COALESCE(actual_distance, estimated_distance, 0)) AS avg_distance_km
                FROM routes
                WHERE route_date >= %s
                """,
                (start_date,)
            )
            route_stats = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS active_schedules,
                    COUNT(DISTINCT zone) AS scheduled_zones
                FROM schedules
                WHERE status = 'active'
                """
            )
            schedule_stats = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS log_events,
                    COUNT(DISTINCT route_id) AS logged_routes
                FROM collection_logs
                WHERE collection_time >= %s
                  AND route_id IS NOT NULL
                """,
                (start_date,)
            )
            log_stats = cursor.fetchone() or {}

            total_routes = route_stats.get('total_routes', 0) or 0
            completed_routes = route_stats.get('completed_routes', 0) or 0
            completion_rate = round((completed_routes / total_routes) * 100, 1) if total_routes else 0

            adherence_score = min(100, round(completion_rate * 0.7 + (route_stats.get('avg_completion_percent', 0) or 0) * 0.3, 1))
            adherence_status = 'Strong' if adherence_score >= 80 else 'Watch' if adherence_score >= 60 else 'At Risk'

            return {
                'success': True,
                'period_days': days,
                'adherence_score': adherence_score,
                'adherence_status': adherence_status,
                'total_routes': total_routes,
                'completed_routes': completed_routes,
                'cancelled_routes': route_stats.get('cancelled_routes', 0) or 0,
                'route_completion_rate': completion_rate,
                'avg_route_bin_completion': round(route_stats.get('avg_completion_percent', 0) or 0, 1),
                'avg_route_distance_km': round(route_stats.get('avg_distance_km', 0) or 0, 2),
                'active_schedules': schedule_stats.get('active_schedules', 0) or 0,
                'scheduled_zones': schedule_stats.get('scheduled_zones', 0) or 0,
                'collection_log_events': log_stats.get('log_events', 0) or 0,
                'logged_routes': log_stats.get('logged_routes', 0) or 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_zone_adherence(self, days=30):
        """Return route adherence grouped by zone."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    v.assigned_zone AS zone,
                    COUNT(r.route_id) AS total_routes,
                    SUM(CASE WHEN r.status = 'completed' THEN 1 ELSE 0 END) AS completed_routes,
                    SUM(CASE WHEN r.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_routes,
                    AVG(CASE WHEN r.total_bins > 0 THEN (r.bins_collected / r.total_bins) * 100 ELSE 0 END) AS avg_bin_completion,
                    AVG(COALESCE(r.actual_distance, r.estimated_distance, 0)) AS avg_distance
                FROM routes r
                LEFT JOIN vehicles v ON v.vehicle_id = r.vehicle_id
                WHERE r.route_date >= %s
                  AND v.assigned_zone IS NOT NULL
                  AND v.assigned_zone <> ''
                GROUP BY v.assigned_zone
                ORDER BY total_routes DESC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                total_routes = row.get('total_routes', 0) or 0
                completed_routes = row.get('completed_routes', 0) or 0
                completion_rate = round((completed_routes / total_routes) * 100, 1) if total_routes else 0
                zones.append({
                    'zone': row.get('zone'),
                    'total_routes': total_routes,
                    'completed_routes': completed_routes,
                    'cancelled_routes': row.get('cancelled_routes', 0) or 0,
                    'completion_rate': completion_rate,
                    'avg_bin_completion': round(row.get('avg_bin_completion', 0) or 0, 1),
                    'avg_distance_km': round(row.get('avg_distance', 0) or 0, 2)
                })

            return {'success': True, 'period_days': days, 'zones': zones}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_delay_indicators(self, days=30):
        """Return routes likely to have timing or execution delays."""
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
                    r.status,
                    r.route_date,
                    r.total_bins,
                    r.bins_collected,
                    v.vehicle_number,
                    v.assigned_zone,
                    COALESCE(r.actual_distance, r.estimated_distance, 0) AS distance_km,
                    COUNT(CASE WHEN wr.status IN ('pending', 'acknowledged') THEN 1 END) AS open_reports
                FROM routes r
                LEFT JOIN vehicles v ON v.vehicle_id = r.vehicle_id
                LEFT JOIN route_bins rb ON rb.route_id = r.route_id
                LEFT JOIN waste_reports wr ON wr.bin_id = rb.bin_id AND wr.reported_at >= %s
                WHERE r.route_date >= %s
                GROUP BY r.route_id, r.route_name, r.status, r.route_date, r.total_bins, r.bins_collected, v.vehicle_number, v.assigned_zone, distance_km
                ORDER BY r.route_date DESC
                LIMIT 20
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            delayed = []
            for row in rows:
                total_bins = row.get('total_bins', 0) or 0
                bins_collected = row.get('bins_collected', 0) or 0
                bin_gap = max(0, total_bins - bins_collected)
                delay_points = (bin_gap * 4) + ((row.get('open_reports', 0) or 0) * 3)
                if row.get('status') != 'completed':
                    delay_points += 10
                delay_level = 'High' if delay_points >= 25 else 'Medium' if delay_points >= 12 else 'Low'

                delayed.append({
                    'route_id': row.get('route_id'),
                    'route_name': row.get('route_name'),
                    'route_date': str(row.get('route_date')),
                    'status': row.get('status'),
                    'vehicle_number': row.get('vehicle_number'),
                    'zone': row.get('assigned_zone'),
                    'distance_km': round(row.get('distance_km', 0) or 0, 2),
                    'total_bins': total_bins,
                    'bins_collected': bins_collected,
                    'open_reports': row.get('open_reports', 0) or 0,
                    'delay_points': delay_points,
                    'delay_level': delay_level
                })

            return {'success': True, 'period_days': days, 'routes': delayed}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_adherence_recommendations(self, days=30):
        """Return schedule adherence recommendations."""
        try:
            overview = self.get_adherence_overview(days)
            zones = self.get_zone_adherence(days)
            delays = self.get_delay_indicators(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('adherence_score', 0) < 70:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Overall Adherence',
                    'recommendation': f"Adherence score is {overview.get('adherence_score')}. Route completion consistency is below target.",
                    'action': 'Rebalance route plans and add contingency slots for high-load days'
                })

            if zones.get('success'):
                low_zone = next((z for z in zones.get('zones', []) if z.get('completion_rate', 0) < 60), None)
                if low_zone:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': f"Zone {low_zone.get('zone')}",
                        'recommendation': f"Completion rate is {low_zone.get('completion_rate')}%.",
                        'action': 'Increase dispatch support and tighten route cutoffs in this zone'
                    })

            if delays.get('success'):
                high_delay = next((r for r in delays.get('routes', []) if r.get('delay_level') == 'High'), None)
                if high_delay:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': f"Route {high_delay.get('route_id')}",
                        'recommendation': f"High delay indicator detected with {high_delay.get('delay_points')} points.",
                        'action': 'Split route workload or assign backup vehicle during peak window'
                    })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Operations',
                    'recommendation': 'Schedule adherence metrics are stable for the selected period.',
                    'action': 'Maintain current planning cadence and monitor weekly trends'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
