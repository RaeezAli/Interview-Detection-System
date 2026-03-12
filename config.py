"""
config.py - Application Configuration
Loads environment variables and provides a Config class for use in app.py.
"""
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

class Config:
    FLASK_ENV            = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG          = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    SECRET_KEY           = os.getenv("SECRET_KEY", "interviewai_secret_key_2025")
    MAX_UPLOAD_SIZE_MB   = int(os.getenv("MAX_UPLOAD_SIZE_MB", 500))
    UPLOAD_FOLDER        = os.getenv("UPLOAD_FOLDER", "uploads")
    WHISPER_MODEL        = os.getenv("WHISPER_MODEL", "base")
    ANALYSIS_FRAME_INTERVAL = int(os.getenv("ANALYSIS_FRAME_INTERVAL", 3))
    CLEANUP_AFTER_HOURS  = int(os.getenv("CLEANUP_AFTER_HOURS", 24))
