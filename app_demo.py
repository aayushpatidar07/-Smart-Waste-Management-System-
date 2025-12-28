"""
Smart Waste Management System - Demo Mode
Run without database for demonstration
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, 
    template_folder='../frontend/templates',
    static_folder='../frontend/static')

app.secret_key = 'demo-secret-key-2025'
CORS(app)

# Demo data for demonstration
DEMO_USERS = {
    'admin': {'password': 'admin123', 'role': 'Admin', 'name': 'Admin User'},
    'staff1': {'password': 'staff123', 'role': 'Staff', 'name': 'Staff Member'},
    'citizen1': {'password': 'citizen123', 'role': 'Citizen', 'name': 'John Citizen'}
}

DEMO_BINS = [
    {'bin_id': 1, 'bin_code': 'BIN001', 'location': 'Main Street', 'waste_level': 85, 'zone': 'Zone A', 'status': 'Active', 'bin_type': 'General'},
    {'bin_id': 2, 'bin_code': 'BIN002', 'location': 'Park Avenue', 'waste_level': 45, 'zone': 'Zone A', 'status': 'Active', 'bin_type': 'Recyclable'},
    {'bin_id': 3, 'bin_code': 'BIN003', 'location': 'City Center', 'waste_level': 92, 'zone': 'Zone B', 'status': 'Active', 'bin_type': 'General'},
    {'bin_id': 4, 'bin_code': 'BIN004', 'location': 'Market Square', 'waste_level': 38, 'zone': 'Zone B', 'status': 'Active', 'bin_type': 'Organic'},
]

DEMO_VEHICLES = [
    {'vehicle_id': 1, 'vehicle_number': 'WM-101', 'driver_name': 'Mike Johnson', 'status': 'On Route', 'current_load': 65},
    {'vehicle_id': 2, 'vehicle_number': 'WM-102', 'driver_name': 'Sarah Williams', 'status': 'Available', 'current_load': 0},
]

DEMO_STATS = {
    'total_bins': 12,
    'full_bins': 3,
    'collections_today': 5,
    'active_alerts': 4
}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if username in DEMO_USERS and DEMO_USERS[username]['password'] == password:
            session['user_id'] = username
            session['username'] = username
            session['role'] = DEMO_USERS[username]['role']
            session['name'] = DEMO_USERS[username]['name']
            
            if request.is_json:
                return jsonify({'success': True, 'role': session['role']})
            
            if session['role'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif session['role'] == 'Staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('citizen_dashboard'))
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

@app.route('/admin/bins')
def admin_bins():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    return render_template('admin/bins.html')

@app.route('/admin/vehicles')
def admin_vehicles():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    return render_template('admin/vehicles.html')

# Staff Routes
@app.route('/staff/dashboard')
def staff_dashboard():
    if 'role' not in session or session['role'] != 'Staff':
        return redirect(url_for('login'))
    return render_template('staff/dashboard.html')

# Citizen Routes
@app.route('/citizen/dashboard')
def citizen_dashboard():
    if 'role' not in session or session['role'] != 'Citizen':
        return redirect(url_for('login'))
    return render_template('citizen/dashboard.html')

# API Endpoints
@app.route('/api/bins')
def api_bins():
    return jsonify(DEMO_BINS)

@app.route('/api/vehicles')
def api_vehicles():
    return jsonify(DEMO_VEHICLES)

@app.route('/api/dashboard/stats')
def api_stats():
    return jsonify(DEMO_STATS)

@app.route('/api/dashboard/waste-trend')
def api_waste_trend():
    trend_data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'datasets': [{
            'label': 'Average Waste Level',
            'data': [45, 52, 48, 65, 72, 68, 55],
            'borderColor': 'rgb(25, 135, 84)',
            'backgroundColor': 'rgba(25, 135, 84, 0.1)'
        }]
    }
    return jsonify(trend_data)

@app.route('/api/dashboard/zone-stats')
def api_zone_stats():
    zone_data = {
        'labels': ['Zone A', 'Zone B', 'Zone C'],
        'datasets': [{
            'label': 'Bins per Zone',
            'data': [4, 5, 3],
            'backgroundColor': ['#198754', '#0dcaf0', '#ffc107']
        }]
    }
    return jsonify(zone_data)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 SMART WASTE MANAGEMENT SYSTEM - DEMO MODE")
    print("=" * 60)
    print("\n⚠️  Running in DEMO mode (without database)")
    print("   For full functionality, configure MySQL database\n")
    print("📍 Server: http://localhost:5000")
    print("\n🔑 Demo Login Credentials:")
    print("   Admin    → username: admin    | password: admin123")
    print("   Staff    → username: staff1   | password: staff123")
    print("   Citizen  → username: citizen1 | password: citizen123")
    print("\n" + "=" * 60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
