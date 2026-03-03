"""
============================================
Smart Waste Management System - Waste Log Service
============================================
Waste Report Logging Module
Tracks waste collection data entries
Author: Smart Waste Team
============================================
"""

from models import Database
from datetime import datetime


class WasteLog:
    """
    Waste Log Model
    Handles logging of waste collection data with bin_id, fill_level, and timestamp
    """
    
    def __init__(self):
        """Initialize database connection"""
        self.db = Database()
    
    def create_waste_log(self, bin_id, fill_level, notes=''):
        """
        Create a new waste log entry
        
        Args:
            bin_id (int): ID of the waste bin
            fill_level (float): Current fill level percentage (0-100)
            notes (str): Optional notes about the waste log entry
            
        Returns:
            dict: Result with log_id and success status
        """
        try:
            # Validate fill level is within acceptable range
            if not (0 <= fill_level <= 100):
                return {
                    'success': False,
                    'message': 'Fill level must be between 0 and 100'
                }
            
            # Insert waste log entry
            query = """
                INSERT INTO waste_logs (bin_id, fill_level, notes, timestamp)
                VALUES (%s, %s, %s, NOW())
            """
            result = self.db.execute_query(
                query,
                (bin_id, fill_level, notes),
                fetch=False
            )
            
            if result and result['last_id']:
                return {
                    'success': True,
                    'log_id': result['last_id'],
                    'message': 'Waste log entry created successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create waste log entry'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating waste log: {str(e)}'
            }
    
    def get_all_logs(self, limit=100):
        """
        Retrieve all waste log entries
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            list: List of waste log entries with bin details
        """
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
            ORDER BY wl.timestamp DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_logs_by_bin(self, bin_id, limit=50):
        """
        Retrieve waste logs for a specific bin
        
        Args:
            bin_id (int): ID of the waste bin
            limit (int): Maximum number of records to return
            
        Returns:
            list: List of waste log entries for the specified bin
        """
        query = """
            SELECT 
                log_id,
                bin_id,
                fill_level,
                notes,
                timestamp
            FROM waste_logs
            WHERE bin_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (bin_id, limit))
    
    def get_log_by_id(self, log_id):
        """
        Retrieve a specific waste log entry by ID
        
        Args:
            log_id (int): ID of the waste log entry
            
        Returns:
            dict: Waste log entry details or None
        """
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
            WHERE wl.log_id = %s
        """
        result = self.db.execute_query(query, (log_id,))
        return result[0] if result else None
    
    def get_recent_logs(self, hours=24):
        """
        Get waste logs from the last N hours
        
        Args:
            hours (int): Number of hours to look back
            
        Returns:
            list: Recent waste log entries
        """
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
            WHERE wl.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            ORDER BY wl.timestamp DESC
        """
        return self.db.execute_query(query, (hours,))
    
    def delete_log(self, log_id):
        """
        Delete a waste log entry
        
        Args:
            log_id (int): ID of the waste log entry to delete
            
        Returns:
            dict: Result with success status
        """
        query = "DELETE FROM waste_logs WHERE log_id = %s"
        result = self.db.execute_query(query, (log_id,), fetch=False)
        
        if result and result['affected_rows'] > 0:
            return {
                'success': True,
                'message': 'Waste log entry deleted successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to delete waste log entry'
            }
