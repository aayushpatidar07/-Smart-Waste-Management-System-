"""
============================================
Smart Waste Management System - Models
============================================
Database models and connection management
Author: Smart Waste Team
IEEE SRS Compliant
============================================
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class Database:
    """
    Database connection manager
    Handles MySQL database connections and operations
    """
    
    def __init__(self):
        """Initialize database connection parameters"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'smart_waste_db')
        self.connection = None
        
    def connect(self):
        """
        Establish connection to MySQL database
        Returns: connection object or None
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                return self.connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None, fetch=True):
        """
        Execute SQL query with parameters
        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch: Whether to fetch results
        Returns: Query results or affected rows
        """
        try:
            connection = self.connect()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                    cursor.close()
                    self.disconnect()
                    return result
                else:
                    connection.commit()
                    affected_rows = cursor.rowcount
                    last_id = cursor.lastrowid
                    cursor.close()
                    self.disconnect()
                    return {'affected_rows': affected_rows, 'last_id': last_id}
        except Error as e:
            print(f"Database error: {e}")
            return None


class User:
    """
    User Model
    Represents system users (admin, staff, citizen)
    """
    
    def __init__(self):
        self.db = Database()
    
    def authenticate(self, username, password):
        """
        Authenticate user login
        Args:
            username: User's username
            password: User's password
        Returns: User data if authenticated, None otherwise
        """
        query = """
            SELECT user_id, username, full_name, email, role, phone, address
            FROM users 
            WHERE username = %s AND password = %s AND status = 'active'
        """
        result = self.db.execute_query(query, (username, password))
        
        if result and len(result) > 0:
            # Update last login
            update_query = "UPDATE users SET last_login = NOW() WHERE user_id = %s"
            self.db.execute_query(update_query, (result[0]['user_id'],), fetch=False)
            return result[0]
        return None
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def create_user(self, username, password, full_name, email, phone, role, address=''):
        """Create new user"""
        query = """
            INSERT INTO users (username, password, full_name, email, phone, role, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(
            query, 
            (username, password, full_name, email, phone, role, address),
            fetch=False
        )
    
    def get_all_users(self, role=None):
        """Get all users, optionally filtered by role"""
        if role:
            query = "SELECT * FROM users WHERE role = %s ORDER BY created_at DESC"
            return self.db.execute_query(query, (role,))
        else:
            query = "SELECT * FROM users ORDER BY created_at DESC"
            return self.db.execute_query(query)


class Bin:
    """
    Smart Bin Model
    Manages waste bin data and operations
    """
    
    def __init__(self):
        self.db = Database()
    
    def get_all_bins(self):
        """Get all bins with their current status"""
        query = """
            SELECT bin_id, bin_code, location, latitude, longitude, 
                   capacity, waste_level, bin_type, status, zone, last_updated
            FROM bins 
            ORDER BY waste_level DESC
        """
        return self.db.execute_query(query)
    
    def get_bin_by_id(self, bin_id):
        """Get specific bin details"""
        query = "SELECT * FROM bins WHERE bin_id = %s"
        result = self.db.execute_query(query, (bin_id,))
        return result[0] if result else None
    
    def get_full_bins(self, threshold=80):
        """
        Get bins that are above threshold capacity
        Default threshold: 80%
        """
        query = """
            SELECT * FROM bins 
            WHERE waste_level >= %s AND status = 'active'
            ORDER BY waste_level DESC
        """
        return self.db.execute_query(query, (threshold,))
    
    def update_waste_level(self, bin_id, waste_level):
        """Update bin waste level"""
        query = """
            UPDATE bins 
            SET waste_level = %s, last_updated = NOW()
            WHERE bin_id = %s
        """
        result = self.db.execute_query(query, (waste_level, bin_id), fetch=False)
        
        # Create alert if bin is full (>= 80%)
        if waste_level >= 80:
            self.create_full_bin_alert(bin_id, waste_level)
        
        return result
    
    def create_full_bin_alert(self, bin_id, waste_level):
        """Create alert when bin reaches threshold"""
        bin_data = self.get_bin_by_id(bin_id)
        if bin_data:
            severity = 'critical' if waste_level >= 90 else 'warning'
            message = f"{bin_data['bin_code']} at {bin_data['location']} has reached {waste_level}% capacity"
            
            query = """
                INSERT INTO alerts (bin_id, alert_type, message, severity, status)
                VALUES (%s, 'full_bin', %s, %s, 'active')
            """
            self.db.execute_query(query, (bin_id, message, severity), fetch=False)
    
    def get_bins_by_zone(self, zone):
        """Get all bins in a specific zone"""
        query = "SELECT * FROM bins WHERE zone = %s"
        return self.db.execute_query(query, (zone,))
    
    def get_bin_history(self, bin_id, days=7):
        """Get sensor log history for a bin"""
        query = """
            SELECT * FROM sensor_logs 
            WHERE bin_id = %s 
            AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY timestamp DESC
        """
        return self.db.execute_query(query, (bin_id, days))


class Vehicle:
    """
    Vehicle Model
    Manages waste collection vehicles
    """
    
    def __init__(self):
        self.db = Database()
    
    def get_all_vehicles(self):
        """Get all vehicles"""
        query = "SELECT * FROM vehicles ORDER BY vehicle_number"
        return self.db.execute_query(query)
    
    def get_vehicle_by_id(self, vehicle_id):
        """Get specific vehicle details"""
        query = "SELECT * FROM vehicles WHERE vehicle_id = %s"
        result = self.db.execute_query(query, (vehicle_id,))
        return result[0] if result else None
    
    def update_vehicle_location(self, vehicle_id, latitude, longitude):
        """Update vehicle GPS location"""
        query = """
            UPDATE vehicles 
            SET current_latitude = %s, current_longitude = %s, 
                last_location_update = NOW()
            WHERE vehicle_id = %s
        """
        return self.db.execute_query(query, (latitude, longitude, vehicle_id), fetch=False)
    
    def update_vehicle_status(self, vehicle_id, status, current_load=None):
        """Update vehicle status and load"""
        if current_load is not None:
            query = """
                UPDATE vehicles 
                SET status = %s, current_load = %s
                WHERE vehicle_id = %s
            """
            return self.db.execute_query(query, (status, current_load, vehicle_id), fetch=False)
        else:
            query = "UPDATE vehicles SET status = %s WHERE vehicle_id = %s"
            return self.db.execute_query(query, (status, vehicle_id), fetch=False)
    
    def get_available_vehicles(self):
        """Get vehicles available for route assignment"""
        query = "SELECT * FROM vehicles WHERE status = 'available'"
        return self.db.execute_query(query)


class Route:
    """
    Route Model
    Manages waste collection routes
    """
    
    def __init__(self):
        self.db = Database()
    
    def create_route(self, route_name, vehicle_id, route_date, start_time, bin_ids):
        """
        Create new collection route
        Args:
            route_name: Name of the route
            vehicle_id: Assigned vehicle ID
            route_date: Date of collection
            start_time: Start time
            bin_ids: List of bin IDs in route
        """
        # Create route
        query = """
            INSERT INTO routes (route_name, vehicle_id, route_date, start_time, 
                               total_bins, status)
            VALUES (%s, %s, %s, %s, %s, 'planned')
        """
        result = self.db.execute_query(
            query, 
            (route_name, vehicle_id, route_date, start_time, len(bin_ids)),
            fetch=False
        )
        
        if result and result['last_id']:
            route_id = result['last_id']
            
            # Add bins to route
            for idx, bin_id in enumerate(bin_ids, 1):
                bin_query = """
                    INSERT INTO route_bins (route_id, bin_id, sequence_order)
                    VALUES (%s, %s, %s)
                """
                self.db.execute_query(bin_query, (route_id, bin_id, idx), fetch=False)
            
            return route_id
        return None
    
    def get_all_routes(self, date=None):
        """Get all routes, optionally filtered by date"""
        if date:
            query = """
                SELECT r.*, v.vehicle_number, v.driver_name
                FROM routes r
                LEFT JOIN vehicles v ON r.vehicle_id = v.vehicle_id
                WHERE r.route_date = %s
                ORDER BY r.start_time
            """
            return self.db.execute_query(query, (date,))
        else:
            query = """
                SELECT r.*, v.vehicle_number, v.driver_name
                FROM routes r
                LEFT JOIN vehicles v ON r.vehicle_id = v.vehicle_id
                ORDER BY r.route_date DESC, r.start_time
            """
            return self.db.execute_query(query)
    
    def get_route_details(self, route_id):
        """Get complete route details with bins"""
        route_query = """
            SELECT r.*, v.vehicle_number, v.driver_name, v.driver_phone
            FROM routes r
            LEFT JOIN vehicles v ON r.vehicle_id = v.vehicle_id
            WHERE r.route_id = %s
        """
        route = self.db.execute_query(route_query, (route_id,))
        
        if route:
            bins_query = """
                SELECT rb.*, b.bin_code, b.location, b.waste_level, b.latitude, b.longitude
                FROM route_bins rb
                JOIN bins b ON rb.bin_id = b.bin_id
                WHERE rb.route_id = %s
                ORDER BY rb.sequence_order
            """
            bins = self.db.execute_query(bins_query, (route_id,))
            
            return {
                'route': route[0],
                'bins': bins
            }
        return None
    
    def update_route_status(self, route_id, status):
        """Update route status"""
        query = "UPDATE routes SET status = %s WHERE route_id = %s"
        return self.db.execute_query(query, (status, route_id), fetch=False)


class WasteReport:
    """
    Waste Report Model
    Manages citizen-reported issues
    """
    
    def __init__(self):
        self.db = Database()
    
    def create_report(self, citizen_id, bin_id, report_type, description, 
                     location, latitude=None, longitude=None, priority='medium'):
        """Create new waste report"""
        query = """
            INSERT INTO waste_reports 
            (citizen_id, bin_id, report_type, description, location, 
             latitude, longitude, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """
        return self.db.execute_query(
            query,
            (citizen_id, bin_id, report_type, description, location, 
             latitude, longitude, priority),
            fetch=False
        )
    
    def get_all_reports(self, status=None):
        """Get all reports, optionally filtered by status"""
        if status:
            query = """
                SELECT wr.*, u.full_name as citizen_name, b.bin_code, b.location as bin_location
                FROM waste_reports wr
                LEFT JOIN users u ON wr.citizen_id = u.user_id
                LEFT JOIN bins b ON wr.bin_id = b.bin_id
                WHERE wr.status = %s
                ORDER BY wr.priority DESC, wr.reported_at DESC
            """
            return self.db.execute_query(query, (status,))
        else:
            query = """
                SELECT wr.*, u.full_name as citizen_name, b.bin_code, b.location as bin_location
                FROM waste_reports wr
                LEFT JOIN users u ON wr.citizen_id = u.user_id
                LEFT JOIN bins b ON wr.bin_id = b.bin_id
                ORDER BY wr.reported_at DESC
            """
            return self.db.execute_query(query)
    
    def update_report_status(self, report_id, status, resolved_by=None, notes=''):
        """Update report status and resolution"""
        if status == 'resolved':
            query = """
                UPDATE waste_reports 
                SET status = %s, resolved_at = NOW(), resolved_by = %s, 
                    resolution_notes = %s
                WHERE report_id = %s
            """
            return self.db.execute_query(query, (status, resolved_by, notes, report_id), fetch=False)
        else:
            query = "UPDATE waste_reports SET status = %s WHERE report_id = %s"
            return self.db.execute_query(query, (status, report_id), fetch=False)
    
    def get_citizen_reports(self, citizen_id):
        """Get all reports by a specific citizen"""
        query = """
            SELECT wr.*, b.bin_code, b.location as bin_location
            FROM waste_reports wr
            LEFT JOIN bins b ON wr.bin_id = b.bin_id
            WHERE wr.citizen_id = %s
            ORDER BY wr.reported_at DESC
        """
        return self.db.execute_query(query, (citizen_id,))


class Alert:
    """
    Alert Model
    Manages system alerts and notifications
    """
    
    def __init__(self):
        self.db = Database()
    
    def get_active_alerts(self):
        """Get all active alerts"""
        query = """
            SELECT a.*, b.bin_code, b.location
            FROM alerts a
            LEFT JOIN bins b ON a.bin_id = b.bin_id
            WHERE a.status = 'active'
            ORDER BY a.severity DESC, a.created_at DESC
        """
        return self.db.execute_query(query)
    
    def acknowledge_alert(self, alert_id, user_id):
        """Acknowledge an alert"""
        query = """
            UPDATE alerts 
            SET status = 'acknowledged', acknowledged_at = NOW(), acknowledged_by = %s
            WHERE alert_id = %s
        """
        return self.db.execute_query(query, (user_id, alert_id), fetch=False)
    
    def resolve_alert(self, alert_id):
        """Resolve an alert"""
        query = """
            UPDATE alerts 
            SET status = 'resolved', resolved_at = NOW()
            WHERE alert_id = %s
        """
        return self.db.execute_query(query, (alert_id,), fetch=False)


class Analytics:
    """
    Analytics Model
    Provides data for dashboard and reports
    """
    
    def __init__(self):
        self.db = Database()
    
    def get_dashboard_stats(self):
        """Get key statistics for dashboard"""
        stats = {}
        
        # Total bins
        query = "SELECT COUNT(*) as total FROM bins WHERE status = 'active'"
        result = self.db.execute_query(query)
        stats['total_bins'] = result[0]['total'] if result else 0
        
        # Full bins (>= 80%)
        query = "SELECT COUNT(*) as count FROM bins WHERE waste_level >= 80 AND status = 'active'"
        result = self.db.execute_query(query)
        stats['full_bins'] = result[0]['count'] if result else 0
        
        # Today's collections
        query = "SELECT COUNT(*) as count FROM collection_logs WHERE DATE(collection_time) = CURDATE()"
        result = self.db.execute_query(query)
        stats['today_collections'] = result[0]['count'] if result else 0
        
        # Active alerts
        query = "SELECT COUNT(*) as count FROM alerts WHERE status = 'active'"
        result = self.db.execute_query(query)
        stats['active_alerts'] = result[0]['count'] if result else 0
        
        # Pending reports
        query = "SELECT COUNT(*) as count FROM waste_reports WHERE status = 'pending'"
        result = self.db.execute_query(query)
        stats['pending_reports'] = result[0]['count'] if result else 0
        
        # Active vehicles
        query = "SELECT COUNT(*) as count FROM vehicles WHERE status IN ('available', 'on-route')"
        result = self.db.execute_query(query)
        stats['active_vehicles'] = result[0]['count'] if result else 0
        
        return stats
    
    def get_waste_trend_data(self, days=7):
        """Get waste level trend data for charts"""
        query = """
            SELECT DATE(timestamp) as date, 
                   AVG(waste_level) as avg_level,
                   MAX(waste_level) as max_level
            FROM sensor_logs
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(timestamp)
            ORDER BY date
        """
        return self.db.execute_query(query, (days,))
    
    def get_zone_statistics(self):
        """Get statistics by zone"""
        query = """
            SELECT zone,
                   COUNT(*) as total_bins,
                   AVG(waste_level) as avg_waste_level,
                   SUM(CASE WHEN waste_level >= 80 THEN 1 ELSE 0 END) as full_bins
            FROM bins
            WHERE status = 'active'
            GROUP BY zone
            ORDER BY zone
        """
        return self.db.execute_query(query)
    
    def get_collection_efficiency(self, days=30):
        """Calculate collection efficiency"""
        query = """
            SELECT 
                COUNT(*) as total_routes,
                SUM(bins_collected) as total_collected,
                SUM(total_bins) as total_planned,
                ROUND(AVG(bins_collected * 100.0 / total_bins), 2) as avg_efficiency
            FROM routes
            WHERE route_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            AND status = 'completed'
        """
        result = self.db.execute_query(query, (days,))
        return result[0] if result else None


class Schedule:
    """
    Schedule Model
    Manages waste collection schedules
    """
    
    def __init__(self):
        self.db = Database()
    
    def get_schedules_by_zone(self, zone):
        """Get collection schedule for a zone"""
        query = """
            SELECT * FROM schedules 
            WHERE zone = %s AND status = 'active'
            ORDER BY 
                FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 
                      'Thursday', 'Friday', 'Saturday', 'Sunday'),
                collection_time
        """
        return self.db.execute_query(query, (zone,))
    
    def get_all_schedules(self):
        """Get all active schedules"""
        query = """
            SELECT * FROM schedules 
            WHERE status = 'active'
            ORDER BY zone,
                FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 
                      'Thursday', 'Friday', 'Saturday', 'Sunday')
        """
        return self.db.execute_query(query)
