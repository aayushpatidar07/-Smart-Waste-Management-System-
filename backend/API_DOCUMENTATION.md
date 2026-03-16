# Smart Waste Management System - API Documentation

## Overview
This document describes the REST API endpoints available in the Smart Waste Management System.

## Base URL
```
http://localhost:5000
```

## Authentication
Most endpoints require authentication using session-based cookies.

## Endpoints

### Authentication

#### POST /login
Login to the system
- **Body**: `{ "username": "string", "password": "string" }`
- **Response**: `{ "success": true, "role": "string", "redirect": "string" }`

#### GET /logout
Logout from the system
- **Response**: Redirect to login page

### Bins Management

#### GET /api/bins
Get all waste bins
- **Auth**: Required
- **Response**: `[{ "id": int, "location": "string", "fill_level": int, "status": "string" }]`

#### POST /api/bins
Create a new bin
- **Auth**: Required (Admin)
- **Body**: `{ "location": "string", "capacity": int }`
- **Response**: `{ "success": true, "bin_id": int }`

#### PUT /api/bins/{id}
Update bin information
- **Auth**: Required (Admin)
- **Body**: `{ "fill_level": int, "status": "string" }`
- **Response**: `{ "success": true }`

### Routes Management

#### GET /api/routes
Get optimized collection routes
- **Auth**: Required
- **Response**: `[{ "route_id": int, "bins": [], "distance": float }]`

### Waste Logs Management

#### GET /api/waste-logs
Get all waste logs (with optional limit)
- **Auth**: Required
- **Query Params**: `limit` (optional, default: 100)
- **Response**: `{ "success": true, "data": [{ "log_id": int, "bin_id": int, "fill_level": float, "timestamp": "string", "notes": "string" }] }`

#### POST /api/waste-logs/create
Create a new waste log entry
- **Auth**: Required
- **Body**: `{ "bin_id": int, "fill_level": float, "notes": "string" }`
- **Response**: `{ "success": true, "log_id": int }`

#### PUT/PATCH /api/waste-logs/{id}
Update an existing waste log
- **Auth**: Required
- **Body**: `{ "fill_level": float, "notes": "string" }`
- **Response**: `{ "success": true, "message": "string" }`

#### DELETE /api/waste-logs/{id}
Delete a waste log entry
- **Auth**: Required (Admin/Staff only)
- **Response**: `{ "success": true, "message": "string" }`

#### POST /api/waste-logs/bulk-create
Create multiple waste logs in one request
- **Auth**: Required
- **Body**: `{ "logs": [{ "bin_id": int, "fill_level": float, "notes": "string" }] }`
- **Response**: `{ "success": true, "created": int, "errors": [] }`

#### GET /api/waste-logs/statistics
Get overall waste logging statistics
- **Auth**: Required
- **Response**: `{ "success": true, "data": { "total_logs": int, "avg_fill_level": float, "bins_logged": int, "distribution": {} } }`

#### GET /api/waste-logs/bin-history/{bin_id}
Get historical trend data for a specific bin
- **Auth**: Required
- **Query Params**: `days` (optional, default: 30)
- **Response**: `{ "success": true, "data": { "bin_info": {}, "history": [], "trend": {} } }`

#### GET /api/waste-logs/zone-statistics/{zone}
Get aggregated statistics for a specific zone
- **Auth**: Required
- **Query Params**: `days` (optional, default: 30)
- **Response**: `{ "success": true, "data": { "zone": "string", "total_bins": int, "total_logs": int, "statistics": {} } }`

#### GET /api/waste-logs/export
Export waste logs data with filtering options
- **Auth**: Required
- **Query Params**: `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `zone` (optional)
- **Response**: `{ "success": true, "data": [], "filters": {} }`

#### GET /api/waste-logs/alerts
Get bins exceeding fill level threshold for alerts
- **Auth**: Required
- **Query Params**: `threshold` (default: 80), `hours` (default: 24)
- **Response**: `{ "success": true, "data": [], "count": int, "threshold": float, "hours_checked": int }`

#### GET /api/waste-logs/efficiency
Analyze collection efficiency metrics
- **Auth**: Required
- **Query Params**: `days` (default: 30)
- **Response**: `{ "success": true, "data": { "overall_metrics": {}, "bin_efficiency": [] } }`

#### GET /api/waste-logs/daily-summary
Get comprehensive daily summary of waste logging activity
- **Auth**: Required
- **Query Params**: `date` (YYYY-MM-DD, optional, default: today)
- **Response**: `{ "success": true, "data": { "date": "string", "summary": {}, "hourly_distribution": [], "zone_breakdown": [] } }`

#### GET /api/waste-logs/trend-insights
Get trend insights across bins over a configurable period
- **Auth**: Required
- **Query Params**: `days` (default: 30), `zone` (optional)
- **Response**: `{ "success": true, "data": { "summary": {}, "insights": [] } }`

#### GET /api/waste-logs/high-risk
Get risk-ranked bins based on latest fill level readings
- **Auth**: Required
- **Query Params**: `hours` (default: 24), `min_fill` (default: 70)
- **Response**: `{ "success": true, "data": { "summary": {}, "bins": [] } }`

#### GET /api/waste-logs/zone-risk-heatmap
Get zone-level risk heatmap data for operations planning
- **Auth**: Required
- **Query Params**: `days` (default: 7)
- **Response**: `{ "success": true, "data": { "summary": {}, "zones": [] } }`

### Reports

#### GET /api/reports
Get waste collection reports
- **Auth**: Required
- **Query Params**: `start_date`, `end_date`
- **Response**: `[{ "date": "string", "collections": int, "weight": float }]`

## Error Codes
- **200**: Success
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **500**: Internal Server Error

## Rate Limiting
Currently no rate limiting is implemented.
