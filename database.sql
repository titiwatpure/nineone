-- Earthwork Dashboard Database Schema
-- Database: earthwork_db

-- Create database
CREATE DATABASE IF NOT EXISTS earthwork_db;
USE earthwork_db;

-- ตาราง Project - เก็บข้อมูลโปรเจค
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    project_code VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    total_volume DECIMAL(15, 3) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ตาราง STA (Station) - เก็บข้อมูล Station
CREATE TABLE IF NOT EXISTS sta_stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT,
    sta_name VARCHAR(100) NOT NULL,
    sta_from VARCHAR(50),
    sta_to VARCHAR(50),
    design_volume DECIMAL(15, 3) DEFAULT 0,
    completed_volume DECIMAL(15, 3) DEFAULT 0,
    status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- ตาราง Layers - เก็บข้อมูล Layer
CREATE TABLE IF NOT EXISTS layers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sta_id INT,
    layer_number INT NOT NULL,
    layer_name VARCHAR(100),
    design_volume DECIMAL(15, 3) DEFAULT 0,
    completed_volume DECIMAL(15, 3) DEFAULT 0,
    thickness DECIMAL(10, 3),
    status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
    completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sta_id) REFERENCES sta_stations(id)
);

-- ตาราง Volume Records - เก็บข้อมูลปริมาตรงานดิน
CREATE TABLE IF NOT EXISTS volume_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sta_id INT,
    layer_id INT,
    record_date DATE NOT NULL,
    volume_type ENUM('cut', 'fill', 'borrow', 'waste') NOT NULL,
    volume DECIMAL(15, 3) NOT NULL,
    unit VARCHAR(20) DEFAULT 'm3',
    remarks TEXT,
    recorded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sta_id) REFERENCES sta_stations(id),
    FOREIGN KEY (layer_id) REFERENCES layers(id)
);

-- ตาราง QAQC Tests - เก็บข้อมูลการทดสอบ
CREATE TABLE IF NOT EXISTS qaqc_tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sta_id INT,
    layer_id INT,
    test_date DATE NOT NULL,
    test_type VARCHAR(100) NOT NULL,
    test_location VARCHAR(255),
    -- Field Density Test
    field_density DECIMAL(10, 4),
    max_dry_density DECIMAL(10, 4),
    compaction_percent DECIMAL(5, 2),
    -- Moisture Content
    moisture_content DECIMAL(5, 2),
    optimum_moisture DECIMAL(5, 2),
    -- CBR Test
    cbr_value DECIMAL(5, 2),
    -- Test Results
    required_value DECIMAL(10, 4),
    actual_value DECIMAL(10, 4),
    result ENUM('pass', 'fail', 'pending') DEFAULT 'pending',
    remarks TEXT,
    tested_by VARCHAR(100),
    approved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sta_id) REFERENCES sta_stations(id),
    FOREIGN KEY (layer_id) REFERENCES layers(id)
);

-- ตาราง Daily Progress - เก็บข้อมูลความก้าวหน้ารายวัน
CREATE TABLE IF NOT EXISTS daily_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT,
    record_date DATE NOT NULL,
    total_volume_today DECIMAL(15, 3) DEFAULT 0,
    cumulative_volume DECIMAL(15, 3) DEFAULT 0,
    weather VARCHAR(50),
    manpower INT,
    equipment_count INT,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- View สำหรับ Summary Dashboard
CREATE OR REPLACE VIEW dashboard_summary AS
SELECT
    p.id AS project_id,
    p.project_name,
    p.total_volume AS design_total_volume,
    COALESCE(SUM(vr.volume), 0) AS completed_volume,
    p.total_volume - COALESCE(SUM(vr.volume), 0) AS remaining_volume,
    ROUND((COALESCE(SUM(vr.volume), 0) / NULLIF(p.total_volume, 0)) * 100, 2) AS completion_percent
FROM projects p
LEFT JOIN sta_stations s ON p.id = s.project_id
LEFT JOIN volume_records vr ON s.id = vr.sta_id
GROUP BY p.id, p.project_name, p.total_volume;

-- View สำหรับ STA Progress
CREATE OR REPLACE VIEW sta_progress_view AS
SELECT
    s.id AS sta_id,
    s.project_id,
    s.sta_name,
    s.sta_from,
    s.sta_to,
    s.design_volume,
    s.completed_volume,
    s.design_volume - s.completed_volume AS remaining_volume,
    ROUND((s.completed_volume / NULLIF(s.design_volume, 0)) * 100, 2) AS progress_percent,
    s.status,
    COUNT(DISTINCT l.id) AS total_layers,
    SUM(CASE WHEN l.status = 'completed' THEN 1 ELSE 0 END) AS completed_layers
FROM sta_stations s
LEFT JOIN layers l ON s.id = l.sta_id
GROUP BY s.id, s.project_id, s.sta_name, s.sta_from, s.sta_to,
         s.design_volume, s.completed_volume, s.status;

-- View สำหรับ Layer Progress
CREATE OR REPLACE VIEW layer_progress_view AS
SELECT
    l.id AS layer_id,
    l.sta_id,
    s.sta_name,
    l.layer_number,
    l.layer_name,
    l.design_volume,
    l.completed_volume,
    l.design_volume - l.completed_volume AS remaining_volume,
    ROUND((l.completed_volume / NULLIF(l.design_volume, 0)) * 100, 2) AS progress_percent,
    l.thickness,
    l.status,
    l.completion_date
FROM layers l
JOIN sta_stations s ON l.sta_id = s.id;

-- View สำหรับ QAQC Summary
CREATE OR REPLACE VIEW qaqc_summary_view AS
SELECT
    s.sta_name,
    l.layer_number,
    l.layer_name,
    COUNT(q.id) AS total_tests,
    SUM(CASE WHEN q.result = 'pass' THEN 1 ELSE 0 END) AS passed_tests,
    SUM(CASE WHEN q.result = 'fail' THEN 1 ELSE 0 END) AS failed_tests,
    SUM(CASE WHEN q.result = 'pending' THEN 1 ELSE 0 END) AS pending_tests,
    ROUND((SUM(CASE WHEN q.result = 'pass' THEN 1 ELSE 0 END) / NULLIF(COUNT(q.id), 0)) * 100, 2) AS pass_rate
FROM qaqc_tests q
JOIN sta_stations s ON q.sta_id = s.id
LEFT JOIN layers l ON q.layer_id = l.id
GROUP BY s.sta_name, l.layer_number, l.layer_name;

-- Insert Sample Data
INSERT INTO projects (project_name, project_code, start_date, end_date, total_volume) VALUES
('Highway Construction Project A', 'HWY-001', '2026-01-01', '2026-12-31', 500000.000);

-- Sample STA Stations
INSERT INTO sta_stations (project_id, sta_name, sta_from, sta_to, design_volume, completed_volume, status) VALUES
(1, 'STA 0+000 - 0+500', '0+000', '0+500', 50000.000, 45000.000, 'in_progress'),
(1, 'STA 0+500 - 1+000', '0+500', '1+000', 60000.000, 60000.000, 'completed'),
(1, 'STA 1+000 - 1+500', '1+000', '1+500', 55000.000, 30000.000, 'in_progress'),
(1, 'STA 1+500 - 2+000', '1+500', '2+000', 70000.000, 10000.000, 'in_progress'),
(1, 'STA 2+000 - 2+500', '2+000', '2+500', 65000.000, 0.000, 'not_started');

-- Sample Layers
INSERT INTO layers (sta_id, layer_number, layer_name, design_volume, completed_volume, thickness, status, completion_date) VALUES
(1, 1, 'Subgrade', 10000.000, 10000.000, 0.30, 'completed', '2026-02-15'),
(1, 2, 'Sub-base', 15000.000, 15000.000, 0.25, 'completed', '2026-02-28'),
(1, 3, 'Base', 15000.000, 12000.000, 0.20, 'in_progress', NULL),
(1, 4, 'Wearing Course', 10000.000, 8000.000, 0.15, 'in_progress', NULL),
(2, 1, 'Subgrade', 15000.000, 15000.000, 0.30, 'completed', '2026-01-30'),
(2, 2, 'Sub-base', 20000.000, 20000.000, 0.25, 'completed', '2026-02-10'),
(2, 3, 'Base', 15000.000, 15000.000, 0.20, 'completed', '2026-02-20'),
(2, 4, 'Wearing Course', 10000.000, 10000.000, 0.15, 'completed', '2026-03-01');

-- Sample QAQC Tests
INSERT INTO qaqc_tests (sta_id, layer_id, test_date, test_type, test_location, field_density, max_dry_density, compaction_percent, moisture_content, optimum_moisture, result, tested_by) VALUES
(1, 1, '2026-02-14', 'Field Density Test', 'STA 0+100 LT', 2.05, 2.10, 97.62, 8.5, 9.0, 'pass', 'Engineer A'),
(1, 1, '2026-02-14', 'Field Density Test', 'STA 0+250 CL', 2.08, 2.10, 99.05, 8.8, 9.0, 'pass', 'Engineer A'),
(1, 2, '2026-02-27', 'Field Density Test', 'STA 0+150 RT', 2.02, 2.08, 97.12, 7.5, 8.0, 'pass', 'Engineer B'),
(1, 3, '2026-03-05', 'Field Density Test', 'STA 0+200 LT', 1.98, 2.12, 93.40, 9.2, 8.5, 'fail', 'Engineer A'),
(2, 5, '2026-01-29', 'Field Density Test', 'STA 0+600 CL', 2.12, 2.15, 98.60, 8.2, 8.5, 'pass', 'Engineer C'),
(2, 6, '2026-02-09', 'CBR Test', 'STA 0+750 RT', NULL, NULL, NULL, NULL, NULL, 'pass', 'Engineer B');

-- Sample Volume Records
INSERT INTO volume_records (sta_id, layer_id, record_date, volume_type, volume, remarks, recorded_by) VALUES
(1, 1, '2026-02-10', 'fill', 5000.000, 'Layer 1 first section', 'Surveyor A'),
(1, 1, '2026-02-15', 'fill', 5000.000, 'Layer 1 completed', 'Surveyor A'),
(1, 2, '2026-02-20', 'fill', 8000.000, 'Layer 2 progress', 'Surveyor B'),
(1, 2, '2026-02-28', 'fill', 7000.000, 'Layer 2 completed', 'Surveyor B'),
(2, 5, '2026-01-25', 'fill', 15000.000, 'Fast track area', 'Surveyor A'),
(2, 6, '2026-02-05', 'fill', 20000.000, 'Sub-base completed', 'Surveyor C');
