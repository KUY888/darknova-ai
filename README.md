# DARKNOVA AI
AI Developer Assistant สำหรับเขียนโค้ด วางแผนโปรเจกต์ และตรวจสอบ Error

## รับ API key ฟรี (Groq)
สมัครที่ https://console.groq.com/keys (ไม่ต้องใช้บัตรเครดิต) แล้วกด Create API Key
ใช้ endpoint แบบ OpenAI-compatible จึงเปลี่ยนผู้ให้บริการได้ผ่าน `AI_API_URL` และ `AI_MODEL`
หากชื่อโมเดลถูกยกเลิก ให้ดูรายการล่าสุดใน console.groq.com

## ติดตั้งบน Termux
```bash
pkg update && pkg upgrade -y
pkg install python git -y
cd darknova-ai
pip install -r requirements.txt
cp .env.example .env
nano .env        # ใส่ AI_API_KEY (Ctrl+O, Enter, Ctrl+X)
python main.py
```
เปิดเบราว์เซอร์ที่ `http://127.0.0.1:5000`

## โหมด
- **Code** เขียน/แก้/อธิบายโค้ด · **Plan** วางแผน 7 ขั้นตอน · **Debug** วิเคราะห์ Error
- **Scan project** ตรวจโครงสร้างโปรเจกต์ (✓ ปกติ / ⚠ ควรแก้ไข / ✗ พบปัญหา)

## ความปลอดภัย
- API key อยู่ใน `.env` เท่านั้น ไม่ส่งไป Frontend และถูกกรองออกจากข้อความ error
- Safety: rule-based + AI moderation (แยกจากโมเดลหลัก) ตรวจก่อนส่งทุกครั้ง
- ละเมิดครบ `VIOLATION_THRESHOLD` ครั้ง จำกัดการส่งข้อความชั่วคราว `COOLDOWN_SECONDS` วินาที (ไม่แบนถาวร)
- Log (`safety.log`) เก็บเฉพาะหมวดหมู่และ ID แบบ hash ไม่เก็บข้อความ
- ถ้า AI moderation ใช้ไม่ได้ ระบบจะปล่อยผ่านเฉพาะกรณีกำกวม เพื่อลด false positive
- สถานะละเมิดเก็บในหน่วยความจำ จะรีเซ็ตเมื่อรีสตาร์ท

หากเปิดให้ใช้งานผ่านเครือข่าย ให้ตั้ง `SECRET_KEY` และใช้ HTTPS ผ่าน reverse proxy

## ติดตั้งเป็นแอป (PWA)
1. รันเซิร์ฟเวอร์ใน Termux: `./start.sh`
2. เปิด `http://localhost:5000` ใน Chrome
3. เมนู ⋮ → **Install app** (หรือ Add to Home screen)

ไอคอน DARKNOVA จะอยู่บนหน้าจอหลักและเปิดแบบเต็มจอ แต่ต้องเปิด Termux ให้เซิร์ฟเวอร์รันอยู่ด้วย
ปิดการประหยัดแบตให้ Termux เพื่อไม่ให้ Android ฆ่าโปรเซส

## นำขึ้นออนไลน์ (Render) แล้วแปลงเป็น APK
1. อัปโปรเจกต์ขึ้น GitHub (`.env` ถูก .gitignore กันไว้แล้ว ห้าม commit)
2. ที่ render.com เลือก New → Blueprint → เลือก repo นี้ (ใช้ `render.yaml`)
3. ตั้งค่า `AI_API_KEY` (key Groq) และ `APP_PASSWORD` (รหัสผ่านเข้าแอป) ในหน้า Environment
4. ได้ลิงก์ `https://....onrender.com` แล้วเปิดใน Chrome → Install app
5. อยากได้ .apk: ใส่ลิงก์ที่ pwabuilder.com
- โหมด production ปิดฟีเจอร์ Scan project (กันอ่านไฟล์บนเซิร์ฟเวอร์)
- ใช้ worker เดียว เพราะเก็บสถานะ violation ในหน่วยความจำ
