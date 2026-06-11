import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import config
from utils.database_utils import get_pending_reminders, mark_reminder_sent

def send_email(receiver_email, subject, message):
    """
    Sends an email using SMTP configuration from config.py.
    Handles exceptions gracefully to prevent database lockups or app crashes.
    """
    # Use config values
    sender_email = config.SMTP_EMAIL
    app_password = config.SMTP_PASSWORD
    smtp_server = config.SMTP_SERVER
    smtp_port = config.SMTP_PORT
    
    if not sender_email or not app_password:
        print("SMTP Credentials not configured. Skipping email send.")
        return False
        
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = f"Smart Timetable AI <{sender_email}>"
        msg["To"] = receiver_email
        
        # Connect to server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print(f"Email reminder successfully sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {receiver_email}. Error: {e}")
        return False

def check_and_trigger_reminders():
    """
    Queries all pending reminders that are due and sends them.
    Returns a list of triggered reminders for the UI to display.
    """
    pending = get_pending_reminders()
    triggered = []
    
    for r in pending:
        success = True
        subject = f"🔔 Reminder: {r['subject']} ({r['event_type']})"
        
        event_time = f"{r['date']} at {r['start_time']}"
        body = (
            f"Hello {r['user_name']},\n\n"
            f"This is a reminder for your upcoming academic event:\n\n"
            f"Event: {r['subject']}\n"
            f"Type: {r['event_type']}\n"
            f"Time: {event_time}\n"
            f"Priority: {r['priority']}\n\n"
            f"Stay organized and good luck!\n\n"
            f"Best regards,\n"
            f"Your Smart Timetable Assistant"
        )
        
        if r['notification_type'] == 'Email':
            # Send SMTP Email
            success = send_email(r['user_email'], subject, body)
        elif r['notification_type'] == 'Dashboard':
            # Dashboard notifications don't require external sending, just display in UI
            success = True
            
        if success:
            mark_reminder_sent(r['id'])
            r['sent_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            triggered.append(r)
            
    return triggered