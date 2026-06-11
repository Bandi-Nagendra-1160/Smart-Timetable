import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Add root folder to python path to avoid import errors when running directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from utils.database_utils import (
    get_connection, add_schedule, get_all_schedules, get_schedule_by_id, 
    update_schedule, delete_schedule
)
from scheduler import detect_conflicts, find_free_slots, suggest_alternative_slots

# Import LangChain libraries with elegant fallback error messages
try:
    from langchain_core.tools import tool
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError as e:
    missing_module = e.name if hasattr(e, 'name') else "LangChain core packages"
    raise ImportError(
        f"\n\n❌ [Smart Timetable Assistant Error] Missing dependency: '{missing_module}'\n"
        f"Your current Python interpreter ({sys.executable}) does not have this package installed.\n"
        "To fix this, please:\n"
        "  1. Activate the local virtual environment:\n"
        "     venv\\Scripts\\activate\n"
        "  2. Install all required packages:\n"
        "     pip install -r requirements.txt\n"
        "Or install it directly on your system Python environment:\n"
        "  pip install langchain langchain-core langchain-community langchain-google-genai python-dotenv plotly\n"
    ) from e

# Define the LangChain Tools with clear docstrings so the agent knows when to use them.

@tool
def read_schedule_tool(date: Optional[str] = None, subject: Optional[str] = None, event_type: Optional[str] = None):
    """
    Reads the student's existing timetable.
    You can optionally filter by a specific date (format: 'YYYY-MM-DD'),
    a subject name (e.g., 'DBMS'), or event type ('Class', 'Exam', 'Assignment', 'Study Session').
    Returns a textual list of schedule events.
    """
    filters = {}
    if date:
        filters['date'] = date
    if subject:
        filters['subject'] = subject
    if event_type:
        filters['event_type'] = event_type
        
    df = get_all_schedules(filters)
    if df.empty:
        return "No schedules found matching the filters."
        
    lines = []
    for _, row in df.iterrows():
        status_symbol = "✅" if row['status'] == "Completed" else "⏳"
        lines.append(
            f"ID: {row['id']} | {row['date']} {row['start_time']}-{row['end_time']} | "
            f"{row['subject']} ({row['event_type']}) | Priority: {row['priority']} | Status: {status_symbol} {row['status']}"
        )
    return "\n".join(lines)

@tool
def create_schedule_tool(
    subject: str, 
    event_type: str, 
    date: str, 
    start_time: str, 
    end_time: str, 
    priority: str = "Medium", 
    status: str = "Pending"
):
    """
    Creates a new schedule event. 
    Arguments:
    - subject: Name of the class, exam, assignment, or study session
    - event_type: Must be 'Class', 'Exam', 'Assignment', or 'Study Session'
    - date: YYYY-MM-DD format
    - start_time: HH:MM format
    - end_time: HH:MM format
    - priority: Optional, 'High', 'Medium', or 'Low' (defaults to Medium)
    - status: Optional, 'Pending' or 'Completed' (defaults to Pending)
    
    Before scheduling, this tool automatically checks for overlaps and database duplication.
    """
    # 1. Clean event type
    valid_types = ['Class', 'Exam', 'Assignment', 'Study Session']
    if event_type not in valid_types:
        # Try to match case-insensitively or return warning
        matched = [t for t in valid_types if t.lower() == event_type.lower()]
        if matched:
            event_type = matched[0]
        else:
            return f"Invalid event_type '{event_type}'. Must be one of {valid_types}."

    # 2. Check conflicts
    conflicts = detect_conflicts(date, start_time, end_time)
    if conflicts:
        conflict_details = []
        for c in conflicts:
            conflict_details.append(f"'{c['subject']}' ({c['event_type']}) scheduled at {c['start_time']}-{c['end_time']}")
        
        # Search for alternative slots on the same day
        alt_slots = find_free_slots(date, 2.0) # default 2 hours
        alt_str = ""
        if alt_slots:
            alt_str = "\nSuggested alternative free slots today:\n" + "\n".join([f"- {s[0]} to {s[1]}" for s in alt_slots[:3]])
        else:
            alt_str = "\nNo alternative free 2-hour slots found on this day."
            
        return (
            f"Conflict detected on {date}! The slot {start_time}-{end_time} overlaps with: "
            f"{', '.join(conflict_details)}.{alt_str}"
        )

    # 3. Add to DB
    try:
        schedule_id = add_schedule(subject, event_type, date, start_time, end_time, priority, status)
        return (
            f"Successfully scheduled '{subject}' ({event_type}) on {date} "
            f"from {start_time} to {end_time} with {priority} priority. Assigned Event ID: {schedule_id}."
        )
    except Exception as e:
        return f"Failed to create schedule. Error: {str(e)}"

@tool
def update_schedule_tool(
    schedule_id: int, 
    subject: Optional[str] = None, 
    event_type: Optional[str] = None, 
    date: Optional[str] = None, 
    start_time: Optional[str] = None, 
    end_time: Optional[str] = None, 
    priority: Optional[str] = None, 
    status: Optional[str] = None
):
    """
    Updates details of an existing schedule event.
    Arguments:
    - schedule_id: The ID of the event to modify (Required)
    Provide only the properties you wish to modify. Other fields will remain unchanged.
    """
    existing = get_schedule_by_id(schedule_id)
    if not existing:
        return f"No schedule event found with ID {schedule_id}."
        
    # Merge existing and update parameters
    new_subject = subject if subject is not None else existing['subject']
    new_event_type = event_type if event_type is not None else existing['event_type']
    new_date = date if date is not None else existing['date']
    new_start_time = start_time if start_time is not None else existing['start_time']
    new_end_time = end_time if end_time is not None else existing['end_time']
    new_priority = priority if priority is not None else existing['priority']
    new_status = status if status is not None else existing['status']
    
    # Check conflicts if time or date is changing
    if date is not None or start_time is not None or end_time is not None:
        conflicts = detect_conflicts(new_date, new_start_time, new_end_time, ignore_id=schedule_id)
        if conflicts:
            conflict_details = []
            for c in conflicts:
                conflict_details.append(f"'{c['subject']}' ({c['event_type']}) at {c['start_time']}-{c['end_time']}")
            return f"Cannot reschedule! Overlaps on {new_date} with: {', '.join(conflict_details)}."
            
    success = update_schedule(
        schedule_id, new_subject, new_event_type, new_date, new_start_time, new_end_time, new_priority, new_status
    )
    if success:
        return f"Successfully updated schedule ID {schedule_id} to: {new_subject} on {new_date} from {new_start_time} to {new_end_time}."
    else:
        return f"Failed to update schedule ID {schedule_id}."

@tool
def delete_schedule_tool(schedule_id: int):
    """
    Deletes an event from the timetable using its schedule ID.
    This also automatically cleans up associated reminders.
    """
    success = delete_schedule(schedule_id)
    if success:
        return f"Successfully deleted schedule ID {schedule_id} from timetable."
    else:
        return f"Could not find or delete schedule ID {schedule_id}."

@tool
def find_free_slots_tool(date: str, duration_hours: float = 1.0):
    """
    Finds available study or class slots of a given duration (in hours, e.g., 1.5 or 2.0) on a specific date (YYYY-MM-DD).
    Returns a list of free slots.
    """
    slots = find_free_slots(date, duration_hours)
    if not slots:
        return f"No free slots of duration {duration_hours} hours found on {date} between 08:00 and 20:00."
    
    slots_str = "\n".join([f"- {s[0]} to {s[1]}" for s in slots[:5]])
    return f"Free slots on {date} for {duration_hours} hours:\n{slots_str}"

@tool
def detect_conflicts_tool(date: str, start_time: str, end_time: str):
    """
    Checks if a time range (start_time to end_time) on a date has overlapping events.
    Useful to verify scheduling slots before booking.
    """
    conflicts = detect_conflicts(date, start_time, end_time)
    if not conflicts:
        return "No conflicts! This slot is completely free."
    
    details = []
    for c in conflicts:
        details.append(f"'{c['subject']}' ({c['event_type']}) from {c['start_time']} to {c['end_time']}")
    return f"Conflict(s) detected: {', '.join(details)}."

@tool
def generate_study_plan_tool(subject: str, exam_date: str, total_study_hours: float = 4.0):
    """
    Automatically allocates and schedules study sessions in the database for an upcoming exam.
    Arguments:
    - subject: The subject of the exam (e.g. 'DBMS')
    - exam_date: Date of the exam (YYYY-MM-DD)
    - total_study_hours: Total hours needed to prepare (e.g., 4.0 or 6.0)
    
    This tool finds free slots in the days leading up to the exam (starting from tomorrow/today)
    and schedules study sessions of 2 hours each until the total hours are reached.
    """
    try:
        exam_dt = datetime.strptime(exam_date, "%Y-%m-%d")
        today = datetime.now()
        
        # Start searching for slots starting from tomorrow up to the day before the exam
        current_dt = today + timedelta(days=1)
        hours_allocated = 0.0
        scheduled_sessions = []
        
        if current_dt >= exam_dt:
            return "The exam is today or has already passed! Cannot plan study sessions in advance."
            
        # Try to schedule 2-hour blocks
        block_duration = 2.0
        
        while current_dt < exam_dt and hours_allocated < total_study_hours:
            date_str = current_dt.strftime("%Y-%m-%d")
            
            # Find free slots on this day
            free_slots = find_free_slots(date_str, block_duration)
            
            if free_slots:
                # Take the first available slot of the day
                slot_start, slot_end = free_slots[0]
                
                # Check how much time we still need
                remaining_hours = total_study_hours - hours_allocated
                session_duration = min(block_duration, remaining_hours)
                
                # Adjust slot_end if we need less than 2 hours
                if session_duration < block_duration:
                    sh, sm = map(int, slot_start.split(':'))
                    end_minutes = sh * 60 + sm + int(session_duration * 60)
                    eh = end_minutes // 60
                    em = end_minutes % 60
                    slot_end = f"{eh:02d}:{em:02d}"
                    
                # Schedule the study session
                session_subject = f"Study Session: {subject} Prep"
                sid = add_schedule(
                    subject=session_subject,
                    event_type="Study Session",
                    date=date_str,
                    start_time=slot_start,
                    end_time=slot_end,
                    priority="High",
                    status="Pending"
                )
                
                scheduled_sessions.append(f"- {date_str} {slot_start}-{slot_end} (Event ID: {sid})")
                hours_allocated += session_duration
                
            current_dt += timedelta(days=1)
            
        if hours_allocated == 0:
            return "Could not allocate any study sessions. No free scheduling blocks found in the days preceding the exam."
        elif hours_allocated < total_study_hours:
            return (
                f"Partially planned study prep. Allocated {hours_allocated} of {total_study_hours} hours:\n"
                + "\n".join(scheduled_sessions)
                + "\nNote: Not enough free slots were found to schedule all requested hours."
            )
        else:
            return (
                f"Successfully planned and booked study sessions for {subject} ({hours_allocated} hours total):\n"
                + "\n".join(scheduled_sessions)
            )
            
    except Exception as e:
        return f"Error generating study plan: {str(e)}"

# Collection of all tools
ALL_TOOLS = [
    read_schedule_tool,
    create_schedule_tool,
    update_schedule_tool,
    delete_schedule_tool,
    find_free_slots_tool,
    detect_conflicts_tool,
    generate_study_plan_tool
]

def get_agent_executor():
    """
    Initializes and returns the LangChain Agent Executor.
    Uses Google Gemini as the LLM.
    """
    # Initialize Google Gemini Chat model
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.2
    )
    
    # Define agent instructions prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are the Smart Timetable Assistant AI, an intelligent Agentic academic scheduler.\n"
            "Your job is to help students manage classes, exams, assignments, study sessions, and reminders.\n"
            "You have tools to read, create, update, and delete schedules, detect conflicts, find free slots, and generate study plans.\n\n"
            "Guidelines:\n"
            "1. Today's date is: " + datetime.now().strftime("%Y-%m-%d") + " (" + datetime.now().strftime("%A") + ")\n"
            "2. When creating or rescheduling events, you must avoid overlapping times with existing events. Check conflicts first or use the tools directly as they verify conflicts automatically.\n"
            "3. If a slot is taken, search for alternative times using find_free_slots_tool and suggest them.\n"
            "4. You can read, add, edit, or delete items. Explain your steps clearly to the student.\n"
            "5. If the student asks you to schedule a study session or plan prep, use the generate_study_plan_tool or find a slot and create it."
        )),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent
    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
    
    # Return executor
    return AgentExecutor(
        agent=agent, 
        tools=ALL_TOOLS, 
        verbose=True, 
        handle_parsing_errors=True
    )
