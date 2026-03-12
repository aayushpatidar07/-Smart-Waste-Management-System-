-- =========================================
-- Smart Waste Management System
-- Waste Logs - Views and Helper Queries
-- Performance Optimization & Analytics
-- =========================================

USE smart_waste_db;

-- =========================================
-- VIEW: waste_logs_summary
-- Purpose: Quick access to waste log summaries
-- =========================================
CREATE OR REPLACE VIEW waste_logs_summary AS
SELECT 
    wl.log_id,
    wl.bin_id,
    b.bin_code,
    b.location,
    b.zone,
    wl.fill_level,
    CASE 
        WHEN wl.fill_level >= 80 THEN 'critical'
        WHEN wl.fill_level >= 60 THEN 'warning'
        ELSE 'normal'
    END AS status,
    wl.notes,
    wl.timestamp
FROM waste_logs wl
JOIN bins b ON wl.bin_id = b.bin_id
ORDER BY wl.timestamp DESC;

-- =========================================
-- VIEW: critical_bins_current
-- Purpose: Show bins currently at critical fill levels
-- =========================================
CREATE OR REPLACE VIEW critical_bins_current AS
SELECT 
    b.bin_id,
    b.bin_code,
    b.location,
    b.zone,
    wl.fill_level,
    wl.timestamp,
    wl.notes,
    TIMESTAMPDIFF(HOUR, wl.timestamp, NOW()) as hours_since_log
FROM waste_logs wl
JOIN bins b ON wl.bin_id = b.bin_id
WHERE wl.fill_level >= 80
  AND wl.log_id IN (
      SELECT MAX(log_id) 
      FROM waste_logs 
      GROUP BY bin_id
  )
ORDER BY wl.fill_level DESC, wl.timestamp ASC;

-- =========================================
-- VIEW: zone_performance_summary
-- Purpose: Aggregated performance metrics by zone
-- =========================================
CREATE OR REPLACE VIEW zone_performance_summary AS
SELECT 
    b.zone,
    COUNT(DISTINCT b.bin_id) as total_bins,
    COUNT(wl.log_id) as total_logs,
    AVG(wl.fill_level) as avg_fill_level,
    MAX(wl.fill_level) as max_fill_level,
    MIN(wl.fill_level) as min_fill_level,
    SUM(CASE WHEN wl.fill_level >= 80 THEN 1 ELSE 0 END) as critical_logs,
    SUM(CASE WHEN wl.fill_level >= 60 AND wl.fill_level < 80 THEN 1 ELSE 0 END) as warning_logs,
    SUM(CASE WHEN wl.fill_level < 60 THEN 1 ELSE 0 END) as normal_logs,
    MAX(wl.timestamp) as last_log_time
FROM waste_logs wl
JOIN bins b ON wl.bin_id = b.bin_id
WHERE wl.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY b.zone
ORDER BY avg_fill_level DESC;

-- =========================================
-- VIEW: bin_activity_metrics
-- Purpose: Track bin activity and collection patterns
-- =========================================
CREATE OR REPLACE VIEW bin_activity_metrics AS
SELECT 
    b.bin_id,
    b.bin_code,
    b.location,
    b.zone,
    COUNT(wl.log_id) as log_count,
    AVG(wl.fill_level) as avg_fill_level,
    MAX(wl.fill_level) as max_fill_level,
    MIN(wl.fill_level) as min_fill_level,
    STDDEV(wl.fill_level) as fill_variance,
    MIN(wl.timestamp) as first_log,
    MAX(wl.timestamp) as last_log,
    DATEDIFF(MAX(wl.timestamp), MIN(wl.timestamp)) as days_active,
    CASE 
        WHEN COUNT(wl.log_id) >= 10 THEN 'High Activity'
        WHEN COUNT(wl.log_id) >= 5 THEN 'Medium Activity'
        ELSE 'Low Activity'
    END as activity_level
FROM waste_logs wl
JOIN bins b ON wl.bin_id = b.bin_id
WHERE wl.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY b.bin_id, b.bin_code, b.location, b.zone
HAVING log_count >= 2
ORDER BY log_count DESC;

-- =========================================
-- VIEW: hourly_log_distribution
-- Purpose: Analyze logging patterns by hour of day
-- =========================================
CREATE OR REPLACE VIEW hourly_log_distribution AS
SELECT 
    HOUR(timestamp) as hour_of_day,
    COUNT(*) as log_count,
    AVG(fill_level) as avg_fill_level,
    SUM(CASE WHEN fill_level >= 80 THEN 1 ELSE 0 END) as critical_count
FROM waste_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY HOUR(timestamp)
ORDER BY hour_of_day;

-- =========================================
-- STORED PROCEDURE: sp_cleanup_old_logs
-- Purpose: Archive or delete logs older than specified days
-- =========================================
DELIMITER //

CREATE PROCEDURE sp_cleanup_old_logs(IN days_to_keep INT)
BEGIN
    DECLARE rows_deleted INT;
    
    -- Delete logs older than specified days
    DELETE FROM waste_logs
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    -- Get count of deleted rows
    SET rows_deleted = ROW_COUNT();
    
    -- Return result
    SELECT rows_deleted as 'Rows Deleted', 
           days_to_keep as 'Days Kept',
           NOW() as 'Cleanup Time';
END //

DELIMITER ;

-- =========================================
-- STORED PROCEDURE: sp_get_bin_trend
-- Purpose: Get fill level trend for a specific bin
-- =========================================
DELIMITER //

CREATE PROCEDURE sp_get_bin_trend(IN p_bin_id INT, IN p_days INT)
BEGIN
    SELECT 
        DATE(timestamp) as log_date,
        COUNT(*) as logs_per_day,
        AVG(fill_level) as avg_fill_level,
        MIN(fill_level) as min_fill_level,
        MAX(fill_level) as max_fill_level
    FROM waste_logs
    WHERE bin_id = p_bin_id
      AND timestamp >= DATE_SUB(NOW(), INTERVAL p_days DAY)
    GROUP BY DATE(timestamp)
    ORDER BY log_date;
END //

DELIMITER ;

-- =========================================
-- STORED PROCEDURE: sp_get_collection_priorities
-- Purpose: Calculate collection priorities for all bins
-- =========================================
DELIMITER //

CREATE PROCEDURE sp_get_collection_priorities()
BEGIN
    SELECT 
        b.bin_id,
        b.bin_code,
        b.location,
        b.zone,
        wl.fill_level,
        wl.timestamp as last_logged,
        TIMESTAMPDIFF(HOUR, wl.timestamp, NOW()) as hours_since_log,
        CASE 
            WHEN wl.fill_level >= 90 THEN 10
            WHEN wl.fill_level >= 80 THEN 8
            WHEN wl.fill_level >= 70 THEN 6
            WHEN wl.fill_level >= 60 THEN 4
            ELSE 2
        END +
        CASE 
            WHEN TIMESTAMPDIFF(HOUR, wl.timestamp, NOW()) > 48 THEN 2
            WHEN TIMESTAMPDIFF(HOUR, wl.timestamp, NOW()) > 24 THEN 1
            ELSE 0
        END as priority_score
    FROM bins b
    LEFT JOIN (
        SELECT bin_id, fill_level, timestamp,
               ROW_NUMBER() OVER (PARTITION BY bin_id ORDER BY timestamp DESC) as rn
        FROM waste_logs
    ) wl ON b.bin_id = wl.bin_id AND wl.rn = 1
    WHERE b.status = 'active'
    ORDER BY priority_score DESC, wl.fill_level DESC;
END //

DELIMITER ;

-- =========================================
-- FUNCTION: fn_get_fill_status
-- Purpose: Get status text for a fill level
-- =========================================
DELIMITER //

CREATE FUNCTION fn_get_fill_status(p_fill_level DECIMAL(5,2))
RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
    DECLARE v_status VARCHAR(10);
    
    IF p_fill_level >= 80 THEN
        SET v_status = 'critical';
    ELSEIF p_fill_level >= 60 THEN
        SET v_status = 'warning';
    ELSE
        SET v_status = 'normal';
    END IF;
    
    RETURN v_status;
END //

DELIMITER ;

-- =========================================
-- FUNCTION: fn_calculate_priority
-- Purpose: Calculate collection priority score
-- =========================================
DELIMITER //

CREATE FUNCTION fn_calculate_priority(
    p_fill_level DECIMAL(5,2),
    p_hours_since_log INT
)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_priority INT DEFAULT 0;
    
    -- Base priority on fill level
    IF p_fill_level >= 90 THEN
        SET v_priority = 10;
    ELSEIF p_fill_level >= 80 THEN
        SET v_priority = 8;
    ELSEIF p_fill_level >= 70 THEN
        SET v_priority = 6;
    ELSEIF p_fill_level >= 60 THEN
        SET v_priority = 4;
    ELSE
        SET v_priority = 2;
    END IF;
    
    -- Adjust for time
    IF p_hours_since_log > 48 THEN
        SET v_priority = LEAST(10, v_priority + 2);
    ELSEIF p_hours_since_log > 24 THEN
        SET v_priority = LEAST(10, v_priority + 1);
    END IF;
    
    RETURN v_priority;
END //

DELIMITER ;

-- =========================================
-- USEFUL QUERIES FOR COMMON OPERATIONS
-- =========================================

-- Query 1: Get today's logging activity
-- SELECT * FROM waste_logs WHERE DATE(timestamp) = CURDATE() ORDER BY timestamp DESC;

-- Query 2: Get bins not logged in last 24 hours
-- SELECT b.* FROM bins b
-- LEFT JOIN (
--     SELECT bin_id, MAX(timestamp) as last_log
--     FROM waste_logs
--     GROUP BY bin_id
-- ) wl ON b.bin_id = wl.bin_id
-- WHERE wl.last_log IS NULL OR wl.last_log < DATE_SUB(NOW(), INTERVAL 24 HOUR);

-- Query 3: Get average fill level by hour for optimization
-- SELECT HOUR(timestamp) as hour, AVG(fill_level) as avg_fill
-- FROM waste_logs
-- WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
-- GROUP BY HOUR(timestamp)
-- ORDER BY avg_fill DESC;

-- Query 4: Find bins with rapidly increasing fill levels
-- SELECT bin_id, AVG(fill_level) as avg_recent
-- FROM waste_logs
-- WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 3 DAY)
-- GROUP BY bin_id
-- HAVING avg_recent > (
--     SELECT AVG(fill_level) * 1.5
--     FROM waste_logs
--     WHERE bin_id = waste_logs.bin_id
--     AND timestamp BETWEEN DATE_SUB(NOW(), INTERVAL 30 DAY) AND DATE_SUB(NOW(), INTERVAL 7 DAY)
-- );

-- Query 5: Zone-wise collection efficiency
-- SELECT b.zone,
--        COUNT(DISTINCT b.bin_id) as bins,
--        COUNT(wl.log_id) as total_logs,
--        AVG(wl.fill_level) as avg_fill,
--        SUM(CASE WHEN wl.fill_level >= 80 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as critical_percentage
-- FROM waste_logs wl
-- JOIN bins b ON wl.bin_id = b.bin_id
-- WHERE wl.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
-- GROUP BY b.zone
-- ORDER BY critical_percentage DESC;

-- =========================================
-- INDEX OPTIMIZATION SUGGESTIONS
-- =========================================

-- Additional indexes for performance (already implemented in main schema):
-- CREATE INDEX idx_bin_id ON waste_logs(bin_id);
-- CREATE INDEX idx_timestamp ON waste_logs(timestamp);
-- CREATE INDEX idx_fill_level ON waste_logs(fill_level);
-- CREATE INDEX idx_bin_timestamp ON waste_logs(bin_id, timestamp);

-- Composite index for common query patterns:
-- CREATE INDEX idx_fill_timestamp ON waste_logs(fill_level, timestamp);

-- =========================================
-- MAINTENANCE COMMANDS
-- =========================================

-- Analyze table statistics for query optimizer:
-- ANALYZE TABLE waste_logs;

-- Optimize table (defragment and rebuild indexes):
-- OPTIMIZE TABLE waste_logs;

-- Check table integrity:
-- CHECK TABLE waste_logs;

-- Repair table if corrupted:
-- REPAIR TABLE waste_logs;

-- =========================================
-- END OF WASTE LOGS HELPER QUERIES
-- =========================================
