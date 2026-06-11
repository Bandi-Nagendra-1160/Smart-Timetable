import streamlit as st
import datetime
import sys
import os

# Add parent folder to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import add_schedule, add_reminder
from utils.notification_utils import inject_custom_css, show_conflict_warning, show_success_banner
from scheduler import detect_conflicts, suggest_alternative_slots, check_duplicate_event

st.set_page_config(page_title="Add Schedule - Smart Timetable AI", layout="centered")
inject_custom_css()

st.title("➕ Schedule an Event")

with st.form("schedule_form"):
    subject = st.text_input("Subject / Course Name", placeholder="e.g., Database Management Systems")
    
    col1, col2 = st.columns(2)
    with col1:
        event_type = st.selectbox(
            "Event Type",
            ["Class", "Exam", "Assignment", "Study Session"]
        )
    with col2:
        priority = st.selectbox(
            "Priority Level",
            ["High", "Medium", "Low"],
            index=1
        )
        
    col3, col4, col5 = st.columns(3)
    with col3:
        event_date = st.date_input("Date", datetime.date.today())
    with col4:
        start_time = st.time_input("Start Time", datetime.time(9, 0))
    with col5:
        end_time = st.time_input("End Time", datetime.time(10, 30))
        
    status = st.selectbox(
        "Initial Status",
        ["Pending", "Completed"],
        index=0
    )
    
    st.markdown("##### 🔔 Reminder Settings")
    col_rem1, col_rem2 = st.columns(2)
    with col_rem1:
        enable_reminder = st.checkbox("Set email/dashboard alert", value=True)
    with col_rem2:
        reminder_lead_time = st.selectbox(
            "Reminder Time Before Event",
            [
                "15 minutes",
                "30 minutes",
                "1 hour",
                "2 hours",
                "1 day"
            ],
            index=3
        )
        
    submitted = st.form_submit_button("Book Event")

if submitted:
    if not subject.strip():
        st.error("Please provide a Subject name.")
    elif start_time >= end_time:
        st.error("End Time must be after Start Time.")
    else:
        date_str = event_date.strftime("%Y-%m-%d")
        start_str = start_time.strftime("%H:%M")
        end_str = end_time.strftime("%H:%M")
        
        # 1. Check for Exact Duplicate
        if check_duplicate_event(subject, event_type, date_str, start_str, end_str):
            st.warning("This exact event is already scheduled. Duplicate prevented.")
        else:
            # 2. Conflict Detection
            conflicts = detect_conflicts(date_str, start_str, end_str)
            if conflicts:
                show_conflict_warning(conflicts)
                
                # Fetch alternatives
                # Calculate duration in hours
                duration_hours = ((end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute)) / 60.0
                alternatives = suggest_alternative_slots(date_str, duration_hours, max_days=3)
                
                if alternatives:
                    st.info("💡 **Here are some recommended alternative slots when you are free:**")
                    for alt_date, slots in alternatives.items():
                        if slots:
                            formatted_date = datetime.datetime.strptime(alt_date, "%Y-%m-%d").strftime("%A, %b %d")
                            slots_str = ", ".join([f"`{s[0]} - {s[1]}`" for s in slots])
                            st.write(f"- **{formatted_date}**: {slots_str}")
            else:
                # 3. Save to database
                schedule_id = add_schedule(
                    subject=subject,
                    event_type=event_type,
                    date=date_str,
                    start_time=start_str,
                    end_time=end_str,
                    priority=priority,
                    status=status
                )
                
                # 4. Handle reminder insertion
                if enable_reminder:
                    # Calculate reminder date-time
                    event_dt = datetime.datetime.combine(event_date, start_time)
                    lead_deltas = {
                        "15 minutes": datetime.timedelta(minutes=15),
                        "30 minutes": datetime.timedelta(minutes=30),
                        "1 hour": datetime.timedelta(hours=1),
                        "2 hours": datetime.timedelta(hours=2),
                        "1 day": datetime.timedelta(days=1)
                    }
                    rem_dt = event_dt - lead_deltas.get(reminder_lead_time, datetime.timedelta(hours=2))
                    rem_str = rem_dt.strftime("%Y-%m-%d %H:%M")
                    
                    # Add email and dashboard reminders
                    add_reminder(schedule_id, rem_str, "Email")
                    add_reminder(schedule_id, rem_str, "Dashboard")
                    
                show_success_banner(f"Successfully scheduled '{subject}' on {date_str} at {start_str}!")
                st.balloons()