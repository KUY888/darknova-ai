import json
import re
import requests
from .config import Config

SYSTEM = {
    "code": "You are DARKNOVA AI, an expert programming assistant. Write, fix and explain "
            "working code in any language (Python, JS, TS, HTML, CSS, C++, Java...). Use fenced "
            "code blocks with language tags. Be concise. Reply in the user's language.",
    "plan": "You are DARKNOVA AI in PLAN mode. Turn the user's goal into a numbered plan: "
            "1 analyze requirements, 2 design structure, 3 files to create, 4 core system, "
            "5 error handling, 6 testing, 7 review/improve. Be specific. Reply in the user's language.",
    "debug": "You are DARKNOVA AI in DEBUG mode. For the given error: 1) error type, 2) root cause, "
             "3) likely file/line, 4) fix, 5) corrected code, 6) short explanation, 7) follow-up "
             "problems to check. Fix the root cause, never hide the error. Reply in the user's language.",
}

MOD_PROMPT = (
    "You are a safety classifier for a coding assistant. Decide if the user's request seeks help "
    "building or improving tools to attack systems without authorization, steal data, defraud, or "
    "harm others (malware, phishing, credential theft, DDoS, etc.). Defensive security, education, "
    "authorized testing and fixing vulnerabilities are NOT harmful. When unsure, answer false. "
    'Reply ONLY with JSON: {"harmful": true|false, "category": "short label"}'
)


class AIError(Exception):
    pass


def _post(system, messages, max_tokens):
    """OpenAI-compatible chat endpoint (Groq by default)."""
    if not Config.API_KEY:
        raise AIError("ยังไม่ได้ตั้งค่า AI_API_KEY ในไฟล์ .env")
    try:
        r = requests.post(
            Config.API_URL,
            headers={"Authorization": "Bearer " + Config.API_KEY,
                     "Content-Type": "application/json", "User-Agent": "darknova-ai/1.0"},
            json={"model": Config.MODEL, "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": system}] + messages},
            timeout=90,
        )
    except requests.RequestException:
        raise AIError("เชื่อมต่อ AI API ไม่ได้ ตรวจสอบอินเทอร์เน็ต")
    if r.status_code == 429:
        raise AIError("ใช้งานเกินโควตาฟรีชั่วคราว รอสักครู่แล้วลองใหม่")
    if r.status_code != 200:
        raise AIError(f"AI API ตอบกลับสถานะ {r.status_code} ตรวจสอบ API key และชื่อ model")
    try:
        return r.json()["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, ValueError):
        raise AIError("รูปแบบคำตอบจาก AI API ไม่ถูกต้อง")


def chat(mode, messages):
    return _post(SYSTEM.get(mode, SYSTEM["code"]), messages, 4000)


def moderate(text):
    """AI moderation. Returns (harmful, category). Raises AIError on failure."""
    out = _post(MOD_PROMPT, [{"role": "user", "content": text[:3000]}], 800)
    m = re.search(r"\{.*\}", out, re.S)
    try:
        d = json.loads(m.group(0))
        return bool(d.get("harmful")), str(d.get("category", ""))[:40]
    except (AttributeError, ValueError):
        return False, ""
