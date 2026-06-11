import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from config import DATABASE_PATH, DEFAULT_USER_NAME, DEFAULT_USER_EMAIL

def get_connection():
    """Returns a connection to the SQLite database. Creates parent directories if missing."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE
    )
    """)
    
    # 2. Schedules Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        event_type TEXT NOT NULL, -- 'Class', 'Exam', 'Assignment', 'Study Session'
        date TEXT NOT NULL,       -- 'YYYY-MM-DD'
        start_time TEXT NOT NULL, -- 'HH:MM'
        end_time TEXT NOT NULL,   -- 'HH:MM'
        priority TEXT NOT NULL,   -- 'High', 'Medium', 'Low'
        status TEXT NOT NULL      -- 'Pending', 'Completed'
    )
    """)
    
    # 3. Reminders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER NOT NULL,
        reminder_time TEXT NOT NULL,     -- 'YYYY-MM-DD HH:MM'
        notification_type TEXT NOT NULL, -- 'Email', 'Dashboard'
        sent_status INTEGER DEFAULT 0,    -- 0 = Pending, 1 = Sent
        FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE
    )
    """)
    
    # Insert default user if not exists
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (DEFAULT_USER_NAME, DEFAULT_USER_EMAIL))
    
    conn.commit()
    conn.close()

def add_schedule(subject, event_type, date, start_time, end_time, priority="Medium", status="Pending"):
    """Inserts a new schedule and returns its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO schedules (subject, event_type, date, start_time, end_time, priority, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (subject, event_type, date, start_time, end_time, priority, status))
    schedule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return schedule_id

def get_all_schedules(filters=None):
    """Retrieves schedules optionally filtered by criteria (e.g. date, event_type)."""
    conn = get_connection()
    query = "SELECT * FROM schedules WHERE 1=1"
    params = []
    
    if filters:
        if 'date' in filters and filters['date']:
            query += " AND date = ?"
            params.append(filters['date'])
        if 'event_type' in filters and filters['event_type']:
            query += " AND event_type = ?"
            params.append(filters['event_type'])
        if 'subject' in filters and filters['subject']:
            query += " AND subject LIKE ?"
            params.append(f"%{filters['subject']}%")
            
    query += " ORDER BY date ASC, start_time ASC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_schedule_by_id(schedule_id):
    """Retrieves a single schedule event by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_schedule(schedule_id, subject, event_type, date, start_time, end_time, priority, status):
    """Updates an existing schedule by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE schedules 
    SET subject = ?, event_type = ?, date = ?, start_time = ?, end_time = ?, priority = ?, status = ?
    WHERE id = ?
    """, (subject, event_type, date, start_time, end_time, priority, status, schedule_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_schedule(schedule_id):
    """Deletes a schedule by its ID and cleans up its reminders."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE schedule_id = ?", (schedule_id,))
    cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def add_reminder(schedule_id, reminder_time, notification_type="Email"):
    """Adds a reminder for a schedule event."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reminders (schedule_id, reminder_time, notification_type, sent_status)
    VALUES (?, ?, ?, 0)
    """, (schedule_id, reminder_time, notification_type))
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id

def get_all_reminders(include_details=True):
    """Gets all reminders, optionally with schedule details joined."""
    conn = get_connection()
    if include_details:
        query = """
        SELECT r.*, s.subject, s.event_type, s.date, s.start_time, s.end_time 
        FROM reminders r
        JOIN schedules s ON r.schedule_id = s.id
        ORDER BY r.reminder_time ASC
        """
    else:
        query = "SELECT * FROM reminders ORDER BY reminder_time ASC"
        
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_pending_reminders():
    """Gets reminders that are due but have not been sent yet."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
    SELECT r.*, s.subject, s.event_type, s.date, s.start_time, s.end_time, u.email as user_email, u.name as user_name
    FROM reminders r
    JOIN schedules s ON r.schedule_id = s.id
    CROSS JOIN users u -- assuming single default user for simplicity
    WHERE r.sent_status = 0 AND r.reminder_time <= ?
    """, (now_str,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_reminder_sent(reminder_id):
    """Marks a reminder as sent."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET sent_status = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def get_user():
    """Retrieves the single user for this local deployment."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user(name, email):
    """Updates the user credentials."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = ?, email = ? WHERE id = (SELECT id FROM users LIMIT 1)", (name, email))
    conn.commit()
    conn.close()
