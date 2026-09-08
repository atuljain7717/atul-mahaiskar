import os
import random
import sqlite3
import json
import urllib.request
import urllib.error

from datetime import datetime, timedelta

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash
from dotenv import load_dotenv


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


# ============================================================
# SESSION CONFIGURATION
# ============================================================

# Required when frontend is hosted on Vercel
# and backend is hosted on Render.

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
    origins=[
        FRONTEND_ORIGIN
    ],
    supports_credentials=True
)


# ============================================================
# DATABASE
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


# Make sure database directory exists
os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)


# ============================================================
# SERVER
# ============================================================

PORT = int(
    os.getenv(
        "PORT",
        "9000"
    )
)


# ============================================================
# RESEND EMAIL CONFIGURATION
# ============================================================

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY",
    ""
)

RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
)

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    ""
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
# DATABASE HELPERS
# ============================================================

def get_db():
    """
    Create and return a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """
    Create required database tables.
    """

    connection = get_db()

    cursor = connection.cursor()

    cursor.execute(
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


# Initialize database
initialize_database()


# ============================================================
# RESEND EMAIL FUNCTION
# ============================================================

def send_email(
    to_email,
    subject,
    body
):
    """
    Send email using Resend HTTPS API.

    Important:
    - Does NOT use Gmail SMTP.
    - Does NOT require SMTP port 587.
    - Uses HTTPS.
    - Email failure does NOT crash the API.
    - Returns True when email succeeds.
    - Returns False when email fails.
    """

    try:

        # ----------------------------------------------------
        # Validate API key
        # ----------------------------------------------------

        if not RESEND_API_KEY:

            print(
                "RESEND_API_KEY is not configured."
            )

            return False


        # ----------------------------------------------------
        # Validate sender
        # ----------------------------------------------------

        if not RESEND_FROM_EMAIL:

            print(
                "RESEND_FROM_EMAIL is not configured."
            )

            return False


        # ----------------------------------------------------
        # Validate recipient
        # ----------------------------------------------------

        if not to_email:

            print(
                "Recipient email is not configured."
            )

            return False


        # ----------------------------------------------------
        # Resend API endpoint
        # ----------------------------------------------------

        resend_url = (
            "https://api.resend.com/emails"
        )


        # ----------------------------------------------------
        # Email payload
        # ----------------------------------------------------

        payload = {
            "from": RESEND_FROM_EMAIL,
            "to": [
                to_email
            ],
            "subject": subject,
            "text": body
        }


        payload_bytes = json.dumps(
            payload
        ).encode(
            "utf-8"
        )


        # ----------------------------------------------------
        # HTTP request
        # ----------------------------------------------------

        request_object = urllib.request.Request(
            resend_url,
            data=payload_bytes,
            method="POST"
        )


        request_object.add_header(
            "Authorization",
            f"Bearer {RESEND_API_KEY}"
        )

        request_object.add_header(
            "Content-Type",
            "application/json"
        )

        request_object.add_header(
            "Accept",
            "application/json"
        )


        # ----------------------------------------------------
        # Send request
        # ----------------------------------------------------

        print(
            "Sending email using Resend..."
        )

        print(
            f"Recipient: {to_email}"
        )


        with urllib.request.urlopen(
            request_object,
            timeout=15
        ) as response:

            response_body = response.read().decode(
                "utf-8"
            )

            status_code = response.status


        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        if 200 <= status_code < 300:

            print(
                "Email sent successfully using Resend."
            )

            return True


        print(
            f"Resend returned HTTP {status_code}"
        )

        print(
            response_body
        )

        return False


    # --------------------------------------------------------
    # HTTP error
    # --------------------------------------------------------

    except urllib.error.HTTPError as error:

        print(
            "Resend email sending failed."
        )

        print(
            f"HTTPError: {error.code}"
        )

        try:

            error_body = error.read().decode(
                "utf-8"
            )

            print(
                error_body
            )

        except Exception:
            pass

        return False


    # --------------------------------------------------------
    # Network / URL error
    # --------------------------------------------------------

    except urllib.error.URLError as error:

        print(
            "Resend network error:"
        )

        print(
            f"URLError: {error.reason}"
        )

        return False


    # --------------------------------------------------------
    # Other error
    # --------------------------------------------------------

    except Exception as error:

        print(
            "Resend email sending failed:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return False


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify(
        {
            "success": True,
            "message": (
                "Atul Mahaiskar Portfolio "
                "Backend is running."
            ),
            "server": "Flask"
        }
    ), 200


@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    database_status = False

    try:

        connection = get_db()

        connection.execute(
            "SELECT 1"
        )

        connection.close()

        database_status = True

    except Exception as error:

        print(
            f"Database health error: {error}"
        )


    return jsonify(
        {
            "success": True,
            "status": "healthy",
            "server": "Flask",
            "database": (
                "SQLite"
                if database_status
                else "SQLite error"
            ),
            "email": bool(
                RESEND_API_KEY
                and RESEND_FROM_EMAIL
                and ADMIN_EMAIL
            ),
            "email_provider": "Resend",
            "otp": True
        }
    ), 200


# ============================================================
# CONTACT FORM
# ============================================================

@app.route(
    "/api/contact",
    methods=["POST"]
)
def contact():

    try:

        # ----------------------------------------------------
        # Read request data
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid request data."
                    )
                }
            ), 400


        name = str(
            data.get(
                "name",
                ""
            )
        ).strip()


        email = str(
            data.get(
                "email",
                ""
            )
        ).strip()


        message = str(
            data.get(
                "message",
                ""
            )
        ).strip()


        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not name:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Name is required."
                    )
                }
            ), 400


        if not email:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Email is required."
                    )
                }
            ), 400


        if "@" not in email or "." not in email:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Please enter a valid "
                        "email address."
                    )
                }
            ), 400


        if not message:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Message is required."
                    )
                }
            ), 400


        # ----------------------------------------------------
        # Save message to SQLite FIRST
        # ----------------------------------------------------

        created_at = datetime.utcnow().isoformat()

        connection = get_db()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO messages (
                name,
                email,
                message,
                created_at,
                is_read
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                message,
                created_at,
                0
            )
        )

        connection.commit()

        message_id = cursor.lastrowid

        connection.close()


        # ----------------------------------------------------
        # Prepare notification email
        # ----------------------------------------------------

        email_subject = (
            f"New Portfolio Contact Message "
            f"from {name}"
        )


        email_body = f"""
New message received from your portfolio website.

Name:
{name}

Email:
{email}

Message:
{message}

Message ID:
{message_id}

Received:
{created_at}
"""


        # ----------------------------------------------------
        # Send notification
        # ----------------------------------------------------

        email_sent = send_email(
            ADMIN_EMAIL,
            email_subject,
            email_body
        )


        # ----------------------------------------------------
        # Return success after DB save
        # ----------------------------------------------------

        return jsonify(
            {
                "success": True,
                "message": (
                    "Your message has been "
                    "sent successfully."
                ),
                "message_id": message_id,
                "email_sent": email_sent
            }
        ), 200


    except Exception as error:

        print(
            "Contact endpoint error:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return jsonify(
            {
                "success": False,
                "message": (
                    "Unable to process your "
                    "message right now."
                )
            }
        ), 500


# ============================================================
# ADMIN LOGIN
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

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid request data."
                    )
                }
            ), 400


        username = str(
            data.get(
                "username",
                ""
            )
        ).strip()


        password = str(
            data.get(
                "password",
                ""
            )
        )


        # ----------------------------------------------------
        # Validate username
        # ----------------------------------------------------

        if username != ADMIN_USERNAME:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid username or password."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Validate password hash
        # ----------------------------------------------------

        if not ADMIN_PASSWORD_HASH:

            print(
                "ADMIN_PASSWORD_HASH is not configured."
            )

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Admin authentication "
                        "is not configured."
                    )
                }
            ), 500


        # ----------------------------------------------------
        # Validate password
        # ----------------------------------------------------

        if not check_password_hash(
            ADMIN_PASSWORD_HASH,
            password
        ):

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid username or password."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Generate OTP
        # ----------------------------------------------------

        otp = str(
            random.randint(
                100000,
                999999
            )
        )


        otp_expires = (
            datetime.utcnow()
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        )


        # ----------------------------------------------------
        # Store OTP in session
        # ----------------------------------------------------

        session.permanent = True

        session["admin_otp"] = otp

        session["admin_otp_expires"] = (
            otp_expires.isoformat()
        )

        session["admin_otp_verified"] = False


        # ----------------------------------------------------
        # OTP email
        # ----------------------------------------------------

        otp_subject = (
            "Portfolio Admin Login OTP"
        )


        otp_body = f"""
Your Portfolio Admin Login OTP is:

{otp}

This OTP will expire in
{OTP_EXPIRY_MINUTES} minutes.

If you did not request this login,
please ignore this email.
"""


        email_sent = send_email(
            ADMIN_EMAIL,
            otp_subject,
            otp_body
        )


        # ----------------------------------------------------
        # Email failed
        # ----------------------------------------------------

        if not email_sent:

            session.pop(
                "admin_otp",
                None
            )

            session.pop(
                "admin_otp_expires",
                None
            )

            session.pop(
                "admin_otp_verified",
                None
            )

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Unable to send OTP email. "
                        "Please check the Resend "
                        "email configuration."
                    )
                }
            ), 500


        return jsonify(
            {
                "success": True,
                "message": (
                    "OTP sent successfully."
                ),
                "otp_required": True
            }
        ), 200


    except Exception as error:

        print(
            "Admin login error:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return jsonify(
            {
                "success": False,
                "message": (
                    "Unable to process "
                    "admin login."
                )
            }
        ), 500


# ============================================================
# VERIFY OTP
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

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid request data."
                    )
                }
            ), 400


        entered_otp = str(
            data.get(
                "otp",
                ""
            )
        ).strip()


        stored_otp = session.get(
            "admin_otp"
        )

        expiry_string = session.get(
            "admin_otp_expires"
        )


        # ----------------------------------------------------
        # Check OTP existence
        # ----------------------------------------------------

        if not stored_otp or not expiry_string:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "OTP expired or not found."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Check expiry
        # ----------------------------------------------------

        try:

            expiry_time = datetime.fromisoformat(
                expiry_string
            )

        except ValueError:

            session.clear()

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid OTP session."
                    )
                }
            ), 401


        if datetime.utcnow() > expiry_time:

            session.pop(
                "admin_otp",
                None
            )

            session.pop(
                "admin_otp_expires",
                None
            )

            session.pop(
                "admin_otp_verified",
                None
            )

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "OTP has expired."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Check OTP
        # ----------------------------------------------------

        if entered_otp != stored_otp:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid OTP."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Authenticate admin
        # ----------------------------------------------------

        session["admin_authenticated"] = True

        session["admin_otp_verified"] = True


        # Remove OTP after successful verification

        session.pop(
            "admin_otp",
            None
        )

        session.pop(
            "admin_otp_expires",
            None
        )


        return jsonify(
            {
                "success": True,
                "message": (
                    "Admin authentication "
                    "successful."
                )
            }
        ), 200


    except Exception as error:

        print(
            "OTP verification error:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return jsonify(
            {
                "success": False,
                "message": (
                    "Unable to verify OTP."
                )
            }
        ), 500


# ============================================================
# ADMIN STATUS
# ============================================================

@app.route(
    "/api/admin/status",
    methods=["GET"]
)
def admin_status():

    authenticated = session.get(
        "admin_authenticated",
        False
    )


    return jsonify(
        {
            "success": True,
            "authenticated": bool(
                authenticated
            )
        }
    ), 200


# ============================================================
# GET MESSAGES
# ============================================================

@app.route(
    "/api/messages",
    methods=["GET"]
)
def get_messages():

    try:

        # ----------------------------------------------------
        # Admin authentication
        # ----------------------------------------------------

        if not session.get(
            "admin_authenticated",
            False
        ):

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Unauthorized."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Fetch messages
        # ----------------------------------------------------

        connection = get_db()

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

            messages.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "email": row["email"],
                    "message": row["message"],
                    "created_at": row["created_at"],
                    "is_read": bool(
                        row["is_read"]
                    )
                }
            )


        return jsonify(
            {
                "success": True,
                "messages": messages,
                "count": len(messages)
            }
        ), 200


    except Exception as error:

        print(
            "Get messages error:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return jsonify(
            {
                "success": False,
                "message": (
                    "Unable to load messages."
                )
            }
        ), 500


# ============================================================
# MARK MESSAGE AS READ
# ============================================================

@app.route(
    "/api/messages/<int:message_id>/read",
    methods=["PATCH"]
)
def mark_message_read(
    message_id
):

    try:

        # ----------------------------------------------------
        # Admin authentication
        # ----------------------------------------------------

        if not session.get(
            "admin_authenticated",
            False
        ):

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Unauthorized."
                    )
                }
            ), 401


        # ----------------------------------------------------
        # Update message
        # ----------------------------------------------------

        connection = get_db()

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE id = ?
            """,
            (
                message_id,
            )
        )

        connection.commit()

        updated_rows = cursor.rowcount

        connection.close()


        if updated_rows == 0:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Message not found."
                    )
                }
            ), 404


        return jsonify(
            {
                "success": True,
                "message": (
                    "Message marked as read."
                )
            }
        ), 200


    except Exception as error:

        print(
            "Mark message read error:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return jsonify(
            {
                "success": False,
                "message": (
                    "Unable to update message."
                )
            }
        ), 500


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route(
    "/api/admin/logout",
    methods=["POST"]
)
def admin_logout():

    session.clear()


    return jsonify(
        {
            "success": True,
            "message": (
                "Logged out successfully."
            )
        }
    ), 200


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify(
        {
            "success": False,
            "message": (
                "Endpoint not found."
            )
        }
    ), 404


@app.errorhandler(500)
def internal_error(error):

    return jsonify(
        {
            "success": False,
            "message": (
                "Internal server error."
            )
        }
    ), 500


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )