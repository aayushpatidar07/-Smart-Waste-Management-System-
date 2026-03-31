"""Bin Sensor Analytics Service"""

from models import Database
from datetime import datetime, timedelta
import statistics


class BinSensorAnalytics:
    """Service for analyzing bin sensor data including fill level, temperature, and condition"""

    def __init__(self):
        self.db = Database()

    def log_sensor_reading(self, bin_id, fill_level, temperature=None, humidity=None, odor_level=None):
        """
        Log sensor reading from a waste bin.

        Args:
            bin_id: ID of the bin
            fill_level: Fill level percentage (0-100)
            temperature: Optional temperature in Celsius
            humidity: Optional humidity percentage
            odor_level: Optional odor level (0-10 scale)

        Returns:
            dict with success status, message, reading_id, and data
        """
        try:
            # Validate inputs
            if not isinstance(bin_id, int) or bin_id <= 0:
                return {"success": False, "message": "Invalid bin ID"}

            if not isinstance(fill_level, (int, float)) or fill_level < 0 or fill_level > 100:
                return {"success": False, "message": "Fill level must be between 0 and 100"}

            if temperature is not None and (temperature < -50 or temperature > 70):
                return {"success": False, "message": "Invalid temperature reading"}

            if humidity is not None and (humidity < 0 or humidity > 100):
                return {"success": False, "message": "Humidity must be between 0 and 100"}

            if odor_level is not None and (odor_level < 0 or odor_level > 10):
                return {"success": False, "message": "Odor level must be between 0 and 10"}

            # Check if bin exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bins WHERE id = %s", (bin_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Bin not found"}

            # Insert sensor reading
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO bin_sensors 
                (bin_id, fill_level, temperature, humidity, odor_level, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (bin_id, fill_level, temperature, humidity, odor_level, timestamp),
            )
            conn.commit()
            reading_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Sensor reading logged successfully",
                "reading_id": reading_id,
                "data": {
                    "bin_id": bin_id,
                    "fill_level": fill_level,
                    "temperature": temperature,
                    "humidity": humidity,
                    "odor_level": odor_level,
                    "timestamp": timestamp,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error logging sensor reading: {str(e)}"}

    def get_sensor_trends(self, bin_id, hours=24):
        """
        Get sensor reading trends for a bin over a time period.

        Args:
            bin_id: ID of the bin
            hours: Number of hours to analyze (default: 24)

        Returns:
            dict with trend analysis including averages, min/max, and status
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get sensor readings
            cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                SELECT fill_level, temperature, humidity, odor_level, timestamp 
                FROM bin_sensors 
                WHERE bin_id = %s AND timestamp >= %s
                ORDER BY timestamp DESC
                """,
                (bin_id, cutoff_time),
            )
            readings = cursor.fetchall()
            cursor.close()
            conn.close()

            if not readings:
                return {"success": False, "message": "No sensor data available"}

            # Extract values
            fill_levels = [r[0] for r in readings if r[0] is not None]
            temperatures = [r[1] for r in readings if r[1] is not None]
            humidities = [r[2] for r in readings if r[2] is not None]
            odor_levels = [r[3] for r in readings if r[3] is not None]

            # Calculate statistics
            result = {
                "success": True,
                "bin_id": bin_id,
                "hours_analyzed": hours,
                "reading_count": len(readings),
                "fill_level": {
                    "current": fill_levels[-1] if fill_levels else 0,
                    "average": round(statistics.mean(fill_levels), 2) if fill_levels else 0,
                    "min": min(fill_levels) if fill_levels else 0,
                    "max": max(fill_levels) if fill_levels else 0,
                    "trend": "increasing" if len(fill_levels) > 1 and fill_levels[-1] > fill_levels[0] else "decreasing",
                } if fill_levels else {},
                "temperature": {
                    "current": temperatures[-1] if temperatures else None,
                    "average": round(statistics.mean(temperatures), 2) if temperatures else None,
                    "min": min(temperatures) if temperatures else None,
                    "max": max(temperatures) if temperatures else None,
                } if temperatures else {},
                "humidity": {
                    "current": humidities[-1] if humidities else None,
                    "average": round(statistics.mean(humidities), 2) if humidities else None,
                    "min": min(humidities) if humidities else None,
                    "max": max(humidities) if humidities else None,
                } if humidities else {},
                "odor_level": {
                    "current": odor_levels[-1] if odor_levels else None,
                    "average": round(statistics.mean(odor_levels), 2) if odor_levels else None,
                    "max": max(odor_levels) if odor_levels else None,
                } if odor_levels else {},
            }

            return result

        except Exception as e:
            return {"success": False, "message": f"Error fetching trends: {str(e)}"}

    def detect_sensor_anomalies(self, bin_id, hours=24):
        """
        Detect anomalies in sensor readings for a bin.

        Args:
            bin_id: ID of the bin
            hours: Number of hours to analyze

        Returns:
            dict with detected anomalies and alerts
        """
        try:
            trends = self.get_sensor_trends(bin_id, hours)
            
            if not trends.get("success"):
                return trends

            anomalies = []

            # Check fill level anomalies
            if "fill_level" in trends:
                fill_data = trends["fill_level"]
                if fill_data.get("current", 0) > 95:
                    anomalies.append({
                        "type": "critical_fill",
                        "severity": "critical",
                        "message": f"Bin fill level critically high: {fill_data['current']}%",
                    })
                elif fill_data.get("current", 0) > 80:
                    anomalies.append({
                        "type": "high_fill",
                        "severity": "warning",
                        "message": f"Bin fill level high: {fill_data['current']}%",
                    })

                if fill_data.get("trend") == "increasing":
                    rate = fill_data.get("max", 0) - fill_data.get("min", 0)
                    if rate > 50:
                        anomalies.append({
                            "type": "rapid_fill",
                            "severity": "warning",
                            "message": f"Rapid fill rate detected: {rate}% change",
                        })

            # Check temperature anomalies
            if "temperature" in trends:
                temp_data = trends["temperature"]
                if temp_data.get("current"):
                    if temp_data["current"] > 60:
                        anomalies.append({
                            "type": "high_temperature",
                            "severity": "warning",
                            "message": f"High temperature detected: {temp_data['current']}°C",
                        })
                    elif temp_data["current"] < -10:
                        anomalies.append({
                            "type": "low_temperature",
                            "severity": "info",
                            "message": f"Low temperature detected: {temp_data['current']}°C",
                        })

            # Check odor level anomalies
            if "odor_level" in trends:
                odor_data = trends["odor_level"]
                if odor_data.get("current", 0) > 8:
                    anomalies.append({
                        "type": "high_odor",
                        "severity": "warning",
                        "message": f"High odor level: {odor_data['current']}/10",
                    })

            return {
                "success": True,
                "bin_id": bin_id,
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
                "status": "critical" if any(a["severity"] == "critical" for a in anomalies) else (
                    "warning" if any(a["severity"] == "warning" for a in anomalies) else "normal"
                ),
            }

        except Exception as e:
            return {"success": False, "message": f"Error detecting anomalies: {str(e)}"}
