import datetime
from utils.database_utils import add_schedule

def export_to_ics(schedules_df):
    """
    Generates standard RFC 5545 iCalendar (.ics) format string from schedules.
    Allows students to import their timetable directly into Google Calendar or Outlook.
    """
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Smart Timetable Assistant AI//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    for _, row in schedules_df.iterrows():
        # Combine date and time
        date_str = row['date'].replace("-", "")
        start_time_str = row['start_time'].replace(":", "") + "00"
        end_time_str = row['end_time'].replace(":", "") + "00"
        
        # Format as UTC/local time blocks
        dtstart = f"{date_str}T{start_time_str}"
        dtend = f"{date_str}T{end_time_str}"
        
        # Generate event uuid
        uid = f"event-{row['id']}@smart-timetable-ai.com"
        
        # Format description
        description = f"Type: {row['event_type']} | Priority: {row['priority']} | Status: {row['status']}"
        
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;TZID=Local:{dtstart}",
            f"DTEND;TZID=Local:{dtend}",
            f"SUMMARY:{row['subject']} ({row['event_type']})",
            f"DESCRIPTION:{description}",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ])
        
    ics_lines.append("END:VCALENDAR")
    return "\n".join(ics_lines)

def import_from_ics(ics_content):
    """
    Parses a basic .ics file format and imports events into the database.
    Returns the number of imported events.
    """
    imported_count = 0
    lines = ics_content.splitlines()
    
    event = {}
    in_event = False
    
    for line in lines:
        line = line.strip()
        if line == "BEGIN:VEVENT":
            event = {}
            in_event = True
        elif line == "END:VEVENT" and in_event:
            # Save event to database
            # Extract attributes
            summary = event.get("SUMMARY", "Imported Event")
            dtstart = event.get("DTSTART", "")
            dtend = event.get("DTEND", "")
            description = event.get("DESCRIPTION", "")
            
            # Simple parsing of dates (expecting YYYYMMDDTHHMMSS)
            try:
                # Handle TZID or other parameters in DTSTART
                if ";" in dtstart:
                    dtstart = dtstart.split(":")[-1]
                if ";" in dtend:
                    dtend = dtend.split(":")[-1]
                    
                start_dt = datetime.datetime.strptime(dtstart[:15], "%Y%m%dT%H%M%S")
                end_dt = datetime.datetime.strptime(dtend[:15], "%Y%m%dT%H%M%S")
                
                date_str = start_dt.strftime("%Y-%m-%d")
                start_time = start_dt.strftime("%H:%M")
                end_time = end_dt.strftime("%H:%M")
                
                # Deduce event type
                event_type = "Class"
                if "Exam" in summary or "exam" in summary.lower():
                    event_type = "Exam"
                elif "Assignment" in summary or "assignment" in summary.lower():
                    event_type = "Assignment"
                elif "Study" in summary or "study" in summary.lower():
                    event_type = "Study Session"
                    
                # Add to DB
                add_schedule(
                    subject=summary.replace(f" ({event_type})", ""),
                    event_type=event_type,
                    date=date_str,
                    start_time=start_time,
                    end_time=end_time,
                    priority="Medium",
                    status="Pending"
                )
                imported_count += 1
            except Exception as e:
                print(f"Error parsing event: {e}")
                
            in_event = False
        elif in_event and ":" in line:
            parts = line.split(":", 1)
            key = parts[0].split(";")[0]  # strip parameters
            val = parts[1]
            event[key] = val
            
    return imported_count

def mock_sync_google_calendar():
    """
    Simulates direct Google API sync flow.
    Returns success message along with number of synced items.
    """
    return {
        "success": True,
        "synced_count": 5,
        "message": "Directly synced 5 schedules with Google Calendar API account."
    }
