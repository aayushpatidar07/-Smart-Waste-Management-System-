"""Environmental Impact Tracking Service"""

from models import Database
from datetime import datetime, timedelta


class EnvironmentalImpactService:
    """Service for tracking and calculating environmental impact metrics"""

    def __init__(self):
        self.db = Database()

    def calculate_carbon_savings(self, waste_recycled_kg, waste_composted_kg):
        """
        Calculate carbon emissions saved through recycling and composting.

        Args:
            waste_recycled_kg: Weight of waste recycled in kg
            waste_composted_kg: Weight of waste composted in kg

        Returns:
            dict with carbon savings calculations
        """
        try:
            if waste_recycled_kg < 0 or waste_composted_kg < 0:
                return {"success": False, "message": "Weights cannot be negative"}

            # Carbon emission factors (kg CO2 per kg of waste diverted)
            recycling_factor = 0.5  # kg CO2 saved per kg recycled
            composting_factor = 1.2  # kg CO2 saved per kg composted

            carbon_from_recycling = waste_recycled_kg * recycling_factor
            carbon_from_composting = waste_composted_kg * composting_factor
            total_carbon_saved = carbon_from_recycling + carbon_from_composting

            # Equivalent calculations
            trees_equivalent = total_carbon_saved / 21  # kg CO2 per tree per year
            car_miles_equivalent = total_carbon_saved / 0.38  # kg CO2 per car mile

            return {
                "success": True,
                "carbon_saved_kg": round(total_carbon_saved, 2),
                "trees_equivalent": round(trees_equivalent, 1),
                "car_miles_offset": round(car_miles_equivalent, 1),
                "recycled_kg": waste_recycled_kg,
                "composted_kg": waste_composted_kg,
                "carbon_from_recycling": round(carbon_from_recycling, 2),
                "carbon_from_composting": round(carbon_from_composting, 2),
            }

        except Exception as e:
            return {"success": False, "message": f"Error calculating carbon: {str(e)}"}

    def record_environmental_impact(self, zone, total_waste_collected_kg, recycled_percentage, 
                                   composted_percentage, landfill_percentage):
        """
        Record daily environmental impact metrics for a zone.

        Args:
            zone: Zone name
            total_waste_collected_kg: Total waste collected in kg
            recycled_percentage: Percentage of waste recycled (0-100)
            composted_percentage: Percentage of waste composted (0-100)
            landfill_percentage: Percentage sent to landfill (0-100)

        Returns:
            dict with recorded impact data and impact_id
        """
        try:
            # Validate percentages sum to 100
            total_percent = recycled_percentage + composted_percentage + landfill_percentage
            if abs(total_percent - 100) > 0.1:
                return {"success": False, "message": f"Percentages must sum to 100 (current: {total_percent}%)"}

            if total_waste_collected_kg < 0:
                return {"success": False, "message": "Waste weight cannot be negative"}

            # Calculate actual weights
            recycled_kg = (total_waste_collected_kg * recycled_percentage) / 100
            composted_kg = (total_waste_collected_kg * composted_percentage) / 100
            landfill_kg = (total_waste_collected_kg * landfill_percentage) / 100

            # Calculate carbon savings
            carbon_result = self.calculate_carbon_savings(recycled_kg, composted_kg)
            
            if not carbon_result.get("success"):
                return carbon_result

            # Record impact
            conn = self.db.get_connection()
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO environmental_impact 
                (zone, total_waste_kg, recycled_kg, composted_kg, landfill_kg, 
                 carbon_saved_kg, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (zone, total_waste_collected_kg, recycled_kg, composted_kg, landfill_kg,
                 carbon_result["carbon_saved_kg"], timestamp),
            )
            conn.commit()
            impact_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Environmental impact recorded",
                "impact_id": impact_id,
                "data": {
                    "zone": zone,
                    "total_waste_kg": total_waste_collected_kg,
                    "recycled_kg": round(recycled_kg, 2),
                    "composted_kg": round(composted_kg, 2),
                    "landfill_kg": round(landfill_kg, 2),
                    "carbon_saved_kg": carbon_result["carbon_saved_kg"],
                    "trees_equivalent": carbon_result["trees_equivalent"],
                    "timestamp": timestamp,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error recording impact: {str(e)}"}

    def get_zone_environmental_summary(self, zone, days=30):
        """
        Get environmental impact summary for a zone over specified period.

        Args:
            zone: Zone name
            days: Number of days to analyze (default: 30)

        Returns:
            dict with environmental metrics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute(
                """
                SELECT 
                    SUM(total_waste_kg) as total_waste,
                    SUM(recycled_kg) as total_recycled,
                    SUM(composted_kg) as total_composted,
                    SUM(landfill_kg) as total_landfill,
                    SUM(carbon_saved_kg) as carbon_saved,
                    COUNT(*) as records,
                    AVG(recycled_kg / total_waste_kg * 100) as avg_recycling_rate
                FROM environmental_impact
                WHERE zone = %s AND DATE(timestamp) >= %s
                """,
                (zone, start_date),
            )
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result or result[5] == 0:
                return {"success": False, "message": "No impact data available"}

            total_waste, total_recycled, total_composted, total_landfill, carbon_saved, records, avg_recycle_rate = result

            # Calculate metrics
            trees_equivalent = (carbon_saved or 0) / 21
            car_miles = (carbon_saved or 0) / 0.38

            return {
                "success": True,
                "zone": zone,
                "period_days": days,
                "total_records": records,
                "total_waste_kg": round(total_waste or 0, 2),
                "total_recycled_kg": round(total_recycled or 0, 2),
                "total_composted_kg": round(total_composted or 0, 2),
                "total_landfill_kg": round(total_landfill or 0, 2),
                "diversion_rate": round(((total_recycled or 0) + (total_composted or 0)) / (total_waste or 1) * 100, 1),
                "carbon_saved_kg": round(carbon_saved or 0, 2),
                "trees_equivalent": round(trees_equivalent, 1),
                "car_miles_offset": round(car_miles, 1),
                "environmental_grade": self._calculate_grade(avg_recycle_rate or 0)
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching summary: {str(e)}"}

    def get_system_wide_impact(self, days=30):
        """
        Get aggregate environmental impact across all zones.

        Args:
            days: Number of days to analyze

        Returns:
            dict with system-wide environmental metrics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute(
                """
                SELECT 
                    COUNT(DISTINCT zone) as zones,
                    SUM(total_waste_kg) as total_waste,
                    SUM(recycled_kg) as total_recycled,
                    SUM(composted_kg) as total_composted,
                    SUM(carbon_saved_kg) as carbon_saved
                FROM environmental_impact
                WHERE DATE(timestamp) >= %s
                """,
                (start_date,),
            )
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result or not result[0]:
                return {"success": False, "message": "No system-wide data available"}

            zones, total_waste, total_recycled, total_composted, carbon_saved = result

            trees_equivalent = (carbon_saved or 0) / 21
            car_miles = (carbon_saved or 0) / 0.38

            return {
                "success": True,
                "period_days": days,
                "zones_active": zones,
                "total_waste_kg": round(total_waste or 0, 2),
                "total_recycled_kg": round(total_recycled or 0, 2),
                "total_composted_kg": round(total_composted or 0, 2),
                "diversion_rate": round(((total_recycled or 0) + (total_composted or 0)) / (total_waste or 1) * 100, 1),
                "carbon_saved_kg": round(carbon_saved or 0, 2),
                "trees_equivalent": round(trees_equivalent, 1),
                "car_miles_offset": round(car_miles, 1),
                "impact_message": f"System saved {round(carbon_saved or 0, 0)} kg CO2 equivalent to {round(trees_equivalent, 0)} trees!"
            }

        except Exception as e:
            return {"success": False, "message": f"Error calculating system impact: {str(e)}"}

    def _calculate_grade(self, recycle_rate):
        """Calculate environmental grade based on recycling rate"""
        if recycle_rate >= 75:
            return "A+"
        elif recycle_rate >= 60:
            return "A"
        elif recycle_rate >= 45:
            return "B"
        elif recycle_rate >= 30:
            return "C"
        else:
            return "D"
