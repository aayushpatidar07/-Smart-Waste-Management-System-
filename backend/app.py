"""
============================================
Smart Waste Management System - Main App
============================================
Flask application with REST APIs
IEEE SRS Compliant System
Author: Smart Waste Team
============================================
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import logging
from logging.handlers import RotatingFileHandler

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models
from models import (
    User, Bin, Vehicle, Route, WasteReport, 
    Alert, Analytics, Schedule
)
from waste_log import WasteLog
from waste_log_basic import BasicWasteLogService
from vehicle_maintenance import VehicleMaintenanceService
from bin_sensor_analytics import BinSensorAnalytics
from collection_alerts import CollectionAlertsService
from route_optimization_insights import RouteOptimizationService
from alert_rules_engine import AlertRulesEngine

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../frontend/templates',
           static_folder='../frontend/static')

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# =============================================
# LOGGING CONFIGURATION
# =============================================

if not app.debug:
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # File handler for error logs
    file_handler = RotatingFileHandler('logs/waste_management.log', 
                                      maxBytes=10240000, 
                                      backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Smart Waste Management System startup')

# =============================================
# AUTHENTICATION DECORATOR
# =============================================

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                return jsonify({'error': 'Unauthorized access'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =============================================
# SESSION MANAGEMENT
# =============================================

@app.before_request
def make_session_permanent():
    """Make session permanent with 24 hour lifetime"""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=24)

@app.before_request
def session_timeout_check():
    """Check for session timeout and refresh"""
    if 'user_id' in session:
        last_activity = session.get('last_activity')
        if last_activity:
            # Check if session is older than 2 hours of inactivity
            if datetime.now() - datetime.fromisoformat(last_activity) > timedelta(hours=2):
                session.clear()
                return redirect(url_for('login'))
        
        # Update last activity time
        session['last_activity'] = datetime.now().isoformat()


# =============================================
# AUTHENTICATION ROUTES
# =============================================

@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'staff':
            return redirect(url_for('staff_dashboard'))
        elif role == 'citizen':
            return redirect(url_for('citizen_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user_model = User()
        user = user_model.authenticate(username, password)
        
        if user:
            # Set session
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['email'] = user['email']
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'role': user['role'],
                    'redirect': f"/{user['role']}/dashboard"
                })
            else:
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'staff':
                    return redirect(url_for('staff_dashboard'))
                elif user['role'] == 'citizen':
                    return redirect(url_for('citizen_dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            else:
                return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))


# =============================================
# ADMIN ROUTES
# =============================================

@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html')

@app.route('/admin/bins')
@login_required
@role_required(['admin'])
def admin_bins():
    """Bin management page"""
    return render_template('admin/bins.html')

@app.route('/admin/vehicles')
@login_required
@role_required(['admin'])
def admin_vehicles():
    """Vehicle management page"""
    return render_template('admin/vehicles.html')

@app.route('/admin/routes')
@login_required
@role_required(['admin'])
def admin_routes():
    """Route management page"""
    return render_template('admin/routes.html')

@app.route('/admin/reports')
@login_required
@role_required(['admin'])
def admin_reports():
    """Reports management page"""
    return render_template('admin/reports.html')

@app.route('/admin/users')
@login_required
@role_required(['admin'])
def admin_users():
    """User management page"""
    return render_template('admin/users.html')


# =============================================
# STAFF ROUTES
# =============================================

@app.route('/staff/dashboard')
@login_required
@role_required(['staff', 'admin'])
def staff_dashboard():
    """Staff dashboard"""
    return render_template('staff/dashboard.html')

@app.route('/staff/collection')
@login_required
@role_required(['staff', 'admin'])
def staff_collection():
    """Collection routes page"""
    return render_template('staff/collection.html')

@app.route('/staff/waste-logs')
@login_required
@role_required(['staff', 'admin'])
def staff_waste_logs():
    """Staff waste log entry page"""
    return render_template('staff/waste_logs.html')


# =============================================
# CITIZEN ROUTES
# =============================================

@app.route('/citizen/dashboard')
@login_required
@role_required(['citizen'])
def citizen_dashboard():
    """Citizen dashboard"""
    return render_template('citizen/dashboard.html')

@app.route('/citizen/report')
@login_required
@role_required(['citizen'])
def citizen_report():
    """Report issue page"""
    return render_template('citizen/report.html')

@app.route('/citizen/schedule')
@login_required
@role_required(['citizen'])
def citizen_schedule():
    """View collection schedule"""
    return render_template('citizen/schedule.html')


# =============================================
# API ENDPOINTS - Dashboard & Analytics
# =============================================

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """Get dashboard statistics"""
    analytics = Analytics()
    stats = analytics.get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/dashboard/waste-trend', methods=['GET'])
@login_required
def api_waste_trend():
    """Get waste trend data for charts"""
    days = request.args.get('days', 7, type=int)
    analytics = Analytics()
    data = analytics.get_waste_trend_data(days)
    return jsonify(data)

@app.route('/api/dashboard/zone-stats', methods=['GET'])
@login_required
def api_zone_stats():
    """Get statistics by zone"""
    analytics = Analytics()
    data = analytics.get_zone_statistics()
    return jsonify(data)


# =============================================
# API ENDPOINTS - Bins
# =============================================

@app.route('/api/bins', methods=['GET'])
@login_required
def api_get_bins():
    """Get all bins"""
    bin_model = Bin()
    bins = bin_model.get_all_bins()
    return jsonify(bins)

@app.route('/api/bins/<int:bin_id>', methods=['GET'])
@login_required
def api_get_bin(bin_id):
    """Get specific bin details"""
    bin_model = Bin()
    bin_data = bin_model.get_bin_by_id(bin_id)
    if bin_data:
        return jsonify(bin_data)
    return jsonify({'error': 'Bin not found'}), 404

@app.route('/api/bins/full', methods=['GET'])
@login_required
def api_get_full_bins():
    """Get bins above threshold"""
    threshold = request.args.get('threshold', 80, type=int)
    bin_model = Bin()
    bins = bin_model.get_full_bins(threshold)
    return jsonify(bins)

@app.route('/api/bins/<int:bin_id>/update', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_update_bin_level(bin_id):
    """Update bin waste level"""
    data = request.get_json()
    waste_level = data.get('waste_level')
    
    bin_model = Bin()
    result = bin_model.update_waste_level(bin_id, waste_level)
    
    if result:
        return jsonify({'success': True, 'message': 'Bin level updated'})
    return jsonify({'error': 'Update failed'}), 500

@app.route('/api/bins/<int:bin_id>/history', methods=['GET'])
@login_required
def api_bin_history(bin_id):
    """Get bin sensor history"""
    days = request.args.get('days', 7, type=int)
    bin_model = Bin()
    history = bin_model.get_bin_history(bin_id, days)
    return jsonify(history)


# =============================================
# API ENDPOINTS - Vehicles
# =============================================

@app.route('/api/vehicles', methods=['GET'])
@login_required
def api_get_vehicles():
    """Get all vehicles"""
    vehicle_model = Vehicle()
    vehicles = vehicle_model.get_all_vehicles()
    return jsonify(vehicles)

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET'])
@login_required
def api_get_vehicle(vehicle_id):
    """Get specific vehicle"""
    vehicle_model = Vehicle()
    vehicle = vehicle_model.get_vehicle_by_id(vehicle_id)
    if vehicle:
        return jsonify(vehicle)
    return jsonify({'error': 'Vehicle not found'}), 404

@app.route('/api/vehicles/<int:vehicle_id>/location', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_update_vehicle_location(vehicle_id):
    """Update vehicle GPS location"""
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    vehicle_model = Vehicle()
    result = vehicle_model.update_vehicle_location(vehicle_id, latitude, longitude)
    
    if result:
        return jsonify({'success': True})
    return jsonify({'error': 'Update failed'}), 500

@app.route('/api/vehicles/<int:vehicle_id>/status', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_update_vehicle_status(vehicle_id):
    """Update vehicle status"""
    data = request.get_json()
    status = data.get('status')
    current_load = data.get('current_load')
    
    vehicle_model = Vehicle()
    result = vehicle_model.update_vehicle_status(vehicle_id, status, current_load)
    
    if result:
        return jsonify({'success': True})
    return jsonify({'error': 'Update failed'}), 500


# =============================================
# API ENDPOINTS - Routes
# =============================================

@app.route('/api/routes', methods=['GET'])
@login_required
def api_get_routes():
    """Get all routes"""
    date = request.args.get('date')
    route_model = Route()
    routes = route_model.get_all_routes(date)
    return jsonify(routes)

@app.route('/api/routes/<int:route_id>', methods=['GET'])
@login_required
def api_get_route(route_id):
    """Get route details with bins"""
    route_model = Route()
    route_data = route_model.get_route_details(route_id)
    if route_data:
        return jsonify(route_data)
    return jsonify({'error': 'Route not found'}), 404

@app.route('/api/routes/create', methods=['POST'])
@login_required
@role_required(['admin'])
def api_create_route():
    """Create new collection route"""
    data = request.get_json()
    
    route_model = Route()
    route_id = route_model.create_route(
        data.get('route_name'),
        data.get('vehicle_id'),
        data.get('route_date'),
        data.get('start_time'),
        data.get('bin_ids', [])
    )
    
    if route_id:
        return jsonify({'success': True, 'route_id': route_id})
    return jsonify({'error': 'Route creation failed'}), 500

@app.route('/api/routes/<int:route_id>/status', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_update_route_status(route_id):
    """Update route status"""
    data = request.get_json()
    status = data.get('status')
    
    route_model = Route()
    result = route_model.update_route_status(route_id, status)
    
    if result:
        return jsonify({'success': True})
    return jsonify({'error': 'Update failed'}), 500


# =============================================
# API ENDPOINTS - Waste Reports
# =============================================

@app.route('/api/reports', methods=['GET'])
@login_required
def api_get_reports():
    """Get all waste reports"""
    status = request.args.get('status')
    report_model = WasteReport()
    
    if session.get('role') == 'citizen':
        reports = report_model.get_citizen_reports(session['user_id'])
    else:
        reports = report_model.get_all_reports(status)
    
    return jsonify(reports)

@app.route('/api/reports/create', methods=['POST'])
@login_required
@role_required(['citizen'])
def api_create_report():
    """Create new waste report"""
    data = request.get_json()
    
    report_model = WasteReport()
    result = report_model.create_report(
        session['user_id'],
        data.get('bin_id'),
        data.get('report_type'),
        data.get('description'),
        data.get('location'),
        data.get('latitude'),
        data.get('longitude'),
        data.get('priority', 'medium')
    )
    
    if result:
        return jsonify({'success': True, 'message': 'Report submitted successfully'})
    return jsonify({'error': 'Report creation failed'}), 500

@app.route('/api/reports/<int:report_id>/status', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_update_report_status(report_id):
    """Update report status"""
    data = request.get_json()
    status = data.get('status')
    notes = data.get('notes', '')
    
    report_model = WasteReport()
    result = report_model.update_report_status(
        report_id, 
        status, 
        session['user_id'] if status == 'resolved' else None,
        notes
    )
    
    if result:
        return jsonify({'success': True})
    return jsonify({'error': 'Update failed'}), 500


# =============================================
# API ENDPOINTS - Alerts
# =============================================

@app.route('/api/alerts', methods=['GET'])
@login_required
def api_get_alerts():
    """Get active alerts"""
    alert_model = Alert()
    alerts = alert_model.get_active_alerts()
    return jsonify(alerts)

@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    alert_model = Alert()
    result = alert_model.acknowledge_alert(alert_id, session['user_id'])
    
    if result:
        return jsonify({'success': True})
    return jsonify({'error': 'Update failed'}), 500

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_resolve_alert(alert_id):
    """Resolve an alert"""
    alert_model = Alert()
    result = alert_model.resolve_alert(alert_id)
    
    if result:
        return jsonify({'success': True})
    return jsonify({'error': 'Update failed'}), 500


# =============================================
# API ENDPOINTS - Schedules
# =============================================

@app.route('/api/schedules', methods=['GET'])
@login_required
def api_get_schedules():
    """Get collection schedules"""
    zone = request.args.get('zone')
    schedule_model = Schedule()
    
    if zone:
        schedules = schedule_model.get_schedules_by_zone(zone)
    else:
        schedules = schedule_model.get_all_schedules()
    
    return jsonify(schedules)


# =============================================
# API ENDPOINTS - AI Predictions
# =============================================

@app.route('/api/ai/predict-collection', methods=['GET'])
@login_required
@role_required(['admin', 'staff'])
def api_predict_collection():
    """AI prediction for bins needing collection"""
    try:
        from ai.predictor import WasteLevelPredictor
        predictor = WasteLevelPredictor()
        predictions = predictor.predict_bins_needing_collection()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'AI prediction unavailable'}), 500

@app.route('/api/ai/optimize-route', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_optimize_route():
    """Optimize collection route"""
    try:
        from ai.route_optimizer import RouteOptimizer
        data = request.get_json()
        bin_ids = data.get('bin_ids', [])
        
        optimizer = RouteOptimizer()
        optimized_route = optimizer.optimize_route(bin_ids)
        return jsonify(optimized_route)
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'Route optimization unavailable'}), 500


# =============================================
# API ENDPOINTS - Users (Admin Only)
# =============================================

@app.route('/api/users', methods=['GET'])
@login_required
@role_required(['admin'])
def api_get_users():
    """Get all users"""
    role = request.args.get('role')
    user_model = User()
    users = user_model.get_all_users(role)
    return jsonify(users)

@app.route('/api/users/create', methods=['POST'])
@login_required
@role_required(['admin'])
def api_create_user():
    """Create new user"""
    data = request.get_json()
    
    user_model = User()
    result = user_model.create_user(
        data.get('username'),
        data.get('password'),
        data.get('full_name'),
        data.get('email'),
        data.get('phone'),
        data.get('role'),
        data.get('address', '')
    )
    
    if result:
        return jsonify({'success': True, 'message': 'User created successfully'})
    return jsonify({'error': 'User creation failed'}), 500


# =============================================
# API ENDPOINTS - Waste Logs (New Feature)
# =============================================

@app.route('/api/waste-logs', methods=['GET'])
@login_required
def api_get_waste_logs():
    """
    Get all waste log entries with bin details.
    Query params: limit (default: 100)
    Returns: JSON with success status and data array
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        result = WasteLog.get_all_logs(limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/create', methods=['POST'])
@login_required
def api_create_waste_log():
    """
    Create a new waste log entry for tracking bin fill levels.
    Required fields: bin_id (int), fill_level (float 0-100)
    Optional fields: notes (string)
    Returns: JSON with success status, log_id, and message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('bin_id') or data.get('fill_level') is None:
            return jsonify({
                'success': False,
                'error': 'bin_id and fill_level are required'
            }), 400
        
        result = WasteLog.create_waste_log(
            bin_id=data.get('bin_id'),
            fill_level=data.get('fill_level'),
            notes=data.get('notes')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/basic-create', methods=['POST'])
@login_required
def api_basic_create_waste_log():
    """Create a basic waste report log with minimal required fields."""
    try:
        data = request.get_json() or {}

        if 'bin_id' not in data or 'fill_level' not in data:
            return jsonify({
                'success': False,
                'message': 'bin_id and fill_level are required'
            }), 400

        result = BasicWasteLogService.log_waste_collection(
            int(data.get('bin_id')),
            float(data.get('fill_level')),
            data.get('timestamp')
        )

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Invalid input types for bin_id or fill_level'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/bin/<int:bin_id>', methods=['GET'])
@login_required
def api_get_waste_logs_by_bin(bin_id):
    """
    Get waste logs for a specific bin with bin details.
    Path param: bin_id
    Query params: limit (default: 50)
    Returns: JSON with success status and data array
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        result = WasteLog.get_logs_by_bin(bin_id, limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/recent', methods=['GET'])
@login_required
def api_get_recent_waste_logs():
    """
    Get recent waste logs from the last N hours.
    Query params: hours (default: 24)
    Returns: JSON with success status and data array
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        result = WasteLog.get_recent_logs(hours)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/<int:log_id>', methods=['GET'])
@login_required
def api_get_waste_log(log_id):
    """
    Get a specific waste log entry by ID with bin details.
    Path param: log_id
    Returns: JSON with success status and log data
    """
    try:
        result = WasteLog.get_log_by_id(log_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/<int:log_id>', methods=['DELETE'])
@login_required
@role_required(['admin', 'staff'])
def api_delete_waste_log(log_id):
    """
    Delete a waste log entry (admin/staff only).
    Path param: log_id
    Returns: JSON with success status and message
    """
    try:
        result = WasteLog.delete_log(log_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/statistics', methods=['GET'])
@login_required
def api_get_waste_log_statistics():
    """
    Get comprehensive waste log statistics and analytics.
    Query params: days (default: 7) - number of days to analyze
    Returns: JSON with statistics including distribution, trends, and top bins
    """
    try:
        days = request.args.get('days', 7, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        result = WasteLog.get_statistics(days)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/bin-history/<int:bin_id>', methods=['GET'])
@login_required
def api_get_bin_history(bin_id):
    """
    Get fill level history and trend analysis for a specific bin.
    Path param: bin_id
    Query params: days (default: 30) - number of days of history
    Returns: JSON with bin history, analytics, and trend data
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        result = WasteLog.get_bin_history(bin_id, days)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/<int:log_id>', methods=['PUT', 'PATCH'])
@login_required
@role_required(['admin', 'staff'])
def api_update_waste_log(log_id):
    """
    Update an existing waste log entry (admin/staff only).
    Path param: log_id
    Body: fill_level (optional), notes (optional)
    Returns: JSON with success status and message
    """
    try:
        data = request.get_json()
        
        fill_level = data.get('fill_level')
        notes = data.get('notes')
        
        result = WasteLog.update_waste_log(log_id, fill_level, notes)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/bulk-create', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_bulk_create_waste_logs():
    """
    Create multiple waste log entries at once (admin/staff only).
    Body: log_entries (array of objects with bin_id, fill_level, notes)
    Returns: JSON with success status, created count, and errors
    """
    try:
        data = request.get_json()
        log_entries = data.get('log_entries', [])
        
        if not log_entries:
            return jsonify({
                'success': False,
                'error': 'log_entries array is required'
            }), 400
        
        result = WasteLog.bulk_create_logs(log_entries)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/zone-statistics/<string:zone>', methods=['GET'])
@login_required
def api_get_zone_statistics(zone):
    """
    Get waste log statistics for a specific zone.
    Path param: zone - zone name to analyze
    Query params: days (default: 7) - number of days to analyze
    Returns: JSON with zone-specific statistics and bin details
    """
    try:
        days = request.args.get('days', 7, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        result = WasteLog.get_zone_statistics(zone, days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/waste-logs/export', methods=['GET'])
@login_required
def api_export_waste_logs():
    """
    Export waste logs data with flexible filtering.
    Query params: 
        - start_date (YYYY-MM-DD format)
        - end_date (YYYY-MM-DD format)
        - zone (zone name filter)
    Returns: JSON with exportable log data (max 10000 records)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        zone = request.args.get('zone')
        
        result = WasteLog.export_logs_data(start_date, end_date, zone)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/alerts', methods=['GET'])
@login_required
def api_get_waste_log_alerts():
    """
    Get bins exceeding fill level threshold for alert generation.
    Query params:
        - threshold (float): Fill level threshold percentage (default: 80)
        - hours (int): Number of hours to look back (default: 24)
    Returns: JSON with bins exceeding threshold
    """
    try:
        threshold = float(request.args.get('threshold', 80))
        hours = int(request.args.get('hours', 24))
        
        result = WasteLog.get_alerts_by_threshold(threshold, hours)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/efficiency', methods=['GET'])
@login_required
def api_get_collection_efficiency():
    """
    Analyze collection efficiency metrics.
    Query params:
        - days (int): Number of days to analyze (default: 30)
    Returns: JSON with efficiency analysis data
    """
    try:
        days = int(request.args.get('days', 30))
        
        result = WasteLog.get_collection_efficiency(days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/daily-summary', methods=['GET'])
@login_required
def api_get_daily_summary():
    """
    Get comprehensive daily summary of waste logging activity.
    Query params:
        - date (str): Date in YYYY-MM-DD format (default: today)
    Returns: JSON with daily summary statistics
    """
    try:
        date = request.args.get('date')
        
        result = WasteLog.get_daily_summary(date)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/trend-insights', methods=['GET'])
@login_required
def api_get_trend_insights():
    """
    Get trend insights across bins over a configurable period.
    Query params:
        - days (int): Number of days to analyze (default: 30)
        - zone (str): Optional zone filter
    Returns: JSON with trend summary and per-bin insight rows
    """
    try:
        days = int(request.args.get('days', 30))
        zone = request.args.get('zone')

        result = WasteLog.get_trend_insights(days, zone)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/high-risk', methods=['GET'])
@login_required
def api_get_high_risk_bins():
    """
    Get high-risk bins based on latest fill level readings.
    Query params:
        - hours (int): Lookback window in hours (default: 24)
        - min_fill (float): Minimum fill percentage (default: 70)
    Returns: JSON with risk-ranked bin list
    """
    try:
        hours = int(request.args.get('hours', 24))
        min_fill = float(request.args.get('min_fill', 70))

        result = WasteLog.get_high_risk_bins(hours, min_fill)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/zone-risk-heatmap', methods=['GET'])
@login_required
def api_get_zone_risk_heatmap():
    """
    Get zone-level risk heatmap data for waste operations.
    Query params:
        - days (int): Number of days to analyze (default: 7)
    Returns: JSON with zone risk summary and zone rows
    """
    try:
        days = int(request.args.get('days', 7))
        result = WasteLog.get_zone_risk_heatmap(days)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/overflow-forecast', methods=['GET'])
@login_required
def api_get_overflow_forecast():
    """
    Forecast bins likely to exceed critical fill threshold.
    Query params:
        - hours_ahead (int): Forecast horizon in hours (default: 24)
        - baseline_days (int): Historical window in days (default: 7)
    Returns: JSON with forecast summary and projected bins
    """
    try:
        hours_ahead = int(request.args.get('hours_ahead', 24))
        baseline_days = int(request.args.get('baseline_days', 7))

        result = WasteLog.get_overflow_forecast(hours_ahead, baseline_days)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-logs/collection-readiness', methods=['GET'])
@login_required
def api_get_collection_readiness():
    """
    Get dispatch-ready bins based on recent high fill readings.
    Query params:
        - hours (int): Lookback window in hours (default: 12)
        - threshold (float): Fill threshold percentage (default: 75)
    Returns: JSON with readiness summary and ranked bins
    """
    try:
        hours = int(request.args.get('hours', 12))
        threshold = float(request.args.get('threshold', 75))

        result = WasteLog.get_collection_readiness(hours, threshold)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# VEHICLE MAINTENANCE ENDPOINTS
# =============================================

@app.route('/api/vehicles/<int:vehicle_id>/maintenance', methods=['POST'])
@login_required
def api_log_vehicle_maintenance(vehicle_id):
    """Log vehicle maintenance record."""
    try:
        data = request.get_json() or {}
        
        if 'maintenance_type' not in data or 'description' not in data:
            return jsonify({
                'success': False,
                'message': 'maintenance_type and description are required'
            }), 400
        
        result = VehicleMaintenanceService.log_maintenance(
            vehicle_id,
            data.get('maintenance_type'),
            data.get('description'),
            float(data.get('cost', 0))
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Invalid input types'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vehicles/<int:vehicle_id>/maintenance/next-schedule', methods=['GET'])
@login_required
def api_get_vehicle_next_maintenance(vehicle_id):
    """Get recommended next maintenance schedule for a vehicle."""
    try:
        result = VehicleMaintenanceService.get_next_maintenance(vehicle_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# COLLECTION ALERTS ENDPOINTS
# =============================================

@app.route('/api/alerts', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_create_collection_alert():
    """Create a new collection alert."""
    try:
        data = request.get_json() or {}
        
        required_fields = ['bin_id', 'alert_type', 'priority', 'message']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'bin_id, alert_type, priority, and message are required'
            }), 400
        
        result = CollectionAlertsService.create_alert(
            int(data.get('bin_id')),
            data.get('alert_type'),
            data.get('priority'),
            data.get('message')
        )
        
        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code
        
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Invalid input types'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/active', methods=['GET'])
@login_required
def api_get_active_alerts():
    """Get all active (unresolved) collection alerts."""
    try:
        priority = request.args.get('priority')
        result = CollectionAlertsService.get_active_alerts(priority)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_resolve_alert(alert_id):
    """Mark an alert as resolved."""
    try:
        data = request.get_json() or {}
        notes = data.get('resolution_notes', '')
        
        result = CollectionAlertsService.resolve_alert(alert_id, notes)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/bin/<int:bin_id>', methods=['GET'])
@login_required
def api_get_bin_alerts(bin_id):
    """Get alerts for a specific bin."""
    try:
        include_resolved = request.args.get('include_resolved', 'false').lower() == 'true'
        result = CollectionAlertsService.get_alerts_by_bin(bin_id, include_resolved)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# ROUTE OPTIMIZATION ENDPOINTS
# =============================================

@app.route('/api/routes/<int:route_id>/optimization-analysis', methods=['GET'])
@login_required
def api_analyze_route_efficiency(route_id):
    """Analyze efficiency metrics and get optimization recommendations for a route."""
    try:
        result = RouteOptimizationService.analyze_route_efficiency(route_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zones/<string:zone>/optimization-suggestions', methods=['GET'])
@login_required
def api_get_zone_optimization_suggestions(zone):
    """Get optimization suggestions for all routes in a specific zone."""
    try:
        result = RouteOptimizationService.get_optimization_suggestions(zone)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# BIN SENSOR ANALYTICS ENDPOINTS
# =============================================

@app.route('/api/bins/<int:bin_id>/sensors/log', methods=['POST'])
@login_required
def api_log_sensor_reading(bin_id):
    """Log sensor reading from a waste bin."""
    try:
        data = request.get_json() or {}
        
        if 'fill_level' not in data:
            return jsonify({
                'success': False,
                'message': 'fill_level is required'
            }), 400
        
        result = BinSensorAnalytics.log_sensor_reading(
            bin_id,
            float(data.get('fill_level')),
            data.get('temperature'),
            data.get('humidity'),
            data.get('odor_level')
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Invalid input types'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bins/<int:bin_id>/sensors/trends', methods=['GET'])
@login_required
def api_get_sensor_trends(bin_id):
    """Get sensor reading trends for a bin."""
    try:
        hours = int(request.args.get('hours', 24))
        
        result = BinSensorAnalytics.get_sensor_trends(bin_id, hours)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bins/<int:bin_id>/sensors/anomalies', methods=['GET'])
@login_required
def api_detect_sensor_anomalies(bin_id):
    """Detect anomalies in sensor readings for a bin."""
    try:
        hours = int(request.args.get('hours', 24))
        
        result = BinSensorAnalytics.detect_sensor_anomalies(bin_id, hours)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# ALERT RULES ENGINE ENDPOINTS
# =============================================

@app.route('/api/alert-rules', methods=['POST'])
@login_required
@role_required(['admin'])
def api_create_alert_rule():
    """Create a new alert rule (admin only)."""
    try:
        data = request.get_json() or {}
        
        if not all(k in data for k in ['rule_name', 'condition_type', 'threshold_value', 'action_type']):
            return jsonify({
                'success': False,
                'message': 'rule_name, condition_type, threshold_value, and action_type are required'
            }), 400
        
        result = AlertRulesEngine.create_rule(
            data.get('rule_name'),
            data.get('condition_type'),
            float(data.get('threshold_value')),
            data.get('action_type')
        )
        
        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code
        
    except (TypeError, ValueError) as e:
        return jsonify({
            'success': False,
            'message': f'Invalid input: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alert-rules', methods=['GET'])
@login_required
def api_get_alert_rules():
    """Retrieve all alert rules."""
    try:
        result = AlertRulesEngine.get_all_rules()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alert-rules/<int:rule_id>', methods=['PUT', 'PATCH'])
@login_required
@role_required(['admin'])
def api_update_alert_rule(rule_id):
    """Update an alert rule (admin only)."""
    try:
        data = request.get_json() or {}
        
        result = AlertRulesEngine.update_rule(rule_id, **data)
        
        status_code = 200 if result.get('success') else (404 if 'not found' in result.get('message', '').lower() else 400)
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alert-rules/<int:rule_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def api_delete_alert_rule(rule_id):
    """Delete an alert rule (admin only)."""
    try:
        result = AlertRulesEngine.delete_rule(rule_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# ERROR HANDLERS
# =============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


# =============================================
# RUN APPLICATION
# =============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    print("=" * 50)
    print("Smart Waste Management System")
    print("=" * 50)
    print(f"Server running on http://localhost:{port}")
    print("=" * 50)
    print("\nDefault Login Credentials:")
    print("Admin    - Username: admin    Password: admin123")
    print("Staff    - Username: staff1   Password: staff123")
    print("Citizen  - Username: citizen1 Password: citizen123")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
