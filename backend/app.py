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
