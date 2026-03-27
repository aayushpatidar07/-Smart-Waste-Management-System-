"""Vehicle Maintenance Tracking Service"""

from models import Database
from datetime import datetime, timedelta


class VehicleMaintenanceService:
    """Service for managing vehicle maintenance records and schedules"""

    def __init__(self):
        self.db = Database()

    def log_maintenance(self, vehicle_id, maintenance_type, description, cost=0):
        """
        Log a maintenance record for a vehicle.

        Args:
            vehicle_id: ID of the vehicle
            maintenance_type: Type of maintenance (oil_change, tire_rotation, inspection, repair, etc.)
            description: Detailed description of maintenance performed
            cost: Cost of maintenance in dollars

        Returns:
            dict with success status, message, maintenance_id, and data
        """
        try:
            # Validate inputs
            if not isinstance(vehicle_id, int) or vehicle_id <= 0:
                return {"success": False, "message": "Invalid vehicle ID"}

            if not maintenance_type or not isinstance(maintenance_type, str):
                return {"success": False, "message": "Invalid maintenance type"}

            if len(description.strip()) < 5:
                return {"success": False, "message": "Description must be at least 5 characters"}

            if cost < 0:
                return {"success": False, "message": "Cost cannot be negative"}

            # Check if vehicle exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Vehicle not found"}

            # Insert maintenance record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO vehicle_maintenance 
                (vehicle_id, maintenance_type, description, cost, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (vehicle_id, maintenance_type, description, cost, timestamp),
            )
            conn.commit()
            maintenance_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": f"Maintenance logged successfully",
                "maintenance_id": maintenance_id,
                "data": {
                    "vehicle_id": vehicle_id,
                    "maintenance_type": maintenance_type,
                    "description": description,
                    "cost": cost,
                    "timestamp": timestamp,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error logging maintenance: {str(e)}"}

    def get_next_maintenance(self, vehicle_id):
        """
        Get recommended next maintenance schedule for a vehicle.

        Args:
            vehicle_id: ID of the vehicle

        Returns:
            dict with maintenance schedule recommendations
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get latest maintenance
            cursor.execute(
                """
                SELECT maintenance_type, timestamp FROM vehicle_maintenance 
                WHERE vehicle_id = %s ORDER BY timestamp DESC LIMIT 1
                """,
                (vehicle_id,),
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if not result:
                return {"success": False, "message": "No maintenance history"}

            maintenance_type, last_time = result
            last_time = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")

            # Recommended intervals (in days)
            intervals = {
                "oil_change": 30,
                "tire_rotation": 60,
                "inspection": 90,
                "filter_replacement": 45,
                "fluid_check": 30,
            }

            days_until_due = intervals.get(maintenance_type, 90)
            next_due = last_time + timedelta(days=days_until_due)

            return {
                "success": True,
                "next_due_date": next_due.strftime("%Y-%m-%d"),
                "days_until_due": (next_due - datetime.now()).days,
                "last_maintenance": last_time.strftime("%Y-%m-%d"),
                "last_type": maintenance_type,
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching schedule: {str(e)}"}
