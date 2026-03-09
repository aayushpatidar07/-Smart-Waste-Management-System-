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
    
    @staticmethod
    def get_statistics(days=7):
        """
        Get comprehensive statistics for waste logs over a specified period.
        
        Args:
            days (int): Number of days to analyze (default: 7)
            
        Returns:
            dict: Response with success status and statistics data
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            time_threshold = datetime.now() - timedelta(days=days)
            
            # Get overall statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_logs,
                    AVG(fill_level) as avg_fill_level,
                    MAX(fill_level) as max_fill_level,
                    MIN(fill_level) as min_fill_level,
                    COUNT(DISTINCT bin_id) as bins_logged
                FROM waste_logs
                WHERE timestamp >= %s
            """
            cursor.execute(stats_query, (time_threshold,))
            overall_stats = cursor.fetchone()
            
            # Get fill level distribution
            distribution_query = """
                SELECT 
                    CASE 
                        WHEN fill_level < 25 THEN 'Low (0-25%)'
                        WHEN fill_level < 50 THEN 'Medium (25-50%)'
                        WHEN fill_level < 75 THEN 'High (50-75%)'
                        ELSE 'Critical (75-100%)'
                    END as fill_range,
                    COUNT(*) as count
                FROM waste_logs
                WHERE timestamp >= %s
                GROUP BY fill_range
                ORDER BY 
                    CASE 
                        WHEN fill_level < 25 THEN 1
                        WHEN fill_level < 50 THEN 2
                        WHEN fill_level < 75 THEN 3
                        ELSE 4
                    END
            """
            cursor.execute(distribution_query, (time_threshold,))
            distribution = cursor.fetchall()
            
            # Get top bins by log count
            top_bins_query = """
                SELECT 
                    b.bin_code,
                    b.location,
                    b.zone,
                    COUNT(*) as log_count,
                    AVG(wl.fill_level) as avg_fill
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.timestamp >= %s
                GROUP BY b.bin_id, b.bin_code, b.location, b.zone
                ORDER BY log_count DESC
                LIMIT 10
            """
            cursor.execute(top_bins_query, (time_threshold,))
            top_bins = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': {
                    'period_days': days,
                    'overall': overall_stats,
                    'distribution': distribution,
                    'top_bins': top_bins
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving statistics: {str(e)}'
            }
    
    @staticmethod
    def get_bin_history(bin_id, days=30):
        """
        Get fill level history for a specific bin with trend analysis.
        
        Args:
            bin_id (int): ID of the bin
            days (int): Number of days of history (default: 30)
            
        Returns:
            dict: Response with success status and bin history data
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            time_threshold = datetime.now() - timedelta(days=days)
            
            # Get bin info
            bin_query = """
                SELECT bin_code, location, zone, capacity
                FROM bins
                WHERE bin_id = %s
            """
            cursor.execute(bin_query, (bin_id,))
            bin_info = cursor.fetchone()
            
            if not bin_info:
                cursor.close()
                db.close()
                return {
                    'success': False,
                    'message': 'Bin not found'
                }
            
            # Get history data
            history_query = """
                SELECT 
                    log_id,
                    fill_level,
                    notes,
                    timestamp
                FROM waste_logs
                WHERE bin_id = %s AND timestamp >= %s
                ORDER BY timestamp ASC
            """
            cursor.execute(history_query, (bin_id, time_threshold))
            history = cursor.fetchall()
            
            # Calculate trend statistics
            if history:
                fill_levels = [record['fill_level'] for record in history]
                avg_fill = sum(fill_levels) / len(fill_levels)
                trend = 'increasing' if len(fill_levels) > 1 and fill_levels[-1] > fill_levels[0] else 'decreasing'
            else:
                avg_fill = 0
                trend = 'no_data'
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': {
                    'bin_info': bin_info,
                    'history': history,
                    'analytics': {
                        'total_logs': len(history),
                        'average_fill_level': round(avg_fill, 2) if history else 0,
                        'trend': trend,
                        'period_days': days
                    }
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving bin history: {str(e)}'
            }
