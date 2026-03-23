"""
Basic Waste Report Logging Service
Provides a minimal, focused API to create simple waste log entries.
"""

from datetime import datetime
from models import Database


class BasicWasteLogService:
    """Service class for basic waste report logging operations."""

    @staticmethod
    def log_waste_collection(bin_id, fill_level, timestamp=None):
        """
        Create a basic waste log record.

        Args:
            bin_id (int): Bin identifier.
            fill_level (float): Fill level percentage (0-100).
            timestamp (str, optional): ISO or '%Y-%m-%d %H:%M:%S' timestamp.

        Returns:
            dict: Standard API response with success, message, and log_id.
        """
        if not isinstance(bin_id, int) or bin_id <= 0:
            return {'success': False, 'message': 'bin_id must be a positive integer'}

        if not isinstance(fill_level, (int, float)) or fill_level < 0 or fill_level > 100:
            return {'success': False, 'message': 'fill_level must be between 0 and 100'}

        parsed_timestamp = None
        if timestamp:
            try:
                parsed_timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                try:
                    parsed_timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return {
                        'success': False,
                        'message': "timestamp must be ISO format or '%Y-%m-%d %H:%M:%S'"
                    }

        db = Database()
        cursor = db.connection.cursor(dictionary=True)

        try:
            # Ensure bin exists before inserting a log record.
            cursor.execute("SELECT bin_id FROM bins WHERE bin_id = %s", (bin_id,))
            if not cursor.fetchone():
                return {'success': False, 'message': 'Bin not found'}

            if parsed_timestamp:
                query = """
                    INSERT INTO waste_logs (bin_id, fill_level, notes, timestamp)
                    VALUES (%s, %s, %s, %s)
                """
                params = (bin_id, float(fill_level), 'Basic waste report log', parsed_timestamp)
            else:
                query = """
                    INSERT INTO waste_logs (bin_id, fill_level, notes)
                    VALUES (%s, %s, %s)
                """
                params = (bin_id, float(fill_level), 'Basic waste report log')

            cursor.execute(query, params)
            db.connection.commit()
            log_id = cursor.lastrowid

            return {
                'success': True,
                'message': 'Basic waste report logged successfully',
                'log_id': log_id,
                'data': {
                    'bin_id': bin_id,
                    'fill_level': float(fill_level),
                    'timestamp': (parsed_timestamp or datetime.now()).isoformat()
                }
            }

        except Exception as e:
            db.connection.rollback()
            return {'success': False, 'message': f'Failed to log waste report: {str(e)}'}

        finally:
            cursor.close()
            db.close()
