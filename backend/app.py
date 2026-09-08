import os
import random
import sqlite3
from datetime import datetime, timedelta

import resend
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY"
)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)
)


# ============================================================
# CORS
# ============================================================

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "https://atul-mahaiskar.vercel.app"
)

CORS(
    app,
    origins=[FRONTEND_ORIGIN],
    supports_credentials=True
)


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "messages.db")

os.makedirs(DATABASE_DIR, exist_ok=True)


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_db()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0
        )
        """
    )

    connection.commit()
    connection.close()


init_database()


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
)

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

OTP_EXPIRY_MINUTES = int(
    os.getenv("OTP_EXPIRY_MINUTES", "5")
)


# ============================================================
# RESEND EMAIL SERVICE
# ============================================================

def send_email(to_email, subject, body):
    """
    Send an email through the official Resend Python SDK.

    Returns:
        {
            "success": True/False,
            "email_id": "...",
            "error": "..."
        }
    """

    if not RESEND_API_KEY:
        print("RESEND ERROR: RESEND_API_KEY is missing.")

        return {
            "success": False,
            "email_id": None,
            "error": "RESEND_API_KEY is not configured."
        }

    if not to_email:
        print("RESEND ERROR: Recipient email is missing.")

        return {
            "success": False,
            "email_id": None,
            "error": "Recipient email is missing."
        }

    try:
        print("=" * 60)
        print("RESEND EMAIL REQUEST")
        print(f"From: {RESEND_FROM_EMAIL}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")

        # Configure Resend
        resend.api_key = RESEND_API_KEY

        email_params = {
            "from": RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }

        response = resend.Emails.send(email_params)

        print("Resend SDK response:")
        print(response)

        email_id = None

        # Handle dictionary response
        if isinstance(response, dict):
            email_id = response.get("id")

            if not email_id:
                data = response.get("data")

                if isinstance(data, dict):
                    email_id = data.get("id")

        # Handle object response
        else:
            email_id = getattr(response, "id", None)

            if not email_id:
                data = getattr(response, "data", None)

                if data:
                    email_id = getattr(data, "id", None)

        if email_id:
            print("RESEND ACCEPTED EMAIL")
            print(f"Resend Email ID: {email_id}")
            print("=" * 60)

            return {
                "success": True,
                "email_id": email_id,
                "error": None
            }

        print("RESEND ERROR: No email ID returned.")
        print("=" * 60)

        return {
            "success": False,
            "email_id": None,
            "error": "Resend did not return an email ID."
        }

    except Exception as error:
        print("=" * 60)
        print("RESEND EMAIL FAILED")
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")
        print("=" * 60)

        return {
            "success": False,
            "email_id": None,
            "error": str(error)
        }


# ============================================================
# ROOT
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "Atul Mahaiskar Portfolio Backend is running.",
        "server": "Flask"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():
    database_status = "SQLite"
    email_status = bool(RESEND_API_KEY)
    otp_status = bool(ADMIN_EMAIL)

    return jsonify({
        "success": True,
        "status": "healthy",
        "server": "Flask",
        "database": database_status,
        "email": email_status,
        "email_provider": "Resend",
        "otp": otp_status
    })


# ============================================================
# CONTACT FORM
# ============================================================

@app.route("/api/contact", methods=["POST"])
def contact():

    try:
        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        message = str(data.get("message", "")).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not name:
            return jsonify({
                "success": False,
                "message": "Name is required.",
                "email_sent": False
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "message": "Email is required.",
                "email_sent": False
            }), 400

        if "@" not in email:
            return jsonify({
                "success": False,
                "message": "Please enter a valid email address.",
                "email_sent": False
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "message": "Message is required.",
                "email_sent": False
            }), 400

        # ----------------------------------------------------
        # SAVE MESSAGE TO SQLITE
        # ----------------------------------------------------

        connection = get_db()

        cursor = connection.execute(
            """
            INSERT INTO messages
            (name, email, message, created_at, is_read)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                message,
                datetime.utcnow().isoformat(),
                0
            )
        )

        message_id = cursor.lastrowid

        connection.commit()
        connection.close()

        # ----------------------------------------------------
        # CREATE EMAIL
        # ----------------------------------------------------

        subject = f"New Portfolio Contact Message from {name}"

        body = f"""
New contact message from your portfolio.

Name:
{name}

Email:
{email}

Message:
{message}

----------------------------------------
Message ID: {message_id}
Received: {datetime.utcnow().isoformat()}
"""

        # ----------------------------------------------------
        # SEND EMAIL
        # ----------------------------------------------------

        email_result = send_email(
            ADMIN_EMAIL,
            subject,
            body
        )

        email_sent = email_result["success"]
        email_id = email_result.get("email_id")

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if email_sent:

            return jsonify({
                "success": True,
                "message": "Your message has been sent successfully.",
                "message_id": message_id,
                "email_sent": True,
                "email_id": email_id
            }), 200

        # ----------------------------------------------------
        # EMAIL FAILURE
        # ----------------------------------------------------

        print(
            f"Contact message {message_id} saved, "
            f"but email delivery failed."
        )

        return jsonify({
            "success": False,
            "message": (
                "Your message was received, but the "
                "email notification could not be sent."
            ),
            "message_id": message_id,
            "email_sent": False
        }), 502

    except Exception as error:

        print("=" * 60)
        print("CONTACT API ERROR")
        print(f"{type(error).__name__}: {error}")
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "Unable to process your message.",
            "email_sent": False
        }), 500


# ============================================================
# ADMIN LOGIN
# ============================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    ""
)


@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    try:
        data = request.get_json(silent=True) or {}

        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required."
            }), 400

        if username != ADMIN_USERNAME:
            return jsonify({
                "success": False,
                "message": "Invalid credentials."
            }), 401

        if not ADMIN_PASSWORD_HASH:
            return jsonify({
                "success": False,
                "message": "Admin password is not configured."
            }), 500

        if not check_password_hash(
            ADMIN_PASSWORD_HASH,
            password
        ):
            return jsonify({
                "success": False,
                "message": "Invalid credentials."
            }), 401

        # ----------------------------------------------------
        # GENERATE OTP
        # ----------------------------------------------------

        otp = str(
            random.randint(100000, 999999)
        )

        session["admin_otp"] = otp

        session["admin_otp_expires"] = (
            datetime.utcnow()
            + timedelta(minutes=OTP_EXPIRY_MINUTES)
        ).isoformat()

        session["admin_username"] = username

        session.permanent = True

        # ----------------------------------------------------
        # SEND OTP EMAIL
        # ----------------------------------------------------

        otp_subject = "Portfolio Admin Login OTP"

        otp_body = f"""
Your Portfolio Admin Login OTP is:

{otp}

This OTP will expire in
{OTP_EXPIRY_MINUTES} minutes.

If you did not request this login,
you can safely ignore this email.
"""

        email_result = send_email(
            ADMIN_EMAIL,
            otp_subject,
            otp_body
        )

        if not email_result["success"]:

            session.clear()

            return jsonify({
                "success": False,
                "message": (
                    "Unable to send OTP email. "
                    "Please try again later."
                ),
                "otp_required": False
            }), 502

        return jsonify({
            "success": True,
            "message": "OTP sent successfully.",
            "otp_required": True
        }), 200

    except Exception as error:

        print("=" * 60)
        print("ADMIN LOGIN ERROR")
        print(f"{type(error).__name__}: {error}")
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "Login failed."
        }), 500


# ============================================================
# VERIFY OTP
# ============================================================

@app.route("/api/admin/verify-otp", methods=["POST"])
def verify_otp():

    try:
        data = request.get_json(silent=True) or {}

        entered_otp = str(
            data.get("otp", "")
        ).strip()

        stored_otp = session.get("admin_otp")
        expires_at = session.get("admin_otp_expires")

        if not stored_otp or not expires_at:
            return jsonify({
                "success": False,
                "message": "OTP expired or unavailable."
            }), 401

        expiry_time = datetime.fromisoformat(
            expires_at
        )

        if datetime.utcnow() > expiry_time:
            session.clear()

            return jsonify({
                "success": False,
                "message": "OTP has expired."
            }), 401

        if entered_otp != stored_otp:
            return jsonify({
                "success": False,
                "message": "Invalid OTP."
            }), 401

        session["admin_authenticated"] = True

        session.pop("admin_otp", None)
        session.pop("admin_otp_expires", None)

        return jsonify({
            "success": True,
            "message": "OTP verified successfully."
        }), 200

    except Exception as error:

        print("=" * 60)
        print("OTP VERIFICATION ERROR")
        print(f"{type(error).__name__}: {error}")
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "OTP verification failed."
        }), 500


# ============================================================
# ADMIN STATUS
# ============================================================

@app.route("/api/admin/status", methods=["GET"])
def admin_status():

    return jsonify({
        "success": True,
        "authenticated": bool(
            session.get("admin_authenticated")
        )
    })


# ============================================================
# GET MESSAGES
# ============================================================

@app.route("/api/messages", methods=["GET"])
def get_messages():

    if not session.get("admin_authenticated"):
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    try:
        connection = get_db()

        rows = connection.execute(
            """
            SELECT
                id,
                name,
                email,
                message,
                created_at,
                is_read
            FROM messages
            ORDER BY id DESC
            """
        ).fetchall()

        connection.close()

        messages = [
            dict(row)
            for row in rows
        ]

        return jsonify({
            "success": True,
            "messages": messages
        }), 200

    except Exception as error:

        print("=" * 60)
        print("GET MESSAGES ERROR")
        print(f"{type(error).__name__}: {error}")
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "Unable to load messages."
        }), 500


# ============================================================
# MARK MESSAGE AS READ
# ============================================================

@app.route(
    "/api/messages/<int:message_id>/read",
    methods=["PATCH", "POST"]
)
def mark_message_read(message_id):

    if not session.get("admin_authenticated"):
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    try:
        connection = get_db()

        connection.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE id = ?
            """,
            (message_id,)
        )

        connection.commit()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Message marked as read."
        }), 200

    except Exception as error:

        print("=" * 60)
        print("MARK MESSAGE READ ERROR")
        print(f"{type(error).__name__}: {error}")
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "Unable to update message."
        }), 500


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "Endpoint not found."
    }), 404


@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error."
    }), 500


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "5000")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )