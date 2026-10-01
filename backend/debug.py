"""Error analyzer + project scanner."""
import os
import re
from pathlib import Path

SKIP = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
CODE_EXT = {".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".go", ".rs"}
KEY_RX = re.compile(r"""(api[_-]?key|secret|token|password)\s*[=:]\s*['"][A-Za-z0-9_\-]{16,}['"]""", re.I)


def analyze_error(text):
    """Extract a hint (type + locations) to attach to the debug prompt."""
    kind = None
    m = re.search(r"^\s*([A-Za-z_.]*(Error|Exception|Warning))\b", text, re.M)
    if m:
        kind = m.group(1)
    locs = re.findall(r'File "([^"]+)", line (\d+)', text)
    locs += re.findall(r"([\w./\\-]+\.(?:js|ts|jsx|java|cpp|c|go|rs|py)):(\d+)", text)
    hint = []
    if kind:
        hint.append(f"Detected error type: {kind}")
    if locs:
        hint.append("Locations: " + ", ".join(f"{f}:{l}" for f, l in locs[:5]))
    return "\n".join(hint)


def redact(text):
    return KEY_RX.sub("[REDACTED]", re.sub(r"(sk-|gsk_)[A-Za-z0-9_\-]{16,}", "[REDACTED]", text))


def scan(path):
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("ไม่พบโฟลเดอร์นี้")
    files = []
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        files += [Path(d) / n for n in names]
        if len(files) > 500:
            break
    names = {f.name for f in files}
    code = [f for f in files if f.suffix in CODE_EXT]
    r = []
    r.append(("ok" if code else "fail", "ไฟล์", f"พบ {len(files)} ไฟล์ (โค้ด {len(code)})"))
    has_dep = names & {"requirements.txt", "package.json", "pyproject.toml", "pom.xml", "Cargo.toml"}
    r.append(("ok" if has_dep else "warn", "Dependencies", ", ".join(has_dep) or "ไม่พบไฟล์ dependencies"))
    gi = root / ".gitignore"
    if ".env" in names and not (gi.exists() and ".env" in gi.read_text(errors="ignore")):
        r.append(("fail", "Config", "มี .env แต่ไม่อยู่ใน .gitignore"))
    elif ".env.example" not in names:
        r.append(("warn", "Config", "ไม่มี .env.example"))
    else:
        r.append(("ok", "Config", "ปกติ"))
    bare = keys = risky = long_files = 0
    for f in code:
        try:
            t = f.read_text(errors="ignore")
        except OSError:
            continue
        bare += len(re.findall(r"except\s*:|catch\s*\([^)]*\)\s*\{\s*\}", t))
        keys += len(KEY_RX.findall(t))
        risky += len(re.findall(r"\beval\(|shell\s*=\s*True|\.innerHTML\s*=", t))
        long_files += t.count("\n") > 600
    r.append(("ok" if not bare else "warn", "Error handling", f"bare except/catch ว่าง {bare} จุด"))
    r.append(("fail" if keys else ("warn" if risky else "ok"), "Security",
              f"hard-coded secret {keys}, โค้ดเสี่ยง (eval/shell/innerHTML) {risky}"))
    r.append(("ok" if not long_files else "warn", "โครงสร้างโค้ด", f"ไฟล์ยาวเกิน 600 บรรทัด {long_files}"))
    sym = {"ok": "✓", "warn": "⚠", "fail": "✗"}
    return "DARKNOVA PROJECT SCAN\n" + "\n".join(f"{sym[s]} {a}: {b}" for s, a, b in r)
