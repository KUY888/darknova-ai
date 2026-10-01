import os
from datetime import timedelta
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from backend.config import Config
from backend.routes import api

if Config.PRODUCTION and not (Config.APP_PASSWORD and Config.API_KEY and os.getenv("SECRET_KEY")):
    raise SystemExit("โหมด production ต้องตั้ง APP_PASSWORD, AI_API_KEY และ SECRET_KEY")

app = Flask(__name__, static_folder="frontend", static_url_path="")
if Config.TRUST_PROXY:  # อยู่หลัง proxy ของโฮสต์ ให้เห็น IP ผู้ใช้จริง
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
app.config.update(SECRET_KEY=Config.SECRET_KEY, MAX_CONTENT_LENGTH=64 * 1024,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=Config.PRODUCTION,
                  PERMANENT_SESSION_LIFETIME=timedelta(days=7))
app.register_blueprint(api)


@app.after_request
def headers(r):
    r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                      "Referrer-Policy": "same-origin"})
    return r


@app.get("/")
def index():
    return send_from_directory("frontend", "index.html")


if __name__ == "__main__":
    if not Config.API_KEY:
        print("⚠ ยังไม่ได้ตั้งค่า AI_API_KEY ใน .env")
    app.run(host=Config.HOST, port=Config.PORT)
