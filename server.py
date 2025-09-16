# /backend/server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import re
import dns.resolver
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
           CREATE TABLE IF NOT EXISTS contact_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_email_message (email, message(255))
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Database '{DB_NAME}' and table 'contact_messages' are ready.")
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
def is_valid_email(email):
    """Check format + MX record existence."""
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    domain = email.split("@")[-1]
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False

def get_client_ip():
    """Get real client IP (handles proxies)."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr

def check_rate_limit(ip, email):
    """Basic spam check: per-IP and per-email cooldown."""
    now = time.time()

    # --- Per IP ---
    if ip not in rate_limit:
        rate_limit[ip] = []
    # keep only recent requests (last 60s)
    rate_limit[ip] = [t for t in rate_limit[ip] if now - t < 60]
    if len(rate_limit[ip]) >= IP_LIMIT:
        return False, "⚠️ Too many requests from your IP. Please try again later."
    rate_limit[ip].append(now)

    # --- Per email (check last submission time) ---
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT created_at 
        FROM contact_messages 
        WHERE email = %s 
        ORDER BY created_at DESC LIMIT 1
    """, (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        last_time = row["created_at"].timestamp()
        if now - last_time < EMAIL_COOLDOWN:
            return False, f"⚠️ You must wait {EMAIL_COOLDOWN} seconds before sending another message."
    
    return True, None

# --- Routes ---
@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()
    honeypot = data.get("website", "").strip()  # hidden field

    # --- Honeypot trap ---
    if honeypot:
        return jsonify({"status": "error", "message": "Spam detected."}), 400

    if not name or not email or not message:
        return jsonify({"status": "error", "message": "All fields are required."}), 400
    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid or non-existent email address."}), 400

    # --- Spam checks ---
    ip = get_client_ip()
    ok, msg = check_rate_limit(ip, email)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 429

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (name, email, message))
            conn.commit()
            response = {"status": "success", "message": "✅ Message submitted successfully."}
        except mysql.connector.Error as e:
            if e.errno == 1062:  # Duplicate entry
                response = {
                    "status": "duplicate",
                    "message": "⚠️ This message was already received earlier. Please wait for a response."
                }
            else:
                raise e

        cursor.close()
        conn.close()
        return jsonify(response), 200

    except mysql.connector.Error as e:
        print("❌ Database Error:", e)
        return jsonify({"status": "error", "message": "Database connection or query failed."}), 500
    except Exception as e:
        print("❌ Unexpected Error:", e)
        return jsonify({"status": "error", "message": "Server error. Please try again later."}), 500

# --- Run Server ---
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
