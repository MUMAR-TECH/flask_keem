-- KEEM Driving School Database Schema
-- MySQL Database

CREATE DATABASE IF NOT EXISTS keem_driving_school;
USE keem_driving_school;

-- Admins Table
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('super_admin', 'admin', 'staff') DEFAULT 'admin',
    branch VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Applications Table
CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    whatsapp VARCHAR(20) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('male', 'female', 'other') NOT NULL,
    nrc_number VARCHAR(50),
    
    -- Address Information
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    province VARCHAR(100) NOT NULL,
    
    -- Application Details
    branch ENUM('Luanshya', 'Mufulira') NOT NULL,
    course_type VARCHAR(100) NOT NULL,
    previous_experience TEXT,
    preferred_language VARCHAR(50) DEFAULT 'English',
    
    -- Emergency Contact
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    
    -- Additional Information
    medical_conditions TEXT,
    profile_photo VARCHAR(255),
    
    -- Application Status
    status ENUM('pending', 'reviewing', 'accepted', 'rejected', 'cancelled') DEFAULT 'pending',
    admin_notes TEXT,
    reviewed_by INT,
    reviewed_at TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (reviewed_by) REFERENCES admins(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_status (status),
    INDEX idx_branch (branch),
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- Students Table (Accepted Applications become Students)
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT UNIQUE NOT NULL,
    student_number VARCHAR(50) UNIQUE NOT NULL,
    enrollment_date DATE NOT NULL,
    course_start_date DATE,
    course_end_date DATE,
    status ENUM('active', 'completed', 'suspended', 'withdrawn') DEFAULT 'active',
    payment_status ENUM('pending', 'partial', 'paid') DEFAULT 'pending',
    total_fee DECIMAL(10, 2),
    amount_paid DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    INDEX idx_student_number (student_number),
    INDEX idx_status (status)
);

-- Courses Table
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    duration_weeks INT NOT NULL,
    fee DECIMAL(10, 2) NOT NULL,
    requirements TEXT,
    branch VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Lessons/Classes Table
CREATE TABLE lessons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    instructor_id INT,
    lesson_date DATE NOT NULL,
    lesson_time TIME NOT NULL,
    duration_minutes INT DEFAULT 60,
    lesson_type ENUM('theory', 'practical', 'assessment') NOT NULL,
    status ENUM('scheduled', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_lesson_date (lesson_date),
    INDEX idx_student_id (student_id)
);

-- Payments Table
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('cash', 'mobile_money', 'bank_transfer', 'card') NOT NULL,
    payment_reference VARCHAR(255),
    payment_date DATE NOT NULL,
    received_by INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (received_by) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_payment_date (payment_date)
);

-- News/Updates Table
CREATE TABLE news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    author_id INT,
    featured_image VARCHAR(255),
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (author_id) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_published (is_published),
    INDEX idx_published_at (published_at)
);

-- Contact Messages Table
CREATE TABLE contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status ENUM('new', 'read', 'replied') DEFAULT 'new',
    replied_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Notifications Table
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES admins(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read)
);

-- System Settings Table
CREATE TABLE settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert Default Admin Account
-- Password: admin123 (Please change after first login)
INSERT INTO admins (name, email, password, role, branch) VALUES
('System Administrator', 'admin@keemdrivingschool.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5cOK4hC5XGe1u', 'super_admin', 'Luanshya');

-- Insert Sample Courses
INSERT INTO courses (name, code, description, duration_weeks, fee, branch, is_active) VALUES
('Class A - Motorcycle License', 'CLASS-A', 'Complete motorcycle driving course including theory and practical training', 4, 1500.00, 'Both', TRUE),
('Class B - Light Vehicle License', 'CLASS-B', 'Comprehensive car driving course for light vehicles', 6, 2500.00, 'Both', TRUE),
('Class C - Heavy Vehicle License', 'CLASS-C', 'Heavy vehicle and truck driving course', 8, 3500.00, 'Both', TRUE),
('Class D - PSV License', 'CLASS-D', 'Public Service Vehicle driving course', 6, 3000.00, 'Both', TRUE),
('Refresher Course', 'REFRESH', 'Refresher course for experienced drivers', 2, 800.00, 'Both', TRUE),
('Defensive Driving', 'DEFENSIVE', 'Advanced defensive driving techniques', 3, 1200.00, 'Both', TRUE);

-- Insert Default Settings
INSERT INTO settings (setting_key, setting_value, description) VALUES
('school_name', 'KEEM Driving School', 'School name'),
('school_email', 'info@keemdrivingschool.com', 'Primary school email'),
('school_phone', '+260 XXX XXXXXX', 'Primary contact number'),
('luanshya_address', 'Plot 123, Main Street, Luanshya', 'Luanshya branch address'),
('mufulira_address', 'Plot 456, Independence Avenue, Mufulira', 'Mufulira branch address'),
('whatsapp_number', '+260 XXX XXXXXX', 'WhatsApp business number'),
('admin_notification_email', 'admin@keemdrivingschool.com', 'Email for admin notifications'),
('admin_notification_whatsapp', '+260 XXX XXXXXX', 'WhatsApp for admin notifications');

-- Create Views for Common Queries

-- View for Application Statistics
CREATE VIEW application_stats AS
SELECT 
    branch,
    status,
    COUNT(*) as count,
    DATE(created_at) as application_date
FROM applications
GROUP BY branch, status, DATE(created_at);

-- View for Recent Applications
CREATE VIEW recent_applications AS
SELECT 
    a.*,
    CONCAT(a.first_name, ' ', a.last_name) as full_name
FROM applications a
ORDER BY a.created_at DESC
LIMIT 50;

-- View for Student Overview
CREATE VIEW student_overview AS
SELECT 
    s.*,
    a.first_name,
    a.last_name,
    a.email,
    a.phone,
    a.branch,
    CONCAT(a.first_name, ' ', a.last_name) as full_name
FROM students s
JOIN applications a ON s.application_id = a.id;