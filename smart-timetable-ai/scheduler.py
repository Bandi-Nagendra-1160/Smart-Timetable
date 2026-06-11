from datetime import datetime, timedelta
import sqlite3
from utils.database_utils import get_connection, get_all_schedules

def parse_time(time_str):
    """Helper to parse 'HH:MM' string into a datetime.time object or time tuple for comparison."""
    return datetime.strptime(time_str, "%H:%M").time()

def time_to_minutes(time_str):
    """Converts a 'HH:MM' time string to minutes since midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def minutes_to_time_str(minutes):
    """Converts minutes since midnight to a 'HH:MM' string."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def check_overlap(start1, end1, start2, end2):
    """Checks if two time ranges (format: 'HH:MM') overlap."""
    s1 = time_to_minutes(start1)
    e1 = time_to_minutes(end1)
    s2 = time_to_minutes(start2)
    e2 = time_to_minutes(end2)
    
    return s1 < e2 and s2 < e1

def detect_conflicts(date, start_time, end_time, ignore_id=None):
    """
    Checks if a proposed schedule slot conflicts with any existing schedules on that date.
    Returns a list of conflicting schedule records (dicts).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM schedules WHERE date = ?"
    params = [date]
    if ignore_id is not None:
        query += " AND id != ?"
        params.append(ignore_id)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    conflicts = []
    for row in rows:
        existing = dict(row)
        if check_overlap(start_time, end_time, existing['start_time'], existing['end_time']):
            conflicts.append(existing)
            
    return conflicts

def find_free_slots(date, duration_hours, day_start="08:00", day_end="20:00"):
    """
    Finds available time slots of a given duration on a specific date.
    Returns a list of tuples: (start_time_str, end_time_str)
    """
    duration_minutes = int(duration_hours * 60)
    start_limit = time_to_minutes(day_start)
    end_limit = time_to_minutes(day_end)
    
    # Get all events on this date
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start_time, end_time FROM schedules 
        WHERE date = ? 
        ORDER BY start_time ASC
    """, (date,))
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Busy intervals in minutes
    busy_intervals = []
    for event in events:
        s = time_to_minutes(event['start_time'])
        e = time_to_minutes(event['end_time'])
        # Only consider events within our limit or overlapping it
        if e > start_limit and s < end_limit:
            busy_intervals.append((max(s, start_limit), min(e, end_limit)))
            
    # Find free slots in 30 minute increments
    free_slots = []
    current_time = start_limit
    
    while current_time + duration_minutes <= end_limit:
        candidate_start = current_time
        candidate_end = current_time + duration_minutes
        
        # Check if candidate overlaps with any busy interval
        overlap = False
        for bs, be in busy_intervals:
            if candidate_start < be and bs < candidate_end:
                overlap = True
                # Jump current_time to the end of this busy interval to skip checks
                current_time = be
                break
                
        if not overlap:
            free_slots.append((minutes_to_time_str(candidate_start), minutes_to_time_str(candidate_end)))
            # Move forward by 30 minutes to check the next possible slot
            current_time += 30
            
    return free_slots

def suggest_alternative_slots(date, duration_hours, max_days=3):
    """
    Finds alternative slots of a given duration starting from 'date' 
    for the next 'max_days' days.
    """
    suggestions = {}
    current_date = datetime.strptime(date, "%Y-%m-%d")
    
    for i in range(max_days):
        date_str = current_date.strftime("%Y-%m-%d")
        slots = find_free_slots(date_str, duration_hours)
        if slots:
            suggestions[date_str] = slots[:3]  # Return top 3 slots per day
        current_date += timedelta(days=1)
        
    return suggestions

def check_duplicate_event(subject, event_type, date, start_time, end_time):
    """Checks if an identical event already exists in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT count(*) FROM schedules 
        WHERE subject = ? AND event_type = ? AND date = ? AND start_time = ? AND end_time = ?
    """, (subject, event_type, date, start_time, end_time))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0