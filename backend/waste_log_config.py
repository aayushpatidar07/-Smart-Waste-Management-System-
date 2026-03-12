"""
Waste Log Configuration
Centralized configuration for waste logging system.
"""

# Fill Level Thresholds
FILL_LEVEL_CRITICAL = 80  # Percentage at which bin is considered critical
FILL_LEVEL_WARNING = 60   # Percentage at which bin is considered warning
FILL_LEVEL_MIN = 0        # Minimum valid fill level
FILL_LEVEL_MAX = 100      # Maximum valid fill level

# Query Limits
MAX_LOGS_PER_QUERY = 10000      # Maximum logs returned in single query
DEFAULT_LOGS_LIMIT = 100         # Default limit for log queries
MAX_BULK_CREATE_SIZE = 1000      # Maximum logs in bulk create operation
MAX_EXPORT_RECORDS = 10000       # Maximum records in export

# Time Windows
DEFAULT_HISTORY_DAYS = 30        # Default days for historical queries
DEFAULT_ALERT_HOURS = 24         # Default hours for alert monitoring
MAX_HISTORY_DAYS = 365           # Maximum days for historical queries

# Data Validation
MAX_NOTES_LENGTH = 1000          # Maximum characters in notes field

# Status Definitions
STATUS_CRITICAL = 'critical'
STATUS_WARNING = 'warning'
STATUS_NORMAL = 'normal'

# Priority Levels (1-10, 10 being highest)
PRIORITY_IMMEDIATE = 10
PRIORITY_URGENT = 8
PRIORITY_HIGH = 6
PRIORITY_MEDIUM = 4
PRIORITY_LOW = 2

# Collection Recommendations
COLLECTION_IMMEDIATE_THRESHOLD = 90    # Fill % requiring immediate collection
COLLECTION_URGENT_THRESHOLD = 80       # Fill % requiring urgent collection
COLLECTION_SCHEDULED_THRESHOLD = 60    # Fill % requiring scheduled collection

# Export Settings
EXPORT_DATE_FORMAT = '%Y-%m-%d'
EXPORT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
EXPORT_CSV_DELIMITER = ','

# Activity Level Classification
ACTIVITY_HIGH_THRESHOLD = 10      # Logs required for high activity classification
ACTIVITY_MEDIUM_THRESHOLD = 5     # Logs required for medium activity classification

# Efficiency Metrics
EFFICIENCY_ANALYSIS_MIN_LOGS = 2  # Minimum logs required for efficiency analysis
EFFICIENCY_TOP_BINS_LIMIT = 50    # Maximum bins in efficiency report

# Error Messages
ERROR_INVALID_BIN_ID = "Invalid bin_id: must be a positive integer"
ERROR_INVALID_FILL_LEVEL = "Invalid fill_level: must be between 0 and 100"
ERROR_INVALID_DATE_FORMAT = "Invalid date format. Use YYYY-MM-DD"
ERROR_DATE_RANGE_INVALID = "Start date cannot be after end date"
ERROR_NOTES_TOO_LONG = f"Notes too long: maximum {MAX_NOTES_LENGTH} characters"
ERROR_BULK_TOO_LARGE = f"Too many logs: maximum {MAX_BULK_CREATE_SIZE} records per batch"
ERROR_NO_UPDATE_DATA = "No update data provided"
ERROR_LOG_NOT_FOUND = "Waste log not found"
ERROR_BIN_NOT_FOUND = "Bin not found"

# Success Messages
SUCCESS_LOG_CREATED = "Waste log created successfully"
SUCCESS_LOG_UPDATED = "Waste log updated successfully"
SUCCESS_LOG_DELETED = "Waste log deleted successfully"
SUCCESS_LOGS_EXPORTED = "Waste logs exported successfully"
SUCCESS_BULK_CREATED = "Bulk logs created successfully"

# Color Codes for UI
COLOR_CRITICAL = '#dc3545'      # Red
COLOR_WARNING_DARK = '#fd7e14'  # Orange
COLOR_WARNING = '#ffc107'       # Yellow
COLOR_SUCCESS_LIGHT = '#20c997' # Teal
COLOR_SUCCESS = '#28a745'       # Green
COLOR_INFO = '#17a2b8'          # Blue
COLOR_SECONDARY = '#6c757d'     # Gray

# Chart Settings
CHART_MAX_DATA_POINTS = 100  # Maximum data points in trend charts
CHART_DEFAULT_HEIGHT = 300   # Default chart height in pixels
