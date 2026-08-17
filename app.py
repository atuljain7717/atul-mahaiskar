
# ============================================================
# ATUL MAHAISKAR PORTFOLIO
# BACKEND - APP.PY
#
# Flask Backend
# Contact Form
# SQLite Database
# Gmail Email Notification
# Admin Login
# Email OTP / 2-Step Verification
# ============================================================

import os
import random
import sqlite3
import smtplib

from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY"
)


# ============================================================
# CORS
# ============================================================

CORS(
    app,
    supports_credentials=True
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "messages.db"
)


# ============================================================
# SERVER CONFIGURATION
# ============================================================

PORT = int(
    os.getenv("PORT", "9000")
)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv("SMTP_PORT", "587")
)

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS",
    ""
)

EMAIL_APP_PASSWORD = os.getenv(
    "EMAIL_APP_PASSWORD",
    ""
)

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    EMAIL_ADDRESS
)


# ============================================================
# ADMIN CONFIGURATION
# ============================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    ""
)


# ============================================================
# OTP CONFIGURATION
# ============================================================

OTP_EXPIRY_MINUTES = int(
    os.getenv(
        "OTP_EXPIRY_MINUTES",
        "5"
    )
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TEXT NOT NULL,

            is_read INTEGER DEFAULT 0

        )
    """)

    connection.commit()

    connection.close()


initialize_database()


# ============================================================
# DATABASE HELPER
# ============================================================

def get_database():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# EMAIL HELPER
# ============================================================

def send_email(
    recipient,
    subject,
    body
):

    if not EMAIL_ADDRESS:

        raise RuntimeError(
            "EMAIL_ADDRESS is not configured."
        )

    if not EMAIL_APP_PASSWORD:

        raise RuntimeError(
            "EMAIL_APP_PASSWORD is not configured."
        )

    email = EmailMessage()

    email["From"] = EMAIL_ADDRESS
    email["To"] = recipient
    email["Subject"] = subject

    email.set_content(body)

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_APP_PASSWORD
        )

        server.send_message(email)


# ============================================================
# EMAIL VALIDATION
# ============================================================

def valid_email(email):

    if not email:
        return False

    if "@" not in email:
        return False

    parts = email.split("@")

    if len(parts) != 2:
        return False

    domain = parts[1]

    if "." not in domain:
        return False

    return True


# ============================================================
# HOME / API STATUS
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({

        "status": "online",

        "message":
            "Atul Mahaiskar Portfolio API",

        "version":
            "1.0",

        "database":
            "connected"

    }), 200


# ============================================================
# CONTACT FORM
#
# POST /api/contact
# ============================================================

@app.route(
    "/api/contact",
    methods=["POST"]
)
def contact():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "Invalid request. JSON data is required."

            }), 400


        # ----------------------------------------------------
        # GET FORM DATA
        # ----------------------------------------------------

        name = str(
            data.get("name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip()

        message = str(
            data.get("message", "")
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not name:

            return jsonify({

                "success": False,

                "message":
                    "Name is required."

            }), 400


        if not valid_email(email):

            return jsonify({

                "success": False,

                "message":
                    "Valid email is required."

            }), 400


        if not message:

            return jsonify({

                "success": False,

                "message":
                    "Message is required."

            }), 400


        if len(name) > 100:

            return jsonify({

                "success": False,

                "message":
                    "Name is too long."

            }), 400


        if len(email) > 254:

            return jsonify({

                "success": False,

                "message":
                    "Email address is too long."

            }), 400


        if len(message) > 5000:

            return jsonify({

                "success": False,

                "message":
                    "Message is too long."

            }), 400


        # ----------------------------------------------------
        # SAVE MESSAGE TO DATABASE
        # ----------------------------------------------------

        connection = get_database()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO messages
            (
                name,
                email,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                message,
                created_at
            )
        )

        connection.commit()

        message_id = cursor.lastrowid

        connection.close()


        # ----------------------------------------------------
        # EMAIL NOTIFICATION
        # ----------------------------------------------------

        email_sent = False

        email_subject = (
            "New Portfolio Message - "
            f"{name}"
        )

        email_body = f"""
Atul Mahaiskar Portfolio

You received a new message from your portfolio.

----------------------------------------
CONTACT DETAILS
----------------------------------------

Name:
{name}

Email:
{email}

Message ID:
{message_id}

Date:
{created_at}

----------------------------------------
MESSAGE
----------------------------------------

{message}

----------------------------------------
Atul Mahaiskar Portfolio
----------------------------------------
"""

        try:

            if ADMIN_EMAIL:

                send_email(
                    ADMIN_EMAIL,
                    email_subject,
                    email_body
                )

                email_sent = True

        except Exception as email_error:

            print(
                "Email notification error:",
                email_error
            )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "message":
                "Your message was received successfully.",

            "id":
                message_id,

            "email_notification":
                email_sent

        }), 201


    except Exception as error:

        print(
            "Contact API error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "An internal server error occurred."

        }), 500


# ============================================================
# ADMIN LOGIN - STEP 1
#
# POST /api/admin/login
#
# Username + Password
# ============================================================

@app.route(
    "/api/admin/login",
    methods=["POST"]
)
def admin_login():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "Invalid request."

            }), 400


        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )


        # ----------------------------------------------------
        # CHECK USERNAME
        # ----------------------------------------------------

        if username != ADMIN_USERNAME:

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password."

            }), 401


        # ----------------------------------------------------
        # CHECK PASSWORD CONFIGURATION
        # ----------------------------------------------------

        if not ADMIN_PASSWORD_HASH:

            return jsonify({

                "success": False,

                "message":
                    "Admin password is not configured."

            }), 500


        # ----------------------------------------------------
        # CHECK PASSWORD
        # ----------------------------------------------------

        try:

            password_valid = check_password_hash(
                ADMIN_PASSWORD_HASH,
                password
            )

        except Exception:

            password_valid = False


        if not password_valid:

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password."

            }), 401


        # ----------------------------------------------------
        # GENERATE OTP
        # ----------------------------------------------------

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        expires_at = (
            datetime.now()
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        )


        # ----------------------------------------------------
        # STORE OTP IN SESSION
        # ----------------------------------------------------

        session["admin_otp"] = otp

        session["admin_otp_expires"] = (
            expires_at.isoformat()
        )

        session["admin_authenticated"] = False


        # ----------------------------------------------------
        # SEND OTP EMAIL
        # ----------------------------------------------------

        otp_subject = (
            "Atul Mahaiskar Portfolio - "
            "Admin Verification Code"
        )

        otp_body = f"""
Atul Mahaiskar Portfolio

Your admin verification code is:

{otp}

This OTP will expire in
{OTP_EXPIRY_MINUTES} minutes.

If you did not request this code,
please ignore this email.

----------------------------------------
Admin Security
----------------------------------------
"""

        try:

            send_email(
                ADMIN_EMAIL,
                otp_subject,
                otp_body
            )

        except Exception as email_error:

            session.pop(
                "admin_otp",
                None
            )

            session.pop(
                "admin_otp_expires",
                None
            )

            print(
                "OTP email error:",
                email_error
            )

            return jsonify({

                "success": False,

                "message":
                    "Unable to send OTP. Check email configuration."

            }), 500


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "message":
                "OTP sent to your admin email.",

            "requires_otp":
                True

        }), 200


    except Exception as error:

        print(
            "Admin login error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Login failed."

        }), 500


# ============================================================
# VERIFY OTP - STEP 2
#
# POST /api/admin/verify-otp
# ============================================================

@app.route(
    "/api/admin/verify-otp",
    methods=["POST"]
)
def verify_otp():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "Invalid request."

            }), 400


        entered_otp = str(
            data.get("otp", "")
        ).strip()


        saved_otp = session.get(
            "admin_otp"
        )

        expiry = session.get(
            "admin_otp_expires"
        )


        # ----------------------------------------------------
        # CHECK OTP
        # ----------------------------------------------------

        if not saved_otp or not expiry:

            return jsonify({

                "success": False,

                "message":
                    "OTP expired or unavailable."

            }), 401


        expiry_time = datetime.fromisoformat(
            expiry
        )


        # ----------------------------------------------------
        # CHECK EXPIRATION
        # ----------------------------------------------------

        if datetime.now() > expiry_time:

            session.pop(
                "admin_otp",
                None
            )

            session.pop(
                "admin_otp_expires",
                None
            )

            return jsonify({

                "success": False,

                "message":
                    "OTP has expired."

            }), 401


        # ----------------------------------------------------
        # CHECK OTP
        # ----------------------------------------------------

        if entered_otp != saved_otp:

            return jsonify({

                "success": False,

                "message":
                    "Invalid OTP."

            }), 401


        # ----------------------------------------------------
        # AUTHENTICATION SUCCESS
        # ----------------------------------------------------

        session["admin_authenticated"] = True

        session.pop(
            "admin_otp",
            None
        )

        session.pop(
            "admin_otp_expires",
            None
        )


        return jsonify({

            "success": True,

            "message":
                "Two-step verification successful."

        }), 200


    except Exception as error:

        print(
            "OTP verification error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "OTP verification failed."

        }), 500


# ============================================================
# ADMIN AUTHENTICATION CHECK
# ============================================================

def admin_required():

    return session.get(
        "admin_authenticated",
        False
    )


# ============================================================
# GET ALL MESSAGES
#
# GET /api/messages
# ============================================================

@app.route(
    "/api/messages",
    methods=["GET"]
)
def get_messages():

    if not admin_required():

        return jsonify({

            "success": False,

            "message":
                "Admin authentication required."

        }), 401


    try:

        connection = get_database()

        cursor = connection.cursor()

        cursor.execute(
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
        )

        rows = cursor.fetchall()

        connection.close()


        messages = []


        for row in rows:

            messages.append({

                "id":
                    row["id"],

                "name":
                    row["name"],

                "email":
                    row["email"],

                "message":
                    row["message"],

                "created_at":
                    row["created_at"],

                "is_read":
                    bool(row["is_read"])

            })


        return jsonify({

            "success": True,

            "messages":
                messages

        }), 200


    except Exception as error:

        print(
            "Get messages error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to retrieve messages."

        }), 500


# ============================================================
# MARK MESSAGE AS READ
#
# PATCH /api/messages/<message_id>/read
# ============================================================

@app.route(
    "/api/messages/<int:message_id>/read",
    methods=["PATCH"]
)
def mark_message_read(message_id):

    if not admin_required():

        return jsonify({

            "success": False,

            "message":
                "Admin authentication required."

        }), 401


    try:

        connection = get_database()

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE id = ?
            """,
            (message_id,)
        )

        connection.commit()

        updated = cursor.rowcount

        connection.close()


        if updated == 0:

            return jsonify({

                "success": False,

                "message":
                    "Message not found."

            }), 404


        return jsonify({

            "success": True,

            "message":
                "Message marked as read."

        }), 200


    except Exception as error:

        print(
            "Mark read error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Unable to update message."

        }), 500


# ============================================================
# ADMIN LOGOUT
#
# POST /api/admin/logout
# ============================================================

@app.route(
    "/api/admin/logout",
    methods=["POST"]
)
def admin_logout():

    session.clear()

    return jsonify({

        "success": True,

        "message":
            "Logged out successfully."

    }), 200


# ============================================================
# ADMIN SESSION STATUS
#
# GET /api/admin/status
# ============================================================

@app.route(
    "/api/admin/status",
    methods=["GET"]
)
def admin_status():

    authenticated = admin_required()

    return jsonify({

        "authenticated":
            authenticated

    }), 200


# ============================================================
# HEALTH CHECK
#
# GET /api/health
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health_check():

    return jsonify({

        "success": True,

        "status":
            "healthy",

        "server":
            "Flask",

        "database":
            "SQLite",

        "email":
            bool(
                EMAIL_ADDRESS
                and EMAIL_APP_PASSWORD
            ),

        "otp":
            True

    }), 200


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "message":
            "API endpoint not found."

    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "success": False,

        "message":
            "Method not allowed for this endpoint."

    }), 405


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print(" ATUL MAHAISKAR PORTFOLIO")
    print(" Flask Backend")
    print("=" * 65)
    print()

    print(
        f" Server: http://127.0.0.1:{PORT}"
    )

    print(
        f" Database: {DATABASE_PATH}"
    )

    print()

    print(" API ENDPOINTS")
    print("-" * 65)

    print(" GET   /")
    print(" GET   /api/health")
    print(" POST  /api/contact")
    print(" POST  /api/admin/login")
    print(" POST  /api/admin/verify-otp")
    print(" GET   /api/admin/status")
    print(" GET   /api/messages")
    print(" PATCH /api/messages/<id>/read")
    print(" POST  /api/admin/logout")

    print()

    print("=" * 65)
    print(" Server starting...")
    print("=" * 65)
    print()


    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True
    );
