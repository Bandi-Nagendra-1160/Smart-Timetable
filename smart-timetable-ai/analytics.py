from datetime import datetime, timedelta
import pandas as pd
from utils.database_utils import get_connection

def get_event_duration_hours(start_time, end_time):
    """Calculates duration in hours between two time strings ('HH:MM')."""
    try:
        h1, m1 = map(int, start_time.split(':'))
        h2, m2 = map(int, end_time.split(':'))
        diff_minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
        return max(0.0, diff_minutes / 60.0)
    except Exception:
        return 0.0

def get_dashboard_metrics():
    """Computes all summary numbers for the top dashboard widgets."""
    conn = get_connection()
    cursor = conn.cursor()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Total classes
    cursor.execute("SELECT count(*) FROM schedules WHERE event_type = 'Class'")
    total_classes = cursor.fetchone()[0]
    
    # 2. Upcoming exams
    cursor.execute("SELECT count(*) FROM schedules WHERE event_type = 'Exam' AND date >= ? AND status = 'Pending'", (today_str,))
    upcoming_exams = cursor.fetchone()[0]
    
    # 3. Pending assignments
    cursor.execute("SELECT count(*) FROM schedules WHERE event_type = 'Assignment' AND status = 'Pending'", ())
    pending_assignments = cursor.fetchone()[0]
    
    # 4. Study hours this week
    today = datetime.now()
    start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    end_of_week = (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT start_time, end_time FROM schedules 
        WHERE event_type = 'Study Session' AND date >= ? AND date <= ?
    """, (start_of_week, end_of_week))
    
    study_sessions = cursor.fetchall()
    total_study_hours = sum(get_event_duration_hours(s['start_time'], s['end_time']) for s in study_sessions)
    
    conn.close()
    
    return {
        "total_classes": total_classes,
        "upcoming_exams": upcoming_exams,
        "pending_assignments": pending_assignments,
        "total_study_hours": round(total_study_hours, 1)
    }

def get_subject_wise_study_time():
    """Calculates total study session hours per subject."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subject, start_time, end_time FROM schedules 
        WHERE event_type = 'Study Session'
    """)
    rows = cursor.fetchall()
    conn.close()
    
    data = []
    for r in rows:
        duration = get_event_duration_hours(r['start_time'], r['end_time'])
        data.append({"Subject": r['subject'], "Hours": duration})
        
    if not data:
        return pd.DataFrame(columns=["Subject", "Hours"])
        
    df = pd.DataFrame(data)
    return df.groupby("Subject")["Hours"].sum().reset_index()

def get_weekly_productivity():
    """Calculates study session hours per day for the current week."""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.now()
    start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    end_of_week = (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT date, start_time, end_time FROM schedules 
        WHERE event_type = 'Study Session' AND date >= ? AND date <= ?
    """, (start_of_week, end_of_week))
    rows = cursor.fetchall()
    conn.close()
    
    # Initialize all week days
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_per_day = {day: 0.0 for day in week_days}
    
    for r in rows:
        dt = datetime.strptime(r['date'], "%Y-%m-%d")
        day_name = dt.strftime("%A")
        duration = get_event_duration_hours(r['start_time'], r['end_time'])
        hours_per_day[day_name] += duration
        
    df = pd.DataFrame(list(hours_per_day.items()), columns=["Day", "Hours"])
    return df

def get_exam_prep_progress():
    """Calculates progress of exams (completed vs pending)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, count(*) as count FROM schedules 
        WHERE event_type = 'Exam' 
        GROUP BY status
    """)
    rows = cursor.fetchall()
    conn.close()
    
    stats = {"Pending": 0, "Completed": 0}
    for r in rows:
        stats[r['status']] = r['count']
        
    return pd.DataFrame(list(stats.items()), columns=["Status", "Count"])

def get_assignment_completion_stats():
    """Calculates completion rate for assignments."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, count(*) as count FROM schedules 
        WHERE event_type = 'Assignment' 
        GROUP BY status
    """)
    rows = cursor.fetchall()
    conn.close()
    
    stats = {"Pending": 0, "Completed": 0}
    for r in rows:
        stats[r['status']] = r['count']
        
    return pd.DataFrame(list(stats.items()), columns=["Status", "Count"])
