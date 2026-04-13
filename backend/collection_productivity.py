"""Collection Productivity Insights Service
Provides productivity and throughput insights for routes, vehicles, and collection teams.
"""

from models import Database


class CollectionProductivityService:
    """Service for collection productivity analytics."""

    def __init__(self):
        self.db = Database()

    def get_productivity_overview(self, days=30):
        """Return overall productivity metrics for recent days."""
        try:
            query = """
                SELECT
                    COUNT(*) AS total_collections,
                    COUNT(DISTINCT vehicle_id) AS active_vehicles,
                    COUNT(DISTINCT route_id) AS active_routes,
                    SUM(COALESCE(waste_amount, 0)) AS total_waste,
                    ROUND(AVG(COALESCE(waste_amount, 0)), 2) AS avg_waste_per_collection,
                    ROUND(AVG(COALESCE(before_level, 0) - COALESCE(after_level, 0)), 2) AS avg_level_reduction
                FROM collection_logs
                WHERE collection_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            rows = self.db.execute_query(query, (days,))
            data = rows[0] if rows else {}

            total_collections = int(data.get('total_collections') or 0)
            active_vehicles = int(data.get('active_vehicles') or 0)
            throughput = round(total_collections / max(1, days), 2)

            return {
                'success': True,
                'period_days': days,
                'total_collections': total_collections,
                'active_vehicles': active_vehicles,
                'active_routes': int(data.get('active_routes') or 0),
                'total_waste': float(data.get('total_waste') or 0),
                'avg_waste_per_collection': float(data.get('avg_waste_per_collection') or 0),
                'avg_level_reduction': float(data.get('avg_level_reduction') or 0),
                'daily_throughput': throughput,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_vehicle_productivity(self, days=30, limit=10):
        """Return top vehicle productivity ranking."""
        try:
            query = """
                SELECT
                    v.vehicle_id,
                    v.vehicle_number,
                    v.driver_name,
                    COUNT(cl.collection_id) AS collections,
                    ROUND(SUM(COALESCE(cl.waste_amount, 0)), 2) AS waste_collected,
                    ROUND(AVG(COALESCE(cl.waste_amount, 0)), 2) AS avg_waste,
                    COUNT(DISTINCT cl.route_id) AS routes_served
                FROM vehicles v
                LEFT JOIN collection_logs cl ON cl.vehicle_id = v.vehicle_id
                    AND cl.collection_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY v.vehicle_id, v.vehicle_number, v.driver_name
                ORDER BY collections DESC, waste_collected DESC
                LIMIT %s
            """
            vehicles = self.db.execute_query(query, (days, limit)) or []
            rank = 1
            for vehicle in vehicles:
                vehicle['rank'] = rank
                rank += 1

            return {
                'success': True,
                'period_days': days,
                'vehicles': vehicles,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_route_productivity(self, days=30):
        """Return route productivity and completion quality."""
        try:
            query = """
                SELECT
                    r.route_id,
                    r.route_name,
                    r.status,
                    r.total_bins,
                    r.bins_collected,
                    ROUND(CASE WHEN r.total_bins > 0 THEN (r.bins_collected * 100.0 / r.total_bins) ELSE 0 END, 1)
                        AS completion_percent,
                    ROUND(COALESCE(r.actual_distance, r.estimated_distance, 0), 2) AS distance_km
                FROM routes r
                WHERE r.route_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY completion_percent DESC, r.route_date DESC
            """
            routes = self.db.execute_query(query, (days,)) or []

            return {
                'success': True,
                'period_days': days,
                'routes': routes,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_zone_productivity(self, days=30):
        """Return zone-wise productivity and service output."""
        try:
            query = """
                SELECT
                    b.zone,
                    COUNT(cl.collection_id) AS collections,
                    ROUND(SUM(COALESCE(cl.waste_amount, 0)), 2) AS waste_collected,
                    COUNT(DISTINCT cl.vehicle_id) AS vehicles_used,
                    ROUND(AVG(COALESCE(cl.before_level, 0)), 1) AS avg_before_level,
                    ROUND(AVG(COALESCE(cl.after_level, 0)), 1) AS avg_after_level
                FROM bins b
                LEFT JOIN collection_logs cl ON cl.bin_id = b.bin_id
                    AND cl.collection_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY b.zone
                ORDER BY collections DESC, waste_collected DESC
            """
            zones = self.db.execute_query(query, (days,)) or []

            for zone in zones:
                before = float(zone.get('avg_before_level') or 0)
                after = float(zone.get('avg_after_level') or 0)
                zone['avg_reduction'] = round(max(0.0, before - after), 1)

            return {
                'success': True,
                'period_days': days,
                'zones': zones,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_productivity_recommendations(self, days=30):
        """Return productivity recommendations from computed indicators."""
        try:
            overview = self.get_productivity_overview(days)
            vehicles = self.get_vehicle_productivity(days, 5)
            routes = self.get_route_productivity(days)

            if not overview.get('success'):
                return {'success': False, 'error': 'Unable to compute recommendations'}

            recs = []

            throughput = float(overview.get('daily_throughput') or 0)
            if throughput < 8:
                recs.append({'priority': 'High', 'title': 'Increase Daily Throughput', 'message': 'Collections per day are below target. Review dispatch windows and route starts.'})

            avg_reduction = float(overview.get('avg_level_reduction') or 0)
            if avg_reduction < 20:
                recs.append({'priority': 'Medium', 'title': 'Improve Collection Depth', 'message': 'Average level reduction is low; check bin assignment and pickup quality.'})

            low_completion_routes = []
            for route in routes.get('routes', []):
                if float(route.get('completion_percent') or 0) < 70:
                    low_completion_routes.append(route.get('route_name'))
            if low_completion_routes:
                recs.append({'priority': 'High', 'title': 'Address Low Completion Routes', 'message': f"Routes under 70% completion: {', '.join(low_completion_routes[:3])}"})

            top_vehicle = vehicles.get('vehicles', [None])[0] if vehicles.get('vehicles') else None
            if top_vehicle and int(top_vehicle.get('collections') or 0) > 0:
                recs.append({'priority': 'Low', 'title': 'Replicate Top Vehicle Pattern', 'message': f"Top performer {top_vehicle.get('vehicle_number')} can be used as benchmark for routing and loading."})

            if not recs:
                recs.append({'priority': 'Low', 'title': 'Maintain Current Productivity', 'message': 'Current productivity indicators are healthy. Continue monitoring trend stability.'})

            return {
                'success': True,
                'period_days': days,
                'recommendations': recs,
                'total_recommendations': len(recs),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
