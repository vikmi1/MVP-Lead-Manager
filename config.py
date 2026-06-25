import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL", "")
DB_PATH = os.getenv("DB_PATH", "leads.db")
LOG_PATH = os.getenv("LOG_PATH", "events.log")
