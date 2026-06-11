import streamlit as st
import datetime
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_all_schedules, add_reminder, get_all_reminders, get_user, update_user
from utils.notification_utils import inject_custom_css, show_success_banner, show_toast_notification
from reminder import check_and_trigger_reminders
import config

st.set_page_config(page_title="Reminders - Smart Timetable AI", layout="wide")
inject_custom_css()

st.title("🔔 Reminder Center")

col_left, col_right = st.columns([1, 1])

# Left column: Configuration & Trigger
with col_left:
    st.subheader("👤 User Configuration")
    user_info = get_user()
    
    if user_info:
        with st.form("user_config_form"):
            new_name = st.text_input("Student Name", value=user_info["name"])
            new_email = st.text_input("Notification Email (SMTP Recipient)", value=user_info["email"])
            save_user = st.form_submit_button("Update User Profile")
            
            if save_user:
                if not new_name.strip() or not new_email.strip():
                    st.error("Fields cannot be empty.")
                else:
                    update_user(new_name, new_email)
                    st.success("User profile updated!")
                    st.rerun()
                    
    st.markdown("---")
    
    st.subheader("⚙️ SMTP Email Server Settings")
    st.markdown(f"""
    - **SMTP Server**: `{config.SMTP_SERVER}`
    - **Port**: `{config.SMTP_PORT}`
    - **Sender Account**: `{config.SMTP_EMAIL}`
    - **App Password Status**: `{'Configured' if config.SMTP_PASSWORD else 'Not Configured'}`
    """)
    st.caption("Change these settings by updating the environment variables or the `.env` file in the project folder.")
    
    st.markdown("---")
    
    st.subheader("⚡ Manual Engine Trigger")
    st.write("Force check pending reminders and trigger emails immediately:")
    
    if st.button("🚀 Trigger Reminder Check"):
        try:
            triggered = check_and_trigger_reminders()
            if triggered:
                st.success(f"Successfully processed {len(triggered)} reminders!")
                for t in triggered:
                    st.write(f"- Sent email for **{t['subject']}** to `{t['user_email']}`")
                show_toast_notification("Reminders triggered successfully!")
            else:
                st.info("No reminders are currently due. Check the schedule list to verify your timing.")
        except Exception as e:
            st.error(f"Error executing engine check: {e}")

# Right column: Create Custom Reminder
with col_right:
    st.subheader("➕ Create Custom Event Reminder")
    
    schedules_df = get_all_schedules()
    if schedules_df.empty:
        st.info("No events scheduled. Add an event before assigning reminders.")
    else:
        # Build event dropdown list
        events_list = []
        for _, row in schedules_df.iterrows():
            events_list.append(f"ID: {row['id']} | {row['subject']} ({row['date']} {row['start_time']})")
            
        with st.form("custom_reminder_form"):
            selected_event = st.selectbox("Select Event", options=events_list)
            event_id = int(selected_event.split(" | ")[0].split(": ")[1])
            
            col_d, col_t = st.columns(2)
            with col_d:
                rem_date = st.date_input("Reminder Date", datetime.date.today())
            with col_t:
                rem_time = st.time_input("Reminder Time", datetime.time(9, 0))
                
            rem_type = st.selectbox("Notification Channel", ["Email", "Dashboard"])
            
            submit_reminder = st.form_submit_button("Save Reminder")
            
            if submit_reminder:
                rem_dt_str = f"{rem_date.strftime('%Y-%m-%d')} {rem_time.strftime('%H:%M')}"
                add_reminder(event_id, rem_dt_str, rem_type)
                st.success(f"Reminder registered for {rem_dt_str}!")
                st.rerun()

st.markdown("---")

# Bottom section: View Reminders History & Logs
st.subheader("📋 Reminder Logs")
reminders_df = get_all_reminders()

if reminders_df.empty:
    st.info("No reminders configured yet.")
else:
    tab_p, tab_s = st.tabs(["⏳ Pending Reminders", "✅ Sent Reminders"])
    
    with tab_p:
        pending = reminders_df[reminders_df["sent_status"] == 0]
        if pending.empty:
            st.caption("No pending reminders.")
        else:
            st.dataframe(
                pending[["id", "subject", "event_type", "date", "reminder_time", "notification_type"]],
                use_container_width=True,
                hide_index=True
            )
            
    with tab_s:
        sent = reminders_df[reminders_df["sent_status"] == 1]
        if sent.empty:
            st.caption("No reminders sent yet.")
        else:
            st.dataframe(
                sent[["id", "subject", "event_type", "date", "reminder_time", "notification_type"]],
                use_container_width=True,
                hide_index=True
            )
