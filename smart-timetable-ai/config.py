import os

# Load environment variables from .env file (handle missing python-dotenv gracefully)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database Configuration
DATABASE_PATH = os.path.join(BASE_DIR, "data", "timetable.db")

# Google Gemini API Configuration
# Prefer GEMINI_API_KEY as per Google Generative AI / LangChain standard, fall back to the provided key for convenience
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyB2Kjl3jG6p8795121elR4LK-yRxOcNrvA")

# SMTP Configuration for Email Reminders
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "bandinagendra1006@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "1234 5678 9012 3456")  # App password

# Default User Information for local dev
DEFAULT_USER_NAME = os.getenv("DEFAULT_USER_NAME", "Student User")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "YOUR_RECEIVER_EMAIL@gmail.com")
