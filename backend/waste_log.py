"""
Waste Log Module - Enhanced Version
Handles waste collection logging functionality for monitoring bin fill levels and timestamps.
Professional implementation with comprehensive error handling.
"""

from models import Database
from datetime import datetime, timedelta


class WasteLog:
    """
    Waste Log Service Class
    Provides comprehensive CRUD operations for waste collection logging.
    Tracks bin fill levels, timestamps, and collection notes.
    """
    
    @staticmethod
    def create_waste_log(bin_id, fill_level, notes=None):
        """
        Create a new waste log entry for tracking bin fill levels.
        
        Args:
            bin_id (int): ID of the bin being logged
            fill_level (float): Fill level percentage (0-100)
            notes (str, optional): Additional notes about the collection
            
        Returns:
            dict: Response with success status, log_id, and message
        """
        try:
            # Validate fill level range
            if not (0 <= fill_level <= 100):
                return {
                    'success': False,
                    'message': 'Fill level must be between 0 and 100'
                }
            
            # Verify bin exists in database
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("SELECT bin_id FROM bins WHERE bin_id = %s", (bin_id,))
            bin_exists = cursor.fetchone()
            
            if not bin_exists:
                cursor.close()
                db.close()
                return {
                    'success': False,
                    'message': 'Bin not found'
                }
            
            # Insert waste log entry
            query = """
                INSERT INTO waste_logs (bin_id, fill_level, notes)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (bin_id, fill_level, notes))
            db.connection.commit()
            log_id = cursor.lastrowid
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'message': 'Waste log created successfully',
                'log_id': log_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating waste log: {str(e)}'
            }
    
    @staticmethod
    def get_all_logs(limit=100):
        """
        Retrieve all waste logs with bin details.
        
        Args:
            limit (int): Maximum number of logs to retrieve (default: 100)
            
        Returns:
            dict: Response with success status and list of waste logs
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    wl.log_id,
                    wl.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    wl.fill_level,
                    wl.notes,
                    wl.timestamp
                FROM waste_logs wl
                LEFT JOIN bins b ON wl.bin_id = b.bin_id
                ORDER BY wl.timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            logs = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': logs
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving waste logs: {str(e)}'
            }
    
    @staticmethod
    def get_logs_by_bin(bin_id, limit=50):
        """
        Retrieve waste logs for a specific bin.
        
        Args:
            bin_id (int): ID of the bin
            limit (int): Maximum number of logs to retrieve (default: 50)
            
        Returns:
            dict: Response with success status and list of waste logs for the bin
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    wl.log_id,
                    wl.bin_id,
                    b.bin_code,
                    b.location,
                    wl.fill_level,
                    wl.notes,
                    wl.timestamp
                FROM waste_logs wl
                LEFT JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.bin_id = %s
                ORDER BY wl.timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (bin_id, limit))
            logs = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': logs
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving bin logs: {str(e)}'
            }
    
    @staticmethod
    def get_log_by_id(log_id):
        """
        Retrieve a specific waste log entry by ID.
        
        Args:
            log_id (int): ID of the waste log entry
            
        Returns:
            dict: Response with success status and log data or error message
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    wl.log_id,
                    wl.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    wl.fill_level,
                    wl.notes,
                    wl.timestamp
                FROM waste_logs wl
                LEFT JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.log_id = %s
            """
            cursor.execute(query, (log_id,))
            log = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if log:
                return {
                    'success': True,
                    'data': log
                }
            else:
                return {
                    'success': False,
                    'message': 'Waste log not found'
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving log: {str(e)}'
            }
    
    @staticmethod
    def get_recent_logs(hours=24):
        """
        Retrieve waste logs from the last N hours.
        
        Args:
            hours (int): Number of hours to look back (default: 24)
            
        Returns:
            dict: Response with success status and list of recent waste logs
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            query = """
                SELECT 
                    wl.log_id,
                    wl.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    wl.fill_level,
                    wl.notes,
                    wl.timestamp
                FROM waste_logs wl
                LEFT JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.timestamp >= %s
                ORDER BY wl.timestamp DESC
            """
            cursor.execute(query, (time_threshold,))
            logs = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': logs
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving recent logs: {str(e)}'
            }
    
    @staticmethod
    def delete_log(log_id):
        """
        Delete a waste log entry.
        
        Args:
            log_id (int): ID of the log to delete
            
        Returns:
            dict: Response with success status and message
        """
        try:
            db = Database()
            cursor = db.connection.cursor()
            
            # Check if log exists
            cursor.execute("SELECT log_id FROM waste_logs WHERE log_id = %s", (log_id,))
            if not cursor.fetchone():
                cursor.close()
                db.close()
                return {
                    'success': False,
                    'message': 'Waste log not found'
                }
            
            # Delete the log
            cursor.execute("DELETE FROM waste_logs WHERE log_id = %s", (log_id,))
            db.connection.commit()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'message': 'Waste log deleted successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting waste log: {str(e)}'
            }
