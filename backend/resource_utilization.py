"""Resource Utilization Tracking Service"""

from models import Database
from datetime import datetime, timedelta


class ResourceUtilizationService:
    """Service for tracking and analyzing resource utilization efficiency"""

    def __init__(self):
        self.db = Database()

    def record_bin_utilization(self, bin_id, capacity_ml, waste_collected_ml, collection_date):
        """
        Record bin utilization metrics from a collection.

        Args:
            bin_id: ID of the bin
            capacity_ml: Bin capacity in milliliters
            waste_collected_ml: Actual waste collected in milliliters
            collection_date: Date of collection

        Returns:
            dict with success status and utilization_id
        """
        try:
            # Validate inputs
            if not isinstance(bin_id, int) or bin_id <= 0:
                return {"success": False, "message": "Invalid bin ID"}

            if capacity_ml <= 0 or waste_collected_ml < 0 or waste_collected_ml > capacity_ml:
                return {"success": False, "message": "Invalid capacity or waste values"}

            # Check if bin exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bins WHERE id = %s", (bin_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Bin not found"}

            # Calculate utilization percentage
            utilization_percent = (waste_collected_ml / capacity_ml) * 100

            # Insert record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO bin_utilization 
                (bin_id, capacity_ml, waste_collected_ml, utilization_percent, collection_date, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (bin_id, capacity_ml, waste_collected_ml, utilization_percent, collection_date, timestamp),
            )
            conn.commit()
            utilization_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Bin utilization recorded successfully",
                "utilization_id": utilization_id,
                "data": {
                    "bin_id": bin_id,
                    "utilization_percent": round(utilization_percent, 2),
                    "waste_collected_ml": waste_collected_ml,
                    "capacity_ml": capacity_ml,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error recording utilization: {str(e)}"}

    def get_bin_utilization_analysis(self, bin_id, days=30):
        """
        Analyze bin utilization over time period.

        Args:
            bin_id: ID of the bin
            days: Number of days to analyze

        Returns:
            dict with utilization analytics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                SELECT 
                    COUNT(*) as collections,
                    AVG(utilization_percent) as avg_utilization,
                    MAX(utilization_percent) as max_utilization,
                    MIN(utilization_percent) as min_utilization,
                    SUM(waste_collected_ml) as total_waste
                FROM bin_utilization
                WHERE bin_id = %s AND collection_date >= %s
                """,
                (bin_id, start_date),
            )

            result = cursor.fetchone()

            # Get bin info
            cursor.execute("SELECT location, zone, capacity FROM bins WHERE id = %s", (bin_id,))
            bin_info = cursor.fetchone()

            cursor.close()
            conn.close()

            if not result or result[0] == 0:
                return {"success": False, "message": "No utilization data available"}

            collections, avg_util, max_util, min_util, total_waste = result
            capacity = bin_info[2] if bin_info else 0

            # Determine efficiency rating
            if avg_util >= 70:
                rating = "Excellent"
            elif avg_util >= 50:
                rating = "Good"
            elif avg_util >= 30:
                rating = "Fair"
            else:
                rating = "Poor - Consider relocating or downsizing"

            return {
                "success": True,
                "bin_id": bin_id,
                "location": bin_info[0] if bin_info else "Unknown",
                "zone": bin_info[1] if bin_info else "Unknown",
                "period_days": days,
                "collections": collections,
                "utilization_metrics": {
                    "average_utilization_percent": round(avg_util or 0, 1),
                    "max_utilization_percent": round(max_util or 0, 1),
                    "min_utilization_percent": round(min_util or 0, 1),
                },
                "total_waste_collected_ml": int(total_waste or 0),
                "efficiency_rating": rating,
                "utilization_variance": round((max_util or 0) - (min_util or 0), 1),
            }

        except Exception as e:
            return {"success": False, "message": f"Error analyzing utilization: {str(e)}"}

    def get_route_efficiency(self, route_id, days=30):
        """
        Analyze route collection efficiency.

        Args:
            route_id: ID of the route
            days: Number of days to analyze

        Returns:
            dict with route efficiency metrics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                SELECT 
                    COUNT(*) as collections,
                    AVG(distance_km) as avg_distance,
                    AVG(time_taken_minutes) as avg_time,
                    SUM(waste_collected_ml) as total_waste,
                    AVG(fuel_used) as avg_fuel
                FROM route_collections
                WHERE route_id = %s AND collection_date >= %s
                """,
                (route_id, start_date),
            )

            result = cursor.fetchone()

            if not result or result[0] == 0:
                return {"success": False, "message": "No route collection data available"}

            collections, avg_distance, avg_time, total_waste, avg_fuel = result

            # Calculate efficiency metrics
            waste_per_km = (total_waste or 0) / avg_distance if avg_distance and avg_distance > 0 else 0
            time_per_km = (avg_time or 0) / avg_distance if avg_distance and avg_distance > 0 else 0
            km_per_liter = avg_distance / avg_fuel if avg_fuel and avg_fuel > 0 else 0

            return {
                "success": True,
                "route_id": route_id,
                "period_days": days,
                "total_collections": collections,
                "efficiency_metrics": {
                    "average_distance_km": round(avg_distance or 0, 2),
                    "average_time_minutes": round(avg_time or 0, 2),
                    "waste_per_km_ml": round(waste_per_km, 2),
                    "time_per_km_minutes": round(time_per_km, 2),
                    "kilometers_per_liter": round(km_per_liter, 2),
                },
                "total_waste_collected_ml": int(total_waste or 0),
                "efficiency_score": round(waste_per_km / 100, 1),
            }

        except Exception as e:
            return {"success": False, "message": f"Error analyzing route: {str(e)}"}

    def get_underutilized_resources(self, utilization_threshold=30, days=30):
        """
        Identify underutilized bins and resources.

        Args:
            utilization_threshold: Threshold percentage for underutilization
            days: Number of days to analyze

        Returns:
            dict with list of underutilized resources
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                SELECT 
                    b.id,
                    b.location,
                    b.zone,
                    AVG(bu.utilization_percent) as avg_utilization,
                    COUNT(bu.id) as collections
                FROM bins b
                LEFT JOIN bin_utilization bu ON b.id = bu.bin_id AND bu.collection_date >= %s
                WHERE b.status = 'active'
                GROUP BY b.id, b.location, b.zone
                HAVING AVG(bu.utilization_percent) < %s OR collections = 0
                ORDER BY avg_utilization ASC
                """,
                (start_date, utilization_threshold),
            )

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            underutilized = []
            for row in results:
                bin_id, location, zone, avg_util, collections = row
                underutilized.append({
                    "bin_id": bin_id,
                    "location": location,
                    "zone": zone,
                    "average_utilization": round(avg_util or 0, 1),
                    "collections": collections or 0,
                    "recommendation": "Consider relocating" if (avg_util or 0) < 20 else "Monitor for adjustment",
                })

            return {
                "success": True,
                "period_days": days,
                "threshold_percent": utilization_threshold,
                "underutilized_bins": underutilized,
                "total_underutilized": len(underutilized),
            }

        except Exception as e:
            return {"success": False, "message": f"Error identifying underutilized resources: {str(e)}"}
