import hmac
import secrets
import time
from flask import Blueprint, jsonify, request, session
from . import ai, debug, safety
from .config import Config

api = Blueprint("api", __name__, url_prefix="/api")
_fails = {}  # ip -> [count, locked_until]  (กัน brute force)


@api.before_request
def gate():
    if request.endpoint in ("api.login", "api.logout", "api.status"):
        return None
    if Config.APP_PASSWORD and not session.get("auth"):
        return jsonify(error="กรุณาเข้าสู่ระบบ", login=True), 401


@api.get("/status")
def status():
    need = bool(Config.APP_PASSWORD)
    return jsonify(auth_required=need, authed=(not need) or bool(session.get("auth")), scan=Config.ENABLE_SCAN)


@api.post("/login")
def login():
    ip, now = request.remote_addr or "?", time.time()
    f = _fails.get(ip, [0, 0])
    if f[1] > now:
        return jsonify(error="ลองผิดหลายครั้ง รอ 15 นาทีแล้วลองใหม่"), 429
    pw = str((request.get_json(silent=True) or {}).get("password", ""))
    if Config.APP_PASSWORD and hmac.compare_digest(pw.encode(), Config.APP_PASSWORD.encode()):
        _fails.pop(ip, None)
        session["auth"] = True
        session.permanent = True
        return jsonify(ok=True)
    f[0] += 1
    _fails[ip] = [0, now + 900] if f[0] >= 5 else f
    return jsonify(error="รหัสผ่านไม่ถูกต้อง"), 401


@api.post("/logout")
def logout():
    session.pop("auth", None)
    return jsonify(ok=True)

WARN = ("DARKNOVA AI ไม่สามารถช่วยดำเนินการตามคำขอนี้ได้ เนื่องจากอาจนำไปสู่การใช้งานที่"
        "ผิดกฎหมายหรือเป็นอันตราย คุณสามารถถามเรื่องการป้องกันระบบหรือการแก้ไขช่องโหว่แทนได้")


def _ids():
    if "uid" not in session:
        session["uid"] = secrets.token_hex(8)
    return [session["uid"], "ip:" + (request.remote_addr or "?")]


def _clean_history(raw):
    out = []
    for m in (raw or [])[-Config.HISTORY_LIMIT:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") \
                and isinstance(m.get("content"), str):
            if (out and out[-1]["role"] == m["role"]) or (not out and m["role"] != "user"):
                continue
            out.append({"role": m["role"], "content": m["content"][:Config.MAX_INPUT]})
    if out and out[-1]["role"] == "user":
        out.pop()
    return out


def _restricted(ids):
    left = safety.retry_after(ids)
    if left:
        mins = max(1, -(-left // 60))
        return jsonify(error=f"TEMPORARY CHAT RESTRICTION\nReason: Repeated Safety Policy Violations\n"
                             f"เหลืออีก ~{mins} นาที", restricted=True, retry_after=left), 429


@api.post("/chat")
def chat():
    ids = _ids()
    if (r := _restricted(ids)):
        return r
    d = request.get_json(silent=True) or {}
    mode, msg = d.get("mode", "code"), d.get("message", "")
    if mode not in ai.SYSTEM or not isinstance(msg, str) or not msg.strip():
        return jsonify(error="คำขอไม่ถูกต้อง"), 400
    if len(msg) > Config.MAX_INPUT:
        return jsonify(error=f"ข้อความยาวเกิน {Config.MAX_INPUT} ตัวอักษร"), 400

    verdict, cat = safety.rule_check(msg)
    if verdict == "review":
        try:
            harmful, cat = ai.moderate(msg)
            verdict = "block" if harmful else "allow"
        except ai.AIError:
            verdict = "allow"  # avoid false positives when moderation is unavailable
    if verdict == "block":
        safety.violation(ids, cat)
        resp = _restricted(ids)
        return resp if resp else (jsonify(error="WARNING\n" + WARN, warning=True), 403)

    if mode == "debug":
        hint = debug.analyze_error(msg)
        msg = (hint + "\n\n" if hint else "") + msg
    try:
        reply = ai.chat(mode, _clean_history(d.get("history")) + [{"role": "user", "content": msg}])
    except ai.AIError as e:
        return jsonify(error=debug.redact(str(e))), 502
    except Exception:
        return jsonify(error="เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์"), 500
    return jsonify(reply=reply)


@api.post("/scan")
def scan():
    if not Config.ENABLE_SCAN:
        return jsonify(error="ฟีเจอร์นี้ปิดบนเซิร์ฟเวอร์ออนไลน์"), 403
    ids = _ids()
    if (r := _restricted(ids)):
        return r
    path = (request.get_json(silent=True) or {}).get("path", "")
    try:
        return jsonify(reply=debug.scan(str(path)))
    except (ValueError, OSError) as e:
        return jsonify(error=str(e) or "สแกนไม่สำเร็จ"), 400
