"""Citizen Engagement Analytics Service"""

from models import Database
from datetime import datetime, timedelta


class CitizenEngagementService:
    """Service for tracking and analyzing citizen participation in waste management"""

    def __init__(self):
        self.db = Database()

    def record_citizen_report(self, citizen_id, report_type, location, description, status="submitted"):
        """
        Record a citizen report or complaint.

        Args:
            citizen_id: ID of the citizen
            report_type: Type of report (overflow, maintenance, illegal_dumping, etc.)
            location: Location description or bin ID
            description: Detailed report description
            status: Report status (submitted, acknowledged, resolved)

        Returns:
            dict with success status, message, and report_id
        """
        try:
            # Validate inputs
            if not isinstance(citizen_id, int) or citizen_id <= 0:
                return {"success": False, "message": "Invalid citizen ID"}

            if not report_type or not isinstance(report_type, str):
                return {"success": False, "message": "Invalid report type"}

            if len(description.strip()) < 10:
                return {"success": False, "message": "Description must be at least 10 characters"}

            # Check if citizen exists
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'citizen'", (citizen_id,))
            if not cursor.fetchone():
                return {"success": False, "message": "Citizen not found"}

            # Insert report record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO citizen_reports 
                (citizen_id, report_type, location, description, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (citizen_id, report_type, location, description, status, timestamp),
            )
            conn.commit()
            report_id = cursor.lastrowid
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Report submitted successfully",
                "report_id": report_id,
                "data": {
                    "citizen_id": citizen_id,
                    "report_type": report_type,
                    "location": location,
                    "status": status,
                    "created_at": timestamp,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error recording report: {str(e)}"}

    def get_citizen_engagement_score(self, citizen_id):
        """
        Calculate citizen engagement score based on participation.

        Args:
            citizen_id: ID of the citizen

        Returns:
            dict with engagement metrics and score
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get citizen info
            cursor.execute("SELECT name, created_at FROM users WHERE id = %s", (citizen_id,))
            result = cursor.fetchone()
            if not result:
                return {"success": False, "message": "Citizen not found"}

            citizen_name, created_at = result

            # Count reports submitted
            cursor.execute(
                "SELECT COUNT(*) FROM citizen_reports WHERE citizen_id = %s",
                (citizen_id,),
            )
            total_reports = cursor.fetchone()[0]

            # Count resolved reports
            cursor.execute(
                "SELECT COUNT(*) FROM citizen_reports WHERE citizen_id = %s AND status = 'resolved'",
                (citizen_id,),
            )
            resolved_reports = cursor.fetchone()[0]

            # Get member tenure in months
            join_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            tenure_months = max(1, (datetime.now() - join_date).days // 30)

            # Calculate engagement score (0-100)
            report_score = min(40, total_reports * 2)
            resolution_score = min(30, resolved_reports * 3) if total_reports > 0 else 0
            tenure_score = min(30, tenure_months)

            total_score = report_score + resolution_score + tenure_score

            # Determine engagement level
            if total_score >= 80:
                level = "Champion"
            elif total_score >= 60:
                level = "Active"
            elif total_score >= 40:
                level = "Engaged"
            else:
                level = "Participant"

            cursor.close()
            conn.close()

            return {
                "success": True,
                "citizen_id": citizen_id,
                "citizen_name": citizen_name,
                "engagement_score": total_score,
                "engagement_level": level,
                "metrics": {
                    "total_reports": total_reports,
                    "resolved_reports": resolved_reports,
                    "resolution_rate": round((resolved_reports / total_reports * 100), 1) if total_reports > 0 else 0,
                    "member_tenure_months": tenure_months,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Error calculating score: {str(e)}"}

    def get_top_engaged_citizens(self, limit=10, days=30):
        """
        Get top engaged citizens by activity.

        Args:
            limit: Number of citizens to return
            days: Period to analyze

        Returns:
            dict with ranked citizen list
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                SELECT 
                    u.id,
                    u.name,
                    COUNT(cr.id) as report_count,
                    SUM(CASE WHEN cr.status = 'resolved' THEN 1 ELSE 0 END) as resolved_count
                FROM users u
                LEFT JOIN citizen_reports cr ON u.id = cr.citizen_id AND DATE(cr.created_at) >= %s
                WHERE u.role = 'citizen'
                GROUP BY u.id, u.name
                HAVING report_count > 0
                ORDER BY report_count DESC
                LIMIT %s
                """,
                (start_date, limit),
            )

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            citizens = []
            for row in results:
                citizen_id, name, report_count, resolved_count = row
                citizens.append({
                    "rank": len(citizens) + 1,
                    "citizen_id": citizen_id,
                    "citizen_name": name,
                    "reports_submitted": report_count,
                    "reports_resolved": resolved_count or 0,
                    "resolution_rate": round((resolved_count or 0) / report_count * 100, 1) if report_count > 0 else 0,
                })

            return {
                "success": True,
                "period_days": days,
                "top_engaged_citizens": citizens,
                "total_records": len(citizens),
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching top citizens: {str(e)}"}

    def get_report_statistics(self, days=30):
        """
        Get overall report statistics.

        Args:
            days: Period to analyze

        Returns:
            dict with report statistics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_reports,
                    SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'acknowledged' THEN 1 ELSE 0 END) as acknowledged,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                    COUNT(DISTINCT citizen_id) as unique_reporters
                FROM citizen_reports
                WHERE DATE(created_at) >= %s
                """,
                (start_date,),
            )

            result = cursor.fetchone()
            
            # Get report type breakdown
            cursor.execute(
                """
                SELECT report_type, COUNT(*) as count
                FROM citizen_reports
                WHERE DATE(created_at) >= %s
                GROUP BY report_type
                """,
                (start_date,),
            )

            type_breakdown = {}
            for row in cursor.fetchall():
                report_type, count = row
                type_breakdown[report_type] = count

            cursor.close()
            conn.close()

            if not result or result[0] == 0:
                return {"success": False, "message": "No report data available"}

            total, pending, acknowledged, resolved, unique = result

            return {
                "success": True,
                "period_days": days,
                "total_reports": total,
                "report_status": {
                    "pending": pending or 0,
                    "acknowledged": acknowledged or 0,
                    "resolved": resolved or 0,
                },
                "resolution_rate": round((resolved or 0) / total * 100, 1),
                "unique_reporters": unique or 0,
                "average_reports_per_citizen": round(total / unique, 2) if unique > 0 else 0,
                "report_types": type_breakdown,
            }

        except Exception as e:
            return {"success": False, "message": f"Error fetching statistics: {str(e)}"}
