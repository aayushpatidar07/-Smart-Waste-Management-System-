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
    
    @staticmethod
    def update_waste_log(log_id, fill_level=None, notes=None):
        """
        Update an existing waste log entry.
        
        Args:
            log_id (int): ID of the log to update
            fill_level (float, optional): New fill level percentage (0-100)
            notes (str, optional): New notes
            
        Returns:
            dict: Response with success status and message
        """
        try:
            # Validate fill level if provided
            if fill_level is not None and not (0 <= fill_level <= 100):
                return {
                    'success': False,
                    'message': 'Fill level must be between 0 and 100'
                }
            
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            # Check if log exists
            cursor.execute("SELECT log_id FROM waste_logs WHERE log_id = %s", (log_id,))
            if not cursor.fetchone():
                cursor.close()
                db.close()
                return {
                    'success': False,
                    'message': 'Waste log not found'
                }
            
            # Build update query dynamically based on provided fields
            update_fields = []
            params = []
            
            if fill_level is not None:
                update_fields.append("fill_level = %s")
                params.append(fill_level)
            
            if notes is not None:
                update_fields.append("notes = %s")
                params.append(notes)
            
            if not update_fields:
                cursor.close()
                db.close()
                return {
                    'success': False,
                    'message': 'No fields to update'
                }
            
            # Execute update
            params.append(log_id)
            query = f"UPDATE waste_logs SET {', '.join(update_fields)} WHERE log_id = %s"
            cursor.execute(query, params)
            db.connection.commit()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'message': 'Waste log updated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating waste log: {str(e)}'
            }
    
    @staticmethod
    def bulk_create_logs(log_entries):
        """
        Create multiple waste log entries at once for efficient batch processing.
        
        Args:
            log_entries (list): List of dicts with keys: bin_id, fill_level, notes (optional)
            
        Returns:
            dict: Response with success status, created count, and any errors
        """
        try:
            if not log_entries or not isinstance(log_entries, list):
                return {
                    'success': False,
                    'message': 'Invalid log entries data'
                }
            
            db = Database()
            cursor = db.connection.cursor()
            
            created_count = 0
            errors = []
            
            for idx, entry in enumerate(log_entries):
                try:
                    bin_id = entry.get('bin_id')
                    fill_level = entry.get('fill_level')
                    notes = entry.get('notes')
                    
                    # Validate entry
                    if not bin_id or fill_level is None:
                        errors.append(f"Entry {idx + 1}: Missing required fields")
                        continue
                    
                    if not (0 <= fill_level <= 100):
                        errors.append(f"Entry {idx + 1}: Fill level must be between 0 and 100")
                        continue
                    
                    # Insert log
                    query = """
                        INSERT INTO waste_logs (bin_id, fill_level, notes)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(query, (bin_id, fill_level, notes))
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Entry {idx + 1}: {str(e)}")
            
            db.connection.commit()
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'message': f'Bulk import completed: {created_count} created',
                'created_count': created_count,
                'total_entries': len(log_entries),
                'errors': errors if errors else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error in bulk create: {str(e)}'
            }
    
    @staticmethod
    def get_zone_statistics(zone, days=7):
        """
        Get statistics for waste logs in a specific zone.
        
        Args:
            zone (str): Zone name to analyze
            days (int): Number of days to analyze (default: 7)
            
        Returns:
            dict: Response with zone-specific statistics
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            time_threshold = datetime.now() - timedelta(days=days)
            
            # Get zone statistics
            stats_query = """
                SELECT 
                    b.zone,
                    COUNT(wl.log_id) as total_logs,
                    AVG(wl.fill_level) as avg_fill_level,
                    MAX(wl.fill_level) as max_fill_level,
                    MIN(wl.fill_level) as min_fill_level,
                    COUNT(DISTINCT wl.bin_id) as bins_in_zone
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE b.zone = %s AND wl.timestamp >= %s
                GROUP BY b.zone
            """
            cursor.execute(stats_query, (zone, time_threshold))
            zone_stats = cursor.fetchone()
            
            # Get bin-level details for the zone
            bins_query = """
                SELECT 
                    b.bin_code,
                    b.location,
                    COUNT(wl.log_id) as log_count,
                    AVG(wl.fill_level) as avg_fill,
                    MAX(wl.timestamp) as last_logged
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE b.zone = %s AND wl.timestamp >= %s
                GROUP BY b.bin_id, b.bin_code, b.location
                ORDER BY log_count DESC
            """
            cursor.execute(bins_query, (zone, time_threshold))
            bins_in_zone = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            if not zone_stats:
                return {
                    'success': True,
                    'data': {
                        'zone': zone,
                        'message': 'No logs found for this zone in the specified period',
                        'bins': []
                    }
                }
            
            return {
                'success': True,
                'data': {
                    'zone': zone,
                    'period_days': days,
                    'statistics': zone_stats,
                    'bins': bins_in_zone
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving zone statistics: {str(e)}'
            }
    
    @staticmethod
    def export_logs_data(start_date=None, end_date=None, zone=None):
        """
        Export waste logs data with flexible filtering for reporting.
        
        Args:
            start_date (str, optional): Start date (YYYY-MM-DD format)
            end_date (str, optional): End date (YYYY-MM-DD format)
            zone (str, optional): Filter by zone
            
        Returns:
            dict: Response with exportable log data
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            # Build query with optional filters
            query = """
                SELECT 
                    wl.log_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    b.capacity,
                    wl.fill_level,
                    wl.notes,
                    wl.timestamp,
                    DATE_FORMAT(wl.timestamp, '%Y-%m-%d') as log_date,
                    TIME_FORMAT(wl.timestamp, '%H:%i:%s') as log_time
                FROM waste_logs wl
                LEFT JOIN bins b ON wl.bin_id = b.bin_id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(wl.timestamp) >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(wl.timestamp) <= %s"
                params.append(end_date)
            
            if zone:
                query += " AND b.zone = %s"
                params.append(zone)
            
            query += " ORDER BY wl.timestamp DESC LIMIT 10000"
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': logs,
                'count': len(logs),
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'zone': zone
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error exporting logs: {str(e)}'
            }
    
    @staticmethod
    def get_alerts_by_threshold(threshold=80, hours=24):
        """
        Get bins that have exceeded a fill level threshold in recent logs.
        Useful for generating alerts and prioritizing collection routes.
        
        Args:
            threshold (float): Fill level threshold percentage (default: 80)
            hours (int): Number of hours to look back (default: 24)
            
        Returns:
            dict: Response with bins exceeding threshold
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            query = """
                SELECT 
                    b.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    b.capacity,
                    wl.fill_level,
                    wl.timestamp,
                    wl.notes
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.fill_level >= %s 
                  AND wl.timestamp >= %s
                  AND wl.log_id IN (
                      SELECT MAX(log_id) 
                      FROM waste_logs 
                      WHERE timestamp >= %s
                      GROUP BY bin_id
                  )
                ORDER BY wl.fill_level DESC, wl.timestamp DESC
            """
            cursor.execute(query, (threshold, time_threshold, time_threshold))
            alerts = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': alerts,
                'count': len(alerts),
                'threshold': threshold,
                'hours_checked': hours
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving alerts: {str(e)}'
            }
    
    @staticmethod
    def get_collection_efficiency(days=30):
        """
        Analyze collection efficiency by measuring time between high fill levels.
        Helps optimize collection schedules and route planning.
        
        Args:
            days (int): Number of days to analyze (default: 30)
            
        Returns:
            dict: Response with efficiency metrics and recommendations
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            time_threshold = datetime.now() - timedelta(days=days)
            
            # Get bins with multiple log entries
            efficiency_query = """
                SELECT 
                    b.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    COUNT(wl.log_id) as log_count,
                    AVG(wl.fill_level) as avg_fill,
                    MAX(wl.fill_level) as max_fill,
                    MIN(wl.fill_level) as min_fill,
                    STDDEV(wl.fill_level) as fill_variance,
                    DATEDIFF(MAX(wl.timestamp), MIN(wl.timestamp)) as days_logged,
                    CASE 
                        WHEN COUNT(wl.log_id) >= 10 THEN 'High Activity'
                        WHEN COUNT(wl.log_id) >= 5 THEN 'Medium Activity'
                        ELSE 'Low Activity'
                    END as activity_level
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.timestamp >= %s
                GROUP BY b.bin_id, b.bin_code, b.location, b.zone
                HAVING log_count >= 2
                ORDER BY log_count DESC, avg_fill DESC
                LIMIT 50
            """
            cursor.execute(efficiency_query, (time_threshold,))
            efficiency_data = cursor.fetchall()
            
            # Calculate overall efficiency metrics
            if efficiency_data:
                total_bins_analyzed = len(efficiency_data)
                avg_logs_per_bin = sum(row['log_count'] for row in efficiency_data) / total_bins_analyzed
                high_activity_bins = sum(1 for row in efficiency_data if row['activity_level'] == 'High Activity')
                
                overall_metrics = {
                    'total_bins_analyzed': total_bins_analyzed,
                    'average_logs_per_bin': round(avg_logs_per_bin, 2),
                    'high_activity_bins': high_activity_bins,
                    'analysis_period_days': days
                }
            else:
                overall_metrics = {
                    'message': 'Insufficient data for efficiency analysis',
                    'analysis_period_days': days
                }
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': {
                    'overall_metrics': overall_metrics,
                    'bin_efficiency': efficiency_data
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error analyzing efficiency: {str(e)}'
            }
    
    @staticmethod
    def get_daily_summary(date=None):
        """
        Get a comprehensive daily summary of waste logging activity.
        
        Args:
            date (str, optional): Date in YYYY-MM-DD format (default: today)
            
        Returns:
            dict: Response with daily summary statistics
        """
        try:
            if date is None:
                date = datetime.now().date()
            else:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            
            db = Database()
            cursor = db.connection.cursor(dictionary=True)
            
            # Get daily statistics
            daily_stats_query = """
                SELECT 
                    COUNT(DISTINCT wl.log_id) as total_logs,
                    COUNT(DISTINCT wl.bin_id) as bins_logged,
                    AVG(wl.fill_level) as avg_fill_level,
                    MAX(wl.fill_level) as max_fill_level,
                    MIN(wl.fill_level) as min_fill_level,
                    SUM(CASE WHEN wl.fill_level >= 80 THEN 1 ELSE 0 END) as critical_logs,
                    SUM(CASE WHEN wl.fill_level >= 60 AND wl.fill_level < 80 THEN 1 ELSE 0 END) as warning_logs,
                    SUM(CASE WHEN wl.fill_level < 60 THEN 1 ELSE 0 END) as normal_logs
                FROM waste_logs wl
                WHERE DATE(wl.timestamp) = %s
            """
            cursor.execute(daily_stats_query, (date,))
            daily_stats = cursor.fetchone()
            
            # Get hourly distribution
            hourly_query = """
                SELECT 
                    HOUR(timestamp) as hour,
                    COUNT(*) as log_count,
                    AVG(fill_level) as avg_fill
                FROM waste_logs
                WHERE DATE(timestamp) = %s
                GROUP BY HOUR(timestamp)
                ORDER BY hour
            """
            cursor.execute(hourly_query, (date,))
            hourly_data = cursor.fetchall()
            
            # Get top zones for the day
            zone_query = """
                SELECT 
                    b.zone,
                    COUNT(wl.log_id) as log_count,
                    AVG(wl.fill_level) as avg_fill
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE DATE(wl.timestamp) = %s
                GROUP BY b.zone
                ORDER BY log_count DESC
            """
            cursor.execute(zone_query, (date,))
            zone_data = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return {
                'success': True,
                'data': {
                    'date': str(date),
                    'summary': daily_stats,
                    'hourly_distribution': hourly_data,
                    'zone_breakdown': zone_data
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving daily summary: {str(e)}'
            }

    @staticmethod
    def get_trend_insights(days=30, zone=None):
        """
        Get trend insights across bins over a configurable time window.

        Args:
            days (int): Number of days to analyze (default: 30)
            zone (str, optional): Restrict analysis to a specific zone

        Returns:
            dict: Trend insights with rising/critical bins and summary metrics
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)

            time_threshold = datetime.now() - timedelta(days=days)

            where_clause = "WHERE wl.timestamp >= %s"
            params = [time_threshold]

            if zone:
                where_clause += " AND b.zone = %s"
                params.append(zone)

            # Compare last and first reading in the selected window for each bin.
            trend_query = f"""
                SELECT
                    b.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    COUNT(wl.log_id) AS reading_count,
                    ROUND(MIN(wl.fill_level), 2) AS min_fill,
                    ROUND(MAX(wl.fill_level), 2) AS max_fill,
                    ROUND(AVG(wl.fill_level), 2) AS avg_fill,
                    ROUND(
                        SUBSTRING_INDEX(
                            GROUP_CONCAT(wl.fill_level ORDER BY wl.timestamp ASC),
                            ',',
                            1
                        ),
                        2
                    ) AS first_fill,
                    ROUND(
                        SUBSTRING_INDEX(
                            GROUP_CONCAT(wl.fill_level ORDER BY wl.timestamp DESC),
                            ',',
                            1
                        ),
                        2
                    ) AS last_fill,
                    MAX(wl.timestamp) AS last_seen
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                {where_clause}
                GROUP BY b.bin_id, b.bin_code, b.location, b.zone
                HAVING reading_count >= 2
                ORDER BY last_fill DESC
                LIMIT 100
            """

            cursor.execute(trend_query, tuple(params))
            rows = cursor.fetchall()

            enriched = []
            for row in rows:
                delta = round(float(row['last_fill']) - float(row['first_fill']), 2)
                trend = 'rising' if delta > 0 else ('falling' if delta < 0 else 'stable')

                row['delta_fill'] = delta
                row['trend'] = trend
                row['needs_attention'] = float(row['last_fill']) >= 80 or delta >= 15
                enriched.append(row)

            rising_bins = [r for r in enriched if r['trend'] == 'rising']
            critical_bins = [r for r in enriched if float(r['last_fill']) >= 80]
            rapid_risers = [r for r in enriched if r['delta_fill'] >= 15]

            response = {
                'period_days': days,
                'zone': zone,
                'total_bins_analyzed': len(enriched),
                'rising_bins': len(rising_bins),
                'critical_bins': len(critical_bins),
                'rapid_risers': len(rapid_risers),
                'top_attention_bins': sorted(
                    [r for r in enriched if r['needs_attention']],
                    key=lambda x: (float(x['last_fill']), x['delta_fill']),
                    reverse=True
                )[:10]
            }

            cursor.close()
            db.close()

            return {
                'success': True,
                'data': {
                    'summary': response,
                    'insights': enriched
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving trend insights: {str(e)}'
            }

    @staticmethod
    def get_high_risk_bins(hours=24, min_fill=70):
        """
        Get high-risk bins based on latest fill level and stale timestamps.

        Args:
            hours (int): Lookback window for recent logs
            min_fill (float): Minimum fill level to include

        Returns:
            dict: High-risk bin list with risk scores
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)

            lookback = datetime.now() - timedelta(hours=hours)

            query = """
                SELECT
                    b.bin_id,
                    b.bin_code,
                    b.location,
                    b.zone,
                    wl.fill_level,
                    wl.timestamp,
                    TIMESTAMPDIFF(HOUR, wl.timestamp, NOW()) AS hours_since_log
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.timestamp >= %s
                  AND wl.log_id IN (
                      SELECT MAX(log_id)
                      FROM waste_logs
                      WHERE timestamp >= %s
                      GROUP BY bin_id
                  )
                  AND wl.fill_level >= %s
                ORDER BY wl.fill_level DESC, wl.timestamp ASC
                LIMIT 100
            """
            cursor.execute(query, (lookback, lookback, min_fill))
            rows = cursor.fetchall()

            for row in rows:
                fill = float(row['fill_level'])
                stale_bonus = 10 if row['hours_since_log'] >= 12 else 0
                row['risk_score'] = round(fill + stale_bonus, 2)
                row['risk_level'] = (
                    'critical' if fill >= 85 else
                    'high' if fill >= 75 else
                    'moderate'
                )

            rows = sorted(rows, key=lambda r: r['risk_score'], reverse=True)

            summary = {
                'hours': hours,
                'min_fill': min_fill,
                'count': len(rows),
                'critical_count': len([r for r in rows if r['risk_level'] == 'critical']),
                'high_count': len([r for r in rows if r['risk_level'] == 'high'])
            }

            cursor.close()
            db.close()

            return {
                'success': True,
                'data': {
                    'summary': summary,
                    'bins': rows
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving high-risk bins: {str(e)}'
            }

    @staticmethod
    def get_zone_risk_heatmap(days=7):
        """
        Get zone-level risk heatmap data for operations planning.

        Args:
            days (int): Number of days to analyze (default: 7)

        Returns:
            dict: Zone-level risk metrics and overall summary
        """
        try:
            db = Database()
            cursor = db.connection.cursor(dictionary=True)

            since = datetime.now() - timedelta(days=days)

            query = """
                SELECT
                    b.zone,
                    COUNT(DISTINCT b.bin_id) AS bins_in_zone,
                    COUNT(wl.log_id) AS total_logs,
                    ROUND(AVG(wl.fill_level), 2) AS avg_fill_level,
                    ROUND(MAX(wl.fill_level), 2) AS peak_fill_level,
                    SUM(CASE WHEN wl.fill_level >= 85 THEN 1 ELSE 0 END) AS critical_events,
                    SUM(CASE WHEN wl.fill_level >= 70 AND wl.fill_level < 85 THEN 1 ELSE 0 END) AS high_events,
                    MAX(wl.timestamp) AS latest_log
                FROM waste_logs wl
                JOIN bins b ON wl.bin_id = b.bin_id
                WHERE wl.timestamp >= %s
                GROUP BY b.zone
                ORDER BY avg_fill_level DESC, critical_events DESC
            """
            cursor.execute(query, (since,))
            zones = cursor.fetchall()

            for zone in zones:
                avg_fill = float(zone['avg_fill_level'] or 0)
                critical_events = int(zone['critical_events'] or 0)
                zone['risk_score'] = round(avg_fill + (critical_events * 2), 2)
                zone['risk_level'] = (
                    'critical' if avg_fill >= 80 or critical_events >= 5 else
                    'high' if avg_fill >= 70 or critical_events >= 2 else
                    'moderate' if avg_fill >= 55 else
                    'low'
                )

            summary = {
                'days': days,
                'zones_analyzed': len(zones),
                'critical_zones': len([z for z in zones if z['risk_level'] == 'critical']),
                'high_zones': len([z for z in zones if z['risk_level'] == 'high']),
                'overall_avg_fill': round(
                    sum(float(z['avg_fill_level'] or 0) for z in zones) / len(zones),
                    2
                ) if zones else 0
            }

            cursor.close()
            db.close()

            return {
                'success': True,
                'data': {
                    'summary': summary,
                    'zones': zones
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving zone risk heatmap: {str(e)}'
            }
