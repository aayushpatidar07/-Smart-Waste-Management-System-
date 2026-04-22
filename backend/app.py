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
from driver_performance import DriverPerformanceService
from alert_rules_engine import AlertRulesEngine
from waste_composition import WasteCompositionService
from environmental_impact import EnvironmentalImpactService
from citizen_engagement import CitizenEngagementService
from resource_utilization import ResourceUtilizationService
from data_quality import DataQualityService
from predictive_analytics import PredictiveAnalyticsService
from real_time_alerts import RealTimeAlertsService
from compliance_reporting import ComplianceReportingService
from collection_productivity import CollectionProductivityService
from service_availability import ServiceAvailabilityService
from waste_audit_insights import WasteAuditInsightsService
from environmental_impact_insights import EnvironmentalImpactService
from vehicle_maintenance_insights import VehicleMaintenanceService
from citizen_feedback_analytics import CitizenFeedbackService
from waste_classification_insights import WasteClassificationService
from bin_health_insights import BinHealthInsightsService
from route_risk_insights import RouteRiskInsightsService
from schedule_adherence_insights import ScheduleAdherenceInsightsService

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
def api_resolve_collection_alert(alert_id):
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
# DRIVER PERFORMANCE ENDPOINTS
# =============================================

@app.route('/api/drivers/<int:driver_id>/trips', methods=['POST'])
@login_required
def api_record_driver_trip(driver_id):
    """Record a completed trip for a driver."""
    try:
        data = request.get_json() or {}
        
        required_fields = ['route_id', 'bins_collected', 'time_taken_minutes', 'distance_km', 'fuel_used']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Missing required fields: ' + ', '.join(required_fields)
            }), 400
        
        result = DriverPerformanceService().record_trip_completion(
            driver_id,
            int(data.get('route_id')),
            int(data.get('bins_collected')),
            float(data.get('time_taken_minutes')),
            float(data.get('distance_km')),
            float(data.get('fuel_used'))
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


@app.route('/api/drivers/<int:driver_id>/performance', methods=['GET'])
@login_required
def api_get_driver_performance(driver_id):
    """Get performance summary for a specific driver."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = DriverPerformanceService().get_driver_performance_summary(driver_id, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/drivers/top-performers', methods=['GET'])
@login_required
def api_get_top_drivers():
    """Get top performing drivers."""
    try:
        limit = request.args.get('limit', 5, type=int)
        days = request.args.get('days', 30, type=int)
        
        if limit < 1 or limit > 20:
            return jsonify({
                'success': False,
                'message': 'Limit must be between 1 and 20'
            }), 400
        
        result = DriverPerformanceService().get_top_drivers(limit, days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# WASTE COMPOSITION ENDPOINTS
# =============================================

@app.route('/api/waste-composition/<int:bin_id>/record', methods=['POST'])
@login_required
def api_record_waste_composition(bin_id):
    """Record waste composition analysis for a bin."""
    try:
        data = request.get_json() or {}
        
        required_fields = ['organic_percentage', 'recyclables_percentage', 'hazardous_percentage', 'inert_percentage']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'All percentage fields are required'
            }), 400
        
        result = WasteCompositionService().record_waste_composition(
            bin_id,
            float(data.get('organic_percentage')),
            float(data.get('recyclables_percentage')),
            float(data.get('hazardous_percentage')),
            float(data.get('inert_percentage')),
            data.get('notes', '')
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Invalid input types for percentages'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-composition/<int:bin_id>/summary', methods=['GET'])
@login_required
def api_get_composition_summary(bin_id):
    """Get waste composition summary for a bin."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = WasteCompositionService().get_composition_summary(bin_id, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/waste-composition/zone/<string:zone>/analysis', methods=['GET'])
@login_required
def api_get_zone_composition(zone):
    """Get waste composition analysis for a zone."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = WasteCompositionService().get_zone_composition_analysis(zone, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# ENVIRONMENTAL IMPACT ENDPOINTS
# =============================================

@app.route('/api/environmental/carbon-savings', methods=['POST'])
@login_required
def api_calculate_carbon_savings():
    """Calculate carbon savings from recycling and composting."""
    try:
        data = request.get_json() or {}
        
        recycled_kg = float(data.get('waste_recycled_kg', 0))
        composted_kg = float(data.get('waste_composted_kg', 0))
        
        result = EnvironmentalImpactService().calculate_carbon_savings(recycled_kg, composted_kg)
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Invalid input types'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/impact/record', methods=['POST'])
@login_required
@role_required(['admin', 'staff'])
def api_record_environmental_impact():
    """Record environmental impact metrics for a zone."""
    try:
        data = request.get_json() or {}
        
        required_fields = ['zone', 'total_waste_collected_kg', 'recycled_percentage', 
                          'composted_percentage', 'landfill_percentage']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        result = EnvironmentalImpactService().record_environmental_impact(
            data.get('zone'),
            float(data.get('total_waste_collected_kg')),
            float(data.get('recycled_percentage')),
            float(data.get('composted_percentage')),
            float(data.get('landfill_percentage'))
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


@app.route('/api/environmental/zone/<string:zone>/summary', methods=['GET'])
@login_required
def api_get_zone_environmental_summary(zone):
    """Get environmental impact summary for a zone."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = EnvironmentalImpactService().get_zone_environmental_summary(zone, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/system-impact', methods=['GET'])
@login_required
def api_get_system_wide_impact():
    """Get system-wide environmental impact metrics."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = EnvironmentalImpactService().get_system_wide_impact(days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# CITIZEN ENGAGEMENT ENDPOINTS
# =============================================

@app.route('/api/citizens/<int:citizen_id>/reports', methods=['POST'])
@login_required
def api_record_citizen_report(citizen_id):
    """Record a citizen report or complaint."""
    try:
        data = request.get_json() or {}
        
        required_fields = ['report_type', 'location', 'description']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'report_type, location, and description are required'
            }), 400
        
        result = CitizenEngagementService().record_citizen_report(
            citizen_id,
            data.get('report_type'),
            data.get('location'),
            data.get('description'),
            data.get('status', 'submitted')
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


@app.route('/api/citizens/<int:citizen_id>/engagement', methods=['GET'])
@login_required
def api_get_citizen_engagement(citizen_id):
    """Get engagement score and metrics for a citizen."""
    try:
        result = CitizenEngagementService().get_citizen_engagement_score(citizen_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/citizens/top-engaged', methods=['GET'])
@login_required
def api_get_top_engaged_citizens():
    """Get top engaged citizens."""
    try:
        limit = request.args.get('limit', 10, type=int)
        days = request.args.get('days', 30, type=int)
        
        if limit < 1 or limit > 50:
            return jsonify({
                'success': False,
                'message': 'Limit must be between 1 and 50'
            }), 400
        
        result = CitizenEngagementService().get_top_engaged_citizens(limit, days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/citizens/report-statistics', methods=['GET'])
@login_required
def api_get_report_statistics():
    """Get overall citizen report statistics."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = CitizenEngagementService().get_report_statistics(days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# RESOURCE UTILIZATION ENDPOINTS
# =============================================

@app.route('/api/bins/<int:bin_id>/utilization/record', methods=['POST'])
@login_required
def api_record_bin_utilization(bin_id):
    """Record bin utilization from collection."""
    try:
        data = request.get_json() or {}
        
        required_fields = ['capacity_ml', 'waste_collected_ml', 'collection_date']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'capacity_ml, waste_collected_ml, and collection_date are required'
            }), 400
        
        result = ResourceUtilizationService().record_bin_utilization(
            bin_id,
            float(data.get('capacity_ml')),
            float(data.get('waste_collected_ml')),
            data.get('collection_date')
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


@app.route('/api/bins/<int:bin_id>/utilization/analysis', methods=['GET'])
@login_required
def api_get_bin_utilization_analysis(bin_id):
    """Get bin utilization analysis."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = ResourceUtilizationService().get_bin_utilization_analysis(bin_id, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/routes/<int:route_id>/efficiency', methods=['GET'])
@login_required
def api_get_route_efficiency(route_id):
    """Get route collection efficiency analysis."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = ResourceUtilizationService().get_route_efficiency(route_id, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/resources/underutilized', methods=['GET'])
@login_required
def api_get_underutilized_resources():
    """Get list of underutilized resources."""
    try:
        threshold = request.args.get('threshold', 30, type=float)
        days = request.args.get('days', 30, type=int)
        
        if threshold < 0 or threshold > 100:
            return jsonify({
                'success': False,
                'message': 'Threshold must be between 0 and 100'
            }), 400
        
        result = ResourceUtilizationService().get_underutilized_resources(threshold, days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# DATA QUALITY ASSESSMENT ENDPOINTS
# =============================================

@app.route('/api/bins/<int:bin_id>/quality/assess', methods=['GET'])
@login_required
def api_assess_bin_data_quality(bin_id):
    """Assess data quality for a specific bin."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = DataQualityService().assess_bin_data_quality(bin_id, days)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/quality/system-overview', methods=['GET'])
@login_required
def api_get_system_data_quality_overview():
    """Get overall system data quality metrics."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 1 and 365'
            }), 400
        
        result = DataQualityService().get_system_data_quality_overview(days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/quality/low-quality-bins', methods=['GET'])
@login_required
def api_identify_low_quality_bins():
    """Identify bins with low data quality."""
    try:
        threshold = request.args.get('threshold', 70, type=float)
        days = request.args.get('days', 30, type=int)
        
        if threshold < 0 or threshold > 100:
            return jsonify({
                'success': False,
                'message': 'Threshold must be between 0 and 100'
            }), 400
        
        result = DataQualityService().identify_low_quality_bins(threshold, days)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# PREDICTIVE ANALYTICS & FORECASTING ROUTES
# =============================================

@app.route('/api/bins/<int:bin_id>/forecast/overflow', methods=['GET'])
@login_required
def forecast_bin_overflow(bin_id):
    """Forecast when a bin will overflow based on historical patterns"""
    try:
        days_ahead = request.args.get('days', 7, type=int)
        if days_ahead < 1 or days_ahead > 30:
            return jsonify({'success': False, 'message': 'Days must be between 1 and 30'}), 400
        
        result = PredictiveAnalyticsService().forecast_bin_overflow(bin_id, days_ahead)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zones/<zone>/forecast/demand', methods=['GET'])
@login_required
def predict_collection_demand(zone):
    """Predict collection demand for a zone"""
    try:
        days_ahead = request.args.get('days', 7, type=int)
        if days_ahead < 1 or days_ahead > 30:
            return jsonify({'success': False, 'message': 'Days must be between 1 and 30'}), 400
        
        result = PredictiveAnalyticsService().predict_collection_demand(zone, days_ahead)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/forecast/waste-volume', methods=['GET'])
@login_required
def forecast_waste_volume():
    """Forecast total system waste volume"""
    try:
        days_ahead = request.args.get('days', 30, type=int)
        if days_ahead < 1 or days_ahead > 90:
            return jsonify({'success': False, 'message': 'Days must be between 1 and 90'}), 400
        
        result = PredictiveAnalyticsService().forecast_waste_volume(days_ahead)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bins/<int:bin_id>/anomalies', methods=['GET'])
@login_required
def identify_anomalies(bin_id):
    """Identify anomalies in bin fill level patterns"""
    try:
        sensitivity = request.args.get('sensitivity', 2.0, type=float)
        if sensitivity < 0.5 or sensitivity > 5.0:
            return jsonify({'success': False, 'message': 'Sensitivity must be between 0.5 and 5.0'}), 400
        
        result = PredictiveAnalyticsService().identify_anomalies(bin_id, sensitivity)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# REAL-TIME MONITORING & ALERTS
# =============================================

@app.route('/api/alerts/create', methods=['POST'])
@login_required
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json() or {}
        alert_type = data.get('alert_type')
        severity = data.get('severity')
        message = data.get('message')
        entity_id = data.get('entity_id')
        entity_type = data.get('entity_type')
        
        if not all([alert_type, severity, message]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        if severity not in ['Critical', 'High', 'Medium', 'Low']:
            return jsonify({'success': False, 'message': 'Invalid severity level'}), 400
        
        result = RealTimeAlertsService().create_alert(alert_type, severity, message, entity_id, entity_type)
        return jsonify(result), (201 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/active', methods=['GET'])
@login_required
def get_active_alerts():
    """Get all active alerts with optional filtering"""
    try:
        severity = request.args.get('severity')
        alert_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        
        result = RealTimeAlertsService().get_active_alerts(severity, alert_type, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/summary', methods=['GET'])
@login_required
def get_alert_summary():
    """Get alert summary statistics"""
    try:
        result = RealTimeAlertsService().get_alert_summary()
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        data = request.get_json() or {}
        notes = data.get('notes')
        
        result = RealTimeAlertsService().acknowledge_alert(alert_id, notes)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes')
        
        result = RealTimeAlertsService().resolve_alert(alert_id, resolution_notes)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/history', methods=['GET'])
@login_required
def get_alert_history():
    """Get historical alerts"""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 200))
        
        result = RealTimeAlertsService().get_alert_history(days, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/entity/<entity_type>/<int:entity_id>', methods=['GET'])
@login_required
def get_entity_alerts(entity_type, entity_id):
    """Get alerts for a specific entity"""
    try:
        status = request.args.get('status', 'Active')
        limit = int(request.args.get('limit', 50))
        
        result = RealTimeAlertsService().get_alerts_by_entity(entity_type, entity_id, status, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/critical-events', methods=['GET'])
@login_required
def get_critical_events():
    """Get critical and high priority events"""
    try:
        hours = int(request.args.get('hours', 24))
        
        result = RealTimeAlertsService().get_critical_events(hours)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# COMPLIANCE & REGULATORY REPORTING
# =============================================

@app.route('/api/compliance/waste-disposal', methods=['POST'])
@login_required
def get_waste_disposal_report():
    """Generate waste disposal compliance report"""
    try:
        data = request.get_json() or {}
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not start_date_str or not end_date_str:
            return jsonify({'success': False, 'message': 'start_date and end_date required'}), 400

        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        result = ComplianceReportingService().generate_waste_disposal_report(start_date, end_date)
        return jsonify(result), (200 if result.get('success') else 400)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compliance/environmental-impact', methods=['POST'])
@login_required
def get_environmental_impact_report():
    """Generate environmental impact compliance report"""
    try:
        data = request.get_json() or {}
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not start_date_str or not end_date_str:
            return jsonify({'success': False, 'message': 'start_date and end_date required'}), 400

        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        result = ComplianceReportingService().generate_environmental_impact_report(start_date, end_date)
        return jsonify(result), (200 if result.get('success') else 400)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compliance/operational-efficiency', methods=['POST'])
@login_required
def get_operational_efficiency_report():
    """Generate operational efficiency report"""
    try:
        data = request.get_json() or {}
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not start_date_str or not end_date_str:
            return jsonify({'success': False, 'message': 'start_date and end_date required'}), 400

        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        result = ComplianceReportingService().generate_operational_efficiency_report(start_date, end_date)
        return jsonify(result), (200 if result.get('success') else 400)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compliance/safety', methods=['GET'])
@login_required
def get_safety_compliance_report():
    """Generate safety compliance report"""
    try:
        result = ComplianceReportingService().generate_safety_compliance_report()
        return jsonify(result), (200 if result.get('success') else 400)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compliance/quarterly-summary', methods=['GET'])
@login_required
def get_quarterly_summary():
    """Generate quarterly compliance summary"""
    try:
        quarter = int(request.args.get('quarter', 1))
        year = int(request.args.get('year', datetime.now().year))

        if quarter < 1 or quarter > 4:
            return jsonify({'success': False, 'message': 'Quarter must be 1-4'}), 400

        result = ComplianceReportingService().generate_quarterly_compliance_summary(quarter, year)
        return jsonify(result), (200 if result.get('success') else 400)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# SERVICE AVAILABILITY INSIGHTS
# =============================================

@app.route('/api/availability/bins', methods=['GET'])
@login_required
def get_bin_availability_insights():
    """Get availability breakdown for smart bins."""
    try:
        result = ServiceAvailabilityService().get_bin_availability()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/availability/vehicles', methods=['GET'])
@login_required
def get_vehicle_availability_insights():
    """Get fleet readiness and vehicle availability metrics."""
    try:
        result = ServiceAvailabilityService().get_vehicle_availability()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/availability/routes', methods=['GET'])
@login_required
def get_route_completion_insights():
    """Get route completion insights for recent days."""
    try:
        days = int(request.args.get('days', 14))
        if days < 1 or days > 90:
            return jsonify({'success': False, 'message': 'days must be between 1 and 90'}), 400

        result = ServiceAvailabilityService().get_route_completion(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/availability/score', methods=['GET'])
@login_required
def get_system_availability_score():
    """Get weighted overall system availability score."""
    try:
        result = ServiceAvailabilityService().get_system_availability_score()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/availability/service-gaps', methods=['GET'])
@login_required
def get_service_gaps():
    """Get zone-level service gaps prioritized by risk."""
    try:
        limit = int(request.args.get('limit', 8))
        if limit < 1 or limit > 20:
            return jsonify({'success': False, 'message': 'limit must be between 1 and 20'}), 400

        result = ServiceAvailabilityService().get_zone_service_gaps(limit)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# COLLECTION PRODUCTIVITY INSIGHTS
# =============================================

@app.route('/api/productivity/overview', methods=['GET'])
@login_required
def get_collection_productivity_overview():
    """Get collection productivity overview metrics."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CollectionProductivityService().get_productivity_overview(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/productivity/vehicles', methods=['GET'])
@login_required
def get_vehicle_productivity_ranking():
    """Get top vehicle productivity ranking."""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 10))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400
        if limit < 1 or limit > 20:
            return jsonify({'success': False, 'message': 'limit must be between 1 and 20'}), 400

        result = CollectionProductivityService().get_vehicle_productivity(days, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/productivity/routes', methods=['GET'])
@login_required
def get_route_productivity_insights():
    """Get route completion and productivity breakdown."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CollectionProductivityService().get_route_productivity(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/productivity/zones', methods=['GET'])
@login_required
def get_zone_productivity_insights():
    """Get zone-wise collection productivity indicators."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CollectionProductivityService().get_zone_productivity(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/productivity/recommendations', methods=['GET'])
@login_required
def get_productivity_recommendations():
    """Get productivity optimization recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CollectionProductivityService().get_productivity_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# WASTE AUDIT INSIGHTS
# =============================================

@app.route('/api/audit/summary', methods=['GET'])
@login_required
def get_waste_audit_summary():
    """Get waste audit summary metrics."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteAuditInsightsService().get_audit_summary(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/audit/zones', methods=['GET'])
@login_required
def get_waste_audit_zone_ranking():
    """Get zone-level audit ranking."""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 8))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400
        if limit < 1 or limit > 20:
            return jsonify({'success': False, 'message': 'limit must be between 1 and 20'}), 400

        result = WasteAuditInsightsService().get_zone_audit_ranking(days, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/audit/timeline', methods=['GET'])
@login_required
def get_waste_audit_timeline():
    """Get daily audit resolution timeline."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteAuditInsightsService().get_resolution_timeline(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/audit/backlog', methods=['GET'])
@login_required
def get_waste_audit_backlog():
    """Get important unresolved audit items."""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 10))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400
        if limit < 1 or limit > 25:
            return jsonify({'success': False, 'message': 'limit must be between 1 and 25'}), 400

        result = WasteAuditInsightsService().get_backlog_items(days, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/audit/recommendations', methods=['GET'])
@login_required
def get_waste_audit_recommendations():
    """Get waste audit improvement recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteAuditInsightsService().get_audit_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# ENVIRONMENTAL IMPACT INSIGHTS
# =============================================

@app.route('/api/impact/summary', methods=['GET'])
@login_required
def get_environmental_impact_summary():
    """Get environmental impact summary."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = EnvironmentalImpactService().get_impact_summary(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/impact/co2-breakdown', methods=['GET'])
@login_required
def get_environmental_co2_breakdown():
    """Get CO2 emissions breakdown by vehicle type."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = EnvironmentalImpactService().get_co2_breakdown(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/impact/composition', methods=['GET'])
@login_required
def get_environmental_composition_impact():
    """Get waste composition environmental impact."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = EnvironmentalImpactService().get_waste_composition_impact(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/impact/trends', methods=['GET'])
@login_required
def get_environmental_trends():
    """Get sustainability improvement trends."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = EnvironmentalImpactService().get_sustainability_trends(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/impact/recommendations', methods=['GET'])
@login_required
def get_environmental_recommendations():
    """Get sustainability improvement recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = EnvironmentalImpactService().get_sustainability_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# VEHICLE MAINTENANCE INSIGHTS
# =============================================

@app.route('/api/maintenance/overview', methods=['GET'])
@login_required
def get_maintenance_overview():
    """Get vehicle maintenance status overview."""
    try:
        result = VehicleMaintenanceService().get_maintenance_overview()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/maintenance/schedule', methods=['GET'])
@login_required
def get_maintenance_schedule():
    """Get maintenance schedule for vehicles."""
    try:
        result = VehicleMaintenanceService().get_maintenance_schedule()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/maintenance/history', methods=['GET'])
@login_required
def get_maintenance_history():
    """Get vehicle maintenance history."""
    try:
        days = int(request.args.get('days', 90))
        if days < 1 or days > 365:
            return jsonify({'success': False, 'message': 'days must be between 1 and 365'}), 400

        result = VehicleMaintenanceService().get_maintenance_history(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/maintenance/fleet-health', methods=['GET'])
@login_required
def get_fleet_health():
    """Get overall fleet health metrics."""
    try:
        result = VehicleMaintenanceService().get_fleet_health()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/maintenance/costs', methods=['GET'])
@login_required
def get_maintenance_costs():
    """Get maintenance cost analysis."""
    try:
        days = int(request.args.get('days', 90))
        if days < 1 or days > 365:
            return jsonify({'success': False, 'message': 'days must be between 1 and 365'}), 400

        result = VehicleMaintenanceService().get_maintenance_costs(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/maintenance/recommendations', methods=['GET'])
@login_required
def get_maintenance_recommendations():
    """Get vehicle maintenance recommendations."""
    try:
        result = VehicleMaintenanceService().get_maintenance_recommendations()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# CITIZEN FEEDBACK ANALYTICS
# =============================================

@app.route('/api/feedback/overview', methods=['GET'])
@login_required
def get_feedback_overview():
    """Get citizen feedback overview."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CitizenFeedbackService().get_feedback_overview(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feedback/complaints', methods=['GET'])
@login_required
def get_complaint_summary():
    """Get complaint summary by category."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CitizenFeedbackService().get_complaint_summary(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feedback/satisfaction-trends', methods=['GET'])
@login_required
def get_satisfaction_trends():
    """Get satisfaction rating trends."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CitizenFeedbackService().get_satisfaction_trends(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feedback/topics', methods=['GET'])
@login_required
def get_feedback_topics():
    """Get most mentioned feedback topics."""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 10))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400
        if limit < 1 or limit > 20:
            return jsonify({'success': False, 'message': 'limit must be between 1 and 20'}), 400

        result = CitizenFeedbackService().get_feedback_topics(days, limit)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feedback/engagement', methods=['GET'])
@login_required
def get_citizen_engagement():
    """Get citizen engagement metrics."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CitizenFeedbackService().get_citizen_engagement(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feedback/recommendations', methods=['GET'])
@login_required
def get_feedback_recommendations():
    """Get citizen feedback recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = CitizenFeedbackService().get_feedback_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# WASTE CLASSIFICATION INSIGHTS
# =============================================

@app.route('/api/classification/summary', methods=['GET'])
@login_required
def get_classification_summary():
    """Get waste classification summary."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteClassificationService().get_classification_summary(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classification/distribution', methods=['GET'])
@login_required
def get_type_distribution():
    """Get bin type distribution."""
    try:
        result = WasteClassificationService().get_type_distribution()
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classification/zones', methods=['GET'])
@login_required
def get_zone_classification():
    """Get waste classification by zone."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteClassificationService().get_zone_classification(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classification/reports', methods=['GET'])
@login_required
def get_report_profile():
    """Get waste report classification profile."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteClassificationService().get_report_profile(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classification/recommendations', methods=['GET'])
@login_required
def get_classification_recommendations():
    """Get waste classification recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = WasteClassificationService().get_classification_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# ROUTE RISK INSIGHTS
# =============================================

@app.route('/api/route-risk/overview', methods=['GET'])
@login_required
def get_route_risk_overview():
    """Get route risk overview metrics."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = RouteRiskInsightsService().get_risk_overview(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/route-risk/routes', methods=['GET'])
@login_required
def get_high_risk_routes():
    """Get high risk routes list."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = RouteRiskInsightsService().get_high_risk_routes(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/route-risk/zones', methods=['GET'])
@login_required
def get_route_risk_zones():
    """Get route risk by zone."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = RouteRiskInsightsService().get_zone_risk_profile(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/route-risk/recommendations', methods=['GET'])
@login_required
def get_route_risk_recommendations():
    """Get route risk recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = RouteRiskInsightsService().get_risk_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# BIN HEALTH INSIGHTS
# =============================================

@app.route('/api/bin-health/overview', methods=['GET'])
@login_required
def get_bin_health_overview():
    """Get bin health overview."""
    try:
        days = int(request.args.get('days', 14))
        if days < 1 or days > 90:
            return jsonify({'success': False, 'message': 'days must be between 1 and 90'}), 400

        result = BinHealthInsightsService().get_health_overview(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bin-health/ranking', methods=['GET'])
@login_required
def get_bin_health_ranking():
    """Get bin health risk ranking."""
    try:
        days = int(request.args.get('days', 14))
        if days < 1 or days > 90:
            return jsonify({'success': False, 'message': 'days must be between 1 and 90'}), 400

        result = BinHealthInsightsService().get_bin_health_ranking(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bin-health/anomalies', methods=['GET'])
@login_required
def get_bin_sensor_anomalies():
    """Get zone-level sensor anomaly summary."""
    try:
        days = int(request.args.get('days', 14))
        if days < 1 or days > 90:
            return jsonify({'success': False, 'message': 'days must be between 1 and 90'}), 400

        result = BinHealthInsightsService().get_sensor_anomaly_summary(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bin-health/recommendations', methods=['GET'])
@login_required
def get_bin_health_recommendations():
    """Get bin health recommendations."""
    try:
        days = int(request.args.get('days', 14))
        if days < 1 or days > 90:
            return jsonify({'success': False, 'message': 'days must be between 1 and 90'}), 400

        result = BinHealthInsightsService().get_health_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# SCHEDULE ADHERENCE INSIGHTS
# =============================================

@app.route('/api/schedule-adherence/overview', methods=['GET'])
@login_required
def get_schedule_adherence_overview():
    """Get schedule adherence overview."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = ScheduleAdherenceInsightsService().get_adherence_overview(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/schedule-adherence/zones', methods=['GET'])
@login_required
def get_schedule_adherence_zones():
    """Get schedule adherence by zone."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = ScheduleAdherenceInsightsService().get_zone_adherence(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/schedule-adherence/delays', methods=['GET'])
@login_required
def get_schedule_delay_indicators():
    """Get schedule delay indicators."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = ScheduleAdherenceInsightsService().get_delay_indicators(days)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/schedule-adherence/recommendations', methods=['GET'])
@login_required
def get_schedule_adherence_recommendations():
    """Get schedule adherence recommendations."""
    try:
        days = int(request.args.get('days', 30))
        if days < 1 or days > 180:
            return jsonify({'success': False, 'message': 'days must be between 1 and 180'}), 400

        result = ScheduleAdherenceInsightsService().get_adherence_recommendations(days)
        return jsonify(result), (200 if result.get('success') else 400)
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
