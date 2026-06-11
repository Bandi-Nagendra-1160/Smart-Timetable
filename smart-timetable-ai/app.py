import streamlit as st
import sys
import os
from datetime import datetime

# Add root folder to python path to avoid import errors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database_utils import init_db, get_user
from database import seed_database
from utils.notification_utils import inject_custom_css
from reminder import check_and_trigger_reminders

# Page Configuration
st.set_page_config(
    page_title="Smart Timetable Assistant AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern custom styling
inject_custom_css()

# Auto-initialize and seed database on first launch
try:
    seed_database()
except Exception as e:
    st.error(f"Error seeding database: {e}")

# Run background reminder engine to trigger any pending notifications immediately
try:
    triggered = check_and_trigger_reminders()
    if triggered:
        st.toast(f"🔔 Triggered {len(triggered)} email reminders!", icon="🚀")
except Exception as e:
    print(f"Error checking reminders: {e}")

# Hero Section
st.markdown("""
<div class="hero-banner">
    <h1 style="margin:0; font-size:2.8rem; font-weight:700;">🤖 Smart Timetable Assistant AI</h1>
    <p style="margin:10px 0 0 0; font-size:1.2rem; opacity:0.9;">
        Empower your academic journey with an Agentic AI planner that organizes classes, tracks assignments, 
        schedules study sessions, detects conflicts, and syncs to Google Calendar.
    </p>
</div>
""", unsafe_allow_html=True)

# Main columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🌟 Features at a Glance")
    
    st.markdown("""
    - **📊 Interactive Dashboard**: Keep track of your academic metrics (classes, exam deadlines, and study session progress).
    - **🤖 Agentic AI Chat**: Book and manage your schedule using natural English. Let the AI find free slots, resolve conflicts, and plan your study time.
    - **📅 Multi-View Timetable**: Filter and browse classes in beautiful daily, weekly, and monthly timetable calendars.
    - **⚡ Conflict Detection Engine**: Real-time warnings when scheduling overlapping sessions, with automatic recommendation of free slots.
    - **📅 Google Calendar Sync**: Export your timetable as standard `.ics` calendar files, or sync them with Google.
    - **📧 SMTP Email Reminders**: Send automated alerts for exams and assignment deadlines directly to your email.
    """)
    
    st.markdown("### 🚀 Quick Start Commands (Chatbot Page)")
    st.info("""
    Try typing these in the **AI Chatbot** sidebar page:
    - *"Find 2 free hours tomorrow afternoon"*
    - *"Schedule Software Engineering revision for 1.5 hours on Friday"*
    - *"Plan study sessions for my upcoming DBMS Exam"*
    - *"Move event ID 3 to Saturday at 10:00 AM"*
    """)

with col2:
    st.subheader("👤 Student Profile")
    
    user_info = get_user()
    if user_info:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding:20px; border-radius:12px;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">NAME</p>
            <h4 style="margin: 0 0 15px 0; color: #90caf9;">{user_info['name']}</h4>
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">REGISTERED EMAIL</p>
            <h4 style="margin: 0; color: #90caf9;">{user_info['email']}</h4>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No user profile initialized.")
        
    st.markdown("---")
    st.subheader("📅 Today is")
    st.write(f"**{datetime.now().strftime('%A, %B %d, %Y')}**")
    
    # Add navigation guidance
    st.markdown("### 👈 Get Started")
    st.caption("Use the sidebar navigation on the left to explore features, view your calendar, add events, plan your exams, or speak to the AI assistant.")