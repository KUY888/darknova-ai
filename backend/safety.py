"""Rule-based safety checks + violation counter + temporary restriction."""
import hashlib
import logging
import re
import threading
import time
from .config import Config

logging.basicConfig(filename="safety.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")
log = logging.getLogger("safety")

_MAKE = r"(สร้าง|เขียน|ทำ|พัฒนา|write|build|create|make|develop|code)"
BLOCK = [
    (re.compile(_MAKE + r".{0,40}(ransomware|แรนซัมแวร์|keylogger|คีย์ล็อกเกอร์|botnet|บอทเน็ต|"
                r"infostealer|credential stealer|phishing\s*(page|site|kit)|หน้าเฟก|หน้าหลอก|ddos)", re.I), "malware"),
    (re.compile(r"(ขโมย|steal|dump|exfiltrate).{0,30}(password|รหัสผ่าน|cookie|token|บัตรเครดิต|credit card)", re.I), "data-theft"),
    (re.compile(r"(แฮก|hack|เจาะ|crack).{0,30}(เฟซบุ๊ก|facebook|ไลน์|บัญชี.{0,6}(คนอื่น|แฟน|เขา)|someone'?s|victim|เหยื่อ)", re.I), "unauthorized-access"),
    (re.compile(r"(หลอก|scam|โกง).{0,20}(โอนเงิน|เหยื่อ|victim)", re.I), "fraud"),
]
RISKY = re.compile(r"(hack|exploit|malware|payload|backdoor|reverse shell|sql\s*injection|brute.?force|"
                   r"แฮก|เจาะระบบ|ขโมย|มัลแวร์|ช่องโหว่)", re.I)
SAFE_CTX = re.compile(r"(ป้องกัน|defen[cs]e|protect|patch|แก้ไข|fix|detect|ตรวจจับ|ctf|authorized|"
                      r"ได้รับอนุญาต|pentest|เรียนรู้|learn|ของตัวเอง|my own)", re.I)

_lock = threading.Lock()
_state = {}  # id -> {"count", "last", "until"}


def _h(x):
    return hashlib.sha256(x.encode()).hexdigest()[:10]


def retry_after(ids):
    now = time.time()
    with _lock:
        return max([int(_state.get(i, {}).get("until", 0) - now) for i in ids] + [0])


def rule_check(text):
    """Returns 'block' (clear violation), 'review' (ambiguous -> AI), or 'allow'."""
    for rx, cat in BLOCK:
        if rx.search(text):
            return ("review", cat) if SAFE_CTX.search(text) else ("block", cat)
    if RISKY.search(text):
        return "review", "risky-keyword"
    return "allow", ""


def violation(ids, category):
    now = time.time()
    with _lock:
        for i in ids:
            s = _state.setdefault(i, {"count": 0, "last": now, "until": 0})
            if now - s["last"] > 3600:  # counter decays after 1 hour
                s["count"] = 0
            s["count"] += 1
            s["last"] = now
            if s["count"] >= Config.THRESHOLD:
                s["until"] = now + Config.COOLDOWN  # temporary only, never permanent
                s["count"] = 0
    log.info("violation id=%s category=%s", _h(ids[0]), category)  # no message content logged
