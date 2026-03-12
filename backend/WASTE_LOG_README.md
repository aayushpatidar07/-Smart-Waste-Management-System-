# Waste Logging Module Documentation

## Overview
The Waste Logging Module provides comprehensive functionality for tracking and analyzing waste collection activities across all bins in the Smart Waste Management System.

## Features

### Core Functionality
- **CRUD Operations**: Create, read, update, and delete waste log entries
- **Bulk Operations**: Import multiple logs in a single transaction
- **Data Export**: Export logs to CSV with flexible filtering

### Analytics & Reporting
- **Overall Statistics**: System-wide metrics and distribution analysis
- **Bin History**: Historical trends and fill level patterns per bin
- **Zone Analytics**: Aggregated statistics by geographic zone
- **Daily Summaries**: Comprehensive daily activity reports with hourly breakdowns

### Monitoring & Alerts
- **Threshold Alerts**: Identify bins exceeding fill level thresholds
- **Collection Efficiency**: Analyze collection patterns and activity levels
- **Priority Scoring**: Calculate collection priorities based on fill levels

## API Endpoints

### Basic Operations

#### GET /api/waste-logs
Get all waste logs with optional limit.
- **Query Params**: `limit` (default: 100, max: 10000)
- **Response**: List of waste log objects

#### POST /api/waste-logs/create
Create a new waste log entry.
- **Body**: `{ "bin_id": int, "fill_level": float, "notes": string }`
- **Validation**: fill_level must be 0-100, notes max 1000 chars

#### PUT/PATCH /api/waste-logs/{id}
Update an existing waste log.
- **Body**: `{ "fill_level": float, "notes": string }`
- **Auth**: Required

#### DELETE /api/waste-logs/{id}
Delete a waste log entry.
- **Auth**: Admin/Staff only

### Bulk Operations

#### POST /api/waste-logs/bulk-create
Create multiple logs in one transaction.
- **Body**: `{ "logs": [{ "bin_id": int, "fill_level": float, "notes": string }] }`
- **Limit**: Maximum 1000 records per batch
- **Response**: Includes count of created records and any validation errors

### Analytics Endpoints

#### GET /api/waste-logs/statistics
Get overall system statistics.
- **Response**: Total logs, average fill level, status distribution

#### GET /api/waste-logs/bin-history/{bin_id}
Get historical data for a specific bin.
- **Query Params**: `days` (default: 30)
- **Response**: Bin info, chronological history, trend analysis

#### GET /api/waste-logs/zone-statistics/{zone}
Get aggregated statistics for a zone.
- **Query Params**: `days` (default: 30)
- **Response**: Zone summary, bin count, fill level statistics

#### GET /api/waste-logs/daily-summary
Get comprehensive daily summary.
- **Query Params**: `date` (YYYY-MM-DD, default: today)
- **Response**: Daily stats, hourly distribution, zone breakdown

### Monitoring Endpoints

#### GET /api/waste-logs/alerts
Get bins exceeding fill level thresholds.
- **Query Params**: 
  - `threshold` (default: 80) - Fill level percentage
  - `hours` (default: 24) - Time window to check
- **Response**: List of bins requiring attention

#### GET /api/waste-logs/efficiency
Analyze collection efficiency metrics.
- **Query Params**: `days` (default: 30)
- **Response**: Activity levels, logs per bin, efficiency metrics

### Export Endpoints

#### GET /api/waste-logs/export
Export logs with filtering options.
- **Query Params**: 
  - `start_date` (YYYY-MM-DD)
  - `end_date` (YYYY-MM-DD)
  - `zone` (optional)
- **Limit**: Maximum 10000 records
- **Format**: JSON array suitable for CSV conversion

## Database Schema

### waste_logs Table
```sql
CREATE TABLE waste_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id INT NOT NULL,
    fill_level DECIMAL(5, 2) NOT NULL,
    notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id) ON DELETE CASCADE,
    CONSTRAINT chk_fill_level CHECK (fill_level >= 0 AND fill_level <= 100)
);
```

### Indexes
- `idx_bin_id`: Fast lookup by bin
- `idx_timestamp`: Time-based queries
- `idx_fill_level`: Status filtering
- `idx_bin_timestamp`: Composite index for bin history queries

## Configuration

### Thresholds
- **Critical**: fill_level >= 80%
- **Warning**: fill_level >= 60%
- **Normal**: fill_level < 60%

### Limits
- Maximum logs per query: 10,000
- Default query limit: 100
- Bulk create maximum: 1,000 records
- Notes maximum length: 1,000 characters

### Time Windows
- Default history: 30 days
- Default alerts: 24 hours
- Maximum history: 365 days

## Utility Functions

### Validation
- `validate_fill_level(fill_level)` - Validate fill level input
- `validate_date_range(start, end)` - Validate date range queries

### Analysis
- `calculate_fill_status(fill_level)` - Get status (critical/warning/normal)
- `calculate_collection_priority(fill_level, hours)` - Calculate priority score
- `get_recommended_collection_time(fill_level, rate)` - Get collection recommendation

### Formatting
- `format_waste_log_for_export(logs)` - Format for CSV export
- `get_fill_level_color(fill_level)` - Get color code for visualization
- `generate_waste_log_summary(logs)` - Generate summary statistics

## Usage Examples

### Create Single Log
```javascript
const data = {
    bin_id: 1,
    fill_level: 75.5,
    notes: "Bin almost full, schedule collection soon"
};

fetch('/api/waste-logs/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});
```

### Bulk Import
```javascript
const logs = [
    { bin_id: 1, fill_level: 80, notes: "Critical" },
    { bin_id: 2, fill_level: 45, notes: "Normal" },
    { bin_id: 3, fill_level: 65, notes: "Warning" }
];

fetch('/api/waste-logs/bulk-create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ logs })
});
```

### Get Alerts
```javascript
fetch('/api/waste-logs/alerts?threshold=80&hours=24')
    .then(response => response.json())
    .then(data => {
        console.log(`${data.count} bins need attention`);
        data.data.forEach(alert => {
            console.log(`Bin ${alert.bin_code}: ${alert.fill_level}%`);
        });
    });
```

### Export Data
```javascript
const startDate = '2026-01-01';
const endDate = '2026-03-12';

fetch(`/api/waste-logs/export?start_date=${startDate}&end_date=${endDate}`)
    .then(response => response.json())
    .then(data => {
        // Convert to CSV and download
        const csv = convertToCSV(data.data);
        downloadCSV(csv, 'waste_logs.csv');
    });
```

## Performance Optimization

### Database Indexes
All critical query paths are optimized with appropriate indexes:
- Bin lookup queries use `idx_bin_id`
- Time range queries use `idx_timestamp`
- Status filtering uses `idx_fill_level`
- Bin history uses composite `idx_bin_timestamp`

### Query Limits
All queries implement limits to prevent performance degradation:
- Default limit of 100 records
- Maximum limit of 10,000 records
- Bulk operations capped at 1,000 records

### Caching Opportunities
Consider implementing caching for:
- Overall statistics (5-10 minute TTL)
- Zone statistics (10-15 minute TTL)
- Daily summaries (1 hour TTL for past dates)

## Error Handling

All endpoints return structured error responses:
```json
{
    "success": false,
    "message": "Descriptive error message",
    "error": "Technical error details (if applicable)"
}
```

Common error scenarios:
- Invalid input validation
- Database connection failures
- Foreign key constraint violations
- Query timeouts
- Data not found

## Security Considerations

- **Authentication**: All endpoints require login
- **Authorization**: Delete operations restricted to admin/staff roles
- **Input Validation**: All inputs validated before database operations
- **SQL Injection**: Protected via parameterized queries
- **XSS Prevention**: Notes field sanitized on output

## Future Enhancements

Potential improvements:
- Real-time WebSocket updates for critical alerts
- Predictive analytics using ML for fill rate forecasting
- Automated collection scheduling based on trends
- Mobile app integration for field staff
- Photo attachments for waste logs
- Integration with IoT sensors for automatic logging
- Advanced data visualization dashboards
- Multi-language support for international deployments

## Maintenance

### Regular Tasks
- Monitor database size and archive old logs
- Review and optimize slow queries
- Update thresholds based on operational data
- Clean up orphaned records
- Generate performance reports

### Backup & Recovery
- Regular database backups
- Transaction log backups
- Point-in-time recovery capability
- Disaster recovery procedures

## Support

For issues or questions:
- Check API documentation
- Review error logs
- Consult configuration settings
- Contact system administrator
