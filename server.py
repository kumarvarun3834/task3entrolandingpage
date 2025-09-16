# /backend/server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import re

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# --- Environment Variables ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "mini_browser")

# --- Database Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

# --- Helper: Validate Email ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- Routes ---
@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    # --- Basic Validation ---
    if not name or not email or not message:
        return jsonify({"status": "error", "message": "All fields are required."}), 400
    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid email address."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, message))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Message submitted successfully."}), 200
    except Exception as e:
        print("Database Error:", e)
        return jsonify({"status": "error", "message": "Server error. Please try again later."}), 500

# --- Run Server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
