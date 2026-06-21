# Smart Waste Management System

## 🌍 AI + IoT Based Waste Collection & Monitoring System

A complete, production-ready smart waste management system built with **Python Flask**, **MySQL**, **Bootstrap**, **Chart.js**, and **scikit-learn**. This system uses IoT sensors and AI/ML algorithms to optimize waste collection routes and monitor bin status in real-time.

--- 
 
## 📋 Table of Contents
 
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [User Roles & Access](#user-roles--access)
- [System Modules](#system-modules)
- [AI/ML Features](#aiml-features)
- [IoT Simulation](#iot-simulation)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

---


## ✨ Features

### Core Features
- ✅ **Real-time Bin Monitoring** - Live waste level tracking with smart sensors
- ✅ **AI-Based Predictions** - Machine learning predicts which bins need collection
- ✅ **Route Optimization** - Intelligent route planning using nearest-neighbor algorithm
- ✅ **Vehicle Tracking** - GPS simulation for waste collection vehicles
- ✅ **Citizen Portal** - Report issues and view collection schedules
- ✅ **Admin Dashboard** - Comprehensive analytics and management
- ✅ **Smart Alerts** - Automatic notifications for full bins
- ✅ **Data Analytics** - Charts and reports for decision making

### Technical Features
- 🔐 **Role-Based Authentication** (Admin, Staff, Citizen)
- 📊 **Interactive Dashboards** with Chart.js
- 🤖 **Machine Learning** with scikit-learn
- 📱 **Responsive Design** with Bootstrap 5
- 🔄 **RESTful APIs** for all operations
- 💾 **MySQL Database** with normalized schema
- 🎯 **IoT Sensor Simulation** for testing

---

## 🛠️ Technology Stack

### Backend
- **Language:** Python 3.8+
- **Framework:** Flask 2.3.2
- **Database:** MySQL 8.0
- **ORM:** MySQL Connector Python
- **AI/ML:** scikit-learn, NumPy, Pandas

### Frontend
- **HTML5** & **CSS3**
- **Bootstrap 5.3** (Responsive UI)
- **JavaScript** (ES6+)
- **jQuery 3.6**
- **Chart.js 4.3** (Data Visualization)
- **Bootstrap Icons**

### AI/ML Components
- Linear Regression for waste level prediction
- Nearest Neighbor algorithm for route optimization
- Time-series analysis for fill rate calculation

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  (Web Browser - Admin/Staff/Citizen Interfaces)         │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Presentation Layer                          │
│  (HTML Templates, CSS, JavaScript, Bootstrap)           │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Application Layer                           │
│  Flask REST APIs - Business Logic                       │
│  ├─ Authentication Module                               │
│  ├─ Bin Management Module                               │
│  ├─ Route Management Module                             │
│  ├─ Vehicle Tracking Module                             │
│  ├─ Report Management Module                            │
│  └─ Analytics Module                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                AI/ML Layer                               │
│  ├─ Waste Level Predictor (scikit-learn)               │
│  └─ Route Optimizer (Custom Algorithm)                 │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Data Layer                                 │
│  MySQL Database (Normalized Schema)                     │
│  ├─ Users        ├─ Bins          ├─ Vehicles          │
│  ├─ Routes       ├─ Reports       ├─ Sensor Logs       │
│  └─ Alerts       └─ Schedules     └─ Collections       │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              IoT Layer (Simulation)                      │
│  Smart Bin Sensors - Waste Level, Temp, Humidity       │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package manager)
- Git (optional)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "smart waste management system"
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
# Copy the example env file
copy .env.example .env

# Edit .env with your database credentials
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=smart_waste_db
# FLASK_SECRET_KEY=your-secret-key
```

---

## 💾 Database Setup

### Step 1: Create Database
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE smart_waste_db;
exit;
```

### Step 2: Import Schema & Sample Data
```bash
# Import the SQL file
mysql -u root -p smart_waste_db < backend/database.sql
```

The database includes:
- **12 Smart Bins** with sample waste levels
- **4 Vehicles** with different statuses
- **6 Users** (2 Admin, 2 Staff, 2 Citizens)
- **Sample routes, reports, and sensor logs**

---

## 🚀 Running the Application

### Method 1: Run Flask Development Server
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run the application
cd backend
python app.py
```

The server will start on `http://localhost:5000`

### Method 2: Run with Custom Port
```bash
# Set environment variable
set FLASK_APP=backend/app.py
set FLASK_PORT=8080

# Run
python backend/app.py
```

---

## 👥 User Roles & Access

### Default Login Credentials

| Role    | Username  | Password    | Access Level           |
|---------|-----------|-------------|------------------------|
| Admin   | admin     | admin123    | Full system access     |
| Staff   | staff1    | staff123    | Routes & collections   |
| Citizen | citizen1  | citizen123  | Report & schedule view |

### Role Permissions

**Admin:**
- Full dashboard with analytics
- Manage bins, vehicles, routes
- View all reports
- Manage users
- Access AI predictions

**Staff:**
- View assigned routes
- Update collection status
- View full bins list
- Mark collections complete

**Citizen:**
- Report bin issues
- View collection schedule
- Track own reports
- View waste guidelines

---

## 📱 System Modules

### 1. Authentication Module
- Session-based login system
- Role-based access control
- Password hashing (to be implemented in production)
- Auto-logout on session expiry

### 2. Smart Bin Monitoring
**Features:**
- Real-time waste level display
- Color-coded status indicators
- Filter by zone, status, level
- Individual bin details
- Sensor history graphs

**Bin Types:**
- General Waste
- Recyclable
- Organic
- Hazardous

### 3. AI-Based Route Optimization
**Algorithm:** Nearest Neighbor with Priority Weighting

**Features:**
- Predicts bins needing collection
- Optimizes collection sequence
- Minimizes total distance
- Considers waste level priority
- Generates daily routes per zone

**How it works:**
1. AI predicts bins that will be full within 24 hours
2. Calculates fill rate from historical data
3. Assigns priority scores
4. Optimizes route using distance + priority
5. Returns ordered collection sequence

### 4. Vehicle Tracking
**Features:**
- Real-time vehicle status
- Current load monitoring
- GPS location simulation
- Zone assignment
- Capacity utilization

**Vehicle Statuses:**
- Available
- On Route
- Maintenance
- Offline

### 5. Citizen Portal
**Features:**
- Report overflowing bins
- View collection schedule by zone
- Track report status
- Waste disposal guidelines
- User-friendly interface

**Report Types:**
- Overflow
- Damage
- Missing
- Bad Smell
- Other

### 6. Admin Dashboard
**Analytics:**
- Total bins count
- Full bins alert
- Today's collections
- Active alerts
- Pending reports

**Charts:**
- 7-day waste trend (Line chart)
- Zone-wise distribution (Doughnut chart)
- Collection efficiency metrics

### 7. Reporting Module
**Features:**
- All citizen reports
- Status tracking
- Priority-based sorting
- Resolution workflow
- Report history

---

## 🤖 AI/ML Features

### 1. Waste Level Predictor

**File:** `backend/ai/predictor.py`

**Functionality:**
- Uses Linear Regression to analyze historical data
- Calculates fill rate (% per hour) for each bin
- Predicts time until bin reaches 100%
- Identifies bins needing collection within 24 hours

**Algorithm:**
```python
1. Fetch sensor logs (last 7 days)
2. Extract timestamps and waste levels
3. Fit Linear Regression model
4. Calculate slope (fill rate)
5. Predict: hours_to_full = (100 - current_level) / fill_rate
6. Return bins where hours_to_full <= 24
```

**Usage:**
```bash
# Test the predictor
cd backend/ai
python predictor.py
```

### 2. Route Optimizer

**File:** `backend/ai/route_optimizer.py`

**Functionality:**
- Nearest Neighbor algorithm with priority weighting
- Calculates distances using Haversine formula
- Prioritizes bins by waste level
- Generates optimal collection sequence

**Algorithm:**
```python
1. Calculate priority score for each bin (based on waste level)
2. Start from highest priority bin
3. For remaining bins:
   - Calculate weighted score = priority - (distance × weight)
   - Select bin with highest score
   - Move to that bin
4. Return optimized sequence with total distance
```

**Usage:**
```bash
# Test the optimizer
cd backend/ai
python route_optimizer.py
```

---

## 🔌 IoT Simulation

### Bin Sensor Simulator

**File:** `backend/iot_simulator/bin_simulator.py`

**Simulated Sensors:**
- Ultrasonic waste level sensor (0-100%)
- Temperature sensor (20-35°C)
- Humidity sensor (40-80%)

**Features:**
- Realistic waste accumulation
- Different fill rates for bin types
- Random variations
- Automatic database updates
- Collection simulation

**Usage:**

```bash
# Single update (all bins)
cd backend/iot_simulator
python bin_simulator.py --mode single

# Continuous mode (updates every 5 minutes)
python bin_simulator.py --mode continuous --interval 5

# Simulate collection from full bins
python bin_simulator.py --mode collect
```

**How it works:**
1. Reads current waste level from database
2. Generates random increase (based on bin type)
3. Updates bin waste level
4. Logs sensor data (waste_level, temp, humidity)
5. Creates alerts if level >= 80%

---

## 📡 API Documentation

### Authentication APIs

#### Login
```http
POST /login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response: 
{
  "success": true,
  "role": "admin",
  "redirect": "/admin/dashboard"
}
```

#### Logout
```http
GET /logout
```

### Bin APIs

#### Get All Bins
```http
GET /api/bins

Response: [
  {
    "bin_id": 1,
    "bin_code": "BIN001",
    "location": "Main Street",
    "waste_level": 85.5,
    "status": "active",
    ...
  }
]
```

#### Get Bin by ID
```http
GET /api/bins/{bin_id}
```

#### Get Full Bins
```http
GET /api/bins/full?threshold=80
```

#### Update Bin Level
```http
POST /api/bins/{bin_id}/update
Content-Type: application/json

{
  "waste_level": 75.5
}
```

### Vehicle APIs

#### Get All Vehicles
```http
GET /api/vehicles
```

#### Update Vehicle Location
```http
POST /api/vehicles/{vehicle_id}/location
Content-Type: application/json

{
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

### Route APIs

#### Get Routes
```http
GET /api/routes?date=2025-12-28
```

#### Create Route
```http
POST /api/routes/create
Content-Type: application/json

{
  "route_name": "Zone A Morning",
  "vehicle_id": 1,
  "route_date": "2025-12-28",
  "start_time": "06:00:00",
  "bin_ids": [1, 2, 3]
}
```

### Report APIs

#### Get All Reports
```http
GET /api/reports?status=pending
```

#### Create Report
```http
POST /api/reports/create
Content-Type: application/json

{
  "bin_id": 1,
  "report_type": "overflow",
  "description": "Bin is completely full",
  "location": "Main Street",
  "priority": "high"
}
```

### AI APIs

#### Predict Collection
```http
GET /api/ai/predict-collection

Response: [
  {
    "bin_id": 1,
    "bin_code": "BIN001",
    "current_level": 85.5,
    "hours_to_full": 12.3,
    "needs_collection": true,
    "priority": "high"
  }
]
```

#### Optimize Route
```http
POST /api/ai/optimize-route
Content-Type: application/json

{
  "bin_ids": [1, 3, 6, 7, 10]
}

Response: {
  "bins": [...],
  "total_distance": 15.2,
  "total_bins": 5
}
```

### Dashboard APIs

#### Get Statistics
```http
GET /api/dashboard/stats

Response: {
  "total_bins": 12,
  "full_bins": 4,
  "today_collections": 8,
  "active_alerts": 3
}
```

#### Get Waste Trend
```http
GET /api/dashboard/waste-trend?days=7
```

---

## 📁 Project Structure

```
smart waste management system/
│
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── models.py              # Database models & queries
│   ├── database.sql           # MySQL schema & sample data
│   │
│   ├── ai/
│   │   ├── predictor.py       # Waste level prediction (ML)
│   │   └── route_optimizer.py # Route optimization algorithm
│   │
│   └── iot_simulator/
│       └── bin_simulator.py   # IoT sensor simulation
│
├── frontend/
│   ├── templates/
│   │   ├── base.html          # Base template
│   │   ├── index.html         # Landing page
│   │   ├── login.html         # Login page
│   │   │
│   │   ├── admin/
│   │   │   ├── dashboard.html # Admin dashboard
│   │   │   ├── bins.html      # Bin management
│   │   │   ├── vehicles.html  # Vehicle management
│   │   │   ├── routes.html    # Route management
│   │   │   ├── reports.html   # Report management
│   │   │   └── users.html     # User management
│   │   │
│   │   ├── staff/
│   │   │   ├── dashboard.html # Staff dashboard
│   │   │   └── collection.html# Collection routes
│   │   │
│   │   └── citizen/
│   │       ├── dashboard.html # Citizen dashboard
│   │       ├── report.html    # Report issue
│   │       └── schedule.html  # Collection schedule
│   │
│   └── static/
│       ├── css/
│       │   └── style.css      # Custom CSS
│       └── js/
│           └── main.js        # Custom JavaScript
│
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

---

## 🎨 Screenshots

### Admin Dashboard
- Real-time statistics cards
- Waste trend line chart
- Zone distribution pie chart
- Full bins alert table
- Recent alerts list

### Bin Management
- Searchable bin list
- Filter by zone/status/level
- Progress bar for waste levels
- Bin details modal

### AI Route Optimization
- Predicts bins needing collection
- Shows optimized route sequence
- Displays total distance
- Priority-based ordering

### Citizen Portal
- Simple, intuitive interface
- Report submission form
- Collection schedule view
- Waste disposal guidelines

---

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smart_waste_db

# Flask
FLASK_SECRET_KEY=your-secret-key-change-this
FLASK_DEBUG=True
PORT=5000
HOST=0.0.0.0
```

### Database Connection

Edit `backend/models.py` if needed:
```python
self.host = os.getenv('DB_HOST', 'localhost')
self.user = os.getenv('DB_USER', 'root')
self.password = os.getenv('DB_PASSWORD', '')
self.database = os.getenv('DB_NAME', 'smart_waste_db')
```

---

## 🧪 Testing

### Test AI Predictor
```bash
cd backend/ai
python predictor.py
```

### Test Route Optimizer
```bash
cd backend/ai
python route_optimizer.py
```

### Test IoT Simulator
```bash
cd backend/iot_simulator
python bin_simulator.py --mode single
```

### Access Test Users
- Admin: `admin / admin123`
- Staff: `staff1 / staff123`
- Citizen: `citizen1 / citizen123`

---

## 📊 Database Schema

### Key Tables

**users** - System users with role-based access
**bins** - Smart waste bins with location & status
**vehicles** - Collection vehicles with GPS tracking
**routes** - Planned collection routes
**waste_reports** - Citizen-reported issues
**sensor_logs** - IoT sensor data history
**alerts** - System notifications
**schedules** - Collection schedules by zone

### Relationships
- Users → Reports (1:N)
- Routes → Vehicles (N:1)
- Routes → Bins (N:M via route_bins)
- Bins → Sensor Logs (1:N)
- Bins → Alerts (1:N)

---

## 🎓 For Students / Interview

### Key Points to Explain

**1. System Overview:**
- IoT-based waste management with AI optimization
- Real-time monitoring using simulated sensors
- ML predicts collection needs
- Web-based dashboard for all stakeholders

**2. Technical Architecture:**
- MVC pattern with Flask
- RESTful API design
- Normalized MySQL database
- Responsive frontend with Bootstrap
- AI/ML integration with scikit-learn

**3. AI/ML Implementation:**
- Linear Regression for waste level prediction
- Time-series analysis for fill rate
- Custom route optimization algorithm
- Priority-based scheduling

**4. Key Features:**
- Role-based authentication
- Real-time data visualization
- Automated alerts
- Route optimization
- Citizen engagement portal

**5. Real-world Applications:**
- Smart cities implementation
- Municipality waste management
- Corporate campus waste tracking
- Residential society management

### Demo Flow

1. **Admin Login** → Show dashboard with live stats
2. **View Full Bins** → Demonstrate alert system
3. **AI Prediction** → Show ML predictions
4. **Route Optimization** → Display optimized route
5. **IoT Simulation** → Run sensor update
6. **Citizen Portal** → Submit a report
7. **Analytics** → Show charts and trends

---

## 🚀 Deployment

### Production Considerations

1. **Security:**
   - Use hashed passwords (bcrypt)
   - Enable HTTPS
   - Set strong SECRET_KEY
   - Implement CSRF protection

2. **Performance:**
   - Use production WSGI server (Gunicorn)
   - Enable database connection pooling
   - Add caching (Redis)
   - Optimize queries

3. **Deployment:**
   - Docker containerization
   - Cloud hosting (AWS, Azure, GCP)
   - CI/CD pipeline
   - Load balancing

### Example Production Config

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:app
```

---

## 📝 License

This project is created for educational purposes - MCA Final Year Project.

**Author:** Smart Waste Team  
**Year:** 2025  
**Institution:** [Your Institution Name]

---

## 🤝 Contributing

For improvements or bug fixes:

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Email: patidaraayush.62@gmail.com

---

## 🎉 Acknowledgments

- **Flask** - Web framework
- **Bootstrap** - UI framework
- **Chart.js** - Data visualization
- **scikit-learn** - Machine learning
- **MySQL** - Database

---

## ⭐ Star this repository if you find it helpful!

Built with ❤️ for sustainable waste management

---

**End of README**
