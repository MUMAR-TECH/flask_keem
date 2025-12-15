"""
Email Sending Utility
Configure your SMTP settings before use
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Email Configuration - Update these with your actual settings
SMTP_SERVER = 'smtp.gmail.com'  # or your hosting SMTP
SMTP_PORT = 587
SMTP_USERNAME = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'
FROM_EMAIL = 'noreply@keemdrivingschool.com'
FROM_NAME = 'KEEM Driving School'

def send_email(to_email, subject, body, attachments=None, html=False):
    """
    Send email with optional attachments
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        attachments: List of file paths to attach
        html: Boolean, if True body is treated as HTML
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments if any
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={os.path.basename(file_path)}'
                        )
                        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_acceptance_email(to_email, subject, application_data, pdf_path=None):
    """
    Send acceptance email with acceptance letter
    """
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #dc2626 0%, #000000 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #dc2626; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Congratulations!</h1>
                <p>Your Application Has Been Accepted</p>
            </div>
            <div class="content">
                <h2>Dear {application_data['first_name']} {application_data['last_name']},</h2>
                
                <p>We are thrilled to inform you that your application to <strong>KEEM Driving School</strong> has been <strong>ACCEPTED</strong>!</p>
                
                <p><strong>Application Details:</strong></p>
                <ul>
                    <li>Application ID: {application_data['id']}</li>
                    <li>Course: {application_data['course_type']}</li>
                    <li>Branch: {application_data['branch']}</li>
                </ul>
                
                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Review the attached acceptance letter carefully</li>
                    <li>Contact us to schedule your enrollment appointment</li>
                    <li>Bring required documents as listed in the acceptance letter</li>
                    <li>Complete payment arrangements</li>
                </ol>
                
                <p><strong>Contact Information:</strong></p>
                <p>
                    📞 Phone: +260 XXX XXXXXX<br>
                    📱 WhatsApp: +260 XXX XXXXXX<br>
                    📧 Email: info@keemdrivingschool.com
                </p>
                
                <p>We look forward to helping you achieve your driving goals!</p>
                
                <p>Best regards,<br>
                <strong>KEEM Driving School Team</strong></p>
            </div>
            <div class="footer">
                <p>KEEM Driving School - Excellence in Driver Training</p>
                <p>Luanshya Branch | Mufulira Branch</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    attachments = [pdf_path] if pdf_path else None
    return send_email(to_email, subject, html_body, attachments, html=True)

def send_bulk_email(recipients, subject, body, html=False):
    """
    Send email to multiple recipients
    """
    results = []
    for recipient in recipients:
        success = send_email(recipient, subject, body, html=html)
        results.append({'email': recipient, 'success': success})
    return results