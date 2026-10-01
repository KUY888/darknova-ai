import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_KEY = os.getenv("AI_API_KEY", "")
    MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-120b")
    API_URL = os.getenv("AI_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(24).hex()
    MAX_INPUT = int(os.getenv("MAX_INPUT_CHARS", "8000"))
    THRESHOLD = int(os.getenv("VIOLATION_THRESHOLD", "3"))
    COOLDOWN = int(os.getenv("COOLDOWN_SECONDS", "600"))
    HISTORY_LIMIT = 20
    ENV = os.getenv("ENV", "development")
    PRODUCTION = ENV == "production"
    APP_PASSWORD = os.getenv("APP_PASSWORD", "")      # ว่าง = ไม่ต้องล็อกอิน (ใช้ในเครื่อง)
    TRUST_PROXY = os.getenv("TRUST_PROXY", "0") == "1"
    ENABLE_SCAN = os.getenv("ENABLE_SCAN", "1") == "1"
