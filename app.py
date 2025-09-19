# /backend/server.py

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from flask_session import Session
import mysql.connector
import os
import re
import dns.resolver
import time

app = Flask(__name__)
CORS(app)

# --- Secret + Sessions ---
app.secret_key = "super-secret-key"  # change this
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

        # Contact form table
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

        # Service request table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                service VARCHAR(50) NOT NULL,
                sub_details TEXT,
                details TEXT,
                budget INT DEFAULT NULL,
                platform VARCHAR(50),
                attachment_link TEXT,
                notes TEXT,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Database '{DB_NAME}' initialized with tables.")
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
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    domain = email.split("@")[-1]
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False

def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr

def check_rate_limit(ip, email, table):
    now = time.time()
    if ip not in rate_limit:
        rate_limit[ip] = []
    rate_limit[ip] = [t for t in rate_limit[ip] if now - t < 60]
    if len(rate_limit[ip]) >= IP_LIMIT:
        return False, "⚠️ Too many requests from your IP. Please try again later."
    rate_limit[ip].append(now)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"""
        SELECT created_at FROM {table} 
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

# --- Landing Page ---
@app.route("/")
def index():
    return render_template("index.html", email=session.get("email"))

# --- Login + Logout ---
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    if not email:
        flash("⚠️ Please enter a valid email.", "error")
        return redirect(url_for("index"))
    session["email"] = email
    flash(f"✅ Logged in as {email}", "success")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Logged out successfully.", "success")
    return redirect(url_for("index"))

# --- Contact Form ---
@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json() if request.is_json else request.form

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()
    honeypot = data.get("website", "").strip() if "website" in data else ""

    if honeypot:
        return jsonify({"status": "error", "message": "Spam detected."}), 400
    if not name or not email or not message:
        return jsonify({"status": "error", "message": "All fields are required."}), 400
    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid or non-existent email address."}), 400

    ip = get_client_ip()
    ok, msg = check_rate_limit(ip, email, "contact_messages")
    if not ok:
        return jsonify({"status": "error", "message": msg}), 429

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (name, email, message))
            conn.commit()
            response = {"status": "success", "message": "✅ Message submitted successfully."}
        except mysql.connector.Error as e:
            if e.errno == 1062:
                response = {"status": "duplicate", "message": "⚠️ This message was already received earlier."}
            else:
                raise e

        cursor.close()
        conn.close()

        if not request.is_json:
            flash(response["message"], response["status"])
            return redirect(url_for("index"))

        return jsonify(response), 200
    except Exception as e:
        print("❌ Contact Error:", e)
        return jsonify({"status": "error", "message": "Server error."}), 500

# --- Service Request Form ---
@app.route("/request-service", methods=["POST"])
def request_service():
    data = request.get_json() if request.is_json else request.form

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    service = data.get("service", "").strip()
    sub_details = data.get("sub_details", "").strip() if "sub_details" in data else ""
    details = data.get("details", "").strip() if "details" in data else ""
    budget = data.get("budget", "").strip() if "budget" in data else None
    platform = data.get("platform", "").strip() if "platform" in data else ""
    attachment_link = data.get("attachment_link", "").strip() if "attachment_link" in data else ""
    notes = data.get("notes", "").strip() if "notes" in data else ""
    deadline = data.get("deadline", "").strip() if "deadline" in data else ""
    honeypot = data.get("website", "").strip() if "website" in data else ""

    if honeypot:
        return jsonify({"status": "error", "message": "Spam detected."}), 400
    if not name or not email or not service:
        return jsonify({"status": "error", "message": "Name, email, and service are required."}), 400
    if budget:
        try:
            budget = int(budget)
        except:
            return jsonify({"status": "error", "message": "Budget must be a number."}), 400

    ip = get_client_ip()
    ok, msg = check_rate_limit(ip, email, "service_requests")
    if not ok:
        return jsonify({"status": "error", "message": msg}), 429

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            INSERT INTO service_requests 
            (name, email, phone, service, sub_details, details, budget, platform, attachment_link, notes, deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, phone, service, sub_details, details, budget, platform, attachment_link, notes, deadline))
        conn.commit()

        response = {"status": "success", "message": "✅ Service request submitted successfully."}

        cursor.close()
        conn.close()

        if not request.is_json:
            flash(response["message"], response["status"])
            return redirect(url_for("index"))

        return jsonify(response), 200
    except Exception as e:
        print("❌ Service Request Error:", e)
        return jsonify({"status": "error", "message": "Server error."}), 500

# --- Run Server ---
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
