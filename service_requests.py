# /backend/service_request.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import re
import time

app = Flask(__name__)
CORS(app)

# --- Environment Variables ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "mini_browser")

# --- Spam Protection ---
rate_limit = {}  # {ip: [timestamps]}
EMAIL_COOLDOWN = 60  # seconds
IP_LIMIT = 5         # max submissions per IP per minute

# --- Database Setup ---
def init_db():
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                service VARCHAR(50) NOT NULL,
                specifics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Database '{DB_NAME}' and table 'service_requests' are ready.")
    except Exception as e:
        print("❌ Database Initialization Error:", e)

# --- Database Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

# --- Helpers ---
def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr

def check_rate_limit(ip, email):
    now = time.time()
    if ip not in rate_limit:
        rate_limit[ip] = []
    rate_limit[ip] = [t for t in rate_limit[ip] if now - t < 60]
    if len(rate_limit[ip]) >= IP_LIMIT:
        return False, "⚠️ Too many requests from your IP. Please try again later."
    rate_limit[ip].append(now)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT created_at FROM service_requests 
        WHERE email = %s ORDER BY created_at DESC LIMIT 1
    """, (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        last_time = row["created_at"].timestamp()
        if now - last_time < EMAIL_COOLDOWN:
            return False, f"⚠️ You must wait {EMAIL_COOLDOWN} seconds before sending another request."
    return True, None

# --- Routes ---
@app.route("/request-service", methods=["POST"])
def request_service():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    service = data.get("service", "").strip()  # fixed options
    specifics = data.get("specifics", "").strip()  # optional text field
    honeypot = data.get("website", "").strip()  # hidden field

    # --- Honeypot ---
    if honeypot:
        return jsonify({"status": "error", "message": "Spam detected."}), 400
    if not name or not email or not service:
        return jsonify({"status": "error", "message": "Name, email, and service are required."}), 400

    # --- Spam check ---
    ip = get_client_ip()
    ok, msg = check_rate_limit(ip, email)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 429

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO service_requests (name, email, service, specifics) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, email, service, specifics))
        conn.commit()

        # --- Logging ---
        print("📩 New Service Request:")
        print(f"Name: {name}, Email: {email}, Service: {service}, Specifics: {specifics}")

        # --- Recent entries ---
        cursor.execute("SELECT id, name, email, service, specifics, created_at FROM service_requests ORDER BY created_at DESC LIMIT 10")
        recent_entries = cursor.fetchall()
        print("🗂 Current Service Requests (last 10 entries):")
        for entry in recent_entries:
            print(entry)

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "✅ Service request submitted successfully.", "recent_entries": recent_entries}), 200

    except mysql.connector.Error as e:
        print("❌ Database Error:", e)
        return jsonify({"status": "error", "message": "Database connection or query failed."}), 500
    except Exception as e:
        print("❌ Unexpected Error:", e)
        return jsonify({"status": "error", "message": "Server error. Please try again later."}), 500

# --- Run Server ---
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
