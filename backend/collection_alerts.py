"""Collection Alerts Service for Waste Management"""

from models import Database
from datetime import datetime, timedelta


class CollectionAlertsService:
    """Service for managing and tracking collection alerts for waste bins"""

    def __init__(self):
        self.db = Database()

    def create_alert(self, bin_id, alert_type, priority, message):
        """
        Create a new collection alert.

        Args:
            bin_id: ID of the bin
            alert_type: Type of alert (overflow, delayed_collection, maintenance_required, etc.)
            priority: Priority level (low, medium, high, critical)
            message: Alert message/description

        Returns:
            dict with success status, message, alert_id, and data
        """
        try:
            # Validate inputs
            if not isinstance(bin_id, int) or bin_id <= 0:
                return {"success": False, "message": "Invalid bin ID"}

            valid_types = ["overflow", "delayed_collection", "maintenance_required", "sensor_failure", "low_battery"]
            if alert_type not in valid_types:
                return {"success": False, "message": f"Invalid alert type. Must be one of: {', '.join(valid_types)}"}

            valid_priorities = ["low", "medium", "high", "critical"]
            if priority not in valid_priorities:
                return {"success": False, "message": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}

            if not message or len(message.strip()) < 5:
                return {"success": False, "message": "Message must be at least 5 characters"}

            # Check if bin exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bins WHERE id = %s", (bin_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Bin not found"}

            # Insert alert record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO collection_alerts 
                (bin_id, alert_type, priority, message, created_at, is_resolved)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (bin_id, alert_type, priority, message, timestamp, 0),
            )
            conn.commit()
            alert_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Alert created successfully",
                "alert_id": alert_id,
                "data": {
                    "bin_id": bin_id,
                    "alert_type": alert_type,
                    "priority": priority,
                    "message": message,
                    "created_at": timestamp,
                    "is_resolved": False,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error creating alert: {str(e)}"}

    def get_active_alerts(self, priority_filter=None):
        """
        Get all active (unresolved) alerts.

        Args:
            priority_filter: Optional priority level to filter by (low, medium, high, critical)

        Returns:
            dict with success status and list of active alerts
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            if priority_filter:
                cursor.execute(
                    """
                    SELECT id, bin_id, alert_type, priority, message, created_at 
                    FROM collection_alerts 
                    WHERE is_resolved = 0 AND priority = %s
                    ORDER BY created_at DESC
                    """,
                    (priority_filter,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, bin_id, alert_type, priority, message, created_at 
                    FROM collection_alerts 
                    WHERE is_resolved = 0
                    ORDER BY priority DESC, created_at DESC
                    """
                )

            alerts = cursor.fetchall()
            cursor.close()
            conn.close()

            alert_list = [
                {
                    "id": alert[0],
                    "bin_id": alert[1],
                    "alert_type": alert[2],
                    "priority": alert[3],
                    "message": alert[4],
                    "created_at": alert[5],
                }
                for alert in alerts
            ]

            return {
                "success": True,
                "active_alerts_count": len(alert_list),
                "alerts": alert_list,
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching alerts: {str(e)}"}

    def resolve_alert(self, alert_id, resolution_notes=""):
        """
        Mark an alert as resolved.

        Args:
            alert_id: ID of the alert to resolve
            resolution_notes: Optional notes about resolution

        Returns:
            dict with success status and message
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Check if alert exists
            cursor.execute("SELECT id FROM collection_alerts WHERE id = %s", (alert_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Alert not found"}

            # Update alert to resolved
            resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                UPDATE collection_alerts 
                SET is_resolved = 1, resolved_at = %s, resolution_notes = %s
                WHERE id = %s
                """,
                (resolved_at, resolution_notes, alert_id),
            )
            conn.commit()
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Alert resolved successfully",
                "resolved_at": resolved_at,
            }

        except Exception as e:
            return {"success": False, "message": f"Error resolving alert: {str(e)}"}

    def get_alerts_by_bin(self, bin_id, include_resolved=False):
        """
        Get all alerts for a specific bin.

        Args:
            bin_id: ID of the bin
            include_resolved: Whether to include resolved alerts

        Returns:
            dict with success status and alert history
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            if include_resolved:
                cursor.execute(
                    """
                    SELECT id, alert_type, priority, message, created_at, is_resolved, resolved_at 
                    FROM collection_alerts 
                    WHERE bin_id = %s
                    ORDER BY created_at DESC
                    """,
                    (bin_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, alert_type, priority, message, created_at, is_resolved, resolved_at 
                    FROM collection_alerts 
                    WHERE bin_id = %s AND is_resolved = 0
                    ORDER BY created_at DESC
                    """,
                    (bin_id,),
                )

            alerts = cursor.fetchall()
            cursor.close()
            conn.close()

            alert_list = [
                {
                    "id": alert[0],
                    "alert_type": alert[1],
                    "priority": alert[2],
                    "message": alert[3],
                    "created_at": alert[4],
                    "is_resolved": bool(alert[5]),
                    "resolved_at": alert[6],
                }
                for alert in alerts
            ]

            return {
                "success": True,
                "bin_id": bin_id,
                "active_count": sum(1 for a in alert_list if not a["is_resolved"]),
                "alerts": alert_list,
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching bin alerts: {str(e)}"}
