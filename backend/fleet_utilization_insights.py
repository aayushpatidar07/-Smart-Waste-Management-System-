"""Fleet Utilization Insights Service
Provides utilization, load efficiency, and idle-risk analytics for vehicles.
"""

from datetime import datetime, timedelta
from models import Database


class FleetUtilizationInsightsService:
    """Service class for fleet utilization analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_utilization_overview(self, days=30):
        """Get overall fleet utilization metrics."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_vehicles,
                    SUM(CASE WHEN status IN ('available', 'on-route') THEN 1 ELSE 0 END) AS operational_vehicles,
                    SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) AS maintenance_vehicles,
                    AVG(current_load) AS avg_current_load,
                    AVG(capacity) AS avg_capacity
                FROM vehicles
                """
            )
            vehicles = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS routes_total,
                    COUNT(DISTINCT vehicle_id) AS vehicles_used,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_routes,
                    AVG(COALESCE(actual_distance, estimated_distance, 0)) AS avg_distance
                FROM routes
                WHERE route_date >= %s
                """,
                (start_date,)
            )
            routes = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS collection_events,
                    COUNT(DISTINCT vehicle_id) AS active_collection_vehicles,
                    AVG(waste_amount) AS avg_waste_per_event
                FROM collection_logs
                WHERE collection_time >= %s
                  AND vehicle_id IS NOT NULL
                """,
                (start_date,)
            )
            collections = cursor.fetchone() or {}

            total_vehicles = vehicles.get('total_vehicles', 0) or 0
            vehicles_used = routes.get('vehicles_used', 0) or 0
            utilization_rate = round((vehicles_used / total_vehicles) * 100, 1) if total_vehicles else 0

            load_ratio = 0
            if (vehicles.get('avg_capacity', 0) or 0) > 0:
                load_ratio = round(((vehicles.get('avg_current_load', 0) or 0) / (vehicles.get('avg_capacity', 1) or 1)) * 100, 1)

            utilization_score = min(100, round(utilization_rate * 0.7 + min(load_ratio, 100) * 0.3, 1))
            utilization_status = 'Efficient' if utilization_score >= 75 else 'Moderate' if utilization_score >= 50 else 'Underused'

            return {
                'success': True,
                'period_days': days,
                'utilization_score': utilization_score,
                'utilization_status': utilization_status,
                'total_vehicles': total_vehicles,
                'operational_vehicles': vehicles.get('operational_vehicles', 0) or 0,
                'maintenance_vehicles': vehicles.get('maintenance_vehicles', 0) or 0,
                'vehicles_used_in_routes': vehicles_used,
                'vehicle_utilization_rate': utilization_rate,
                'avg_load_ratio': load_ratio,
                'routes_total': routes.get('routes_total', 0) or 0,
                'completed_routes': routes.get('completed_routes', 0) or 0,
                'collection_events': collections.get('collection_events', 0) or 0,
                'avg_distance_km': round(routes.get('avg_distance', 0) or 0, 2),
                'avg_waste_per_event': round(collections.get('avg_waste_per_event', 0) or 0, 2)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_vehicle_utilization_ranking(self, days=30):
        """Get per-vehicle utilization ranking."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    v.vehicle_id,
                    v.vehicle_number,
                    v.vehicle_type,
                    v.status,
                    v.capacity,
                    v.current_load,
                    v.assigned_zone,
                    COUNT(r.route_id) AS route_count,
                    SUM(CASE WHEN r.status = 'completed' THEN 1 ELSE 0 END) AS completed_routes,
                    AVG(COALESCE(r.actual_distance, r.estimated_distance, 0)) AS avg_distance,
                    COUNT(cl.collection_id) AS collection_events,
                    AVG(cl.waste_amount) AS avg_waste_amount
                FROM vehicles v
                LEFT JOIN routes r ON r.vehicle_id = v.vehicle_id AND r.route_date >= %s
                LEFT JOIN collection_logs cl ON cl.vehicle_id = v.vehicle_id AND cl.collection_time >= %s
                GROUP BY v.vehicle_id, v.vehicle_number, v.vehicle_type, v.status, v.capacity, v.current_load, v.assigned_zone
                ORDER BY route_count DESC, collection_events DESC
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            vehicles = []
            for row in rows:
                capacity = row.get('capacity', 0) or 0
                current_load = row.get('current_load', 0) or 0
                load_percent = round((current_load / capacity) * 100, 1) if capacity else 0
                score = (row.get('route_count', 0) or 0) * 6 + (row.get('collection_events', 0) or 0) * 2
                score += int(load_percent / 10)
                level = 'High' if score >= 40 else 'Medium' if score >= 18 else 'Low'

                vehicles.append({
                    'vehicle_id': row.get('vehicle_id'),
                    'vehicle_number': row.get('vehicle_number'),
                    'vehicle_type': row.get('vehicle_type'),
                    'status': row.get('status'),
                    'assigned_zone': row.get('assigned_zone'),
                    'route_count': row.get('route_count', 0) or 0,
                    'completed_routes': row.get('completed_routes', 0) or 0,
                    'collection_events': row.get('collection_events', 0) or 0,
                    'avg_distance_km': round(row.get('avg_distance', 0) or 0, 2),
                    'avg_waste_amount': round(row.get('avg_waste_amount', 0) or 0, 2),
                    'load_percent': load_percent,
                    'utilization_score': score,
                    'utilization_level': level
                })

            return {'success': True, 'period_days': days, 'vehicles': vehicles[:20]}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_idle_fleet_alerts(self, days=30):
        """Get vehicles with low activity signals."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    v.vehicle_id,
                    v.vehicle_number,
                    v.status,
                    v.assigned_zone,
                    COUNT(DISTINCT r.route_id) AS route_count,
                    COUNT(cl.collection_id) AS collection_events
                FROM vehicles v
                LEFT JOIN routes r ON r.vehicle_id = v.vehicle_id AND r.route_date >= %s
                LEFT JOIN collection_logs cl ON cl.vehicle_id = v.vehicle_id AND cl.collection_time >= %s
                GROUP BY v.vehicle_id, v.vehicle_number, v.status, v.assigned_zone
                ORDER BY route_count ASC, collection_events ASC
                """,
                (start_date, start_date)
            )
            rows = cursor.fetchall()

            idle = []
            for row in rows:
                route_count = row.get('route_count', 0) or 0
                events = row.get('collection_events', 0) or 0
                if route_count <= 1 and events <= 2 and row.get('status') != 'maintenance':
                    idle.append({
                        'vehicle_id': row.get('vehicle_id'),
                        'vehicle_number': row.get('vehicle_number'),
                        'status': row.get('status'),
                        'assigned_zone': row.get('assigned_zone'),
                        'route_count': route_count,
                        'collection_events': events,
                        'idle_risk': 'High' if route_count == 0 else 'Medium'
                    })

            return {'success': True, 'period_days': days, 'idle_vehicles': idle}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_utilization_recommendations(self, days=30):
        """Get recommendations for fleet utilization optimization."""
        try:
            overview = self.get_utilization_overview(days)
            ranking = self.get_vehicle_utilization_ranking(days)
            idle = self.get_idle_fleet_alerts(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('vehicle_utilization_rate', 0) < 60:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Fleet Utilization',
                    'recommendation': f"Vehicle utilization rate is {overview.get('vehicle_utilization_rate')}%.",
                    'action': 'Consolidate low-demand routes and reassign underused vehicles'
                })

            if overview.get('maintenance_vehicles', 0) > 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Maintenance Load',
                    'recommendation': f"{overview.get('maintenance_vehicles')} vehicles are in maintenance state.",
                    'action': 'Stagger preventive maintenance to reduce operational impact'
                })

            if idle.get('success') and idle.get('idle_vehicles'):
                top_idle = idle.get('idle_vehicles')[0]
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': f"Vehicle {top_idle.get('vehicle_number')}",
                    'recommendation': f"Low activity detected ({top_idle.get('route_count')} routes, {top_idle.get('collection_events')} events).",
                    'action': 'Reassign to high-demand zone or reserve as rapid-response asset'
                })

            if ranking.get('success') and ranking.get('vehicles'):
                top = ranking.get('vehicles')[0]
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Best Performer',
                    'recommendation': f"Vehicle {top.get('vehicle_number')} shows strong utilization score {top.get('utilization_score')}.",
                    'action': 'Replicate route and dispatch strategy for similar vehicle types'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
