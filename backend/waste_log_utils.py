"""
Waste Log Utilities Module
Helper functions and utilities for waste logging operations.
"""

from datetime import datetime, timedelta
import csv
import io


def validate_fill_level(fill_level):
    """
    Validate fill level input.
    
    Args:
        fill_level: The fill level value to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if fill_level is None:
        return False, "Fill level is required"
    
    try:
        fill_level = float(fill_level)
    except (ValueError, TypeError):
        return False, "Fill level must be a number"
    
    if fill_level < 0 or fill_level > 100:
        return False, "Fill level must be between 0 and 100"
    
    return True, None


def validate_date_range(start_date, end_date):
    """
    Validate date range for queries.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        tuple: (is_valid, error_message, parsed_start, parsed_end)
    """
    try:
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = None
            
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = None
        
        if start and end and start > end:
            return False, "Start date cannot be after end date", None, None
        
        return True, None, start, end
        
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD", None, None


def calculate_fill_status(fill_level):
    """
    Calculate status based on fill level.
    
    Args:
        fill_level (float): Fill level percentage
        
    Returns:
        str: Status ('critical', 'warning', 'normal')
    """
    if fill_level >= 80:
        return 'critical'
    elif fill_level >= 60:
        return 'warning'
    else:
        return 'normal'


def get_fill_level_color(fill_level):
    """
    Get color code for fill level visualization.
    
    Args:
        fill_level (float): Fill level percentage
        
    Returns:
        str: Color code
    """
    if fill_level >= 90:
        return '#dc3545'  # danger
    elif fill_level >= 80:
        return '#fd7e14'  # warning-dark
    elif fill_level >= 60:
        return '#ffc107'  # warning
    elif fill_level >= 40:
        return '#20c997'  # success-light
    else:
        return '#28a745'  # success


def format_waste_log_for_export(logs):
    """
    Format waste logs for CSV export.
    
    Args:
        logs (list): List of log dictionaries
        
    Returns:
        str: CSV formatted string
    """
    if not logs:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=logs[0].keys())
    writer.writeheader()
    writer.writerows(logs)
    
    return output.getvalue()


def calculate_collection_priority(fill_level, last_collection_hours=None):
    """
    Calculate collection priority score.
    
    Args:
        fill_level (float): Current fill level percentage
        last_collection_hours (int, optional): Hours since last collection
        
    Returns:
        int: Priority score (1-10, 10 being highest priority)
    """
    # Base priority on fill level
    if fill_level >= 90:
        base_priority = 10
    elif fill_level >= 80:
        base_priority = 8
    elif fill_level >= 70:
        base_priority = 6
    elif fill_level >= 60:
        base_priority = 4
    else:
        base_priority = 2
    
    # Adjust for time since last collection
    if last_collection_hours:
        if last_collection_hours > 48:
            base_priority = min(10, base_priority + 2)
        elif last_collection_hours > 24:
            base_priority = min(10, base_priority + 1)
    
    return base_priority


def generate_waste_log_summary(logs):
    """
    Generate summary statistics from waste logs.
    
    Args:
        logs (list): List of waste log dictionaries
        
    Returns:
        dict: Summary statistics
    """
    if not logs:
        return {
            'total_logs': 0,
            'avg_fill_level': 0,
            'max_fill_level': 0,
            'min_fill_level': 0,
            'critical_count': 0,
            'warning_count': 0,
            'normal_count': 0
        }
    
    fill_levels = [log['fill_level'] for log in logs]
    
    critical = sum(1 for fl in fill_levels if fl >= 80)
    warning = sum(1 for fl in fill_levels if 60 <= fl < 80)
    normal = sum(1 for fl in fill_levels if fl < 60)
    
    return {
        'total_logs': len(logs),
        'avg_fill_level': round(sum(fill_levels) / len(fill_levels), 2),
        'max_fill_level': max(fill_levels),
        'min_fill_level': min(fill_levels),
        'critical_count': critical,
        'warning_count': warning,
        'normal_count': normal
    }


def get_recommended_collection_time(fill_level, fill_rate_per_day=None):
    """
    Recommend optimal collection time based on fill level and rate.
    
    Args:
        fill_level (float): Current fill level percentage
        fill_rate_per_day (float, optional): Average daily fill rate
        
    Returns:
        dict: Recommendation with urgency and estimated days
    """
    if fill_level >= 90:
        return {
            'urgency': 'immediate',
            'message': 'Collection required immediately',
            'estimated_days': 0
        }
    elif fill_level >= 80:
        return {
            'urgency': 'urgent',
            'message': 'Collection required within 24 hours',
            'estimated_days': 1
        }
    elif fill_rate_per_day and fill_rate_per_day > 0:
        remaining_capacity = 80 - fill_level
        days_until_critical = int(remaining_capacity / fill_rate_per_day)
        
        return {
            'urgency': 'scheduled',
            'message': f'Schedule collection within {days_until_critical} days',
            'estimated_days': days_until_critical
        }
    else:
        return {
            'urgency': 'normal',
            'message': 'No immediate collection required',
            'estimated_days': None
        }
