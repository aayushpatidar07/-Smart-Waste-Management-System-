"""Waste Composition Analysis Service"""

from models import Database
from datetime import datetime, timedelta


class WasteCompositionService:
    """Service for analyzing waste composition and categorization"""

    def __init__(self):
        self.db = Database()

    def record_waste_composition(self, bin_id, organic_percentage, recyclables_percentage, 
                                hazardous_percentage, inert_percentage, notes=""):
        """
        Record waste composition analysis for a bin.

        Args:
            bin_id: ID of the bin
            organic_percentage: Percentage of organic waste (0-100)
            recyclables_percentage: Percentage of recyclables (0-100)
            hazardous_percentage: Percentage of hazardous waste (0-100)
            inert_percentage: Percentage of inert waste (0-100)
            notes: Optional notes about the composition

        Returns:
            dict with success status, message, and composition_id
        """
        try:
            # Validate inputs
            if not isinstance(bin_id, int) or bin_id <= 0:
                return {"success": False, "message": "Invalid bin ID"}

            percentages = [organic_percentage, recyclables_percentage, hazardous_percentage, inert_percentage]
            
            # Check all are numbers and non-negative
            if not all(isinstance(p, (int, float)) and p >= 0 for p in percentages):
                return {"success": False, "message": "All percentages must be non-negative numbers"}
            
            # Check sum equals 100
            total = sum(percentages)
            if abs(total - 100) > 0.1:  # Allow small rounding error
                return {"success": False, "message": f"Percentages must sum to 100 (current: {total}%)"}

            # Check if bin exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bins WHERE id = %s", (bin_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Bin not found"}

            # Insert composition record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO waste_composition 
                (bin_id, organic_percent, recyclables_percent, hazardous_percent, inert_percent, notes, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (bin_id, organic_percentage, recyclables_percentage, hazardous_percentage, inert_percentage, notes, timestamp),
            )
            conn.commit()
            composition_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Waste composition recorded successfully",
                "composition_id": composition_id,
                "data": {
                    "bin_id": bin_id,
                    "organic": organic_percentage,
                    "recyclables": recyclables_percentage,
                    "hazardous": hazardous_percentage,
                    "inert": inert_percentage,
                    "timestamp": timestamp,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error recording composition: {str(e)}"}

    def get_composition_summary(self, bin_id, days=30):
        """
        Get waste composition summary for a bin over specified period.

        Args:
            bin_id: ID of the bin
            days: Number of days to analyze (default: 30)

        Returns:
            dict with composition statistics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Get composition statistics
            cursor.execute(
                """
                SELECT 
                    AVG(organic_percent) as avg_organic,
                    AVG(recyclables_percent) as avg_recyclables,
                    AVG(hazardous_percent) as avg_hazardous,
                    AVG(inert_percent) as avg_inert,
                    COUNT(*) as total_records,
                    MAX(timestamp) as latest_record
                FROM waste_composition
                WHERE bin_id = %s AND DATE(timestamp) >= %s
                """,
                (bin_id, start_date),
            )
            
            result = cursor.fetchone()
            
            # Get bin location
            cursor.execute("SELECT location, zone FROM bins WHERE id = %s", (bin_id,))
            bin_info = cursor.fetchone()
            
            cursor.close()
            conn.close()

            if not result or result[4] == 0:
                return {"success": False, "message": "No composition data available"}

            avg_organic, avg_recyclables, avg_hazardous, avg_inert, count, latest = result
            
            # Determine dominant waste type
            avgs = {
                "organic": avg_organic or 0,
                "recyclables": avg_recyclables or 0,
                "hazardous": avg_hazardous or 0,
                "inert": avg_inert or 0
            }
            dominant_type = max(avgs, key=avgs.get)

            return {
                "success": True,
                "bin_id": bin_id,
                "location": bin_info[0] if bin_info else "Unknown",
                "zone": bin_info[1] if bin_info else "Unknown",
                "period_days": days,
                "total_records": count,
                "latest_record": latest.strftime("%Y-%m-%d %H:%M:%S") if latest else None,
                "average_composition": {
                    "organic": round(avg_organic or 0, 1),
                    "recyclables": round(avg_recyclables or 0, 1),
                    "hazardous": round(avg_hazardous or 0, 1),
                    "inert": round(avg_inert or 0, 1),
                },
                "dominant_waste_type": dominant_type,
                "recommendation": self._get_recommendation(dominant_type)
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching composition: {str(e)}"}

    def get_zone_composition_analysis(self, zone, days=30):
        """
        Get average waste composition for all bins in a zone.

        Args:
            zone: Zone name
            days: Number of days to analyze

        Returns:
            dict with zone-wide composition analysis
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute(
                """
                SELECT 
                    AVG(wc.organic_percent) as avg_organic,
                    AVG(wc.recyclables_percent) as avg_recyclables,
                    AVG(wc.hazardous_percent) as avg_hazardous,
                    AVG(wc.inert_percent) as avg_inert,
                    COUNT(DISTINCT wc.bin_id) as bins_analyzed,
                    COUNT(*) as total_records
                FROM waste_composition wc
                JOIN bins b ON wc.bin_id = b.id
                WHERE b.zone = %s AND DATE(wc.timestamp) >= %s
                """,
                (zone, start_date),
            )
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result or result[5] == 0:
                return {"success": False, "message": "No composition data for zone"}

            avg_organic, avg_recyclables, avg_hazardous, avg_inert, bins_count, total_records = result

            return {
                "success": True,
                "zone": zone,
                "period_days": days,
                "bins_analyzed": bins_count,
                "total_records": total_records,
                "average_composition": {
                    "organic": round(avg_organic or 0, 1),
                    "recyclables": round(avg_recyclables or 0, 1),
                    "hazardous": round(avg_hazardous or 0, 1),
                    "inert": round(avg_inert or 0, 1),
                },
                "high_recyclables": avg_recyclables and avg_recyclables > 40,
                "high_hazardous": avg_hazardous and avg_hazardous > 10,
            }

        except Exception as e:
            return {"success": False, "message": f"Error analyzing zone: {str(e)}"}

    def _get_recommendation(self, waste_type):
        """Get recommendation based on dominant waste type"""
        recommendations = {
            "organic": "Consider composting programs in this area",
            "recyclables": "Implement separate recycling collection",
            "hazardous": "Requires special handling and disposal procedures",
            "inert": "Suitable for landfill or recycling programs"
        }
        return recommendations.get(waste_type, "Review collection strategy")
