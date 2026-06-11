import sys
import os
from datetime import datetime, timedelta

# Add root folder to python path to avoid import errors when running directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database_utils import init_db, add_schedule, get_all_schedules, add_reminder, get_connection

def seed_database():
    """Seeds the database with standard academic schedules, assignments, exams, and study sessions."""
    init_db()
    
    # Check if we already have schedules. If so, don't double seed.
    schedules = get_all_schedules()
    if len(schedules) > 0:
        print("Database already contains schedules. Skipping seeding.")
        return

    print("Seeding database with default schedules...")
    
    today = datetime.now()
    
    # Let's compute some dates relative to today
    monday = today - timedelta(days=today.weekday())  # Start of current week
    tuesday = monday + timedelta(days=1)
    wednesday = monday + timedelta(days=2)
    thursday = monday + timedelta(days=3)
    friday = monday + timedelta(days=4)
    saturday = monday + timedelta(days=5)
    
    # Format dates as YYYY-MM-DD
    monday_str = monday.strftime("%Y-%m-%d")
    tuesday_str = tuesday.strftime("%Y-%m-%d")
    wednesday_str = wednesday.strftime("%Y-%m-%d")
    thursday_str = thursday.strftime("%Y-%m-%d")
    friday_str = friday.strftime("%Y-%m-%d")
    saturday_str = saturday.strftime("%Y-%m-%d")
    
    # Add Classes
    c1 = add_schedule("Database Management Systems", "Class", monday_str, "09:00", "10:30", "High", "Completed" if today.weekday() > 0 else "Pending")
    c2 = add_schedule("Artificial Intelligence", "Class", monday_str, "11:00", "12:30", "High", "Completed" if today.weekday() > 0 else "Pending")
    c3 = add_schedule("Software Engineering", "Class", tuesday_str, "09:00", "10:30", "Medium", "Completed" if today.weekday() > 1 else "Pending")
    c4 = add_schedule("Computer Networks", "Class", tuesday_str, "14:00", "15:30", "Medium", "Completed" if today.weekday() > 1 else "Pending")
    c5 = add_schedule("Database Management Systems", "Class", wednesday_str, "09:00", "10:30", "High", "Completed" if today.weekday() > 2 else "Pending")
    c6 = add_schedule("Artificial Intelligence", "Class", wednesday_str, "11:00", "12:30", "High", "Completed" if today.weekday() > 2 else "Pending")
    c7 = add_schedule("Software Engineering", "Class", thursday_str, "09:00", "10:30", "Medium", "Completed" if today.weekday() > 3 else "Pending")
    c8 = add_schedule("Computer Networks", "Class", thursday_str, "14:00", "15:30", "Medium", "Completed" if today.weekday() > 3 else "Pending")
    c9 = add_schedule("Web Development Lab", "Class", friday_str, "10:00", "12:00", "Low", "Completed" if today.weekday() > 4 else "Pending")
    
    # Add Exams
    e1 = add_schedule("DBMS Midterm Exam", "Exam", thursday_str, "11:00", "13:00", "High", "Pending")
    e2 = add_schedule("AI Final Prep Exam", "Exam", (today + timedelta(days=7)).strftime("%Y-%m-%d"), "10:00", "12:00", "High", "Pending")
    
    # Add Assignments
    a1 = add_schedule("AI Assignment 2 Submission", "Assignment", wednesday_str, "23:59", "23:59", "High", "Pending")
    a2 = add_schedule("Software Design Doc Draft", "Assignment", friday_str, "17:00", "17:00", "Medium", "Pending")
    
    # Add Study Sessions
    s1 = add_schedule("DBMS Group Revision", "Study Session", tuesday_str, "16:00", "18:00", "Medium", "Pending")
    s2 = add_schedule("AI Model Implementation Session", "Study Session", thursday_str, "15:00", "17:00", "High", "Pending")
    
    # Add Reminders for Exams and Assignments
    # Reminder for DBMS midterm: 2 hours before the exam
    e1_time = datetime.strptime(f"{thursday_str} 11:00", "%Y-%m-%d %H:%M")
    add_reminder(e1, (e1_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), "Email")
    add_reminder(e1, (e1_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"), "Dashboard")
    
    # Reminder for AI Assignment: 1 day before
    a1_time = datetime.strptime(f"{wednesday_str} 23:59", "%Y-%m-%d %H:%M")
    add_reminder(a1, (a1_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "Email")
    
    # Reminder for AI Prep Exam: 1 day before
    e2_time = datetime.strptime(f"{(today + timedelta(days=7)).strftime('%Y-%m-%d')} 10:00", "%Y-%m-%d %H:%M")
    add_reminder(e2, (e2_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "Email")
    
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()