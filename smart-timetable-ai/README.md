# 📚 Smart Timetable Assistant AI

An AI-powered academic scheduling assistant built for students to manage classes, exams, assignments, study sessions, and reminders. The system is built using **Agentic AI** principles (powered by **LangChain** and **Google Gemini**), allowing the assistant to analyze schedules, make scheduling decisions, resolve conflicts, and plan study slots automatically based on natural language commands.

---

## 🛠️ Tech Stack
- **Frontend**: Streamlit (with custom CSS glassmorphic theme and Plotly charts)
- **Backend**: Python 3.8+
- **Database**: SQLite
- **AI Engine**: LangChain agents, Google Gemini API (`gemini-1.5-flash`)
- **Data & Calendar**: Pandas, standard iCalendar (.ics) RFC 5545 format
- **Notifications**: SMTP Mail Engine (Python standard library `smtplib`)

---

## 📂 Project Folder Structure

```text
smart-timetable-ai/
│
├── app.py                  # Home Landing Page & Database Initializer
├── database.py             # Database Schema Seeding Script
├── config.py               # Central Environment & SMTP Configuration
├── ai_agent.py             # LangChain Agent Executor and Custom Schedule Tools
├── ai_chat.py              # Backward-compatible AI routing wrapper
├── scheduler.py            # Conflict Detection and Free Slot Search Algorithms
├── reminder.py             # Background SMTP Mail Dispatcher
├── analytics.py            # Dashboard Analytics & Metric Calculators
├── requirements.txt        # Project Dependencies (Streamlit, LangChain, Plotly)
├── README.md               # Setup & Documentation
│
├── pages/
│   ├── dashboard.py        # Analytics & Today's Schedule Overview
│   ├── add_schedule.py     # Manual Schedule Entry Form with Conflict Warnings
│   ├── view_schedule.py    # List/Day/Week/Month Calendar Grid & Import/Export
│   ├── study_planner.py    # Exam Workload Analyzer & Automatic Study Planner
│   ├── reminders.py        # Custom Reminder Manager & SMTP Config Editor
│   └── chatbot.py          # Conversational Agentic AI Assistant Chat
│
├── utils/
│   ├── database_utils.py   # Database CRUD and Query Helpers
│   ├── calendar_utils.py   # RFC 5545 iCalendar Exporter & Importer
│   └── notification_utils.py # Standardized Streamlit Banners and custom CSS Theme
│
└── data/
    └── timetable.db        # SQLite Database File (auto-generated)
```

---

## 🗄️ Database Schema

The system uses three tables inside `data/timetable.db`:

### 1. `users`
Tracks the active student's notification profile.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `name` (TEXT)
* `email` (TEXT UNIQUE)

### 2. `schedules`
Stores classes, assignments, exams, and study blocks.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `subject` (TEXT)
* `event_type` (TEXT) - `Class`, `Exam`, `Assignment`, `Study Session`
* `date` (TEXT) - `YYYY-MM-DD`
* `start_time` (TEXT) - `HH:MM`
* `end_time` (TEXT) - `HH:MM`
* `priority` (TEXT) - `High`, `Medium`, `Low`
* `status` (TEXT) - `Pending`, `Completed`

### 3. `reminders`
Schedules notification triggers for course deadlines or exam revisions.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `schedule_id` (INTEGER, FOREIGN KEY referencing `schedules.id` ON DELETE CASCADE)
* `reminder_time` (TEXT) - `YYYY-MM-DD HH:MM`
* `notification_type` (TEXT) - `Email` or `Dashboard`
* `sent_status` (INTEGER) - `0` (Pending) or `1` (Sent)

---

## 🚀 Setup & Run Instructions

Follow these steps to run the application on your computer:

### Step 1: Open terminal in Workspace
Navigate to your project root folder:
```bash
cd d:\smart-timetable-ai
```

### Step 2: Set up Virtual Environment
Activate your Python virtual environment to make sure imports don't conflict:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate
  ```

### Step 3: Install Dependencies
Install all required libraries (including LangChain, Gemini, and Plotly) into the environment:
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (`.env`)
Create a file named `.env` in the root project folder (`d:\smart-timetable-ai\.env`) and configure your API keys:
```env
# Google Gemini Key
GEMINI_API_KEY=your_gemini_api_key_here

# SMTP Sender Configuration (e.g. Gmail)
SMTP_EMAIL=your_sender_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Student Info
DEFAULT_USER_NAME=Student Name
DEFAULT_USER_EMAIL=your_recipient_email@gmail.com
```
*Note: If `GEMINI_API_KEY` is not provided in `.env`, the code will default to a pre-defined evaluation key.*

### Step 5: Run the Timetable Application
Launch the Streamlit app:
```bash
streamlit run app.py
```
This will automatically open the application inside your default web browser (typically at `http://localhost:8501`). On first launch, it will automatically initialize the database schema and populate it with sample events.

---

## 🌎 Deployment Instructions

To share this application with other students, you can deploy it in production:

### Option 1: Streamlit Community Cloud (Easiest)
1. Commit the code and push it to a private or public GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click "New App", select your repository, branch (`main`), and entry point file (`app.py`).
4. Under **Advanced Settings**, paste the contents of your `.env` file into the **Secrets** section:
   ```toml
   GEMINI_API_KEY = "your_actual_key"
   SMTP_EMAIL = "your_sender_gmail@gmail.com"
   SMTP_PASSWORD = "your_gmail_app_password"
   ```
5. Click **Deploy**. Your app will be live on a public URL!

### Option 2: Docker Container (Self-hosted on AWS/GCP/DigitalOcean)
Create a `Dockerfile` in the root folder:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
Build and run the container:
```bash
docker build -t smart-timetable-ai .
docker run -p 8501:8501 --env-file .env smart-timetable-ai
```
