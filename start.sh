#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"
termux-wake-lock 2>/dev/null   # กัน Android ปิดโปรเซสตอนพับจอ
python main.py
