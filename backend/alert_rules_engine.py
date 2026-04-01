"""Alert Rules Engine Service"""

from models import Database
from datetime import datetime


class AlertRulesEngine:
    """Service for managing and evaluating alert rules"""

    def __init__(self):
        self.db = Database()

    def create_rule(self, rule_name, condition_type, threshold_value, action_type):
        """
        Create a new alert rule.

        Args:
            rule_name: Name of the alert rule
            condition_type: Type of condition (filled, overflow, offline, maintenance_due)
            threshold_value: Threshold value for the condition
            action_type: Type of action (email, sms, dashboard, all)

        Returns:
            dict with success status, message, and rule_id
        """
        try:
            # Validate inputs
            if not rule_name or len(rule_name.strip()) < 3:
                return {"success": False, "message": "Rule name must be at least 3 characters"}

            valid_conditions = ["filled", "overflow", "offline", "maintenance_due", "temperature"]
            if condition_type not in valid_conditions:
                return {"success": False, "message": f"Invalid condition type. Must be one of: {', '.join(valid_conditions)}"}

            if not isinstance(threshold_value, (int, float)) or threshold_value < 0:
                return {"success": False, "message": "Threshold value must be a non-negative number"}

            valid_actions = ["email", "sms", "dashboard", "all"]
            if action_type not in valid_actions:
                return {"success": False, "message": f"Invalid action type. Must be one of: {', '.join(valid_actions)}"}

            # Insert new rule
            conn = self.db.get_connection()
            cursor = conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO alert_rules 
                (rule_name, condition_type, threshold_value, action_type, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (rule_name, condition_type, threshold_value, action_type, True, created_at),
            )
            conn.commit()
            rule_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Alert rule created successfully",
                "rule_id": rule_id,
                "data": {
                    "rule_name": rule_name,
                    "condition_type": condition_type,
                    "threshold_value": threshold_value,
                    "action_type": action_type,
                    "is_active": True,
                    "created_at": created_at,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error creating rule: {str(e)}"}

    def get_all_rules(self):
        """
        Retrieve all alert rules.

        Returns:
            dict with success status and list of rules
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, rule_name, condition_type, threshold_value, action_type, 
                       is_active, created_at
                FROM alert_rules ORDER BY created_at DESC
                """
            )
            rules = cursor.fetchall()
            cursor.close()
            conn.close()

            rules_list = []
            for rule in rules:
                rules_list.append({
                    "id": rule[0],
                    "rule_name": rule[1],
                    "condition_type": rule[2],
                    "threshold_value": rule[3],
                    "action_type": rule[4],
                    "is_active": bool(rule[5]),
                    "created_at": rule[6],
                })

            return {"success": True, "rules": rules_list, "total": len(rules_list)}

        except Exception as e:
            return {"success": False, "message": f"Error retrieving rules: {str(e)}"}

    def update_rule(self, rule_id, **kwargs):
        """
        Update an alert rule.

        Args:
            rule_id: ID of the rule to update
            **kwargs: Fields to update (rule_name, threshold_value, action_type, is_active)

        Returns:
            dict with success status and message
        """
        try:
            if not isinstance(rule_id, int) or rule_id <= 0:
                return {"success": False, "message": "Invalid rule ID"}

            allowed_fields = ["rule_name", "threshold_value", "action_type", "is_active"]
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not updates:
                return {"success": False, "message": "No valid fields to update"}

            # Validate fields
            if "rule_name" in updates and len(str(updates["rule_name"]).strip()) < 3:
                return {"success": False, "message": "Rule name must be at least 3 characters"}

            if "threshold_value" in updates and not isinstance(updates["threshold_value"], (int, float)):
                return {"success": False, "message": "Threshold value must be a number"}

            if "action_type" in updates and updates["action_type"] not in ["email", "sms", "dashboard", "all"]:
                return {"success": False, "message": "Invalid action type"}

            # Build UPDATE query
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [rule_id]

            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE alert_rules SET {set_clause} WHERE id = %s", values)
            conn.commit()

            if cursor.rowcount == 0:
                return {"success": False, "message": "Rule not found"}

            cursor.close()
            conn.close()

            return {"success": True, "message": "Alert rule updated successfully"}

        except Exception as e:
            return {"success": False, "message": f"Error updating rule: {str(e)}"}

    def delete_rule(self, rule_id):
        """
        Delete an alert rule.

        Args:
            rule_id: ID of the rule to delete

        Returns:
            dict with success status and message
        """
        try:
            if not isinstance(rule_id, int) or rule_id <= 0:
                return {"success": False, "message": "Invalid rule ID"}

            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alert_rules WHERE id = %s", (rule_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return {"success": False, "message": "Rule not found"}

            cursor.close()
            conn.close()

            return {"success": True, "message": "Alert rule deleted successfully"}

        except Exception as e:
            return {"success": False, "message": f"Error deleting rule: {str(e)}"}
