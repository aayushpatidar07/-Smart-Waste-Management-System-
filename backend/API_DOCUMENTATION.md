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
