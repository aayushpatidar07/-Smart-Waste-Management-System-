"""Predictive Analytics and Forecasting Service"""

from models import Database
from datetime import datetime, timedelta
import statistics


class PredictiveAnalyticsService:
    """Service for predictive analytics and forecasting waste management metrics"""

    def __init__(self):
        self.db = Database()

    def forecast_bin_overflow(self, bin_id, days_ahead=7):
        """
        Forecast when a bin will likely overflow based on historical fill rates.

        Args:
            bin_id: ID of the bin
            days_ahead: Number of days to forecast

        Returns:
            dict with overflow prediction
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get last 30 days of fill level data
            cursor.execute(
                """
                SELECT waste_level, timestamp FROM waste_logs
                WHERE bin_id = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY timestamp ASC
                """,
                (bin_id,),
            )

            records = cursor.fetchall()
            
            if not records or len(records) < 5:
                return {"success": False, "message": "Insufficient historical data"}

            # Extract fill levels
            fill_levels = [record[0] for record in records]
            avg_daily_increase = statistics.mean(fill_levels) / max(len(records) / 30, 1)

            # Get current fill level
            cursor.execute(
                "SELECT waste_level FROM waste_logs WHERE bin_id = %s ORDER BY timestamp DESC LIMIT 1",
                (bin_id,),
            )
            current_result = cursor.fetchone()
            current_level = current_result[0] if current_result else 0

            # Get bin capacity
            cursor.execute("SELECT capacity FROM bins WHERE id = %s", (bin_id,))
            capacity_result = cursor.fetchone()
            capacity = capacity_result[0] if capacity_result else 100

            cursor.close()
            conn.close()

            # Calculate overflow prediction
            threshold = capacity * 0.85
            days_to_threshold = max(0, (threshold - current_level) / avg_daily_increase) if avg_daily_increase > 0 else float('inf')
            
            if days_to_threshold > days_ahead:
                status = "Safe"
                confidence = 95
            elif days_to_threshold > days_ahead * 0.5:
                status = "Warning"
                confidence = 85
            else:
                status = "Critical"
                confidence = 90

            return {
                "success": True,
                "bin_id": bin_id,
                "current_fill_level": round(current_level, 1),
                "threshold_level": round(threshold, 1),
                "days_to_overflow": round(days_to_threshold, 1),
                "overflow_status": status,
                "confidence_percent": confidence,
                "recommendation": "Schedule immediate collection" if status == "Critical" 
                                 else "Plan collection soon" if status == "Warning" 
                                 else "Routine monitoring sufficient",
            }

        except Exception as e:
            return {"success": False, "message": f"Error forecasting overflow: {str(e)}"}

    def predict_collection_demand(self, zone, days_ahead=7):
        """
        Predict waste collection demand for a zone.

        Args:
            zone: Zone name
            days_ahead: Number of days to forecast

        Returns:
            dict with demand prediction
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get historical collection data
            cursor.execute(
                """
                SELECT COUNT(*) as collection_count, DATE(timestamp) as collection_date
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.id
                WHERE b.zone = %s AND wl.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(wl.timestamp)
                ORDER BY collection_date
                """,
                (zone,),
            )

            records = cursor.fetchall()
            cursor.close()
            conn.close()

            if not records or len(records) < 5:
                return {"success": False, "message": "Insufficient historical data"}

            # Calculate average daily collections
            collection_counts = [record[0] for record in records]
            avg_daily_collections = statistics.mean(collection_counts)
            
            # Estimate upcoming demand
            predicted_collections = round(avg_daily_collections * days_ahead)
            
            # Determine trend
            recent_avg = statistics.mean(collection_counts[-7:]) if len(collection_counts) >= 7 else avg_daily_collections
            trend = "increasing" if recent_avg > avg_daily_collections else "decreasing" if recent_avg < avg_daily_collections else "stable"

            return {
                "success": True,
                "zone": zone,
                "forecast_period_days": days_ahead,
                "predicted_collections": predicted_collections,
                "average_daily_collections": round(avg_daily_collections, 1),
                "trend": trend,
                "resource_recommendation": f"Allocate {'additional' if trend == 'increasing' else 'standard'} collection vehicles",
            }

        except Exception as e:
            return {"success": False, "message": f"Error predicting demand: {str(e)}"}

    def forecast_waste_volume(self, days_ahead=30):
        """
        Forecast total system waste volume for upcoming period.

        Args:
            days_ahead: Number of days to forecast

        Returns:
            dict with volume forecast
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get daily waste volume for last 60 days
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, SUM(waste_level) as total_waste
                FROM waste_logs
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 60 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY date
                """,
            )

            records = cursor.fetchall()
            cursor.close()
            conn.close()

            if not records or len(records) < 10:
                return {"success": False, "message": "Insufficient historical data"}

            # Calculate trend
            waste_volumes = [record[1] for record in records]
            avg_daily_volume = statistics.mean(waste_volumes)
            
            # Simple trend analysis
            recent_avg = statistics.mean(waste_volumes[-14:])
            growth_rate = ((recent_avg - avg_daily_volume) / avg_daily_volume) if avg_daily_volume > 0 else 0

            # Forecast
            adjusted_avg = avg_daily_volume * (1 + growth_rate)
            forecasted_volume = adjusted_avg * days_ahead

            return {
                "success": True,
                "forecast_period_days": days_ahead,
                "average_daily_volume": round(avg_daily_volume, 2),
                "recent_trend_growth_percent": round(growth_rate * 100, 1),
                "forecasted_total_volume": round(forecasted_volume, 2),
                "resource_capacity_recommendation": "Monitor landfill capacity" if forecasted_volume > 500000 else "Normal operations",
            }

        except Exception as e:
            return {"success": False, "message": f"Error forecasting volume: {str(e)}"}

    def identify_anomalies(self, bin_id, sensitivity=2.0):
        """
        Identify anomalies in bin fill level patterns.

        Args:
            bin_id: ID of the bin
            sensitivity: Standard deviation multiplier (higher = less sensitive)

        Returns:
            dict with detected anomalies
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get last 30 days of data
            cursor.execute(
                """
                SELECT waste_level, timestamp FROM waste_logs
                WHERE bin_id = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY timestamp DESC
                LIMIT 30
                """,
                (bin_id,),
            )

            records = cursor.fetchall()
            cursor.close()
            conn.close()

            if not records or len(records) < 5:
                return {"success": False, "message": "Insufficient data for anomaly detection"}

            fill_levels = [record[0] for record in records]
            mean_level = statistics.mean(fill_levels)
            std_dev = statistics.stdev(fill_levels) if len(fill_levels) > 1 else 0

            # Find anomalies
            anomalies = []
            threshold = std_dev * sensitivity
            
            for i, level in enumerate(fill_levels):
                if abs(level - mean_level) > threshold:
                    anomalies.append({
                        "fill_level": round(level, 1),
                        "deviation_percent": round(abs(level - mean_level) / mean_level * 100, 1) if mean_level > 0 else 0,
                        "timestamp": records[i][1],
                        "type": "unusually_high" if level > mean_level else "unusually_low",
                    })

            return {
                "success": True,
                "bin_id": bin_id,
                "baseline_level": round(mean_level, 1),
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies[:10],  # Return top 10
                "investigation_recommended": len(anomalies) > 5,
            }

        except Exception as e:
            return {"success": False, "message": f"Error detecting anomalies: {str(e)}"}
