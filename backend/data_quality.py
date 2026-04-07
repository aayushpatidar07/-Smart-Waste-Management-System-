"""Data Quality Assessment Service"""

from models import Database
from datetime import datetime, timedelta


class DataQualityService:
    """Service for assessing and monitoring data quality in the system"""

    def __init__(self):
        self.db = Database()

    def assess_bin_data_quality(self, bin_id, days=30):
        """
        Assess data quality for a specific bin.

        Args:
            bin_id: ID of the bin
            days: Number of days to analyze

        Returns:
            dict with data quality metrics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # Get bin info
            cursor.execute("SELECT location, zone FROM bins WHERE id = %s", (bin_id,))
            bin_info = cursor.fetchone()
            if not bin_info:
                return {"success": False, "message": "Bin not found"}

            # Count total expected readings (daily)
            total_days = days
            expected_readings = total_days

            # Count actual readings
            cursor.execute(
                """
                SELECT COUNT(*) FROM waste_logs 
                WHERE bin_id = %s AND DATE(timestamp) >= %s
                """,
                (bin_id, start_date),
            )
            actual_readings = cursor.fetchone()[0]

            # Get completeness score
            completeness_percent = (actual_readings / expected_readings * 100) if expected_readings > 0 else 0

            # Check for anomalies (unrealistic fill levels)
            cursor.execute(
                """
                SELECT COUNT(*) FROM waste_logs 
                WHERE bin_id = %s AND DATE(timestamp) >= %s 
                AND (fill_level > 100 OR fill_level < 0)
                """,
                (bin_id, start_date),
            )
            anomalies = cursor.fetchone()[0]

            # Check for missing critical fields
            cursor.execute(
                """
                SELECT COUNT(*) FROM waste_logs 
                WHERE bin_id = %s AND DATE(timestamp) >= %s 
                AND (notes IS NULL OR notes = '')
                """,
                (bin_id, start_date),
            )
            missing_notes = cursor.fetchone()[0]

            # Calculate accuracy score
            anomaly_rate = (anomalies / actual_readings * 100) if actual_readings > 0 else 0
            accuracy_percent = max(0, 100 - anomaly_rate)

            # Overall quality score
            quality_score = (completeness_percent * 0.5 + accuracy_percent * 0.5)

            # Determine quality grade
            if quality_score >= 90:
                grade = "A"
                status = "Excellent"
            elif quality_score >= 80:
                grade = "B"
                status = "Good"
            elif quality_score >= 70:
                grade = "C"
                status = "Fair"
            else:
                grade = "D"
                status = "Poor"

            cursor.close()
            conn.close()

            return {
                "success": True,
                "bin_id": bin_id,
                "location": bin_info[0],
                "zone": bin_info[1],
                "period_days": days,
                "data_quality": {
                    "completeness_percent": round(completeness_percent, 1),
                    "accuracy_percent": round(accuracy_percent, 1),
                    "overall_score": round(quality_score, 1),
                },
                "quality_grade": grade,
                "quality_status": status,
                "metrics": {
                    "expected_readings": expected_readings,
                    "actual_readings": actual_readings,
                    "anomalies_detected": anomalies,
                    "missing_notes": missing_notes,
                    "anomaly_rate_percent": round(anomaly_rate, 1),
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error assessing data quality: {str(e)}"}

    def get_system_data_quality_overview(self, days=30):
        """
        Get overall data quality overview for entire system.

        Args:
            days: Number of days to analyze

        Returns:
            dict with system-wide quality metrics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # Get total bins
            cursor.execute("SELECT COUNT(*) FROM bins WHERE status = 'active'")
            total_bins = cursor.fetchone()[0]

            # Count bins with data
            cursor.execute(
                """
                SELECT COUNT(DISTINCT bin_id) FROM waste_logs 
                WHERE DATE(timestamp) >= %s
                """,
                (start_date,),
            )
            bins_with_data = cursor.fetchone()[0]

            # Get average readings per bin
            cursor.execute(
                """
                SELECT COUNT(*) FROM waste_logs 
                WHERE DATE(timestamp) >= %s
                """,
                (start_date,),
            )
            total_readings = cursor.fetchone()[0]

            # Count anomalies
            cursor.execute(
                """
                SELECT COUNT(*) FROM waste_logs 
                WHERE DATE(timestamp) >= %s 
                AND (fill_level > 100 OR fill_level < 0)
                """,
                (start_date,),
            )
            total_anomalies = cursor.fetchone()[0]

            # Get duplicate readings
            cursor.execute(
                """
                SELECT COUNT(*) FROM waste_logs wl1
                WHERE DATE(wl1.timestamp) >= %s
                AND EXISTS (
                    SELECT 1 FROM waste_logs wl2 
                    WHERE wl1.bin_id = wl2.bin_id 
                    AND wl1.fill_level = wl2.fill_level
                    AND DATE(wl1.timestamp) = DATE(wl2.timestamp)
                    AND wl1.id < wl2.id
                )
                """,
                (start_date,),
            )
            duplicate_readings = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            # Calculate metrics
            coverage_percent = (bins_with_data / total_bins * 100) if total_bins > 0 else 0
            avg_readings = (total_readings / bins_with_data) if bins_with_data > 0 else 0
            anomaly_rate = (total_anomalies / total_readings * 100) if total_readings > 0 else 0

            return {
                "success": True,
                "period_days": days,
                "system_overview": {
                    "total_active_bins": total_bins,
                    "bins_with_data": bins_with_data,
                    "data_coverage_percent": round(coverage_percent, 1),
                    "total_readings": total_readings,
                    "average_readings_per_bin": round(avg_readings, 2),
                },
                "quality_metrics": {
                    "anomalies_detected": total_anomalies,
                    "duplicate_readings": duplicate_readings,
                    "anomaly_rate_percent": round(anomaly_rate, 1),
                },
                "data_health": "Good" if coverage_percent >= 80 and anomaly_rate < 5 else "Fair" if coverage_percent >= 60 else "Poor",
            }

        except Exception as e:
            return {"success": False, "message": f"Error getting system overview: {str(e)}"}

    def identify_low_quality_bins(self, quality_threshold=70, days=30):
        """
        Identify bins with low data quality.

        Args:
            quality_threshold: Quality score threshold
            days: Number of days to analyze

        Returns:
            dict with list of low-quality bins
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
                    COUNT(wl.id) as reading_count,
                    SUM(CASE WHEN wl.fill_level > 100 OR wl.fill_level < 0 THEN 1 ELSE 0 END) as anomaly_count
                FROM bins b
                LEFT JOIN waste_logs wl ON b.id = wl.bin_id AND DATE(wl.timestamp) >= %s
                WHERE b.status = 'active'
                GROUP BY b.id, b.location, b.zone
                HAVING COUNT(wl.id) = 0 OR 
                       (SUM(CASE WHEN wl.fill_level > 100 OR wl.fill_level < 0 THEN 1 ELSE 0 END) / COUNT(wl.id) * 100) > %s
                ORDER BY anomaly_count DESC
                """,
                (start_date, 100 - quality_threshold),
            )

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            low_quality_bins = []
            for row in results:
                bin_id, location, zone, reading_count, anomaly_count = row
                quality_score = 0 if reading_count == 0 else max(0, 100 - (anomaly_count / reading_count * 100))
                
                low_quality_bins.append({
                    "bin_id": bin_id,
                    "location": location,
                    "zone": zone,
                    "reading_count": reading_count or 0,
                    "anomaly_count": anomaly_count or 0,
                    "quality_score": round(quality_score, 1),
                    "recommendation": "No recent data - check sensor" if reading_count == 0 else "High anomaly rate - verify readings",
                })

            return {
                "success": True,
                "period_days": days,
                "quality_threshold": quality_threshold,
                "low_quality_bins": low_quality_bins,
                "total_identified": len(low_quality_bins),
            }

        except Exception as e:
            return {"success": False, "message": f"Error identifying low-quality bins: {str(e)}"}
