import streamlit as st
import datetime
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_all_schedules, add_schedule
from utils.notification_utils import inject_custom_css, show_success_banner
from scheduler import find_free_slots, detect_conflicts

# Try importing the AI agent component
try:
    from ai_agent import generate_study_plan_tool
    has_dependencies = True
    import_error_msg = ""
except ImportError as e:
    has_dependencies = False
    import_error_msg = str(e)

st.set_page_config(page_title="Smart Study Planner - Smart Timetable AI", layout="wide")
inject_custom_css()

if not has_dependencies:
    st.error(
        "❌ **Missing Dependencies**: The required AI Agent or LangChain packages are not installed in your active Python environment.\n\n"
        f"**Error details**: {import_error_msg}\n\n"
        f"Your current Python interpreter is: `{sys.executable}`\n\n"
        "To resolve this, open your terminal and run:\n"
        "```bash\n"
        "pip install langchain langchain-core langchain-community langchain-google-genai python-dotenv plotly\n"
        "```\n"
        "Or activate your virtual environment before launching Streamlit:\n"
        "```powershell\n"
        "venv\\Scripts\\activate\n"
        "pip install -r requirements.txt\n"
        "```"
    )
    st.stop()

st.title("🎯 Smart Study Planner")

# Load current schedule workload analysis
schedules_df = get_all_schedules()

col_intro, col_stats = st.columns([2, 1])

with col_intro:
    st.markdown("""
    The **Smart Study Planner** analyzes your current course load, detects upcoming exams, 
    and automatically balances your schedule. It schedules study blocks around your existing classes and assignments 
    to ensure you are prepared for your exams.
    """)
    
    st.info("💡 **Planning Tip**: High-priority exams should have at least 4-6 hours of scheduled study blocks spread across the preceding week.")

# 1. Workload Analysis
with col_stats:
    st.subheader("📊 Workload Analysis")
    if schedules_df.empty:
        st.write("No active classes or exams to analyze.")
    else:
        # Calculate active hours filled
        classes_count = len(schedules_df[schedules_df["event_type"] == "Class"])
        exams_count = len(schedules_df[(schedules_df["event_type"] == "Exam") & (schedules_df["status"] == "Pending")])
        study_sessions_count = len(schedules_df[schedules_df["event_type"] == "Study Session"])
        
        st.write(f"- 🏫 **Scheduled Classes**: {classes_count}")
        st.write(f"- 📝 **Pending Exams**: {exams_count}")
        st.write(f"- 📚 **Planned Study Blocks**: {study_sessions_count}")

st.markdown("---")

# 2. Planning Form
st.subheader("📅 Schedule Study Blocks for an Exam")

# Get list of pending exams for selection
exams_list = []
if not schedules_df.empty:
    exams_df = schedules_df[(schedules_df["event_type"] == "Exam") & (schedules_df["status"] == "Pending")]
    for _, row in exams_df.iterrows():
        exams_list.append(f"{row['subject']} (Exam Date: {row['date']})")

with st.form("planner_form"):
    st.write("Configure the study planner parameters to generate balanced sessions.")
    
    col1, col2 = st.columns(2)
    with col1:
        if exams_list:
            selected_exam = st.selectbox("Select Upcoming Exam", options=exams_list)
            # Parse subject and date from selection
            subject_selected = selected_exam.split(" (Exam Date:")[0]
            exam_date_str = selected_exam.split(" (Exam Date: ")[1][:-1]
            exam_date = datetime.datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        else:
            selected_exam = None
            subject_selected = st.text_input("Enter Subject Name manually", placeholder="e.g., DBMS")
            exam_date = st.date_input("Exam Date", datetime.date.today() + datetime.timedelta(days=7))
            exam_date_str = exam_date.strftime("%Y-%m-%d")
            
    with col2:
        total_hours = st.slider("Total Study Hours to Schedule", min_value=2, max_value=12, value=4, step=2)
        
    submitted = st.form_submit_button("⚡ Auto-Generate Study Plan")

if submitted:
    if not subject_selected.strip():
        st.error("Please provide a subject name to plan study sessions.")
    elif exam_date <= datetime.date.today():
        st.error("Exam date must be in the future to plan study sessions.")
    else:
        # Use our LangChain agentic tool's logic directly to update database
        st.write("🔍 Running study planner tool... searching for free slots...")
        
        # Invoke generate_study_plan_tool function directly
        result_message = generate_study_plan_tool.run({
            "subject": subject_selected,
            "exam_date": exam_date_str,
            "total_study_hours": float(total_hours)
        })
        
        if "Successfully" in result_message or "Partially" in result_message:
            st.success(result_message)
            st.balloons()
        else:
            st.warning(result_message)

st.markdown("---")

# 3. AI-Powered Subject Balancing Recommendations
st.subheader("💡 Smart Recommendations")

today_str = datetime.date.today().strftime("%Y-%m-%d")
upcoming_exams_df = pd.DataFrame()
if not schedules_df.empty:
    upcoming_exams_df = schedules_df[(schedules_df["event_type"] == "Exam") & (schedules_df["date"] >= today_str) & (schedules_df["status"] == "Pending")]

if upcoming_exams_df.empty:
    st.info("No upcoming exams found. Add an exam using the 'Add Schedule' page to get tailored study suggestions!")
else:
    for _, exam in upcoming_exams_df.iterrows():
        exam_date_obj = datetime.datetime.strptime(exam['date'], "%Y-%m-%d").date()
        days_left = (exam_date_obj - datetime.date.today()).days
        
        # Check if study sessions already exist for this exam subject
        related_study = schedules_df[
            (schedules_df["event_type"] == "Study Session") & 
            (schedules_df["subject"].str.contains(exam['subject'], case=False))
        ]
        total_study_time = len(related_study) * 2.0  # Assumes 2 hour blocks
        
        # Suggest status
        if days_left <= 3 and total_study_time < 4.0:
            st.warning(
                f"🚨 **High Urgency**: Your **{exam['subject']} Exam** is in **{days_left} days** (Date: {exam['date']}). "
                f"You only have {total_study_time} hours of study sessions booked. "
                f"We recommend scheduling at least {max(0.0, 6.0 - total_study_time)} more hours of preparation."
            )
        elif days_left <= 7 and total_study_time < 2.0:
            st.info(
                f"📅 **Preparation Alert**: The **{exam['subject']} Exam** is in **{days_left} days**. "
                f"Consider scheduling 4 hours of revision sessions over this week."
            )
        else:
            st.success(
                f"✅ **On Track**: Your preparation for **{exam['subject']}** (in {days_left} days) is looking good with "
                f"{total_study_time} hours of planned revision sessions."
            )
