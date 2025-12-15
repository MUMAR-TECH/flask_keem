"""
KEEM Driving School - Complete Flask Application with SQLAlchemy ORM
"""
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import os
import json
import random
import string
from sqlalchemy.orm import joinedload
from sqlalchemy import event, and_, or_
from sqlalchemy.exc import IntegrityError
import logging

# Import utility modules
from utils.email_sender import send_email, send_acceptance_email, send_bulk_email
from utils.pdf_generator import generate_application_pdf, generate_acceptance_letter, generate_invoice_pdf
from utils.excel_exporter import export_applications_to_excel, export_students_to_excel, export_payments_to_excel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'keem-driving-school-secret-key-2024-advanced'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keem_driving.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # Set to True for SQL debugging

# Upload Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# Ensure necessary directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('exports/excel', exist_ok=True)
os.makedirs('exports/pdf', exist_ok=True)
os.makedirs('static/documents', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============== DATABASE MODELS ==============

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='admin')
    branch = db.Column(db.String(20), default='Luanshya')
    specialization = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    managed_branch = db.relationship('Branch', backref='manager', foreign_keys='Branch.manager_id', uselist=False)
    reviewed_applications = db.relationship('Application', backref='reviewer', foreign_keys='Application.reviewed_by')
    created_students = db.relationship('Student', backref='creator', foreign_keys='Student.created_by')
    assigned_lessons = db.relationship('Lesson', backref='instructor', foreign_keys='Lesson.instructor_id')
    received_payments = db.relationship('Payment', backref='receiver', foreign_keys='Payment.received_by')
    verified_payments = db.relationship('Payment', backref='verifier', foreign_keys='Payment.verified_by')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    @property
    def is_instructor(self):
        return self.role == 'instructor'
    
    def can_access_branch(self, branch_id):
        if self.role == 'super_admin' or self.branch == 'Both':
            return True
        # Check if branch matches user's branch
        branch = Branch.query.get(branch_id)
        return branch and branch.name == self.branch

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    manager_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='branch_ref', foreign_keys='Application.branch_id')
    students = db.relationship('Student', backref='student_branch', foreign_keys='Student.branch_id')
    courses = db.relationship('Course', backref='course_branch', foreign_keys='Course.branch_id')

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    duration_weeks = db.Column(db.Integer, nullable=False)
    total_hours = db.Column(db.Integer, nullable=False)
    theory_hours = db.Column(db.Integer, default=0)
    practical_hours = db.Column(db.Integer, default=0)
    fee = db.Column(db.Numeric(10, 2), nullable=False)
    requirements = db.Column(db.Text)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = db.relationship('Branch', backref='branch_courses', foreign_keys=[branch_id])
    instructor = db.relationship('Admin', backref='instructor_courses', foreign_keys=[instructor_id])
    applications = db.relationship('Application', backref='course_applications', foreign_keys='Application.course_id')
    students = db.relationship('Student', backref='student_course', foreign_keys='Student.course_id')
    lessons = db.relationship('Lesson', backref='course_lessons', foreign_keys='Lesson.course_id')

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Application Details
    application_number = db.Column(db.String(50), unique=True, nullable=False)
    application_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), default='pending')
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    whatsapp = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    nrc_number = db.Column(db.String(50), unique=True)
    
    # Address Information
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    province = db.Column(db.String(50), nullable=False)
    
    # Course Selection
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    preferred_schedule = db.Column(db.String(50))
    preferred_language = db.Column(db.String(50), default='English')
    
    # Background Information
    education_level = db.Column(db.String(50))
    previous_experience = db.Column(db.Text)
    medical_conditions = db.Column(db.Text)
    
    # Emergency Contact
    emergency_name = db.Column(db.String(100), nullable=False)
    emergency_phone = db.Column(db.String(20), nullable=False)
    emergency_relation = db.Column(db.String(50))
    
    # Administrative
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    reviewed_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    
    # Documents
    profile_photo = db.Column(db.String(200))
    nrc_copy = db.Column(db.String(200))
    medical_certificate = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='applications', foreign_keys=[course_id])
    branch = db.relationship('Branch', backref='applications', foreign_keys=[branch_id])
    reviewer_rel = db.relationship('Admin', backref='reviewed_apps', foreign_keys=[reviewed_by])
    student = db.relationship('Student', backref='application', uselist=False, foreign_keys='Student.application_id')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.utcnow().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Student Information
    student_number = db.Column(db.String(50), unique=True, nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), unique=True, nullable=False)
    
    # Enrollment Details
    enrollment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    course_start_date = db.Column(db.Date, nullable=False)
    course_end_date = db.Column(db.Date)
    
    # Academic Status
    status = db.Column(db.String(20), default='active')
    progress_percentage = db.Column(db.Integer, default=0)
    last_assessment_score = db.Column(db.Integer)
    
    # Financial Information
    total_fee = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0)
    payment_status = db.Column(db.String(20), default='pending')
    
    # Relationships
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    assigned_instructor = db.Column(db.Integer, db.ForeignKey('admins.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='students', foreign_keys=[course_id])
    branch = db.relationship('Branch', backref='students', foreign_keys=[branch_id])
    instructor = db.relationship('Admin', backref='assigned_students', foreign_keys=[assigned_instructor])
    creator_rel = db.relationship('Admin', backref='created_students_rel', foreign_keys=[created_by])
    payments = db.relationship('Payment', backref='student_payments', foreign_keys='Payment.student_id')
    lessons = db.relationship('Lesson', backref='student_lessons', foreign_keys='Lesson.student_id')
    
    @property
    def balance(self):
        return float(self.total_fee) - float(self.amount_paid)
    
    @property
    def full_name(self):
        if self.application:
            return self.application.full_name
        return "Unknown"
    
    @property
    def email(self):
        if self.application:
            return self.application.email
        return None
    
    @property
    def phone(self):
        if self.application:
            return self.application.phone
        return None

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Lesson Details
    lesson_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    lesson_type = db.Column(db.String(20), nullable=False)
    
    # Scheduling
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    # Status
    status = db.Column(db.String(20), default='scheduled')
    completion_date = db.Column(db.Date)
    completion_time = db.Column(db.Time)
    
    # Assessment
    attendance_status = db.Column(db.String(20))
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    
    # Resources
    materials = db.Column(db.Text)
    location = db.Column(db.String(200))
    vehicle_used = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='lessons', foreign_keys=[course_id])
    student = db.relationship('Student', backref='lessons', foreign_keys=[student_id])
    instructor_rel = db.relationship('Admin', backref='lessons_given', foreign_keys=[instructor_id])
    
    @property
    def scheduled_datetime(self):
        return datetime.combine(self.scheduled_date, self.scheduled_time)
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_upcoming(self):
        return self.scheduled_date >= datetime.utcnow().date() and self.status == 'scheduled'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Payment Details
    payment_number = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Payment Method
    payment_method = db.Column(db.String(20), nullable=False)
    payment_method_details = db.Column(db.Text)
    reference_number = db.Column(db.String(100))
    
    # Payment Status
    status = db.Column(db.String(20), default='pending')
    
    # Dates
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    received_date = db.Column(db.Date)
    
    # Administrative
    received_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='student_payments_rel', foreign_keys=[student_id])
    receiver = db.relationship('Admin', backref='received_payments_rel', foreign_keys=[received_by])
    verifier = db.relationship('Admin', backref='verified_payments_rel', foreign_keys=[verified_by])
    
    @property
    def student_name(self):
        if self.student and self.student.application:
            return self.student.application.full_name
        return "Unknown"
    
    @property
    def student_number(self):
        if self.student:
            return self.student.student_number
        return "Unknown"

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Sender Information
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    
    # Message Details
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='new')
    
    # Response
    responded_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    response = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    responder = db.relationship('Admin', backref='responded_messages', foreign_keys=[responded_by])
    
    @property
    def is_responded(self):
        return self.status == 'replied' and self.response is not None

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Recipient
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    
    # Notification Details
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    
    # Metadata
    related_id = db.Column(db.Integer)
    related_type = db.Column(db.String(50))
    
    # Action
    action_url = db.Column(db.String(200))
    action_text = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(20), default='string')
    category = db.Column(db.String(50), default='general')
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def typed_value(self):
        if self.setting_type == 'integer':
            return int(self.setting_value) if self.setting_value else 0
        elif self.setting_type == 'boolean':
            return self.setting_value.lower() == 'true'
        elif self.setting_type == 'json':
            try:
                return json.loads(self.setting_value) if self.setting_value else {}
            except:
                return {}
        else:
            return self.setting_value

class StudentPortalAccess(db.Model):
    __tablename__ = 'student_portal_access'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    access_code = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    student = db.relationship('Student', backref='portal_access', foreign_keys=[student_id], uselist=False)
    
    def generate_new_access_code(self):
        """Generate and set new access code"""
        self.access_code = generate_access_code()
        db.session.commit()
        return self.access_code
    
    def record_login(self):
        """Record successful login"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()


# ============== FLASK-LOGIN CONFIGURATION ==============

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('admin_login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============== HELPER FUNCTIONS ==============

def generate_application_number():
    """Generate unique application number"""
    today = datetime.utcnow()
    year = today.year
    month = today.month
    
    # Count applications for this month
    count = Application.query.filter(
        db.extract('year', Application.created_at) == year,
        db.extract('month', Application.created_at) == month
    ).count()
    
    return f"APP-{year}-{month:02d}-{count + 1:04d}"

def generate_student_number(application_id):
    """Generate unique student number"""
    today = datetime.utcnow()
    return f"STU-{today.strftime('%Y%m')}{application_id:04d}"

def generate_payment_number(student_id):
    """Generate unique payment number"""
    today = datetime.utcnow()
    count = Payment.query.filter(
        db.extract('year', Payment.created_at) == today.year,
        db.extract('month', Payment.created_at) == today.month
    ).count()
    return f"PAY-{today.strftime('%Y%m')}{student_id:03d}-{count + 1:03d}"

def save_uploaded_file(file, folder='documents'):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        return filename
    return None


def create_notification(user_id, user_type, title, message, notification_type='system', related_id=None, related_type=None, action_url=None):
    """Create a notification"""
    notification = Notification(
        user_id=user_id,
        user_type=user_type,
        title=title,
        message=message,
        notification_type=notification_type,
        related_id=related_id,
        related_type=related_type,
        action_url=action_url
    )
    db.session.add(notification)
    db.session.commit()
    return notification




def generate_access_code():
    """Generate a unique 8-character access code"""
    while True:
        # Generate a code like: ABC123XY
        letters = ''.join(random.choices(string.ascii_uppercase, k=4))
        numbers = ''.join(random.choices(string.digits, k=3))
        letters2 = ''.join(random.choices(string.ascii_uppercase, k=1))
        access_code = f"{letters}{numbers}{letters2}"
        
        # Check if code exists
        exists = db.session.query(StudentPortalAccess.query.filter_by(access_code=access_code).exists()).scalar()
        if not exists:
            return access_code





def generate_student_id_number():
    """Generate student ID in format: YYYYMMDDD"""
    today = datetime.utcnow()
    
    # Get the last student number for today
    last_student = Student.query.filter(
        Student.student_number.like(f'{today.strftime("%Y%m")}%')
    ).order_by(Student.id.desc()).first()
    
    if last_student:
        try:
            # Extract the sequential number
            last_number = int(last_student.student_number[-3:])
            next_number = last_number + 1
        except:
            next_number = 1
    else:
        next_number = 1
    
    # Format: YYYYMM + 3-digit sequential number
    student_number = f"{today.strftime('%Y%m')}{next_number:03d}"
    
    return student_number

# ============== PUBLIC ROUTES ==============

@app.route('/')
def index():
    """Homepage"""
    courses = Course.query.filter_by(is_active=True).limit(6).all()
    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('index.html', courses=courses, branches=branches)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/courses')
def courses_page():
    """Courses page"""
    courses = Course.query.filter_by(is_active=True).all()
    categories = db.session.query(Course.category).distinct().all()
    return render_template('courses.html', courses=courses, categories=[c[0] for c in categories])

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    """Course detail page"""
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', course=course)

@app.route('/branches')
def branches_page():
    """Branches page"""
    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('branches.html', branches=branches)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            # Save to database
            contact_msg = ContactMessage(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            db.session.add(contact_msg)
            db.session.commit()
            
            # Send notification to admin
            admin_email = "admin@keemdrivingschool.com"
            email_subject = f"New Contact Message: {subject}"
            email_body = f"""
            New contact message received from website:
            
            Name: {name}
            Email: {email}
            Phone: {phone}
            Subject: {subject}
            
            Message:
            {message}
            
            Message ID: {contact_msg.id}
            Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
            """
            
            send_email(admin_email, email_subject, email_body)
            
            # Send confirmation to user
            user_message = f"""
            Dear {name},
            
            Thank you for contacting KEEM Driving School!
            
            We have received your message and will respond within 24 hours.
            
            Your message:
            {message}
            
            Best regards,
            KEEM Driving School Team
            """
            send_email(email, "Message Received - KEEM Driving School", user_message)
            
            return jsonify({
                'success': True,
                'message': 'Message sent successfully! We will contact you soon.'
            })
            
        except Exception as e:
            logger.error(f"Contact form error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred. Please try again.'
            }), 500
    
    return render_template('contact.html')

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    """Application form page"""
    if request.method == 'GET':
        courses = Course.query.filter_by(is_active=True).all()
        branches = Branch.query.filter_by(is_active=True).all()
        return render_template('apply.html', courses=courses, branches=branches)
    
    # POST request - handle application submission
    try:
        data = request.form
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 
                          'gender', 'nrc_number', 'address', 'city', 'province', 
                          'course_id', 'branch_id', 'emergency_name', 'emergency_phone']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Please fill in the {field.replace("_", " ")} field.'
                }), 400
        
        # Generate application number
        application_number = generate_application_number()
        
        # Create application
        application = Application(
            application_number=application_number,
            application_date=datetime.utcnow().date(),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            whatsapp=data.get('whatsapp', data.get('phone')),
            date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date(),
            gender=data.get('gender'),
            nrc_number=data.get('nrc_number'),
            address=data.get('address'),
            city=data.get('city'),
            province=data.get('province'),
            course_id=int(data.get('course_id')),
            preferred_schedule=data.get('preferred_schedule'),
            preferred_language=data.get('preferred_language', 'English'),
            education_level=data.get('education_level'),
            previous_experience=data.get('previous_experience'),
            medical_conditions=data.get('medical_conditions'),
            emergency_name=data.get('emergency_name'),
            emergency_phone=data.get('emergency_phone'),
            emergency_relation=data.get('emergency_relation'),
            branch_id=int(data.get('branch_id'))
        )
        
        # Handle file uploads
        if 'profile_photo' in request.files:
            profile_photo = save_uploaded_file(request.files['profile_photo'], 'profile_photos')
            if profile_photo:
                application.profile_photo = profile_photo
        
        if 'nrc_copy' in request.files:
            nrc_copy = save_uploaded_file(request.files['nrc_copy'], 'documents')
            if nrc_copy:
                application.nrc_copy = nrc_copy
        
        if 'medical_certificate' in request.files:
            medical_cert = save_uploaded_file(request.files['medical_certificate'], 'documents')
            if medical_cert:
                application.medical_certificate = medical_cert
        
        db.session.add(application)
        db.session.commit()
        
        # Send notifications
        admin_email = "admin@keemdrivingschool.com"
        email_subject = f"New Application Received: {application_number}"
        email_body = f"""
        New application received!
        
        Application Number: {application_number}
        Name: {application.full_name}
        Email: {application.email}
        Phone: {application.phone}
        Course: {application.course.name}
        Branch: {application.branch.name}
        
        Please login to the admin dashboard to review this application.
        """
        
        send_email(admin_email, email_subject, email_body)
        
        # Send confirmation to applicant
        applicant_message = f"""
        Dear {application.first_name},
        
        Thank you for applying to KEEM Driving School!
        
        Your application has been received successfully.
        
        Application Details:
        - Application Number: {application_number}
        - Course: {application.course.name}
        - Branch: {application.branch.name}
        
        We will review your application and get back to you within 2-3 business days.
        
        You can check your application status at any time using this link:
        {url_for('check_application_status', application_number=application_number, _external=True)}
        
        Best regards,
        KEEM Driving School Team
        """
        
        send_email(application.email, "Application Received - KEEM Driving School", applicant_message)
        
        # Create notification for admin
        create_notification(
            user_id=1,  # Super admin
            user_type='admin',
            title='New Application Received',
            message=f'New application from {application.full_name} for {application.course.name}',
            notification_type='application',
            related_id=application.id,
            related_type='application',
            action_url=url_for('view_application', application_id=application.id)
        )
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully! Check your email for confirmation.',
            'application_number': application_number,
            'application_id': application.id
        })
        
    except Exception as e:
        logger.error(f"Application submission error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/application-status/<string:application_number>')
def check_application_status(application_number):
    """Check application status"""
    application = Application.query.filter_by(application_number=application_number).first_or_404()
    return render_template('application_status.html', application=application)

# ============== ADMIN ROUTES ==============

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        admin = Admin.query.filter_by(email=email, is_active=True).first()
        
        if admin and admin.check_password(password):
            login_user(admin, remember=remember)
            admin.update_last_login()
            flash('Login successful!', 'success')
            
            # Log the login
            logger.info(f"Admin logged in: {admin.email}")
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    
    # Get statistics based on user role
    if current_user.is_super_admin or current_user.branch == 'Both':
        # Show all data
        total_applications = Application.query.count()
        pending_applications = Application.query.filter_by(status='pending').count()
        accepted_applications = Application.query.filter_by(status='accepted').count()
        total_students = Student.query.count()
        active_students = Student.query.filter_by(status='active').count()
        total_payments = Payment.query.count()
        recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    else:
        # Show only data for user's branch
        total_applications = Application.query.filter_by(branch_id=current_user.branch_id).count()
        pending_applications = Application.query.filter_by(branch_id=current_user.branch_id, status='pending').count()
        accepted_applications = Application.query.filter_by(branch_id=current_user.branch_id, status='accepted').count()
        total_students = Student.query.filter_by(branch_id=current_user.branch_id).count()
        active_students = Student.query.filter_by(branch_id=current_user.branch_id, status='active').count()
        total_payments = Payment.query.join(Student).filter(Student.branch_id == current_user.branch_id).count()
        recent_payments = Payment.query.join(Student).filter(Student.branch_id == current_user.branch_id)\
            .order_by(Payment.created_at.desc()).limit(5).all()
    
    # Get recent applications
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(10).all()
    
    # Get upcoming lessons for instructors
    if current_user.is_instructor:
        upcoming_lessons = Lesson.query.filter_by(
            instructor_id=current_user.id,
            status='scheduled'
        ).filter(Lesson.scheduled_date >= datetime.utcnow().date())\
         .order_by(Lesson.scheduled_date, Lesson.scheduled_time)\
         .limit(5).all()
    else:
        upcoming_lessons = []
    
    # Get notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        user_type='admin',
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    stats = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'total_students': total_students,
        'active_students': active_students,
        'total_payments': total_payments
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_applications=recent_applications,
                         recent_payments=recent_payments,
                         upcoming_lessons=upcoming_lessons,
                         notifications=notifications)

@app.route('/admin/applications')
@admin_required
def admin_applications():
    """View all applications"""
    status = request.args.get('status', 'all')
    branch_id = request.args.get('branch_id', 'all')
    course_id = request.args.get('course_id', 'all')
    
    query = Application.query.options(
        joinedload(Application.course),
        joinedload(Application.branch),
        joinedload(Application.reviewer_rel)
    )
    
    # Apply filters based on user role
    if not current_user.is_super_admin and current_user.branch != 'Both':
        query = query.filter_by(branch_id=current_user.branch_id)
    elif branch_id != 'all':
        query = query.filter_by(branch_id=int(branch_id))
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if course_id != 'all':
        query = query.filter_by(course_id=int(course_id))
    
    # Apply date filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if date_from:
        query = query.filter(Application.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Application.created_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
    
    applications = query.order_by(Application.created_at.desc()).all()
    
    # Get filter options
    branches = Branch.query.filter_by(is_active=True).all()
    courses = Course.query.filter_by(is_active=True).all()
    
    return render_template('admin/applications.html',
                         applications=applications,
                         status=status,
                         branch_id=branch_id,
                         course_id=course_id,
                         branches=branches,
                         courses=courses)

@app.route('/admin/application/<int:application_id>')
@admin_required
def view_application(application_id):
    """View single application details"""
    application = Application.query.options(
        joinedload(Application.course),
        joinedload(Application.branch),
        joinedload(Application.reviewer_rel)
    ).get_or_404(application_id)
    
    # Check permission
    if not current_user.can_access_branch(application.branch_id):
        flash('You do not have permission to view this application.', 'error')
        return redirect(url_for('admin_applications'))
    
    return render_template('admin/view_application.html', application=application)

@app.route('/admin/application/<int:application_id>/update', methods=['POST'])
@admin_required
def update_application():
    """Update application status and details"""
    application = Application.query.get_or_404(request.view_args.get('application_id'))
    
    # Check permission
    if not current_user.can_access_branch(application.branch_id):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        action = request.form.get('action')
        notes = request.form.get('notes', '')
        
        if action == 'accept':
            application.status = 'accepted'
            application.reviewed_by = current_user.id
            application.reviewed_at = datetime.utcnow()
            application.admin_notes = notes
            
            # Create student record
            student_number = generate_student_number(application.id)
            course = Course.query.get(application.course_id)
            
            student = Student(
                student_number=student_number,
                application_id=application.id,
                enrollment_date=datetime.utcnow().date(),
                course_start_date=datetime.utcnow().date() + timedelta(days=7),  # Start in 1 week
                course_end_date=datetime.utcnow().date() + timedelta(weeks=course.duration_weeks),
                course_id=application.course_id,
                branch_id=application.branch_id,
                total_fee=course.fee,
                assigned_instructor=course.instructor_id,
                created_by=current_user.id
            )
            
            db.session.add(student)
            
            # Send acceptance email
            pdf_path = generate_acceptance_letter(application)
            application_data = {
                'id': application.id,
                'first_name': application.first_name,
                'last_name': application.last_name,
                'course_type': application.course.name,
                'branch': application.branch.name
            }
            send_acceptance_email(application.email, 
                                "Congratulations! Your Application Has Been Accepted", 
                                application_data, pdf_path)
            
            flash('Application accepted and student record created.', 'success')
            
        elif action == 'reject':
            application.status = 'rejected'
            application.reviewed_by = current_user.id
            application.reviewed_at = datetime.utcnow()
            application.admin_notes = notes
            flash('Application rejected.', 'info')
            
        elif action == 'review':
            application.status = 'reviewing'
            application.reviewed_by = current_user.id
            application.reviewed_at = datetime.utcnow()
            application.admin_notes = notes
            flash('Application marked as reviewing.', 'info')
            
        elif action == 'cancel':
            application.status = 'cancelled'
            application.admin_notes = notes
            flash('Application cancelled.', 'warning')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Application updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating application: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/students')
@admin_required
def admin_students():
    """View all students"""
    status = request.args.get('status', 'all')
    branch_id = request.args.get('branch_id', 'all')
    course_id = request.args.get('course_id', 'all')
    
    query = Student.query.options(
        joinedload(Student.application),
        joinedload(Student.course),
        joinedload(Student.branch),
        joinedload(Student.instructor)
    )
    
    # Apply filters based on user role
    if not current_user.is_super_admin and current_user.branch != 'Both':
        query = query.filter_by(branch_id=current_user.branch_id)
    elif branch_id != 'all':
        query = query.filter_by(branch_id=int(branch_id))
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if course_id != 'all':
        query = query.filter_by(course_id=int(course_id))
    
    students = query.order_by(Student.enrollment_date.desc()).all()
    
    # Get filter options
    branches = Branch.query.filter_by(is_active=True).all()
    courses = Course.query.filter_by(is_active=True).all()
    
    return render_template('admin/students.html',
                         students=students,
                         status=status,
                         branch_id=branch_id,
                         course_id=course_id,
                         branches=branches,
                         courses=courses)

@app.route('/admin/student/<int:student_id>')
@admin_required
def view_student(student_id):
    """View single student details"""
    student = Student.query.options(
        joinedload(Student.application),
        joinedload(Student.course),
        joinedload(Student.branch),
        joinedload(Student.instructor),
        joinedload(Student.creator_rel)
    ).get_or_404(student_id)
    
    # Check permission
    if not current_user.can_access_branch(student.branch_id):
        flash('You do not have permission to view this student.', 'error')
        return redirect(url_for('admin_students'))
    
    # Get student's payments
    payments = Payment.query.filter_by(student_id=student_id).order_by(Payment.payment_date.desc()).all()
    
    # Get student's lessons
    lessons = Lesson.query.filter_by(student_id=student_id)\
        .order_by(Lesson.scheduled_date, Lesson.scheduled_time).all()
    
    return render_template('admin/view_student.html',
                         student=student,
                         payments=payments,
                         lessons=lessons)

@app.route('/admin/payments')
@admin_required
def admin_payments():
    """View all payments"""
    status = request.args.get('status', 'all')
    payment_method = request.args.get('payment_method', 'all')
    
    query = Payment.query.options(
        joinedload(Payment.student).joinedload(Student.application),
        joinedload(Payment.receiver),
        joinedload(Payment.verifier)
    )
    
    # Apply filters based on user role
    if not current_user.is_super_admin and current_user.branch != 'Both':
        query = query.join(Student).filter(Student.branch_id == current_user.branch_id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if payment_method != 'all':
        query = query.filter_by(payment_method=payment_method)
    
    # Apply date filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if date_from:
        query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    payments = query.order_by(Payment.payment_date.desc()).all()
    
    return render_template('admin/payments.html', payments=payments, status=status, payment_method=payment_method)

@app.route('/admin/add-payment', methods=['POST'])
@admin_required
@role_required(['super_admin', 'admin'])
def add_payment():
    """Add new payment"""
    try:
        data = request.form
        
        student_id = data.get('student_id')
        amount = float(data.get('amount'))
        payment_method = data.get('payment_method')
        payment_date = datetime.strptime(data.get('payment_date'), '%Y-%m-%d').date()
        notes = data.get('notes', '')
        
        student = Student.query.get_or_404(student_id)
        
        # Check permission
        if not current_user.can_access_branch(student.branch_id):
            return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        # Generate payment number
        payment_number = generate_payment_number(student_id)
        
        # Create payment
        payment = Payment(
            payment_number=payment_number,
            student_id=student_id,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            received_by=current_user.id,
            received_date=datetime.utcnow().date(),
            status='completed',
            notes=notes
        )
        
        # Update student's payment status
        student.amount_paid = student.amount_paid + amount
        
        if student.amount_paid >= student.total_fee:
            student.payment_status = 'paid'
        elif student.amount_paid > 0:
            student.payment_status = 'partial'
        
        db.session.add(payment)
        db.session.commit()
        
        # Generate invoice PDF
        pdf_path = generate_invoice_pdf(payment)
        
        # Send email notification
        if student.application:
            email_subject = f"Payment Received - {payment_number}"
            email_body = f"""
            Dear {student.application.first_name},
            
            We have received your payment of ZMW {amount:,.2f} for {student.course.name}.
            
            Payment Details:
            - Payment Number: {payment_number}
            - Amount: ZMW {amount:,.2f}
            - Method: {payment_method}
            - Date: {payment_date.strftime('%B %d, %Y')}
            
            Your current balance: ZMW {student.balance:,.2f}
            
            Thank you for your payment!
            
            Best regards,
            KEEM Driving School Team
            """
            
            send_email(student.application.email, email_subject, email_body, attachments=[pdf_path])
        
        flash('Payment added successfully and invoice sent.', 'success')
        return jsonify({'success': True, 'message': 'Payment added successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding payment: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============== EXPORT ROUTES ==============

@app.route('/admin/export/applications/excel')
@admin_required
def export_applications_excel():
    """Export applications to Excel"""
    applications = Application.query.options(
        joinedload(Application.course),
        joinedload(Application.branch)
    ).all()
    
    applications_data = []
    for app in applications:
        applications_data.append({
            'id': app.id,
            'application_number': app.application_number,
            'first_name': app.first_name,
            'last_name': app.last_name,
            'email': app.email,
            'phone': app.phone,
            'date_of_birth': app.date_of_birth,
            'gender': app.gender,
            'nrc_number': app.nrc_number,
            'address': app.address,
            'city': app.city,
            'province': app.province,
            'course': app.course.name if app.course else '',
            'branch': app.branch.name if app.branch else '',
            'status': app.status,
            'application_date': app.application_date,
            'created_at': app.created_at,
            'admin_notes': app.admin_notes
        })
    
    excel_path = export_applications_to_excel(applications_data)
    return send_file(excel_path, as_attachment=True)

@app.route('/admin/export/students/excel')
@admin_required
def export_students_excel():
    """Export students to Excel"""
    students = Student.query.options(
        joinedload(Student.application),
        joinedload(Student.course),
        joinedload(Student.branch)
    ).all()
    
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'student_number': student.student_number,
            'first_name': student.application.first_name if student.application else '',
            'last_name': student.application.last_name if student.application else '',
            'email': student.application.email if student.application else '',
            'phone': student.application.phone if student.application else '',
            'course': student.course.name if student.course else '',
            'branch': student.branch.name if student.branch else '',
            'enrollment_date': student.enrollment_date,
            'course_start_date': student.course_start_date,
            'course_end_date': student.course_end_date,
            'status': student.status,
            'payment_status': student.payment_status,
            'total_fee': float(student.total_fee) if student.total_fee else 0,
            'amount_paid': float(student.amount_paid) if student.amount_paid else 0,
            'balance': student.balance,
            'progress_percentage': student.progress_percentage
        })
    
    excel_path = export_students_to_excel(students_data)
    return send_file(excel_path, as_attachment=True)

@app.route('/admin/export/payments/excel')
@admin_required
def export_payments_excel():
    """Export payments to Excel"""
    payments = Payment.query.options(
        joinedload(Payment.student).joinedload(Student.application),
        joinedload(Payment.receiver)
    ).all()
    
    payments_data = []
    for payment in payments:
        payments_data.append({
            'id': payment.id,
            'payment_number': payment.payment_number,
            'student_number': payment.student.student_number if payment.student else '',
            'student_name': payment.student_name,
            'amount': float(payment.amount) if payment.amount else 0,
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date,
            'status': payment.status,
            'received_by': payment.receiver.name if payment.receiver else '',
            'notes': payment.notes
        })
    
    excel_path = export_payments_to_excel(payments_data)
    return send_file(excel_path, as_attachment=True)

@app.route('/admin/export/application/<int:application_id>/pdf')
@admin_required
def export_application_pdf(application_id):
    """Export single application as PDF"""
    application = Application.query.get_or_404(application_id)
    
    # Check permission
    if not current_user.can_access_branch(application.branch_id):
        flash('You do not have permission to export this application.', 'error')
        return redirect(url_for('admin_applications'))
    
    pdf_path = generate_application_pdf(application)
    return send_file(pdf_path, as_attachment=True, download_name=f"application_{application.application_number}.pdf")

@app.route('/admin/export/invoice/<int:payment_id>/pdf')
@admin_required
def export_invoice_pdf(payment_id):
    """Export invoice as PDF"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Check permission
    if payment.student and not current_user.can_access_branch(payment.student.branch_id):
        flash('You do not have permission to export this invoice.', 'error')
        return redirect(url_for('admin_payments'))
    
    pdf_path = generate_invoice_pdf(payment)
    return send_file(pdf_path, as_attachment=True, download_name=f"invoice_{payment.payment_number}.pdf")

# ============== API ENDPOINTS ==============

@app.route('/api/statistics')
@admin_required
def api_statistics():
    """Get dashboard statistics API"""
    
    # Date range for statistics
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    if current_user.is_super_admin or current_user.branch == 'Both':
        # All branches
        applications = Application.query.filter(Application.created_at.between(start_date, end_date)).all()
        students = Student.query.filter(Student.created_at.between(start_date, end_date)).all()
        payments = Payment.query.filter(Payment.created_at.between(start_date, end_date)).all()
    else:
        # User's branch only
        applications = Application.query.filter(
            Application.branch_id == current_user.branch_id,
            Application.created_at.between(start_date, end_date)
        ).all()
        
        students = Student.query.filter(
            Student.branch_id == current_user.branch_id,
            Student.created_at.between(start_date, end_date)
        ).all()
        
        payments = Payment.query.join(Student).filter(
            Student.branch_id == current_user.branch_id,
            Payment.created_at.between(start_date, end_date)
        ).all()
    
    # Calculate statistics
    stats = {
        'applications': {
            'total': len(applications),
            'pending': len([a for a in applications if a.status == 'pending']),
            'accepted': len([a for a in applications if a.status == 'accepted']),
            'rejected': len([a for a in applications if a.status == 'rejected'])
        },
        'students': {
            'total': len(students),
            'active': len([s for s in students if s.status == 'active']),
            'completed': len([s for s in students if s.status == 'completed'])
        },
        'payments': {
            'total': len(payments),
            'total_amount': sum(float(p.amount) for p in payments),
            'completed': len([p for p in payments if p.status == 'completed'])
        }
    }
    
    return jsonify(stats)

@app.route('/api/courses')
def api_courses():
    """Get courses API (public)"""
    branch_id = request.args.get('branch_id')
    
    query = Course.query.filter_by(is_active=True)
    
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    
    courses = query.all()
    
    courses_data = []
    for course in courses:
        courses_data.append({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'description': course.description,
            'category': course.category,
            'duration_weeks': course.duration_weeks,
            'total_hours': course.total_hours,
            'fee': float(course.fee) if course.fee else 0,
            'branch': course.branch.name if course.branch else '',
            'requirements': course.requirements
        })
    
    return jsonify(courses_data)

@app.route('/api/branches')
def api_branches():
    """Get branches API (public)"""
    branches = Branch.query.filter_by(is_active=True).all()
    
    branches_data = []
    for branch in branches:
        branches_data.append({
            'id': branch.id,
            'name': branch.name,
            'code': branch.code,
            'address': branch.address,
            'city': branch.city,
            'phone': branch.phone,
            'email': branch.email
        })
    
    return jsonify(branches_data)






@app.route('/student-portal', methods=['GET'])
def student_portal_home():
    """Student portal home page"""
    return render_template('student_portal/home.html')

@app.route('/student-portal/login', methods=['GET', 'POST'])
def student_portal_login():
    """Student portal login"""
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        access_code = request.form.get('access_code')
        
        # Try to find student by student number
        student = Student.query.filter_by(student_number=student_id).first()
        
        if not student:
            # Try to find by application email or phone
            application = Application.query.filter(
                (Application.email == student_id) | (Application.phone == student_id)
            ).first()
            
            if application and application.student:
                student = application.student
        
        if student:
            # Check portal access
            portal_access = StudentPortalAccess.query.filter_by(
                student_id=student.id,
                access_code=access_code,
                is_active=True
            ).first()
            
            if portal_access:
                # Login successful
                session['student_id'] = student.id
                session['student_number'] = student.student_number
                session['student_name'] = student.full_name
                session['access_code'] = access_code
                
                # Record login
                portal_access.record_login()
                
                flash(f'Welcome back, {student.full_name}!', 'success')
                return redirect(url_for('student_portal_dashboard'))
        
        flash('Invalid Student ID or Access Code', 'error')
    
    return render_template('student_portal/login.html')

@app.route('/student-portal/register', methods=['GET', 'POST'])
def student_portal_register():
    """Register for student portal access"""
    if request.method == 'POST':
        student_number = request.form.get('student_number')
        email = request.form.get('email')
        phone = request.form.get('phone')
        date_of_birth = request.form.get('date_of_birth')
        
        # Find student
        student = Student.query.filter_by(student_number=student_number).first()
        
        if not student:
            flash('Student not found. Please check your student number.', 'error')
            return render_template('student_portal/register.html')
        
        # Verify identity
        if student.application:
            if (student.application.email != email or 
                student.application.phone != phone):
                flash('Email or phone does not match our records.', 'error')
                return render_template('student_portal/register.html')
            
            # Verify date of birth
            if student.application.date_of_birth != datetime.strptime(date_of_birth, '%Y-%m-%d').date():
                flash('Date of birth does not match our records.', 'error')
                return render_template('student_portal/register.html')
        
        # Check if already registered
        existing_access = StudentPortalAccess.query.filter_by(student_id=student.id).first()
        
        if existing_access:
            if existing_access.is_active:
                flash('You already have portal access. Please login.', 'info')
                return redirect(url_for('student_portal_login'))
            else:
                # Reactivate
                existing_access.is_active = True
                existing_access.access_code = generate_access_code()
                db.session.commit()
                
                # Send email with new access code
                email_body = f"""
                Your student portal access has been reactivated!
                
                Student Number: {student.student_number}
                Access Code: {existing_access.access_code}
                
                You can now login at: {url_for('student_portal_login', _external=True)}
                
                Best regards,
                KEEM Driving School
                """
                
                send_email(email, 'Student Portal Access Reactivated', email_body)
                
                flash('Portal access reactivated! Check your email for your access code.', 'success')
                return redirect(url_for('student_portal_login'))
        
        # Create new portal access
        access_code = generate_access_code()
        
        portal_access = StudentPortalAccess(
            student_id=student.id,
            access_code=access_code,
            email=email,
            phone=phone
        )
        
        try:
            db.session.add(portal_access)
            db.session.commit()
            
            # Send welcome email with access code
            email_body = f"""
            Welcome to KEEM Driving School Student Portal!
            
            Your portal access has been created successfully.
            
            Login Details:
            Student Number: {student.student_number}
            Access Code: {access_code}
            
            Login URL: {url_for('student_portal_login', _external=True)}
            
            Important:
            - Keep your access code confidential
            - Change your access code regularly
            - Report any suspicious activity immediately
            
            You can use the portal to:
            - Check your application status
            - View your course progress
            - See your payment history
            - Download important documents
            - View your class schedule
            
            Best regards,
            KEEM Driving School
            """
            
            send_email(email, 'Welcome to KEEM Student Portal', email_body)
            
            # Also send SMS/WhatsApp if possible
            sms_body = f"KEEM Student Portal: Your access code is {access_code}. Login at {url_for('student_portal_login', _external=True)}"
            # send_whatsapp_notification(phone, sms_body)  # Uncomment when implemented
            
            flash('Portal access created! Check your email for your access code.', 'success')
            return redirect(url_for('student_portal_login'))
            
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('student_portal/register.html')

@app.route('/student-portal/dashboard')
def student_portal_dashboard():
    """Student portal dashboard"""
    if 'student_id' not in session:
        flash('Please login to access the student portal.', 'error')
        return redirect(url_for('student_portal_login'))
    
    student_id = session['student_id']
    student = Student.query.options(
        joinedload(Student.application),
        joinedload(Student.course),
        joinedload(Student.branch),
        joinedload(Student.instructor)
    ).get_or_404(student_id)
    
    # Get recent payments
    payments = Payment.query.filter_by(student_id=student_id)\
        .order_by(Payment.payment_date.desc())\
        .limit(5).all()
    
    # Get upcoming lessons
    upcoming_lessons = Lesson.query.filter_by(
        student_id=student_id,
        status='scheduled'
    ).filter(Lesson.scheduled_date >= datetime.utcnow().date())\
     .order_by(Lesson.scheduled_date, Lesson.scheduled_time)\
     .limit(5).all()
    
    # Get completed lessons
    completed_lessons = Lesson.query.filter_by(
        student_id=student_id,
        status='completed'
    ).order_by(Lesson.completion_date.desc())\
     .limit(5).all()
    
    # Calculate progress
    total_lessons = Lesson.query.filter_by(student_id=student_id).count()
    completed_count = Lesson.query.filter_by(student_id=student_id, status='completed').count()
    
    if total_lessons > 0:
        progress_percentage = int((completed_count / total_lessons) * 100)
        student.progress_percentage = progress_percentage
        db.session.commit()
    
    return render_template('student_portal/dashboard.html',
                         student=student,
                         payments=payments,
                         upcoming_lessons=upcoming_lessons,
                         completed_lessons=completed_lessons)

@app.route('/student-portal/application-status')
def student_application_status():
    """View application status in student portal"""
    if 'student_id' not in session:
        flash('Please login to access the student portal.', 'error')
        return redirect(url_for('student_portal_login'))
    
    student_id = session['student_id']
    student = Student.query.options(
        joinedload(Student.application).joinedload(Application.course),
        joinedload(Student.application).joinedload(Application.branch)
    ).get_or_404(student_id)
    
    return render_template('student_portal/application_status.html',
                         student=student,
                         application=student.application)

@app.route('/student-portal/payment-history')
def student_payment_history():
    """View payment history in student portal"""
    if 'student_id' not in session:
        flash('Please login to access the student portal.', 'error')
        return redirect(url_for('student_portal_login'))
    
    student_id = session['student_id']
    payments = Payment.query.filter_by(student_id=student_id)\
        .order_by(Payment.payment_date.desc())\
        .all()
    
    student = Student.query.get(student_id)
    
    return render_template('student_portal/payment_history.html',
                         payments=payments,
                         student=student)

@app.route('/student-portal/lesson-schedule')
def student_lesson_schedule():
    """View lesson schedule in student portal"""
    if 'student_id' not in session:
        flash('Please login to access the student portal.', 'error')
        return redirect(url_for('student_portal_login'))
    
    student_id = session['student_id']
    
    # Get filter parameters
    view = request.args.get('view', 'upcoming')  # upcoming, completed, all
    month = request.args.get('month')
    
    query = Lesson.query.filter_by(student_id=student_id)\
        .options(joinedload(Lesson.instructor_rel))
    
    if view == 'upcoming':
        query = query.filter(Lesson.scheduled_date >= datetime.utcnow().date())
        query = query.filter_by(status='scheduled')
    elif view == 'completed':
        query = query.filter_by(status='completed')
    
    if month:
        # Filter by specific month
        year, month_num = map(int, month.split('-'))
        query = query.filter(
            db.extract('year', Lesson.scheduled_date) == year,
            db.extract('month', Lesson.scheduled_date) == month_num
        )
    
    lessons = query.order_by(Lesson.scheduled_date, Lesson.scheduled_time).all()
    
    student = Student.query.get(student_id)
    
    return render_template('student_portal/lesson_schedule.html',
                         lessons=lessons,
                         student=student,
                         view=view)

@app.route('/student-portal/documents')
def student_documents():
    """View and download documents in student portal"""
    if 'student_id' not in session:
        flash('Please login to access the student portal.', 'error')
        return redirect(url_for('student_portal_login'))
    
    student_id = session['student_id']
    student = Student.query.options(
        joinedload(Student.application)
    ).get_or_404(student_id)
    
    # Collect available documents
    documents = []
    
    if student.application:
        app = student.application
        
        if app.profile_photo:
            documents.append({
                'name': 'Profile Photo',
                'type': 'photo',
                'filename': app.profile_photo,
                'upload_date': app.created_at
            })
        
        if app.nrc_copy:
            documents.append({
                'name': 'NRC Copy',
                'type': 'id',
                'filename': app.nrc_copy,
                'upload_date': app.created_at
            })
        
        if app.medical_certificate:
            documents.append({
                'name': 'Medical Certificate',
                'type': 'medical',
                'filename': app.medical_certificate,
                'upload_date': app.created_at
            })
    
    # Add acceptance letter if accepted
    if student.application and student.application.status == 'accepted':
        documents.append({
            'name': 'Acceptance Letter',
            'type': 'letter',
            'generated': True,
            'action': 'generate_acceptance'
        })
    
    # Add payment receipts
    payments = Payment.query.filter_by(student_id=student_id).all()
    for payment in payments:
        documents.append({
            'name': f'Payment Receipt - {payment.payment_number}',
            'type': 'receipt',
            'generated': True,
            'payment_id': payment.id,
            'date': payment.payment_date
        })
    
    return render_template('student_portal/documents.html',
                         documents=documents,
                         student=student)

@app.route('/student-portal/profile')
def student_profile():
    """View and update student profile"""
    if 'student_id' not in session:
        flash('Please login to access the student portal.', 'error')
        return redirect(url_for('student_portal_login'))
    
    student_id = session['student_id']
    student = Student.query.options(
        joinedload(Student.application),
        joinedload(Student.course),
        joinedload(Student.branch),
        joinedload(Student.instructor)
    ).get_or_404(student_id)
    
    return render_template('student_portal/profile.html', student=student)

@app.route('/student-portal/update-profile', methods=['POST'])
def student_update_profile():
    """Update student contact information"""
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    student_id = session['student_id']
    student = Student.query.get_or_404(student_id)
    
    try:
        data = request.json
        
        if not student.application:
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        
        # Update contact information
        if 'email' in data and data['email']:
            student.application.email = data['email']
        
        if 'phone' in data and data['phone']:
            student.application.phone = data['phone']
        
        if 'whatsapp' in data:
            student.application.whatsapp = data['whatsapp']
        
        if 'address' in data and data['address']:
            student.application.address = data['address']
        
        if 'emergency_phone' in data and data['emergency_phone']:
            student.application.emergency_phone = data['emergency_phone']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating student profile: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/student-portal/change-access-code', methods=['POST'])
def student_change_access_code():
    """Change student portal access code"""
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    student_id = session['student_id']
    
    portal_access = StudentPortalAccess.query.filter_by(
        student_id=student_id,
        is_active=True
    ).first()
    
    if not portal_access:
        return jsonify({'success': False, 'message': 'Portal access not found'}), 404
    
    try:
        new_access_code = portal_access.generate_new_access_code()
        
        # Send notification
        email_body = f"""
        Your student portal access code has been changed.
        
        New Access Code: {new_access_code}
        
        If you did not request this change, please contact us immediately.
        
        Best regards,
        KEEM Driving School
        """
        
        send_email(portal_access.email, 'Access Code Changed', email_body)
        
        # Update session
        session['access_code'] = new_access_code
        
        return jsonify({
            'success': True,
            'message': 'Access code changed successfully',
            'new_code': new_access_code
        })
        
    except Exception as e:
        logger.error(f"Error changing access code: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/student-portal/logout')
def student_portal_logout():
    """Logout from student portal"""
    session.pop('student_id', None)
    session.pop('student_number', None)
    session.pop('student_name', None)
    session.pop('access_code', None)
    
    flash('You have been logged out from the student portal.', 'info')
    return redirect(url_for('student_portal_home'))

# ============== PUBLIC STUDENT LOOKUP ==============

@app.route('/check-student-status', methods=['GET', 'POST'])
def check_student_status():
    """Public page to check student status with student ID"""
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        dob = request.form.get('date_of_birth')
        
        # Find student by student number
        student = Student.query.filter_by(student_number=student_id).first()
        
        if not student:
            flash('Student not found. Please check your Student ID.', 'error')
            return render_template('public/check_student_status.html')
        
        # Verify date of birth
        if student.application and student.application.date_of_birth:
            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                if student.application.date_of_birth != dob_date:
                    flash('Date of birth does not match our records.', 'error')
                    return render_template('public/check_student_status.html')
            except:
                flash('Invalid date format.', 'error')
                return render_template('public/check_student_status.html')
        
        # Store in session for verification
        session['verified_student_id'] = student.id
        session['verification_time'] = datetime.utcnow().timestamp()
        
        return redirect(url_for('view_student_status_public', student_id=student_id))
    
    return render_template('public/check_student_status.html')

@app.route('/student-status/<string:student_id>')
def view_student_status_public(student_id):
    """Public view of student status (read-only)"""
    # Check if verification is valid (within 5 minutes)
    verification_time = session.get('verification_time')
    if not verification_time or (datetime.utcnow().timestamp() - verification_time) > 300:
        flash('Verification expired. Please verify your identity again.', 'error')
        return redirect(url_for('check_student_status'))
    
    student = Student.query.filter_by(student_number=student_id).first_or_404()
    
    # Verify the student matches the session
    if session.get('verified_student_id') != student.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('check_student_status'))
    
    return render_template('public/student_status.html', student=student)

@app.route('/student-lookup', methods=['GET'])
def student_lookup():
    """API endpoint for student lookup (for external systems)"""
    student_id = request.args.get('student_id')
    dob = request.args.get('dob')
    email = request.args.get('email')
    
    if not student_id:
        return jsonify({'error': 'Student ID is required'}), 400
    
    student = Student.query.filter_by(student_number=student_id).first()
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Basic information (public)
    response = {
        'student_number': student.student_number,
        'full_name': student.full_name,
        'course': student.course.name if student.course else None,
        'status': student.status,
        'enrollment_date': student.enrollment_date.strftime('%Y-%m-%d') if student.enrollment_date else None,
        'payment_status': student.payment_status
    }
    
    # Verify identity for sensitive information
    if dob and student.application and student.application.date_of_birth:
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            if student.application.date_of_birth == dob_date:
                response['email'] = student.application.email
                response['phone'] = student.application.phone
                response['progress'] = student.progress_percentage
        except:
            pass
    
    return jsonify(response)



# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403







@app.route('/admin/student-portal/access')
@admin_required
@role_required(['super_admin', 'admin'])
def admin_student_portal_access():
    """Admin management of student portal access"""
    query = StudentPortalAccess.query.options(
        joinedload(StudentPortalAccess.student).joinedload(Student.application)
    )
    
    # Apply filters
    status = request.args.get('status', 'active')
    search = request.args.get('search')
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search:
        query = query.join(Student).join(Application).filter(
            (Student.student_number.ilike(f'%{search}%')) |
            (Application.first_name.ilike(f'%{search}%')) |
            (Application.last_name.ilike(f'%{search}%')) |
            (Application.email.ilike(f'%{search}%'))
        )
    
    portal_accesses = query.order_by(StudentPortalAccess.created_at.desc()).all()
    
    return render_template('admin/student_portal_access.html',
                         portal_accesses=portal_accesses,
                         status=status,
                         search=search)

@app.route('/admin/student-portal/generate-access/<int:student_id>', methods=['POST'])
@admin_required
@role_required(['super_admin', 'admin'])
def admin_generate_student_access(student_id):
    """Generate portal access for a student"""
    student = Student.query.get_or_404(student_id)
    
    # Check if already has access
    existing = StudentPortalAccess.query.filter_by(student_id=student_id).first()
    
    if existing:
        if existing.is_active:
            return jsonify({'success': False, 'message': 'Student already has active portal access'})
        else:
            # Reactivate
            existing.is_active = True
            existing.access_code = generate_access_code()
            db.session.commit()
            
            # Send notification
            email_body = f"""
            Your student portal access has been generated by administrator.
            
            Student Number: {student.student_number}
            Access Code: {existing.access_code}
            
            Login at: {url_for('student_portal_login', _external=True)}
            
            Best regards,
            KEEM Driving School
            """
            
            send_email(existing.email, 'Student Portal Access Generated', email_body)
            
            return jsonify({
                'success': True,
                'message': 'Portal access reactivated',
                'access_code': existing.access_code
            })
    
    # Create new access
    if not student.application:
        return jsonify({'success': False, 'message': 'Student application not found'})
    
    access_code = generate_access_code()
    
    portal_access = StudentPortalAccess(
        student_id=student.id,
        access_code=access_code,
        email=student.application.email,
        phone=student.application.phone
    )
    
    try:
        db.session.add(portal_access)
        db.session.commit()
        
        # Send notification
        email_body = f"""
        Your student portal access has been generated by administrator.
        
        Student Number: {student.student_number}
        Access Code: {access_code}
        
        Login at: {url_for('student_portal_login', _external=True)}
        
        You can use the portal to:
        - Check your application status
        - View your course progress
        - See your payment history
        - Download important documents
        
        Best regards,
        KEEM Driving School
        """
        
        send_email(student.application.email, 'Student Portal Access Generated', email_body)
        
        return jsonify({
            'success': True,
            'message': 'Portal access created successfully',
            'access_code': access_code
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating student access: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/student-portal/reset-access/<int:access_id>', methods=['POST'])
@admin_required
@role_required(['super_admin', 'admin'])
def admin_reset_student_access(access_id):
    """Reset student portal access code"""
    portal_access = StudentPortalAccess.query.get_or_404(access_id)
    
    try:
        old_code = portal_access.access_code
        new_code = portal_access.generate_new_access_code()
        
        # Send notification
        email_body = f"""
        Your student portal access code has been reset by administrator.
        
        Old Access Code: {old_code}
        New Access Code: {new_code}
        
        Login at: {url_for('student_portal_login', _external=True)}
        
        If you did not request this change, please contact us immediately.
        
        Best regards,
        KEEM Driving School
        """
        
        send_email(portal_access.email, 'Access Code Reset', email_body)
        
        return jsonify({
            'success': True,
            'message': 'Access code reset successfully',
            'new_code': new_code
        })
        
    except Exception as e:
        logger.error(f"Error resetting student access: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/student-portal/disable-access/<int:access_id>', methods=['POST'])
@admin_required
@role_required(['super_admin', 'admin'])
def admin_disable_student_access(access_id):
    """Disable student portal access"""
    portal_access = StudentPortalAccess.query.get_or_404(access_id)
    
    try:
        portal_access.is_active = False
        db.session.commit()
        
        # Send notification
        email_body = f"""
        Your student portal access has been disabled by administrator.
        
        If you believe this is a mistake, please contact us immediately.
        
        Best regards,
        KEEM Driving School
        """
        
        send_email(portal_access.email, 'Portal Access Disabled', email_body)
        
        return jsonify({
            'success': True,
            'message': 'Portal access disabled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error disabling student access: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500










# ============== INITIALIZATION ==============

def init_database():
    """Initialize database with default data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if super admin exists
        super_admin = Admin.query.filter_by(email='admin@keemdrivingschool.com').first()
        if not super_admin:
            super_admin = Admin(
                username='superadmin',
                name='System Administrator',
                email='admin@keemdrivingschool.com',
                role='super_admin',
                branch='Both',
                is_active=True
            )
            super_admin.set_password('admin123')
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Super admin created: admin@keemdrivingschool.com / admin123")
        
        # Check if branches exist
        if not Branch.query.first():
            branch1 = Branch(
                name='Luanshya Branch',
                code='LUAN-001',
                address='Plot 123, Main Street, Luanshya',
                city='Luanshya',
                phone='+260 123 456 789',
                email='luanshya@keemdrivingschool.com',
                manager_id=super_admin.id,
                is_active=True
            )
            
            branch2 = Branch(
                name='Mufulira Branch',
                code='MUFU-001',
                address='Plot 456, Independence Avenue, Mufulira',
                city='Mufulira',
                phone='+260 987 654 321',
                email='mufulira@keemdrivingschool.com',
                manager_id=super_admin.id,
                is_active=True
            )
            
            db.session.add_all([branch1, branch2])
            db.session.commit()
            print("✅ Branches created: Luanshya, Mufulira")
        
        # Check if courses exist
        if not Course.query.first():
            branch = Branch.query.first()
            courses = [
                Course(
                    name='Class A - Motorcycle License',
                    code='CLASS-A',
                    description='Complete motorcycle driving course including theory and practical training',
                    category='Motorcycle',
                    duration_weeks=4,
                    total_hours=40,
                    theory_hours=10,
                    practical_hours=30,
                    fee=1500.00,
                    requirements='Minimum age: 16 years\nValid NRC\nMedical Certificate',
                    branch_id=branch.id,
                    instructor_id=super_admin.id,
                    is_active=True
                ),
                Course(
                    name='Class B - Light Vehicle License',
                    code='CLASS-B',
                    description='Comprehensive car driving course for light vehicles',
                    category='Light Vehicle',
                    duration_weeks=6,
                    total_hours=60,
                    theory_hours=20,
                    practical_hours=40,
                    fee=2500.00,
                    requirements='Minimum age: 18 years\nValid NRC\nMedical Certificate',
                    branch_id=branch.id,
                    instructor_id=super_admin.id,
                    is_active=True
                )
            ]
            
            db.session.add_all(courses)
            db.session.commit()
            print("✅ Sample courses created")

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run application
    app.run(debug=True, host='0.0.0.0', port=5000)