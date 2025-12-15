# KEEM Driving School - Complete Deployment Guide

## 📋 Table of Contents
1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [cPanel Deployment](#cpanel-deployment)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## 📁 Project Structure

```
keem_driving_school/
│
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .htaccess                      # Apache configuration
├── passenger_wsgi.py              # WSGI entry point for cPanel
│
├── utils/                         # Utility modules
│   ├── __init__.py
│   ├── email_sender.py           # Email functionality
│   ├── whatsapp_sender.py        # WhatsApp notifications
│   ├── pdf_generator.py          # PDF generation
│   └── excel_exporter.py         # Excel exports
│
├── templates/                     # HTML templates
│   ├── base.html                 # Base template
│   ├── index.html                # Homepage
│   ├── about.html                # About page
│   ├── courses.html              # Courses page
│   ├── branches.html             # Branches page
│   ├── contact.html              # Contact page
│   ├── apply.html                # Application form
│   ├── application_status.html   # Status check
│   │
│   ├── admin/                    # Admin templates
│   │   ├── base_admin.html      # Admin base
│   │   ├── login.html           # Admin login
│   │   ├── dashboard.html       # Dashboard
│   │   ├── applications.html    # Applications list
│   │   ├── view_application.html # View single application
│   │   └── settings.html        # Settings
│   │
│   └── errors/                  # Error pages
│       ├── 404.html
│       └── 500.html
│
├── static/                       # Static files
│   ├── css/
│   │   └── custom.css
│   ├── js/
│   │   └── main.js
│   ├── images/
│   └── uploads/                 # User uploads
│
├── exports/                     # Generated exports
│   ├── pdfs/
│   └── excel/
│
└── database.sql                 # Database schema

```

---

## 🔧 Prerequisites

### Required Software
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)
- virtualenv (recommended)

### Required Python Packages
```
Flask==2.3.0
Flask-MySQLdb==1.0.1
mysqlclient==2.1.1
Werkzeug==2.3.0
reportlab==4.0.4
openpyxl==3.1.2
twilio==8.5.0
Pillow==10.0.0
python-dotenv==1.0.0
```

---

## 💻 Local Development Setup

### Step 1: Clone/Create Project Directory
```bash
mkdir keem_driving_school
cd keem_driving_school
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create requirements.txt
```
Flask==2.3.0
Flask-MySQLdb==1.0.1
mysqlclient==2.1.1
Werkzeug==2.3.0
reportlab==4.0.4
openpyxl==3.1.2
twilio==8.5.0
Pillow==10.0.0
python-dotenv==1.0.0
```

### Step 5: Setup MySQL Database
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE keem_driving_school;

# Import schema
mysql -u root -p keem_driving_school < database.sql

# Create MySQL user (optional but recommended)
CREATE USER 'keem_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON keem_driving_school.* TO 'keem_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 6: Configure Application
Edit `app.py` with your database credentials:
```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'keem_user'
app.config['MYSQL_PASSWORD'] = 'your_secure_password'
app.config['MYSQL_DB'] = 'keem_driving_school'
```

### Step 7: Configure Email (utils/email_sender.py)
```python
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'  # Use App Password for Gmail
FROM_EMAIL = 'noreply@keemdrivingschool.com'
```

### Step 8: Configure WhatsApp (utils/whatsapp_sender.py)
Sign up for Twilio: https://www.twilio.com/
```python
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
```

### Step 9: Create Necessary Directories
```bash
mkdir -p static/uploads
mkdir -p exports/pdfs
mkdir -p exports/excel
mkdir -p templates/admin
mkdir -p templates/errors
mkdir -p utils
```

### Step 10: Run Development Server
```bash
python app.py
```
Visit: http://localhost:5000

---

## 🚀 cPanel Deployment

### Step 1: Prepare Files for Upload
1. Compress your project:
```bash
# Exclude virtual environment
tar -czf keem_app.tar.gz --exclude='venv' --exclude='__pycache__' *
```

### Step 2: Create passenger_wsgi.py
```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/public_html/keem_driving_school'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['PYTHON_EGG_CACHE'] = '/home/yourusername/.python-eggs'

# Import Flask application
from app import app as application
```

### Step 3: Create .htaccess
```apache
# Enable Python application
PassengerEnabled On
PassengerPython /home/yourusername/virtualenv/keem_driving_school/3.9/bin/python

# Redirect all traffic to passenger_wsgi.py
RewriteEngine On
RewriteBase /
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [QSA,L]

# Security Headers
<IfModule mod_headers.c>
    Header set X-Content-Type-Options "nosniff"
    Header set X-Frame-Options "SAMEORIGIN"
    Header set X-XSS-Protection "1; mode=block"
</IfModule>

# Prevent access to sensitive files
<FilesMatch "(\.py|\.pyc|\.log|\.ini|\.conf)$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

### Step 4: Upload to cPanel
1. Login to cPanel
2. Open **File Manager**
3. Navigate to `public_html` or your desired directory
4. Create folder: `keem_driving_school`
5. Upload `keem_app.tar.gz`
6. Extract the archive
7. Upload `passenger_wsgi.py` and `.htaccess`

### Step 5: Setup Python Environment in cPanel
1. Go to **Setup Python App** in cPanel
2. Click **Create Application**
3. Configure:
   - Python Version: 3.9 or higher
   - Application Root: `/home/yourusername/public_html/keem_driving_school`
   - Application URL: `/` or `/keem`
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `app`

4. Click **Create**

### Step 6: Install Dependencies
1. In Python App section, click **Enter to the virtual environment**
2. Copy the command and run in **Terminal**:
```bash
source /home/yourusername/virtualenv/keem_driving_school/3.9/bin/activate
cd /home/yourusername/public_html/keem_driving_school
pip install -r requirements.txt
```

### Step 7: Setup MySQL Database
1. Go to **MySQL Databases** in cPanel
2. Create database: `username_keem_db`
3. Create user: `username_keem_user`
4. Set strong password
5. Add user to database with ALL PRIVILEGES
6. Go to **phpMyAdmin**
7. Select your database
8. Import `database.sql`

### Step 8: Configure Application for Production
Edit `app.py`:
```python
# Production settings
app.config['SECRET_KEY'] = 'GENERATE_STRONG_SECRET_KEY_HERE'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'username_keem_user'
app.config['MYSQL_PASSWORD'] = 'your_database_password'
app.config['MYSQL_DB'] = 'username_keem_db'

# Change to production mode
if __name__ == '__main__':
    app.run(debug=False)  # Disable debug in production
```

### Step 9: Set Permissions
```bash
# Make sure these directories are writable
chmod 755 static/uploads
chmod 755 exports/pdfs
chmod 755 exports/excel
```

### Step 10: Restart Application
1. Go back to **Setup Python App**
2. Click **Restart** button
3. Your app should now be live!

---

## ⚙️ Configuration

### Email Configuration (Gmail)
1. Enable 2-Factor Authentication on Gmail
2. Generate App Password:
   - Google Account → Security → App passwords
   - Create password for "Mail"
3. Use generated password in `email_sender.py`

### WhatsApp Configuration (Twilio)
1. Sign up: https://www.twilio.com/try-twilio
2. Get free trial credits
3. Enable WhatsApp Sandbox
4. Add your credentials to `whatsapp_sender.py`

### Admin Account
Default admin credentials (from database.sql):
- Email: admin@keemdrivingschool.com
- Password: admin123

**IMPORTANT:** Change this password immediately after first login!

To create new admin:
```sql
INSERT INTO admins (name, email, password, role, branch) 
VALUES ('Your Name', 'email@example.com', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5cOK4hC5XGe1u', 
        'admin', 'Luanshya');
```

---

## 🧪 Testing

### Test Application Form
1. Visit: `yourdomain.com/apply`
2. Fill out the form completely
3. Submit application
4. Check:
   - Database for new entry
   - Admin email for notification
   - WhatsApp for notification

### Test Admin Panel
1. Visit: `yourdomain.com/admin/login`
2. Login with admin credentials
3. Test:
   - View applications
   - Accept/Reject applications
   - Export to PDF
   - Export to Excel

### Test Email Delivery
```python
# Test script (test_email.py)
from utils.email_sender import send_email

result = send_email(
    'test@example.com',
    'Test Email',
    'This is a test email from KEEM Driving School'
)
print("Email sent:", result)
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "Internal Server Error"
**Solution:**
- Check error logs in cPanel (Errors → Error Log)
- Verify Python version compatibility
- Check file permissions
- Verify database credentials

#### 2. MySQL Connection Error
**Solution:**
```python
# Verify credentials
mysql -u username_keem_user -p
# If connection fails, recreate user in cPanel
```

#### 3. Import Errors
**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### 4. File Upload Issues
**Solution:**
```bash
# Fix permissions
chmod 755 static/uploads
chown username:username static/uploads
```

#### 5. Email Not Sending
**Solutions:**
- Verify SMTP credentials
- Check if port 587 is open
- Use App Password for Gmail
- Disable less secure app access

#### 6. WhatsApp Messages Not Sending
**Solutions:**
- Verify Twilio credentials
- Check sandbox configuration
- Verify phone number format (+260...)
- Check Twilio console for errors

### Debug Mode
For development only:
```python
# Enable detailed errors
app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
```

### Database Check
```sql
-- Verify tables exist
SHOW TABLES;

-- Check admin accounts
SELECT * FROM admins;

-- Check applications
SELECT COUNT(*) FROM applications;
```

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks
1. **Weekly:**
   - Check error logs
   - Review pending applications
   - Backup database

2. **Monthly:**
   - Update dependencies
   - Review security logs
   - Clean old uploads

3. **Quarterly:**
   - Update Python/Flask versions
   - Security audit
   - Performance optimization

### Backup Strategy
```bash
# Database backup
mysqldump -u username -p username_keem_db > backup_$(date +%Y%m%d).sql

# Files backup
tar -czf keem_backup_$(date +%Y%m%d).tar.gz /path/to/keem_driving_school
```

### Security Checklist
- [ ] Change default admin password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS (SSL certificate)
- [ ] Regular security updates
- [ ] Input validation
- [ ] SQL injection prevention (using parameterized queries)
- [ ] XSS prevention (Flask auto-escaping)
- [ ] CSRF protection (implement Flask-WTF)
- [ ] Rate limiting for forms
- [ ] Regular backups

---

## 📄 License
Copyright © 2024 KEEM Driving School. All rights reserved.

---

## 📮 Contact
For technical support, contact your system administrator or the development team.