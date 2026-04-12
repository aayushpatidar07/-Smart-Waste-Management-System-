"""Service Availability Insights Service
Tracks bin, vehicle, and route availability to surface operational gaps.
"""

from models import Database


class ServiceAvailabilityService:
    """Service for service availability and continuity insights."""

    def __init__(self):
        self.db = Database()

    def get_bin_availability(self):
        """Return bin availability breakdown and zone-level status."""
        try:
            summary_query = """
                SELECT
                    COUNT(*) AS total_bins,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_bins,
                    SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) AS maintenance_bins,
                    SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) AS inactive_bins
                FROM bins
            """
            summary = self.db.execute_query(summary_query)
            summary = summary[0] if summary else {}

            total_bins = int(summary.get('total_bins') or 0)
            active_bins = int(summary.get('active_bins') or 0)

            zone_query = """
                SELECT
                    zone,
                    COUNT(*) AS total_bins,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_bins,
                    ROUND(
                        (SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) * 100.0) /
                        NULLIF(COUNT(*), 0),
                        1
                    ) AS availability_percent
                FROM bins
                GROUP BY zone
                ORDER BY availability_percent ASC, zone ASC
            """
            zones = self.db.execute_query(zone_query) or []

            return {
                'success': True,
                'total_bins': total_bins,
                'active_bins': active_bins,
                'maintenance_bins': int(summary.get('maintenance_bins') or 0),
                'inactive_bins': int(summary.get('inactive_bins') or 0),
                'availability_percent': round((active_bins * 100.0 / total_bins), 1) if total_bins else 0.0,
                'zones': zones,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_vehicle_availability(self):
        """Return vehicle readiness and assignment coverage."""
        try:
            query = """
                SELECT
                    COUNT(*) AS total_vehicles,
                    SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available,
                    SUM(CASE WHEN status = 'on-route' THEN 1 ELSE 0 END) AS on_route,
                    SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) AS maintenance,
                    SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) AS offline
                FROM vehicles
            """
            result = self.db.execute_query(query)
            data = result[0] if result else {}

            total = int(data.get('total_vehicles') or 0)
            available = int(data.get('available') or 0)
            on_route = int(data.get('on_route') or 0)
            ready = available + on_route

            return {
                'success': True,
                'total_vehicles': total,
                'available': available,
                'on_route': on_route,
                'maintenance': int(data.get('maintenance') or 0),
                'offline': int(data.get('offline') or 0),
                'readiness_percent': round((ready * 100.0 / total), 1) if total else 0.0,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_route_completion(self, days=14):
        """Return route completion health for the last N days."""
        try:
            query = """
                SELECT
                    COUNT(*) AS total_routes,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_routes,
                    SUM(CASE WHEN status = 'in-progress' THEN 1 ELSE 0 END) AS in_progress_routes,
                    SUM(CASE WHEN status = 'planned' THEN 1 ELSE 0 END) AS planned_routes,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_routes,
                    ROUND(AVG(CASE WHEN total_bins > 0 THEN (bins_collected * 100.0 / total_bins) ELSE 0 END), 1)
                        AS avg_collection_progress
                FROM routes
                WHERE route_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            result = self.db.execute_query(query, (days,))
            data = result[0] if result else {}

            total_routes = int(data.get('total_routes') or 0)
            completed_routes = int(data.get('completed_routes') or 0)
            denominator = max(1, total_routes - int(data.get('cancelled_routes') or 0))

            return {
                'success': True,
                'period_days': days,
                'total_routes': total_routes,
                'completed_routes': completed_routes,
                'in_progress_routes': int(data.get('in_progress_routes') or 0),
                'planned_routes': int(data.get('planned_routes') or 0),
                'cancelled_routes': int(data.get('cancelled_routes') or 0),
                'completion_rate_percent': round((completed_routes * 100.0 / denominator), 1),
                'avg_collection_progress_percent': float(data.get('avg_collection_progress') or 0),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_alert_pressure(self, hours=24):
        """Return active/critical alert pressure for recent hours."""
        try:
            query = """
                SELECT
                    COUNT(*) AS total_alerts,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_alerts,
                    SUM(CASE WHEN severity = 'critical' AND status = 'active' THEN 1 ELSE 0 END) AS critical_active,
                    SUM(CASE WHEN severity = 'warning' AND status = 'active' THEN 1 ELSE 0 END) AS warning_active
                FROM alerts
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            result = self.db.execute_query(query, (hours,))
            data = result[0] if result else {}

            return {
                'success': True,
                'hours': hours,
                'total_alerts': int(data.get('total_alerts') or 0),
                'active_alerts': int(data.get('active_alerts') or 0),
                'critical_active': int(data.get('critical_active') or 0),
                'warning_active': int(data.get('warning_active') or 0),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_zone_service_gaps(self, limit=8):
        """Return zones with lowest service availability and highest pressure."""
        try:
            query = """
                SELECT
                    b.zone,
                    COUNT(*) AS total_bins,
                    SUM(CASE WHEN b.status <> 'active' THEN 1 ELSE 0 END) AS unavailable_bins,
                    ROUND(
                        (SUM(CASE WHEN b.status = 'active' THEN 1 ELSE 0 END) * 100.0) /
                        NULLIF(COUNT(*), 0),
                        1
                    ) AS availability_percent,
                    COALESCE(SUM(a.active_alerts), 0) AS active_alerts
                FROM bins b
                LEFT JOIN (
                    SELECT bin_id, COUNT(*) AS active_alerts
                    FROM alerts
                    WHERE status = 'active'
                    GROUP BY bin_id
                ) a ON a.bin_id = b.bin_id
                GROUP BY b.zone
                ORDER BY availability_percent ASC, active_alerts DESC, b.zone ASC
                LIMIT %s
            """
            gaps = self.db.execute_query(query, (limit,)) or []

            for gap in gaps:
                availability = float(gap.get('availability_percent') or 0)
                alerts = int(gap.get('active_alerts') or 0)
                if availability < 70 or alerts >= 5:
                    gap['priority'] = 'High'
                elif availability < 85 or alerts >= 2:
                    gap['priority'] = 'Medium'
                else:
                    gap['priority'] = 'Low'

            return {
                'success': True,
                'total_zones': len(gaps),
                'service_gaps': gaps,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_system_availability_score(self):
        """Return a weighted system availability score."""
        try:
            bins_data = self.get_bin_availability()
            vehicles_data = self.get_vehicle_availability()
            routes_data = self.get_route_completion(14)
            alerts_data = self.get_alert_pressure(24)

            if not all([bins_data.get('success'), vehicles_data.get('success'), routes_data.get('success'), alerts_data.get('success')]):
                return {'success': False, 'error': 'Unable to compute availability score'}

            bin_score = float(bins_data.get('availability_percent') or 0)
            vehicle_score = float(vehicles_data.get('readiness_percent') or 0)
            route_score = float(routes_data.get('completion_rate_percent') or 0)

            active_alerts = int(alerts_data.get('active_alerts') or 0)
            critical_active = int(alerts_data.get('critical_active') or 0)
            alert_penalty_score = max(0.0, 100.0 - (critical_active * 8.0) - (active_alerts * 1.5))

            weighted_score = round(
                (bin_score * 0.35) +
                (vehicle_score * 0.30) +
                (route_score * 0.20) +
                (alert_penalty_score * 0.15),
                1
            )

            if weighted_score >= 85:
                status = 'Healthy'
            elif weighted_score >= 70:
                status = 'Watch'
            else:
                status = 'Critical'

            return {
                'success': True,
                'availability_score': weighted_score,
                'status': status,
                'components': {
                    'bins': round(bin_score, 1),
                    'vehicles': round(vehicle_score, 1),
                    'routes': round(route_score, 1),
                    'alert_resilience': round(alert_penalty_score, 1),
                },
                'active_alerts': active_alerts,
                'critical_alerts': critical_active,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
