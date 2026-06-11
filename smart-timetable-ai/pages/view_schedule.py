import streamlit as st
import pandas as pd
import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_all_schedules, delete_schedule, update_schedule, get_schedule_by_id
from utils.notification_utils import inject_custom_css, show_success_banner, show_toast_notification
from utils.calendar_utils import export_to_ics, import_from_ics, mock_sync_google_calendar

st.set_page_config(page_title="Timetable View - Smart Timetable AI", layout="wide")
inject_custom_css()

st.title("📅 Academic Timetable")

# Get schedules
schedules_df = get_all_schedules()

# Actions (Sync & Import/Export) in expandable menu
with st.sidebar:
    st.header("⚙️ Timetable Actions")
    
    # 1. Google Calendar Mock Sync
    if st.button("🔄 Sync with Google Calendar"):
        sync_res = mock_sync_google_calendar()
        if sync_res["success"]:
            st.success(sync_res["message"])
            show_toast_notification("Google Calendar Synced!")
            
    st.markdown("---")
    
    # 2. Export to .ics
    if not schedules_df.empty:
        ics_data = export_to_ics(schedules_df)
        st.download_button(
            label="📥 Export Timetable (.ics)",
            data=ics_data,
            file_name="academic_timetable.ics",
            mime="text/calendar",
            help="Download as standard iCalendar file to import into Google Calendar or Outlook"
        )
    else:
        st.caption("No events to export.")
        
    st.markdown("---")
    
    # 3. Import from .ics
    st.subheader("📤 Import Calendar")
    uploaded_file = st.file_uploader("Upload .ics file", type=["ics"])
    if uploaded_file is not None:
        ics_text = uploaded_file.read().decode("utf-8")
        imported_count = import_from_ics(ics_text)
        if imported_count > 0:
            st.success(f"Successfully imported {imported_count} events!")
            st.rerun()
        else:
            st.warning("No new events could be parsed or imported.")

# Main Timetable Views
if schedules_df.empty:
    st.info("Your timetable is empty. Add schedules via 'Add Schedule' page or use the AI Chatbot!")
else:
    # Event Filtering
    st.subheader("🔍 Filter Timetable")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        f_type = st.multiselect("Event Type", options=["Class", "Exam", "Assignment", "Study Session"], default=[])
    with col_f2:
        f_priority = st.multiselect("Priority", options=["High", "Medium", "Low"], default=[])
    with col_f3:
        f_search = st.text_input("Search Course Name", "")
        
    # Apply filters to working dataframe
    filtered_df = schedules_df.copy()
    if f_type:
        filtered_df = filtered_df[filtered_df['event_type'].isin(f_type)]
    if f_priority:
        filtered_df = filtered_df[filtered_df['priority'].isin(f_priority)]
    if f_search:
        filtered_df = filtered_df[filtered_df['subject'].str.contains(f_search, case=False)]
        
    tab_list, tab_daily, tab_weekly, tab_monthly, tab_manage = st.tabs([
        "📋 List View", "☀️ Daily View", "📅 Weekly View", "🗓️ Monthly View", "⚙️ Manage Events"
    ])
    
    # 1. LIST VIEW
    with tab_list:
        if filtered_df.empty:
            st.caption("No events match current filter criteria.")
        else:
            # Color priority strings for display
            display_df = filtered_df.copy()
            st.dataframe(
                display_df[["id", "date", "start_time", "end_time", "subject", "event_type", "priority", "status"]],
                use_container_width=True,
                hide_index=True
            )
            
    # 2. DAILY VIEW
    with tab_daily:
        selected_date = st.date_input("Select Date for Daily View", datetime.date.today())
        date_str = selected_date.strftime("%Y-%m-%d")
        day_events = filtered_df[filtered_df['date'] == date_str]
        
        if day_events.empty:
            st.info(f"No events scheduled on {selected_date.strftime('%A, %b %d, %Y')}.")
        else:
            st.markdown(f"#### Timetable for {selected_date.strftime('%A, %B %d, %Y')}")
            for _, row in day_events.iterrows():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid {'#dc3545' if row['priority']=='High' else '#ffc107' if row['priority']=='Medium' else '#28a745'};">
                    <strong>{row['start_time']} - {row['end_time']}</strong> | {row['subject']} ({row['event_type']}) <br>
                    <span style="font-size: 0.85rem; opacity:0.7;">Priority: {row['priority']} | Status: {row['status']}</span>
                </div>
                """, unsafe_allow_html=True)
                
    # 3. WEEKLY VIEW
    with tab_weekly:
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        
        st.markdown(f"#### Week of {start_of_week.strftime('%B %d, %Y')}")
        
        week_days = []
        for i in range(7):
            day = start_of_week + datetime.timedelta(days=i)
            week_days.append(day)
            
        cols = st.columns(7)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, col in enumerate(cols):
            day_str = week_days[i].strftime("%Y-%m-%d")
            day_events = filtered_df[filtered_df['date'] == day_str]
            
            with col:
                st.markdown(f"""
                <div style="text-align: center; background: rgba(30, 60, 114, 0.2); padding: 8px; border-radius: 6px; margin-bottom: 10px;">
                    <strong>{day_names[i][:3]}</strong><br>
                    <small>{week_days[i].strftime('%d/%m')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if day_events.empty:
                    st.caption("Free")
                else:
                    for _, row in day_events.iterrows():
                        color = '#dc3545' if row['priority']=='High' else '#ffc107' if row['priority']=='Medium' else '#28a745'
                        st.markdown(f"""
                        <div style="
                            background: rgba(255,255,255,0.03); 
                            border-left: 3px solid {color}; 
                            padding: 6px; 
                            border-radius: 4px; 
                            margin-bottom: 6px; 
                            font-size: 0.8rem;
                            line-height: 1.2;
                        ">
                            <strong>{row['start_time']}</strong><br>
                            {row['subject'][:15]}...<br>
                            <small>({row['event_type'][:5]}.)</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
    # 4. MONTHLY VIEW
    with tab_monthly:
        # Show events grouped by week/date in a compact grid
        today_date = datetime.date.today()
        st.markdown(f"#### Calendar for {today_date.strftime('%B %Y')}")
        
        # Group filtered events by day and list them
        month_events = filtered_df[filtered_df['date'].str.startswith(today_date.strftime("%Y-%m"))]
        if month_events.empty:
            st.info("No events scheduled this month.")
        else:
            monthly_summary = month_events.groupby('date').size().reset_index(name='count')
            st.write("Days with scheduled activities this month:")
            for _, row in monthly_summary.iterrows():
                dt = datetime.datetime.strptime(row['date'], "%Y-%m-%d").strftime("%A, %b %d")
                st.write(f"- **{dt}**: {row['count']} event(s)")
                
    # 5. MANAGE EVENTS (EDIT & DELETE)
    with tab_manage:
        st.subheader("✏️ Edit or Delete Events")
        
        selected_id = st.selectbox(
            "Select Event ID to modify",
            options=filtered_df["id"].tolist(),
            format_func=lambda x: f"ID: {x} - {filtered_df[filtered_df['id']==x]['subject'].values[0]} ({filtered_df[filtered_df['id']==x]['date'].values[0]})"
        )
        
        if selected_id:
            event = get_schedule_by_id(selected_id)
            if event:
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    # Update status directly
                    new_status = st.selectbox("Update Status", ["Pending", "Completed"], index=0 if event['status'] == "Pending" else 1)
                    if st.button("💾 Save Status Update"):
                        update_schedule(
                            event['id'], event['subject'], event['event_type'], 
                            event['date'], event['start_time'], event['end_time'], 
                            event['priority'], new_status
                        )
                        st.success("Event status updated!")
                        st.rerun()
                        
                with col_e2:
                    # Delete event
                    st.warning("Deletions are permanent and clear all reminders.")
                    if st.button("🗑️ Delete Event"):
                        delete_schedule(selected_id)
                        st.success("Event deleted from timetable.")
                        st.rerun()