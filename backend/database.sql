-- =========================================
-- Smart Waste Management System
-- MySQL Database Schema
-- IEEE SRS Compliant Database Design
-- =========================================

-- Create Database
CREATE DATABASE IF NOT EXISTS smart_waste_db;
USE smart_waste_db;

-- =========================================
-- Table: users
-- Purpose: Store all users (admin, staff, citizens)
-- =========================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    role ENUM('admin', 'staff', 'citizen') NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    status ENUM('active', 'inactive') DEFAULT 'active',
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB;

-- =========================================
-- Table: bins
-- Purpose: Store smart bin information
-- =========================================
CREATE TABLE bins (
    bin_id INT AUTO_INCREMENT PRIMARY KEY,
    bin_code VARCHAR(20) UNIQUE NOT NULL,
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    capacity DECIMAL(5, 2) DEFAULT 100.00, -- in liters
    waste_level DECIMAL(5, 2) DEFAULT 0.00, -- percentage (0-100)
    bin_type ENUM('general', 'recyclable', 'organic', 'hazardous') DEFAULT 'general',
    status ENUM('active', 'maintenance', 'inactive') DEFAULT 'active',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_collected TIMESTAMP NULL,
    zone VARCHAR(50),
    INDEX idx_status (status),
    INDEX idx_waste_level (waste_level),
    INDEX idx_zone (zone)
) ENGINE=InnoDB;

-- =========================================
-- Table: vehicles
-- Purpose: Track waste collection vehicles
-- =========================================
CREATE TABLE vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50) DEFAULT 'Truck',
    driver_name VARCHAR(100),
    driver_phone VARCHAR(15),
    capacity DECIMAL(8, 2) DEFAULT 1000.00, -- in liters
    current_load DECIMAL(8, 2) DEFAULT 0.00,
    status ENUM('available', 'on-route', 'maintenance', 'offline') DEFAULT 'available',
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),
    last_location_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    assigned_zone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_vehicle_number (vehicle_number)
) ENGINE=InnoDB;

-- =========================================
-- Table: routes
-- Purpose: Store collection routes
-- =========================================
CREATE TABLE routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL,
    vehicle_id INT,
    route_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    total_bins INT DEFAULT 0,
    bins_collected INT DEFAULT 0,
    status ENUM('planned', 'in-progress', 'completed', 'cancelled') DEFAULT 'planned',
    estimated_distance DECIMAL(8, 2), -- in km
    actual_distance DECIMAL(8, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    INDEX idx_route_date (route_date),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- =========================================
-- Table: route_bins
-- Purpose: Map bins to routes (many-to-many)
-- =========================================
CREATE TABLE route_bins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    bin_id INT NOT NULL,
    sequence_order INT,
    collected BOOLEAN DEFAULT FALSE,
    collection_time TIMESTAMP NULL,
    FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE,
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id) ON DELETE CASCADE,
    INDEX idx_route (route_id),
    INDEX idx_bin (bin_id)
) ENGINE=InnoDB;

-- =========================================
-- Table: waste_reports
-- Purpose: Citizen-reported issues
-- =========================================
CREATE TABLE waste_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    citizen_id INT,
    bin_id INT,
    report_type ENUM('overflow', 'damage', 'missing', 'smell', 'other') NOT NULL,
    description TEXT,
    location VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    image_path VARCHAR(255),
    status ENUM('pending', 'acknowledged', 'resolved', 'rejected') DEFAULT 'pending',
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolved_by INT,
    resolution_notes TEXT,
    FOREIGN KEY (citizen_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id) ON DELETE SET NULL,
    FOREIGN KEY (resolved_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_reported_at (reported_at)
) ENGINE=InnoDB;

-- =========================================
-- Table: sensor_logs
-- Purpose: IoT sensor data history
-- =========================================
CREATE TABLE sensor_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id INT NOT NULL,
    waste_level DECIMAL(5, 2) NOT NULL,
    temperature DECIMAL(5, 2), -- in Celsius
    humidity DECIMAL(5, 2), -- percentage
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sensor_status ENUM('normal', 'warning', 'error') DEFAULT 'normal',
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id) ON DELETE CASCADE,
    INDEX idx_bin_timestamp (bin_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- =========================================
-- Table: collection_logs
-- Purpose: Track all waste collection activities
-- =========================================
CREATE TABLE collection_logs (
    collection_id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id INT NOT NULL,
    vehicle_id INT,
    route_id INT,
    collected_by INT, -- staff user_id
    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    waste_amount DECIMAL(8, 2), -- in kg or liters
    before_level DECIMAL(5, 2),
    after_level DECIMAL(5, 2),
    notes TEXT,
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE SET NULL,
    FOREIGN KEY (collected_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_collection_time (collection_time),
    INDEX idx_bin (bin_id)
) ENGINE=InnoDB;

-- =========================================
-- Table: schedules
-- Purpose: Waste collection schedules for citizens
-- =========================================
CREATE TABLE schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    zone VARCHAR(50) NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    collection_time TIME NOT NULL,
    waste_type ENUM('general', 'recyclable', 'organic', 'hazardous') DEFAULT 'general',
    status ENUM('active', 'inactive') DEFAULT 'active',
    INDEX idx_zone (zone),
    INDEX idx_day (day_of_week)
) ENGINE=InnoDB;

-- =========================================
-- Table: alerts
-- Purpose: System alerts and notifications
-- =========================================
CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id INT,
    alert_type ENUM('full_bin', 'sensor_error', 'maintenance_required', 'route_delay', 'other') NOT NULL,
    message TEXT NOT NULL,
    severity ENUM('info', 'warning', 'critical') DEFAULT 'warning',
    status ENUM('active', 'acknowledged', 'resolved') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP NULL,
    acknowledged_by INT,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- =========================================
-- SAMPLE DATA INSERTION
-- =========================================

-- Insert Users (Password: 'password123' - In production, use hashed passwords)
INSERT INTO users (username, password, full_name, email, phone, role, address) VALUES
('admin', 'admin123', 'System Administrator', 'admin@smartwaste.com', '9876543210', 'admin', 'City Corporation Office'),
('staff1', 'staff123', 'John Doe', 'john@smartwaste.com', '9876543211', 'staff', 'Zone A Collection Center'),
('staff2', 'staff123', 'Jane Smith', 'jane@smartwaste.com', '9876543212', 'staff', 'Zone B Collection Center'),
('citizen1', 'citizen123', 'Robert Brown', 'robert@email.com', '9876543213', 'citizen', 'Street 1, Zone A'),
('citizen2', 'citizen123', 'Emily Davis', 'emily@email.com', '9876543214', 'citizen', 'Street 5, Zone B'),
('citizen3', 'citizen123', 'Michael Wilson', 'michael@email.com', '9876543215', 'citizen', 'Street 10, Zone C');

-- Insert Smart Bins
INSERT INTO bins (bin_code, location, latitude, longitude, capacity, waste_level, bin_type, zone) VALUES
('BIN001', 'Main Street Junction', 28.6139, 77.2090, 100, 85.5, 'general', 'Zone A'),
('BIN002', 'Park Avenue', 28.6149, 77.2100, 100, 45.2, 'recyclable', 'Zone A'),
('BIN003', 'School Road', 28.6159, 77.2110, 100, 92.8, 'general', 'Zone A'),
('BIN004', 'Market Square', 28.6169, 77.2120, 100, 67.3, 'organic', 'Zone B'),
('BIN005', 'Hospital Gate', 28.6179, 77.2130, 100, 23.1, 'hazardous', 'Zone B'),
('BIN006', 'Community Center', 28.6189, 77.2140, 100, 88.9, 'general', 'Zone B'),
('BIN007', 'Bus Station', 28.6199, 77.2150, 100, 78.4, 'general', 'Zone C'),
('BIN008', 'Shopping Mall', 28.6209, 77.2160, 100, 34.6, 'recyclable', 'Zone C'),
('BIN009', 'Temple Street', 28.6219, 77.2170, 100, 56.2, 'general', 'Zone C'),
('BIN010', 'Railway Station', 28.6229, 77.2180, 100, 91.3, 'general', 'Zone C'),
('BIN011', 'Garden Park', 28.6239, 77.2190, 100, 12.5, 'organic', 'Zone A'),
('BIN012', 'Office Complex', 28.6249, 77.2200, 100, 73.8, 'general', 'Zone A');

-- Insert Vehicles
INSERT INTO vehicles (vehicle_number, vehicle_type, driver_name, driver_phone, capacity, current_load, status, assigned_zone) VALUES
('TRK-001', 'Compactor Truck', 'Ravi Kumar', '9876501001', 2000, 450, 'available', 'Zone A'),
('TRK-002', 'Tipper Truck', 'Suresh Yadav', '9876501002', 1500, 0, 'available', 'Zone B'),
('TRK-003', 'Mini Truck', 'Amit Singh', '9876501003', 1000, 780, 'on-route', 'Zone C'),
('TRK-004', 'Compactor Truck', 'Vijay Sharma', '9876501004', 2000, 0, 'maintenance', 'Zone A');

-- Insert Routes
INSERT INTO routes (route_name, vehicle_id, route_date, start_time, status, total_bins, bins_collected, estimated_distance) VALUES
('Zone A Morning Route', 1, CURDATE(), '06:00:00', 'completed', 5, 5, 12.5),
('Zone B Morning Route', 2, CURDATE(), '06:30:00', 'in-progress', 4, 2, 10.8),
('Zone C Evening Route', 3, CURDATE(), '15:00:00', 'planned', 6, 0, 15.2);

-- Insert Route-Bin Mappings
INSERT INTO route_bins (route_id, bin_id, sequence_order, collected) VALUES
(1, 1, 1, TRUE),
(1, 2, 2, TRUE),
(1, 3, 3, TRUE),
(2, 4, 1, TRUE),
(2, 5, 2, TRUE),
(2, 6, 3, FALSE),
(3, 7, 1, FALSE),
(3, 8, 2, FALSE),
(3, 9, 3, FALSE),
(3, 10, 4, FALSE);

-- Insert Waste Reports
INSERT INTO waste_reports (citizen_id, bin_id, report_type, description, status, priority) VALUES
(4, 1, 'overflow', 'Bin is completely full and waste is spilling out', 'acknowledged', 'high'),
(5, 3, 'overflow', 'Urgent - bin overflowing for 2 days', 'pending', 'critical'),
(6, 6, 'smell', 'Bad odor coming from the bin', 'pending', 'medium'),
(4, 10, 'damage', 'Bin lid is broken', 'resolved', 'low');

-- Insert Sensor Logs (Last 24 hours sample data)
INSERT INTO sensor_logs (bin_id, waste_level, temperature, humidity, sensor_status) VALUES
(1, 85.5, 28.5, 65.2, 'warning'),
(2, 45.2, 27.8, 62.1, 'normal'),
(3, 92.8, 29.2, 68.5, 'warning'),
(4, 67.3, 26.5, 60.3, 'normal'),
(5, 23.1, 25.8, 58.7, 'normal'),
(6, 88.9, 30.1, 70.2, 'warning'),
(7, 78.4, 28.3, 64.5, 'normal'),
(8, 34.6, 27.1, 61.8, 'normal'),
(9, 56.2, 28.7, 66.3, 'normal'),
(10, 91.3, 29.8, 69.1, 'warning'),
(11, 12.5, 26.2, 59.4, 'normal'),
(12, 73.8, 28.9, 67.8, 'normal');

-- Insert Collection Logs
INSERT INTO collection_logs (bin_id, vehicle_id, route_id, collected_by, waste_amount, before_level, after_level) VALUES
(1, 1, 1, 2, 85.0, 85.5, 5.2),
(2, 1, 1, 2, 45.0, 45.2, 3.1),
(4, 2, 2, 3, 67.0, 67.3, 8.5);

-- Insert Schedules
INSERT INTO schedules (zone, day_of_week, collection_time, waste_type) VALUES
('Zone A', 'Monday', '06:00:00', 'general'),
('Zone A', 'Wednesday', '06:00:00', 'recyclable'),
('Zone A', 'Friday', '06:00:00', 'organic'),
('Zone B', 'Tuesday', '06:30:00', 'general'),
('Zone B', 'Thursday', '06:30:00', 'recyclable'),
('Zone B', 'Saturday', '07:00:00', 'organic'),
('Zone C', 'Monday', '15:00:00', 'general'),
('Zone C', 'Wednesday', '15:00:00', 'recyclable'),
('Zone C', 'Friday', '15:00:00', 'organic');

-- Insert Alerts
INSERT INTO alerts (bin_id, alert_type, message, severity, status) VALUES
(1, 'full_bin', 'BIN001 at Main Street Junction has reached 85% capacity', 'warning', 'acknowledged'),
(3, 'full_bin', 'BIN003 at School Road has reached 92% capacity - CRITICAL', 'critical', 'active'),
(6, 'full_bin', 'BIN006 at Community Center has reached 88% capacity', 'warning', 'active'),
(10, 'full_bin', 'BIN010 at Railway Station has reached 91% capacity', 'critical', 'active');

-- =========================================
-- USEFUL VIEWS FOR REPORTING
-- =========================================

-- View: Full Bins Alert
CREATE VIEW v_full_bins AS
SELECT 
    b.bin_id,
    b.bin_code,
    b.location,
    b.waste_level,
    b.bin_type,
    b.zone,
    b.last_updated
FROM bins b
WHERE b.waste_level >= 80 AND b.status = 'active'
ORDER BY b.waste_level DESC;

-- View: Today's Collection Summary
CREATE VIEW v_today_collection AS
SELECT 
    r.route_id,
    r.route_name,
    v.vehicle_number,
    r.total_bins,
    r.bins_collected,
    r.status,
    ROUND((r.bins_collected * 100.0 / r.total_bins), 2) AS completion_percentage
FROM routes r
LEFT JOIN vehicles v ON r.vehicle_id = v.vehicle_id
WHERE r.route_date = CURDATE();

-- View: Pending Reports
CREATE VIEW v_pending_reports AS
SELECT 
    wr.report_id,
    u.full_name AS citizen_name,
    b.bin_code,
    b.location,
    wr.report_type,
    wr.priority,
    wr.reported_at
FROM waste_reports wr
LEFT JOIN users u ON wr.citizen_id = u.user_id
LEFT JOIN bins b ON wr.bin_id = b.bin_id
WHERE wr.status IN ('pending', 'acknowledged')
ORDER BY wr.priority DESC, wr.reported_at ASC;

-- =========================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =========================================
-- Already created inline with table definitions

-- =========================================
-- END OF SCHEMA
-- =========================================

SELECT 'Smart Waste Management Database Created Successfully!' AS Status;
