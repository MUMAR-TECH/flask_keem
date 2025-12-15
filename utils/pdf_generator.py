"""
Complete PDF Generation Utility for KEEM Driving School
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import locale

# Set locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    pass

def format_currency(amount):
    """Format amount as currency"""
    try:
        return f"ZMW {float(amount):,.2f}"
    except:
        return f"ZMW {amount}"

def generate_application_pdf(application):
    """
    Generate detailed PDF for a single application
    """
    os.makedirs('exports/pdf/applications', exist_ok=True)
    
    filename = f"exports/pdf/applications/application_{application.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          topMargin=1*cm, bottomMargin=1*cm,
                          leftMargin=1.5*cm, rightMargin=1.5*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#DC2626'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    title = Paragraph("KEEM DRIVING SCHOOL - APPLICATION FORM", title_style)
    story.append(title)
    
    # Application Summary
    summary_data = [
        ["Application Number:", application.application_number],
        ["Application Date:", application.application_date.strftime('%B %d, %Y')],
        ["Status:", f"<b>{application.status.upper()}</b>"],
        ["Branch:", application.branch.name if application.branch else 'N/A'],
        ["Course Applied:", application.course.name if application.course else 'N/A']
    ]
    
    summary_table = Table(summary_data, colWidths=[4*cm, 10*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    
    story.append(Spacer(1, 20))
    
    # Personal Information
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=10,
        spaceBefore=20
    )
    
    story.append(Paragraph("Personal Information", header_style))
    
    personal_data = [
        ["Full Name:", f"{application.first_name} {application.last_name}"],
        ["Email Address:", application.email],
        ["Phone Number:", application.phone],
        ["WhatsApp:", application.whatsapp or application.phone],
        ["Date of Birth:", application.date_of_birth.strftime('%B %d, %Y')],
        ["Age:", str(application.age)],
        ["Gender:", application.gender.title()],
        ["NRC Number:", application.nrc_number or 'N/A'],
        ["Address:", application.address],
        ["City:", application.city],
        ["Province:", application.province]
    ]
    
    personal_table = Table(personal_data, colWidths=[4*cm, 10*cm])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(personal_table)
    
    story.append(Spacer(1, 20))
    
    # Course Information
    story.append(Paragraph("Course Information", header_style))
    
    course_data = [
        ["Course Name:", application.course.name if application.course else 'N/A'],
        ["Course Code:", application.course.code if application.course else 'N/A'],
        ["Category:", application.course.category if application.course else 'N/A'],
        ["Duration:", f"{application.course.duration_weeks} weeks ({application.course.total_hours} hours)" if application.course else 'N/A'],
        ["Course Fee:", format_currency(application.course.fee) if application.course else 'N/A'],
        ["Preferred Schedule:", application.preferred_schedule or 'Flexible'],
        ["Preferred Language:", application.preferred_language or 'English']
    ]
    
    course_table = Table(course_data, colWidths=[4*cm, 10*cm])
    course_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(course_table)
    
    story.append(Spacer(1, 20))
    
    # Background Information
    story.append(Paragraph("Background Information", header_style))
    
    background_data = [
        ["Education Level:", application.education_level or 'Not specified'],
        ["Previous Experience:", application.previous_experience or 'No experience'],
        ["Medical Conditions:", application.medical_conditions or 'None']
    ]
    
    background_table = Table(background_data, colWidths=[4*cm, 10*cm])
    background_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(background_table)
    
    story.append(Spacer(1, 20))
    
    # Emergency Contact
    story.append(Paragraph("Emergency Contact", header_style))
    
    emergency_data = [
        ["Name:", application.emergency_name],
        ["Phone:", application.emergency_phone],
        ["Relationship:", application.emergency_relation or 'Not specified']
    ]
    
    emergency_table = Table(emergency_data, colWidths=[4*cm, 10*cm])
    emergency_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(emergency_table)
    
    # Admin Notes (if any)
    if application.admin_notes:
        story.append(Spacer(1, 20))
        story.append(Paragraph("Administrative Notes", header_style))
        
        notes_style = ParagraphStyle(
            'Notes',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6B7280'),
            backColor=colors.HexColor('#FEF3C7'),
            borderPadding=10,
            borderColor=colors.HexColor('#F59E0B'),
            borderWidth=1
        )
        
        notes = Paragraph(application.admin_notes, notes_style)
        story.append(notes)
    
    # Footer
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )
    
    footer = Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | "
        f"KEEM Driving School | {application.branch.name if application.branch else 'Main Branch'}",
        footer_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    return filename

def generate_acceptance_letter(application):
    """
    Generate official acceptance letter PDF
    """
    os.makedirs('exports/pdf/acceptance_letters', exist_ok=True)
    
    filename = f"exports/pdf/acceptance_letters/acceptance_{application.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          topMargin=2*cm, bottomMargin=2*cm,
                          leftMargin=2.5*cm, rightMargin=2.5*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Letterhead
    letterhead_style = ParagraphStyle(
        'Letterhead',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_RIGHT,
        spaceAfter=20
    )
    
    letterhead = Paragraph(
        "KEEM Driving School<br/>"
        "Excellence in Driver Training<br/>"
        "Plot 123, Main Street, Luanshya<br/>"
        "Phone: +260 123 456 789 | Email: info@keemdrivingschool.com",
        letterhead_style
    )
    story.append(letterhead)
    
    # Date
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20
    )
    
    date = Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", date_style)
    story.append(date)
    
    # Reference
    ref_style = ParagraphStyle(
        'Reference',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=30
    )
    
    ref = Paragraph(f"Reference: {application.application_number}", ref_style)
    story.append(ref)
    
    # Recipient Address
    recipient_style = ParagraphStyle(
        'Recipient',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=30
    )
    
    recipient = Paragraph(
        f"{application.first_name} {application.last_name}<br/>"
        f"{application.address}<br/>"
        f"{application.city}, {application.province}<br/>"
        f"Phone: {application.phone}<br/>"
        f"Email: {application.email}",
        recipient_style
    )
    story.append(recipient)
    
    # Subject
    subject_style = ParagraphStyle(
        'Subject',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=20
    )
    
    subject = Paragraph("LETTER OF ACCEPTANCE", subject_style)
    story.append(subject)
    
    # Salutation
    salutation_style = ParagraphStyle(
        'Salutation',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10
    )
    
    salutation = Paragraph(f"Dear {application.first_name} {application.last_name},", salutation_style)
    story.append(salutation)
    
    # Body
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=10,
        alignment=TA_JUSTIFY
    )
    
    body_text = [
        Paragraph(
            "We are pleased to inform you that your application to KEEM Driving School has been <b>ACCEPTED</b>. "
            "Congratulations on taking this important step towards becoming a certified driver!",
            body_style
        ),
        Spacer(1, 10),
        Paragraph("<b>Application Details:</b>", body_style),
        Paragraph(f"Application Number: {application.application_number}", body_style),
        Paragraph(f"Course: {application.course.name if application.course else 'N/A'}", body_style),
        Paragraph(f"Branch: {application.branch.name if application.branch else 'N/A'}", body_style),
        Spacer(1, 10),
        Paragraph("<b>Next Steps:</b>", body_style),
        Paragraph("1. Visit our branch office within 7 days to complete enrollment", body_style),
        Paragraph("2. Bring the following documents:", body_style),
        Paragraph("   • Original NRC and 2 photocopies", body_style),
        Paragraph("   • 2 passport-sized photographs", body_style),
        Paragraph("   • Medical certificate (if applicable)", body_style),
        Paragraph("3. Pay the registration fee of ZMW 500", body_style),
        Paragraph("4. Receive your training schedule and student ID", body_style),
        Paragraph("5. Attend the orientation session", body_style),
        Spacer(1, 10),
        Paragraph(
            "Our team will contact you within 2 business days to schedule your orientation session. "
            "Welcome to KEEM Driving School! We look forward to helping you achieve your driving goals.",
            body_style
        )
    ]
    
    for element in body_text:
        story.append(element)
    
    story.append(Spacer(1, 30))
    
    # Closing
    closing_style = ParagraphStyle(
        'Closing',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=5
    )
    
    closing = Paragraph("Sincerely,", closing_style)
    story.append(closing)
    
    story.append(Spacer(1, 40))
    
    # Signature
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=20
    )
    
    signature = Paragraph(
        "_________________________<br/>"
        "<b>KEEM Driving School Management</b><br/>"
        "Director",
        signature_style
    )
    story.append(signature)
    
    # Footer
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )
    
    footer = Paragraph(
        "KEEM Driving School | Excellence in Driver Training | "
        "Luanshya & Mufulira Branches | License No: XYZ12345",
        footer_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    return filename

def generate_invoice_pdf(payment):
    """
    Generate invoice PDF for payment
    """
    os.makedirs('exports/pdf/invoices', exist_ok=True)
    
    filename = f"exports/pdf/invoices/invoice_{payment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          topMargin=1.5*cm, bottomMargin=1.5*cm,
                          leftMargin=2*cm, rightMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Header
    header_table_data = [
        [
            Paragraph(
                "<b>KEEM DRIVING SCHOOL</b><br/>"
                "Excellence in Driver Training<br/>"
                "Plot 123, Main Street, Luanshya<br/>"
                "Phone: +260 123 456 789<br/>"
                "Email: info@keemdrivingschool.com",
                ParagraphStyle('Left', parent=styles['Normal'], fontSize=9)
            ),
            Paragraph(
                "<b>INVOICE</b><br/>"
                f"Date: {datetime.now().strftime('%B %d, %Y')}<br/>"
                f"Invoice #: {payment.payment_number}<br/>"
                f"Status: <font color='green'><b>PAID</b></font>",
                ParagraphStyle('Right', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
            )
        ]
    ]
    
    header_table = Table(header_table_data, colWidths=[10*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    
    # Bill To
    story.append(Spacer(1, 10))
    
    bill_to_style = ParagraphStyle(
        'BillTo',
        parent=styles['Heading3'],
        fontSize=10,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=5
    )
    
    story.append(Paragraph("BILL TO", bill_to_style))
    
    if payment.student and payment.student.application:
        bill_to_data = [
            [
                Paragraph(
                    f"{payment.student.application.first_name} {payment.student.application.last_name}<br/>"
                    f"{payment.student.application.address}<br/>"
                    f"{payment.student.application.city}, {payment.student.application.province}<br/>"
                    f"Phone: {payment.student.application.phone}<br/>"
                    f"Email: {payment.student.application.email}",
                    ParagraphStyle('BillToDetails', parent=styles['Normal'], fontSize=9)
                )
            ]
        ]
        
        bill_to_table = Table(bill_to_data)
        bill_to_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(bill_to_table)
    
    story.append(Spacer(1, 20))
    
    # Invoice Items
    items_header_style = ParagraphStyle(
        'ItemsHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    items_data = [
        [
            Paragraph("<b>Description</b>", items_header_style),
            Paragraph("<b>Student #</b>", items_header_style),
            Paragraph("<b>Course</b>", items_header_style),
            Paragraph("<b>Amount</b>", items_header_style)
        ]
    ]
    
    # Add payment item
    if payment.student:
        course_name = payment.student.course.name if payment.student.course else "Driving Course"
        items_data.append([
            Paragraph(f"Payment for {course_name}", ParagraphStyle('Item', parent=styles['Normal'], fontSize=9)),
            Paragraph(payment.student.student_number, ParagraphStyle('Item', parent=styles['Normal'], fontSize=9)),
            Paragraph(course_name, ParagraphStyle('Item', parent=styles['Normal'], fontSize=9)),
            Paragraph(format_currency(payment.amount), ParagraphStyle('Item', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT))
        ])
    
    items_table = Table(items_data, colWidths=[7*cm, 3*cm, 4*cm, 2*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    
    story.append(Spacer(1, 20))
    
    # Totals
    totals_data = [
        ["Subtotal:", format_currency(payment.amount)],
        ["Tax (0%):", "ZMW 0.00"],
        ["<b>Total Paid:</b>", f"<b>{format_currency(payment.amount)}</b>"]
    ]
    
    totals_table = Table(totals_data, colWidths=[14*cm, 2*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(totals_table)
    
    # Payment Details
    story.append(Spacer(1, 20))
    
    payment_details_style = ParagraphStyle(
        'PaymentDetails',
        parent=styles['Heading3'],
        fontSize=10,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=5
    )
    
    story.append(Paragraph("PAYMENT DETAILS", payment_details_style))
    
    payment_details_data = [
        ["Payment Method:", payment.payment_method.title()],
        ["Payment Date:", payment.payment_date.strftime('%B %d, %Y')],
        ["Received By:", payment.receiver.name if payment.receiver else 'N/A'],
        ["Reference:", payment.reference_number or 'N/A'],
        ["Notes:", payment.notes or 'N/A']
    ]
    
    payment_details_table = Table(payment_details_data, colWidths=[4*cm, 12*cm])
    payment_details_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(payment_details_table)
    
    # Student Balance (if applicable)
    if payment.student:
        story.append(Spacer(1, 20))
        
        balance_style = ParagraphStyle(
            'Balance',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6B7280')
        )
        
        balance = Paragraph(
            f"<b>Student Balance:</b> {format_currency(payment.student.balance)} "
            f"(Total Fee: {format_currency(payment.student.total_fee)} - "
            f"Paid: {format_currency(payment.student.amount_paid)})",
            balance_style
        )
        story.append(balance)
    
    # Footer
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )
    
    footer = Paragraph(
        "Thank you for your payment!<br/>"
        "This invoice is computer generated and does not require a signature.<br/>"
        "For any inquiries, please contact info@keemdrivingschool.com or call +260 123 456 789",
        footer_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    return filename

def generate_student_report(student):
    """
    Generate comprehensive student report PDF
    """
    os.makedirs('exports/pdf/student_reports', exist_ok=True)
    
    filename = f"exports/pdf/student_reports/student_{student.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          topMargin=1.5*cm, bottomMargin=1.5*cm,
                          leftMargin=2*cm, rightMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#DC2626'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    title = Paragraph("STUDENT PROGRESS REPORT", title_style)
    story.append(title)
    
    # Student Information
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    info = Paragraph(
        f"<b>Student Number:</b> {student.student_number} | "
        f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}",
        info_style
    )
    story.append(info)
    
    # Student Details
    if student.application:
        details_data = [
            ["Student Name:", f"{student.application.first_name} {student.application.last_name}"],
            ["Course:", student.course.name if student.course else 'N/A'],
            ["Enrollment Date:", student.enrollment_date.strftime('%B %d, %Y')],
            ["Course Duration:", f"{student.course.duration_weeks} weeks" if student.course else 'N/A'],
            ["Instructor:", student.instructor.name if student.instructor else 'Not assigned'],
            ["Branch:", student.branch.name if student.branch else 'N/A'],
            ["Status:", student.status.title()],
            ["Progress:", f"{student.progress_percentage}%"]
        ]
        
        details_table = Table(details_data, colWidths=[5*cm, 11*cm])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(details_table)
    
    story.append(Spacer(1, 20))
    
    # Progress Summary
    progress_header_style = ParagraphStyle(
        'ProgressHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=10
    )
    
    story.append(Paragraph("Progress Summary", progress_header_style))
    
    # Create a progress bar visualization
    progress_width = 400
    progress_filled = (student.progress_percentage / 100) * progress_width
    
    # Note: For actual progress bar graphics, we'd need to use ReportLab's drawing capabilities
    # For now, we'll show a textual representation
    
    progress_data = [
        ["Overall Progress:", f"{student.progress_percentage}%"],
        ["Last Assessment Score:", f"{student.last_assessment_score or 'N/A'}/100"],
        ["Lessons Completed:", f"{len([l for l in student.lessons if l.status == 'completed'])}"],
        ["Attendance Rate:", "Calculating..."]
    ]
    
    progress_table = Table(progress_data, colWidths=[6*cm, 10*cm])
    progress_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(progress_table)
    
    # Financial Summary
    story.append(Spacer(1, 20))
    story.append(Paragraph("Financial Summary", progress_header_style))
    
    financial_data = [
        ["Total Course Fee:", format_currency(student.total_fee)],
        ["Amount Paid:", format_currency(student.amount_paid)],
        ["Outstanding Balance:", format_currency(student.balance)],
        ["Payment Status:", student.payment_status.title()]
    ]
    
    financial_table = Table(financial_data, colWidths=[6*cm, 10*cm])
    financial_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (2, 2), (2, 2), colors.HexColor('#FEF2F2') if student.balance > 0 else colors.HexColor('#F0FDF4')),
    ]))
    story.append(financial_table)
    
    # Recent Lessons (if any)
    if student.lessons:
        story.append(Spacer(1, 20))
        story.append(Paragraph("Recent Lessons", progress_header_style))
        
        lessons_header = ["Date", "Type", "Status", "Score", "Instructor"]
        lessons_data = [lessons_header]
        
        for lesson in sorted(student.lessons, key=lambda x: x.scheduled_date, reverse=True)[:5]:
            lessons_data.append([
                lesson.scheduled_date.strftime('%Y-%m-%d'),
                lesson.lesson_type.title(),
                lesson.status.title(),
                str(lesson.score) if lesson.score else "N/A",
                lesson.instructor.name if lesson.instructor else "N/A"
            ])
        
        lessons_table = Table(lessons_data, colWidths=[3*cm, 3*cm, 3*cm, 2*cm, 5*cm])
        lessons_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))
        story.append(lessons_table)
    
    # Footer
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )
    
    footer = Paragraph(
        f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | "
        f"KEEM Driving School - {student.branch.name if student.branch else 'Main Branch'}",
        footer_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    return filename