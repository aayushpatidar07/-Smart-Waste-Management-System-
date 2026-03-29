"""Route Optimization Insights Service"""

from models import Database
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2


class RouteOptimizationService:
    """Service for analyzing and optimizing waste collection routes"""

    def __init__(self):
        self.db = Database()

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula (in km)"""
        if not all([lat1, lon1, lat2, lon2]):
            return 0
        
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c

    def analyze_route_efficiency(self, route_id):
        """
        Analyze efficiency of a specific route.

        Args:
            route_id: ID of the route to analyze

        Returns:
            dict with efficiency metrics and recommendations
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get route details
            cursor.execute(
                """
                SELECT id, vehicle_id, scheduled_date, estimated_time, 
                       vehicle_zone, status FROM routes WHERE id = %s
                """,
                (route_id,),
            )
            route = cursor.fetchone()
            
            if not route:
                return {"success": False, "message": "Route not found"}

            route_id, vehicle_id, scheduled_date, estimated_time, zone, status = route

            # Get bins assigned to this route
            cursor.execute(
                """
                SELECT b.id, b.location_latitude, b.location_longitude, 
                       COALESCE(wl.current_fill_level, 0) as fill_level
                FROM bins b
                LEFT JOIN waste_logs wl ON b.id = wl.bin_id
                WHERE b.assigned_zone = %s
                ORDER BY wl.timestamp DESC LIMIT 1
                """,
                (zone,),
            )
            bins = cursor.fetchall()

            if not bins:
                cursor.close()
                conn.close()
                return {"success": True, "efficiency_score": 0, "bins_count": 0, "recommendations": []}

            # Calculate total distance
            total_distance = 0
            high_fill_bins = 0
            avg_fill_level = 0

            for i, bin_data in enumerate(bins):
                bin_id, lat, lon, fill_level = bin_data
                avg_fill_level += fill_level

                # Calculate distance to next bin
                if i < len(bins) - 1:
                    next_bin = bins[i + 1]
                    distance = self.calculate_distance(lat, lon, next_bin[1], next_bin[2])
                    total_distance += distance

                if fill_level >= 75:
                    high_fill_bins += 1

            avg_fill_level = avg_fill_level / len(bins) if bins else 0
            cursor.close()
            conn.close()

            # Calculate efficiency score (0-100)
            efficiency_score = min(100, int((avg_fill_level / 100) * 100))

            # Generate recommendations
            recommendations = []
            if high_fill_bins / len(bins) > 0.3:
                recommendations.append(
                    "High fill levels detected. Consider prioritizing this route earlier in the day."
                )
            if total_distance > 50:
                recommendations.append("Route distance is high. Consider optimizing collection sequence.")
            if avg_fill_level < 30:
                recommendations.append("Low average fill levels. Route may be executed too early in schedule.")

            return {
                "success": True,
                "route_id": route_id,
                "efficiency_score": efficiency_score,
                "total_distance_km": round(total_distance, 2),
                "bins_count": len(bins),
                "high_fill_bins": high_fill_bins,
                "average_fill_level": round(avg_fill_level, 1),
                "status": status,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"success": False, "message": f"Error analyzing route: {str(e)}"}

    def get_optimization_suggestions(self, zone):
        """
        Get optimization suggestions for all routes in a zone.

        Args:
            zone: Zone name to analyze

        Returns:
            dict with suggestions and improvement opportunities
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get recent routes for the zone
            cursor.execute(
                """
                SELECT id, estimated_time, status FROM routes 
                WHERE vehicle_zone = %s AND scheduled_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY scheduled_date DESC LIMIT 10
                """,
                (zone,),
            )
            routes = cursor.fetchall()

            if not routes:
                cursor.close()
                conn.close()
                return {
                    "success": True,
                    "zone": zone,
                    "routes_count": 0,
                    "average_efficiency": 0,
                    "suggestions": [],
                }

            suggestions = []
            total_efficiency = 0
            completed_routes = 0

            for route_id, est_time, status in routes:
                if status == "completed":
                    completed_routes += 1
                    analysis = self.analyze_route_efficiency(route_id)
                    if analysis["success"]:
                        total_efficiency += analysis.get("efficiency_score", 0)

            avg_efficiency = (
                total_efficiency / completed_routes if completed_routes > 0 else 0
            )

            # Generate zone-level suggestions
            if avg_efficiency < 50:
                suggestions.append(
                    "Zone efficiency is below 50%. Review route sequencing and bin assignments."
                )
            if len(routes) < 5:
                suggestions.append("Limited route history. More data needed for accurate recommendations.")
            else:
                suggestions.append("Consistent data available. Optimization model is reliable.")

            cursor.close()
            conn.close()

            return {
                "success": True,
                "zone": zone,
                "routes_count": len(routes),
                "completed_routes": completed_routes,
                "average_efficiency": round(avg_efficiency, 1),
                "suggestions": suggestions,
            }

        except Exception as e:
            return {"success": False, "message": f"Error generating suggestions: {str(e)}"}
