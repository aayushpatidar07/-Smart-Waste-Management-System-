"""Driver Performance Analytics Service"""

from models import Database
from datetime import datetime, timedelta


class DriverPerformanceService:
    """Service for analyzing driver performance metrics"""

    def __init__(self):
        self.db = Database()

    def record_trip_completion(self, driver_id, route_id, bins_collected, time_taken_minutes, distance_km, fuel_used):
        """
        Record a completed trip for performance tracking.

        Args:
            driver_id: ID of the driver
            route_id: ID of the collection route
            bins_collected: Number of bins collected
            time_taken_minutes: Time taken to complete route in minutes
            distance_km: Distance traveled in kilometers
            fuel_used: Fuel consumed in liters

        Returns:
            dict with success status, message, and trip_id
        """
        try:
            # Validate inputs
            if not isinstance(driver_id, int) or driver_id <= 0:
                return {"success": False, "message": "Invalid driver ID"}
            
            if not isinstance(bins_collected, int) or bins_collected < 0:
                return {"success": False, "message": "Invalid bins collected count"}
            
            if time_taken_minutes <= 0 or distance_km <= 0:
                return {"success": False, "message": "Invalid time or distance values"}
            
            if fuel_used < 0:
                return {"success": False, "message": "Invalid fuel usage"}

            # Check if driver exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'staff'", (driver_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Driver not found"}

            # Insert trip record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            efficiency = bins_collected / distance_km if distance_km > 0 else 0
            fuel_efficiency = distance_km / fuel_used if fuel_used > 0 else 0
            
            cursor.execute(
                """
                INSERT INTO driver_trips 
                (driver_id, route_id, bins_collected, time_taken_minutes, distance_km, fuel_used, 
                 efficiency_score, fuel_efficiency, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (driver_id, route_id, bins_collected, time_taken_minutes, distance_km, fuel_used, 
                 efficiency, fuel_efficiency, timestamp),
            )
            conn.commit()
            trip_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Trip recorded successfully",
                "trip_id": trip_id,
                "data": {
                    "driver_id": driver_id,
                    "route_id": route_id,
                    "bins_collected": bins_collected,
                    "time_taken_minutes": time_taken_minutes,
                    "distance_km": distance_km,
                    "fuel_used": fuel_used,
                    "efficiency_score": round(efficiency, 2),
                    "fuel_efficiency": round(fuel_efficiency, 2),
                    "timestamp": timestamp,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error recording trip: {str(e)}"}

    def get_driver_performance_summary(self, driver_id, days=30):
        """
        Get performance summary for a driver over specified period.

        Args:
            driver_id: ID of the driver
            days: Number of days to analyze (default: 30)

        Returns:
            dict with performance metrics and statistics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Get trip statistics
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_trips,
                    SUM(bins_collected) as total_bins,
                    AVG(efficiency_score) as avg_efficiency,
                    AVG(fuel_efficiency) as avg_fuel_efficiency,
                    SUM(distance_km) as total_distance,
                    SUM(fuel_used) as total_fuel,
                    AVG(time_taken_minutes) as avg_time
                FROM driver_trips
                WHERE driver_id = %s AND DATE(timestamp) >= %s
                """,
                (driver_id, start_date),
            )
            
            result = cursor.fetchone()
            
            # Get driver name
            cursor.execute("SELECT name FROM users WHERE id = %s", (driver_id,))
            driver_name = cursor.fetchone()
            
            cursor.close()
            conn.close()

            if not result or result[0] == 0:
                return {"success": False, "message": "No trip data available"}

            total_trips, total_bins, avg_efficiency, avg_fuel_efficiency, total_distance, total_fuel, avg_time = result

            return {
                "success": True,
                "driver_id": driver_id,
                "driver_name": driver_name[0] if driver_name else "Unknown",
                "period_days": days,
                "total_trips": total_trips,
                "total_bins_collected": int(total_bins) if total_bins else 0,
                "average_efficiency": round(avg_efficiency, 2) if avg_efficiency else 0,
                "average_fuel_efficiency": round(avg_fuel_efficiency, 2) if avg_fuel_efficiency else 0,
                "total_distance_km": round(total_distance, 2) if total_distance else 0,
                "total_fuel_liters": round(total_fuel, 2) if total_fuel else 0,
                "average_trip_time_minutes": round(avg_time, 2) if avg_time else 0,
                "performance_rating": "Excellent" if avg_efficiency and avg_efficiency > 0.8 else 
                                     "Good" if avg_efficiency and avg_efficiency > 0.6 else 
                                     "Average" if avg_efficiency and avg_efficiency > 0.4 else "Needs Improvement"
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching performance: {str(e)}"}

    def get_top_drivers(self, limit=5, days=30):
        """
        Get top performing drivers by efficiency score.

        Args:
            limit: Number of drivers to return
            days: Period to analyze

        Returns:
            dict with ranked driver list
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute(
                """
                SELECT 
                    dt.driver_id,
                    u.name,
                    COUNT(*) as trips,
                    AVG(dt.efficiency_score) as avg_efficiency,
                    SUM(dt.bins_collected) as total_bins
                FROM driver_trips dt
                JOIN users u ON dt.driver_id = u.id
                WHERE DATE(dt.timestamp) >= %s
                GROUP BY dt.driver_id, u.name
                ORDER BY avg_efficiency DESC
                LIMIT %s
                """,
                (start_date, limit),
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            drivers = []
            for row in results:
                drivers.append({
                    "rank": len(drivers) + 1,
                    "driver_id": row[0],
                    "driver_name": row[1],
                    "trips": row[2],
                    "average_efficiency": round(row[3], 2),
                    "total_bins": int(row[4]) if row[4] else 0,
                })

            return {
                "success": True,
                "period_days": days,
                "top_drivers": drivers,
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching top drivers: {str(e)}"}
