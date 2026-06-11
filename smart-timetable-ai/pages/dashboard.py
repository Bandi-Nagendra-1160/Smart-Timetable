import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

try:
    import plotly.express as px
    has_plotly = True
except ImportError:
    has_plotly = False

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_all_schedules, get_all_reminders
from utils.notification_utils import inject_custom_css
from analytics import (
    get_dashboard_metrics, get_subject_wise_study_time, get_weekly_productivity,
    get_exam_prep_progress, get_assignment_completion_stats
)

st.set_page_config(page_title="Dashboard - Smart Timetable AI", layout="wide")
inject_custom_css()

st.title("📊 Timetable Dashboard")

# Load metrics
metrics = get_dashboard_metrics()

# Display Metrics Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Classes", value=metrics["total_classes"])
with col2:
    st.metric(label="Upcoming Exams", value=metrics["upcoming_exams"])
with col3:
    st.metric(label="Pending Assignments", value=metrics["pending_assignments"])
with col4:
    st.metric(label="Study Hours This Week", value=f"{metrics['total_study_hours']} hrs")

st.markdown("---")

# Main content: Left = Schedule & Reminders, Right = Visual Analytics
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📅 Today's Schedule")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Query today's schedules
    today_schedules = get_all_schedules(filters={"date": today_str})
    
    if today_schedules.empty:
        st.info("No events scheduled for today. Time to relax or schedule a study session!")
    else:
        for _, row in today_schedules.iterrows():
            # Style cards based on priority and type
            priority_color = {
                "High": "#dc3545",
                "Medium": "#ffc107",
                "Low": "#28a745"
            }.get(row['priority'], "#6c757d")
            
            event_icon = {
                "Class": "🏫",
                "Exam": "📝",
                "Assignment": "⏳",
                "Study Session": "📚"
            }.get(row['event_type'], "📅")
            
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.03); 
                border-left: 5px solid {priority_color}; 
                border-radius: 8px; 
                padding: 12px 18px; 
                margin-bottom: 12px;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 1.1rem;">{event_icon} {row['subject']}</strong>
                    <span class="badge-{"pending" if row['status'] == "Pending" else "completed"}">{row['status']}</span>
                </div>
                <div style="margin-top: 5px; font-size: 0.9rem; opacity: 0.8;">
                    ⏱️ {row['start_time']} - {row['end_time']} | Priority: <span style="color: {priority_color}; font-weight: bold;">{row['priority']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    
    st.subheader("🔔 Upcoming Reminders")
    # Fetch active reminders (unsent reminders for future times)
    reminders = get_all_reminders()
    if not reminders.empty:
        pending_reminders = reminders[reminders['sent_status'] == 0].head(5)
    else:
        pending_reminders = pd.DataFrame()
        
    if pending_reminders.empty:
        st.info("No pending reminders.")
    else:
        for _, row in pending_reminders.iterrows():
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.02); 
                border: 1px solid rgba(255, 255, 255, 0.05); 
                border-radius: 8px; 
                padding: 10px 15px; 
                margin-bottom: 10px;
            ">
                <strong>🔔 {row['subject']} ({row['event_type']})</strong><br>
                <span style="font-size: 0.85rem; opacity: 0.7;">
                    Trigger Time: {row['reminder_time']} | Method: {row['notification_type']}
                </span>
            </div>
            """, unsafe_allow_html=True)

with right_col:
    st.subheader("📊 Study & Progress Analytics")
    
    # Tabs for analytics categories
    tab1, tab2 = st.tabs(["📚 Study Analysis", "🏆 Course Progress"])
    
    with tab1:
        # Subject-wise study hours
        st.markdown("#### Study Hours per Subject")
        subject_study = get_subject_wise_study_time()
        if subject_study.empty:
            st.info("No study sessions recorded yet. Start booking study hours!")
        else:
            if has_plotly:
                fig_sub = px.bar(
                    subject_study,
                    x="Subject",
                    y="Hours",
                    color="Subject",
                    title="Subject-wise Study Time (Hours)",
                    template="plotly_dark"
                )
                fig_sub.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_sub, use_container_width=True)
            else:
                st.bar_chart(subject_study.set_index("Subject"))
            
        # Weekly productivity
        st.markdown("#### Weekly Study Productivity")
        weekly_prod = get_weekly_productivity()
        if has_plotly:
            fig_week = px.line(
                weekly_prod,
                x="Day",
                y="Hours",
                title="Weekly Study Activity (Hours/Day)",
                markers=True,
                template="plotly_dark"
            )
            fig_week.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            fig_week.update_traces(line_color='#2a5298', line_width=3)
            st.plotly_chart(fig_week, use_container_width=True)
        else:
            st.line_chart(weekly_prod.set_index("Day"))
        
    with tab2:
        col_progress1, col_progress2 = st.columns(2)
        
        with col_progress1:
            st.markdown("#### Exam Preparation")
            exam_stats = get_exam_prep_progress()
            if exam_stats["Count"].sum() == 0:
                st.info("No exams scheduled.")
            else:
                if has_plotly:
                    fig_exam = px.pie(
                        exam_stats,
                        values="Count",
                        names="Status",
                        color="Status",
                        color_discrete_map={"Pending": "#ffc107", "Completed": "#28a745"},
                        title="Exams Status",
                        hole=0.4,
                        template="plotly_dark"
                    )
                    fig_exam.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    st.plotly_chart(fig_exam, use_container_width=True)
                else:
                    st.dataframe(exam_stats.set_index("Status"), use_container_width=True)
                
        with col_progress2:
            st.markdown("#### Assignment Completion")
            ass_stats = get_assignment_completion_stats()
            if ass_stats["Count"].sum() == 0:
                st.info("No assignments scheduled.")
            else:
                if has_plotly:
                    fig_ass = px.pie(
                        ass_stats,
                        values="Count",
                        names="Status",
                        color="Status",
                        color_discrete_map={"Pending": "#dc3545", "Completed": "#28a745"},
                        title="Assignments",
                        hole=0.4,
                        template="plotly_dark"
                    )
                    fig_ass.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    st.plotly_chart(fig_ass, use_container_width=True)
                else:
                    st.dataframe(ass_stats.set_index("Status"), use_container_width=True)
