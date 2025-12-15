"""
SQLite Database Setup for KEEM Driving School with Proper Relationships
"""
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_database():
    """Create SQLite database with all tables and proper relationships"""
    conn = sqlite3.connect('keem_driving.db')
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
    # ============== CORE TABLES ==============
    
    # Admins Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        role TEXT CHECK(role IN ('super_admin', 'admin', 'instructor', 'staff')) DEFAULT 'admin',
        branch TEXT CHECK(branch IN ('Luanshya', 'Mufulira', 'Both')) DEFAULT 'Luanshya',
        specialization TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Branches Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        code TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        manager_id INTEGER,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (manager_id) REFERENCES admins(id) ON DELETE SET NULL
    )
    ''')
    
    # Courses Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        category TEXT CHECK(category IN ('Motorcycle', 'Light Vehicle', 'Heavy Vehicle', 'PSV', 'Special')) NOT NULL,
        duration_weeks INTEGER NOT NULL,
        total_hours INTEGER NOT NULL,
        theory_hours INTEGER DEFAULT 0,
        practical_hours INTEGER DEFAULT 0,
        fee DECIMAL(10, 2) NOT NULL,
        requirements TEXT,
        branch_id INTEGER,
        instructor_id INTEGER,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL,
        FOREIGN KEY (instructor_id) REFERENCES admins(id) ON DELETE SET NULL
    )
    ''')
    
    # Applications Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Application Details
        application_number TEXT UNIQUE NOT NULL,
        application_date DATE NOT NULL,
        status TEXT CHECK(status IN ('pending', 'reviewing', 'accepted', 'rejected', 'cancelled')) DEFAULT 'pending',
        
        -- Personal Information
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        whatsapp TEXT,
        date_of_birth DATE NOT NULL,
        gender TEXT CHECK(gender IN ('male', 'female', 'other')) NOT NULL,
        nrc_number TEXT UNIQUE,
        
        -- Address Information
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        province TEXT NOT NULL,
        
        -- Course Selection
        course_id INTEGER NOT NULL,
        preferred_schedule TEXT,
        preferred_language TEXT DEFAULT 'English',
        
        -- Background Information
        education_level TEXT,
        previous_experience TEXT,
        medical_conditions TEXT,
        
        -- Emergency Contact
        emergency_name TEXT NOT NULL,
        emergency_phone TEXT NOT NULL,
        emergency_relation TEXT,
        
        -- Administrative
        branch_id INTEGER NOT NULL,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        admin_notes TEXT,
        
        -- Documents
        profile_photo TEXT,
        nrc_copy TEXT,
        medical_certificate TEXT,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Keys
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
        FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE RESTRICT,
        FOREIGN KEY (reviewed_by) REFERENCES admins(id) ON DELETE SET NULL
    )
    ''')
    
    # Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Student Information
        student_number TEXT UNIQUE NOT NULL,
        application_id INTEGER UNIQUE NOT NULL,
        
        -- Enrollment Details
        enrollment_date DATE NOT NULL,
        course_start_date DATE NOT NULL,
        course_end_date DATE,
        
        -- Academic Status
        status TEXT CHECK(status IN ('active', 'completed', 'suspended', 'withdrawn', 'on_leave')) DEFAULT 'active',
        progress_percentage INTEGER DEFAULT 0,
        last_assessment_score INTEGER,
        
        -- Financial Information
        total_fee DECIMAL(10, 2) NOT NULL,
        amount_paid DECIMAL(10, 2) DEFAULT 0,
        payment_status TEXT CHECK(payment_status IN ('pending', 'partial', 'paid', 'overdue')) DEFAULT 'pending',
        
        -- Relationships
        course_id INTEGER NOT NULL,
        branch_id INTEGER NOT NULL,
        assigned_instructor INTEGER,
        
        -- Administrative
        created_by INTEGER,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Keys
        FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
        FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE RESTRICT,
        FOREIGN KEY (assigned_instructor) REFERENCES admins(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
    )
    ''')
    
    # ============== ACADEMIC TABLES ==============
    
    # Lessons/Sessions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Lesson Details
        lesson_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        lesson_type TEXT CHECK(lesson_type IN ('theory', 'practical', 'assessment', 'simulation')) NOT NULL,
        
        -- Scheduling
        course_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        instructor_id INTEGER NOT NULL,
        scheduled_date DATE NOT NULL,
        scheduled_time TIME NOT NULL,
        duration_minutes INTEGER DEFAULT 60,
        
        -- Status
        status TEXT CHECK(status IN ('scheduled', 'completed', 'cancelled', 'rescheduled', 'no_show')) DEFAULT 'scheduled',
        completion_date DATE,
        completion_time TIME,
        
        -- Assessment
        attendance_status TEXT CHECK(attendance_status IN ('present', 'absent', 'late', 'excused')),
        score INTEGER CHECK(score >= 0 AND score <= 100),
        feedback TEXT,
        
        -- Resources
        materials TEXT,
        location TEXT,
        vehicle_used TEXT,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Keys
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (instructor_id) REFERENCES admins(id) ON DELETE RESTRICT,
        
        -- Constraints
        UNIQUE(student_id, scheduled_date, scheduled_time)
    )
    ''')
    
    # ============== FINANCIAL TABLES ==============
    
    # Payments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Payment Details
        payment_number TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        
        -- Payment Method
        payment_method TEXT CHECK(payment_method IN ('cash', 'mobile_money', 'bank_transfer', 'card', 'check')) NOT NULL,
        payment_method_details TEXT,
        reference_number TEXT,
        
        -- Payment Status
        status TEXT CHECK(status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled')) DEFAULT 'pending',
        
        -- Dates
        payment_date DATE NOT NULL,
        received_date DATE,
        
        -- Administrative
        received_by INTEGER NOT NULL,
        verified_by INTEGER,
        notes TEXT,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Keys
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (received_by) REFERENCES admins(id) ON DELETE RESTRICT,
        FOREIGN KEY (verified_by) REFERENCES admins(id) ON DELETE SET NULL
    )
    ''')
    
    # Payment Installments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_installments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_plan_id INTEGER NOT NULL,
        installment_number INTEGER NOT NULL,
        due_date DATE NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        status TEXT CHECK(status IN ('pending', 'paid', 'overdue', 'cancelled')) DEFAULT 'pending',
        payment_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (payment_plan_id) REFERENCES payment_plans(id) ON DELETE CASCADE,
        FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL
    )
    ''')
    
    # ============== COMMUNICATION TABLES ==============
    
    # Contact Messages Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Sender Information
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        
        -- Message Details
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        
        -- Status
        status TEXT CHECK(status IN ('new', 'read', 'replied', 'archived')) DEFAULT 'new',
        
        -- Response
        responded_by INTEGER,
        response TEXT,
        response_date TIMESTAMP,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Keys
        FOREIGN KEY (responded_by) REFERENCES admins(id) ON DELETE SET NULL
    )
    ''')
    
    # Notifications Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Recipient
        user_id INTEGER NOT NULL,
        user_type TEXT CHECK(user_type IN ('admin', 'student', 'instructor')) NOT NULL,
        
        -- Notification Details
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT CHECK(notification_type IN ('application', 'payment', 'lesson', 'system', 'alert')) NOT NULL,
        
        -- Status
        is_read BOOLEAN DEFAULT 0,
        
        -- Metadata
        related_id INTEGER,
        related_type TEXT,
        
        -- Action
        action_url TEXT,
        action_text TEXT,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        read_at TIMESTAMP,
        
        -- Foreign Keys
        FOREIGN KEY (user_id) REFERENCES admins(id) ON DELETE CASCADE
    )
    ''')
    

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_portal_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        access_code VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        login_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    ''')





    # ============== SYSTEM TABLES ==============
    
    # System Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT CHECK(setting_type IN ('string', 'integer', 'boolean', 'json')) DEFAULT 'string',
        category TEXT DEFAULT 'general',
        description TEXT,
        is_public BOOLEAN DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Audit Log Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Actor Information
        user_id INTEGER,
        user_type TEXT CHECK(user_type IN ('admin', 'student', 'system')) NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        
        -- Action Details
        action TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id INTEGER,
        
        -- Changes
        old_values TEXT,
        new_values TEXT,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ============== INSERT DEFAULT DATA ==============
    
    # Insert Default Super Admin
    hashed_password = generate_password_hash('admin123')
    cursor.execute('''
    INSERT OR IGNORE INTO admins (username, name, email, password, role, branch) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'superadmin',
        'System Administrator',
        'admin@keemdrivingschool.com',
        hashed_password,
        'super_admin',
        'Both'
    ))
    
    # Insert Branches
    branches = [
        ('Luanshya Branch', 'LUAN-001', 'Plot 123, Main Street, Luanshya', 'Luanshya', '+260 123 456 789', 'luanshya@keemdrivingschool.com', 1),
        ('Mufulira Branch', 'MUFU-001', 'Plot 456, Independence Avenue, Mufulira', 'Mufulira', '+260 987 654 321', 'mufulira@keemdrivingschool.com', 1)
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO branches (name, code, address, city, phone, email, manager_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', branches)
    
    # Insert Courses with proper relationships
    courses = [
        ('Class A - Motorcycle License', 'CLASS-A', 'Complete motorcycle driving course including theory and practical training', 
         'Motorcycle', 4, 40, 10, 30, 1500.00, 'Minimum age: 16 years\nValid NRC\nMedical Certificate', 1, 1),
        ('Class B - Light Vehicle License', 'CLASS-B', 'Comprehensive car driving course for light vehicles', 
         'Light Vehicle', 6, 60, 20, 40, 2500.00, 'Minimum age: 18 years\nValid NRC\nMedical Certificate', 1, 1),
        ('Class C - Heavy Vehicle License', 'CLASS-C', 'Heavy vehicle and truck driving course', 
         'Heavy Vehicle', 8, 80, 25, 55, 3500.00, 'Minimum age: 21 years\nValid NRC\nMedical Certificate\nClass B License', 2, 1),
        ('Class D - PSV License', 'CLASS-D', 'Public Service Vehicle driving course', 
         'PSV', 6, 65, 20, 45, 3000.00, 'Minimum age: 21 years\nValid NRC\nMedical Certificate\nClass B License', 2, 1),
        ('Refresher Course', 'REFRESH', 'Refresher course for experienced drivers', 
         'Special', 2, 20, 5, 15, 800.00, 'Valid Driver\'s License', 1, 1),
        ('Defensive Driving', 'DEFENSIVE', 'Advanced defensive driving techniques', 
         'Special', 3, 30, 10, 20, 1200.00, 'Valid Driver\'s License', 1, 1)
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO courses 
    (name, code, description, category, duration_weeks, total_hours, theory_hours, practical_hours, fee, requirements, branch_id, instructor_id, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(name, code, desc, cat, dur, th, theory, practical, fee, req, branch, instr, 1) 
          for name, code, desc, cat, dur, th, theory, practical, fee, req, branch, instr in courses])
    
    # Insert System Settings
    settings = [
        ('school_name', 'KEEM Driving School', 'string', 'general', 'School name'),
        ('school_email', 'info@keemdrivingschool.com', 'string', 'general', 'Primary school email'),
        ('school_phone', '+260 123 456 789', 'string', 'general', 'Primary contact number'),
        ('whatsapp_number', '+260 987 654 321', 'string', 'general', 'WhatsApp business number'),
        ('notification_email', 'notifications@keemdrivingschool.com', 'string', 'notifications', 'Email for notifications'),
        ('currency', 'ZMW', 'string', 'financial', 'Default currency'),
        ('tax_rate', '16', 'string', 'financial', 'Tax rate percentage'),
        ('application_fee', '50', 'string', 'financial', 'Non-refundable application fee'),
        ('max_students_per_class', '15', 'integer', 'academic', 'Maximum students per class'),
        ('lesson_duration', '60', 'integer', 'academic', 'Default lesson duration in minutes'),
        ('auto_accept_applications', 'false', 'boolean', 'applications', 'Automatically accept applications'),
        ('allow_online_payments', 'true', 'boolean', 'financial', 'Allow online payments'),
        ('maintenance_mode', 'false', 'boolean', 'system', 'Maintenance mode status')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO settings (setting_key, setting_value, setting_type, category, description)
    VALUES (?, ?, ?, ?, ?)
    ''', settings)
    
    conn.commit()
    
    # Create Indexes for Performance
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)',
        'CREATE INDEX IF NOT EXISTS idx_applications_course_id ON applications(course_id)',
        'CREATE INDEX IF NOT EXISTS idx_applications_branch_id ON applications(branch_id)',
        'CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at)',
        'CREATE INDEX IF NOT EXISTS idx_students_student_number ON students(student_number)',
        'CREATE INDEX IF NOT EXISTS idx_students_course_id ON students(course_id)',
        'CREATE INDEX IF NOT EXISTS idx_students_status ON students(status)',
        'CREATE INDEX IF NOT EXISTS idx_payments_student_id ON payments(student_id)',
        'CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)',
        'CREATE INDEX IF NOT EXISTS idx_lessons_student_id ON lessons(student_id)',
        'CREATE INDEX IF NOT EXISTS idx_lessons_instructor_id ON lessons(instructor_id)',
        'CREATE INDEX IF NOT EXISTS idx_lessons_status ON lessons(status)',
        'CREATE INDEX IF NOT EXISTS idx_contact_messages_status ON contact_messages(status)',
        'CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)',

        'CREATE INDEX IF NOT EXISTS idx_student_access_code ON student_portal_access(access_code)',
        'CREATE INDEX IF NOT EXISTS idx_student_access_email ON student_portal_access(email)',
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()
    
    print("✅ Database created successfully!")
    print("📊 Tables created: admins, branches, courses, applications, students, lessons, payments, contact_messages, notifications, settings, audit_logs")
    print("👤 Default admin: admin@keemdrivingschool.com / admin123")
    print("🏢 Branches: Luanshya, Mufulira")
    print("📚 Courses: 6 sample courses")

def seed_sample_data():
    """Seed database with sample data for testing"""
    conn = sqlite3.connect('keem_driving.db')
    cursor = conn.cursor()
    
    # Insert sample applications
    sample_applications = [
        ('APP-2024-0001', '2024-01-15', 'accepted', 'John', 'Doe', 'john@example.com', '+260 111 222 333', 
         '+260 111 222 333', '1995-05-15', 'male', '123456/78/9', '123 Main St', 'Luanshya', 'Copperbelt',
         1, 'Weekday mornings', 'English', 'High School', 'Some driving experience', 'None',
         'Jane Doe', '+260 444 555 666', 'Sister', 1, 1),
        
        ('APP-2024-0002', '2024-01-16', 'pending', 'Mary', 'Smith', 'mary@example.com', '+260 222 333 444',
         '+260 222 333 444', '1998-08-22', 'female', '987654/32/1', '456 Park Ave', 'Mufulira', 'Copperbelt',
         2, 'Weekend afternoons', 'English', 'College', 'No experience', 'None',
         'Bob Smith', '+260 555 666 777', 'Father', 2, 1)
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO applications 
    (application_number, application_date, status, first_name, last_name, email, phone, whatsapp, 
     date_of_birth, gender, nrc_number, address, city, province, course_id, preferred_schedule, 
     preferred_language, education_level, previous_experience, medical_conditions, emergency_name, 
     emergency_phone, emergency_relation, branch_id, reviewed_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_applications)
    
    # Get the inserted application IDs
    cursor.execute('SELECT id, application_number FROM applications WHERE application_number IN ("APP-2024-0001", "APP-2024-0002")')
    apps = cursor.fetchall()
    
    # Insert sample students for accepted applications
    if apps:
        for app_id, app_number in apps:
            if '0001' in app_number:  # Only create student for accepted application
                student_number = f"STU-{datetime.now().strftime('%Y%m')}{app_id:04d}"
                cursor.execute('''
                INSERT OR IGNORE INTO students 
                (student_number, application_id, enrollment_date, course_start_date, course_end_date,
                 status, total_fee, amount_paid, payment_status, course_id, branch_id, assigned_instructor, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student_number, app_id, '2024-01-20', '2024-02-01', '2024-03-01',
                    'active', 2500.00, 500.00, 'partial', 1, 1, 1, 1
                ))
    
    conn.commit()
    conn.close()
    print("✅ Sample data seeded successfully!")

if __name__ == '__main__':
    create_database()
    seed_sample_data()