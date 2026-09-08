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

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

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


initialize_database()


# ============================================================
# RESEND EMAIL SERVICE
# ============================================================

def send_email(
    to_email,
    subject,
    body
):
    """
    Send an email using the Resend HTTPS API.

    Returns:

        {
            "success": True/False,
            "email_id": "...",
            "error": None
        }

    The browser is NOT involved in this process.
    """

    try:

        # ----------------------------------------------------
        # Validate configuration
        # ----------------------------------------------------

        if not RESEND_API_KEY:

            print(
                "RESEND ERROR: API key is missing."
            )

            return {
                "success": False,
                "email_id": None,
                "error": (
                    "RESEND_API_KEY is not configured."
                )
            }


        if not RESEND_FROM_EMAIL:

            print(
                "RESEND ERROR: sender email is missing."
            )

            return {
                "success": False,
                "email_id": None,
                "error": (
                    "RESEND_FROM_EMAIL is not configured."
                )
            }


        if not to_email:

            print(
                "RESEND ERROR: recipient email is missing."
            )

            return {
                "success": False,
                "email_id": None,
                "error": (
                    "ADMIN_EMAIL is not configured."
                )
            }


        # ----------------------------------------------------
        # Resend API
        # ----------------------------------------------------

        resend_url = (
            "https://api.resend.com/emails"
        )


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
        # Logging
        # ----------------------------------------------------

        print("")
        print(
            "========================================"
        )

        print(
            "RESEND EMAIL REQUEST"
        )

        print(
            f"From: {RESEND_FROM_EMAIL}"
        )

        print(
            f"To: {to_email}"
        )

        print(
            f"Subject: {subject}"
        )

        print(
            "========================================"
        )


        # ----------------------------------------------------
        # Send request
        # ----------------------------------------------------

        with urllib.request.urlopen(
            request_object,
            timeout=20
        ) as response:

            response_body = (
                response
                .read()
                .decode("utf-8")
            )

            status_code = response.status


        print(
            f"Resend HTTP status: {status_code}"
        )

        print(
            f"Resend response: {response_body}"
        )


        # ----------------------------------------------------
        # Parse response
        # ----------------------------------------------------

        try:

            resend_result = json.loads(
                response_body
            )

        except json.JSONDecodeError:

            resend_result = {}


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if 200 <= status_code < 300:

            email_id = (
                resend_result.get("id")
            )


            print(
                "RESEND ACCEPTED EMAIL"
            )

            print(
                f"Resend Email ID: {email_id}"
            )


            return {
                "success": True,
                "email_id": email_id,
                "error": None
            }


        # ----------------------------------------------------
        # RESEND API FAILURE
        # ----------------------------------------------------

        error_message = (
            resend_result.get("message")
            or resend_result.get("error")
            or response_body
            or f"HTTP {status_code}"
        )


        print(
            "RESEND REJECTED EMAIL"
        )

        print(
            f"Error: {error_message}"
        )


        return {
            "success": False,
            "email_id": None,
            "error": str(error_message)
        }


    # ========================================================
    # HTTP ERROR
    # ========================================================

    except urllib.error.HTTPError as error:

        try:

            error_body = (
                error
                .read()
                .decode("utf-8")
            )

        except Exception:

            error_body = ""


        print(
            "RESEND HTTP ERROR"
        )

        print(
            f"HTTP status: {error.code}"
        )

        print(
            f"Response: {error_body}"
        )


        try:

            error_json = json.loads(
                error_body
            )

            error_message = (
                error_json.get("message")
                or error_json.get("error")
                or error_body
            )

        except Exception:

            error_message = error_body


        return {
            "success": False,
            "email_id": None,
            "error": str(error_message)
        }


    # ========================================================
    # NETWORK ERROR
    # ========================================================

    except urllib.error.URLError as error:

        print(
            "RESEND NETWORK ERROR"
        )

        print(
            f"Reason: {error.reason}"
        )


        return {
            "success": False,
            "email_id": None,
            "error": str(error.reason)
        }


    # ========================================================
    # UNKNOWN ERROR
    # ========================================================

    except Exception as error:

        print(
            "RESEND UNEXPECTED ERROR"
        )

        print(
            f"{type(error).__name__}: {error}"
        )


        return {
            "success": False,
            "email_id": None,
            "error": str(error)
        }


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
        # Read request
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
        # Save message
        # ----------------------------------------------------

        created_at = (
            datetime.utcnow()
            .isoformat()
        )


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
        # Prepare admin email
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
        # Send admin email
        # ----------------------------------------------------

        email_result = send_email(
            ADMIN_EMAIL,
            email_subject,
            email_body
        )


        email_sent = (
            email_result["success"]
        )


        email_id = (
            email_result.get(
                "email_id"
            )
        )


        email_error = (
            email_result.get(
                "error"
            )
        )


        # ----------------------------------------------------
        # EMAIL SUCCESS
        # ----------------------------------------------------

        if email_sent:

            return jsonify(
                {
                    "success": True,
                    "message": (
                        "Your message has been "
                        "sent successfully."
                    ),
                    "message_id": message_id,
                    "email_sent": True,
                    "email_id": email_id
                }
            ), 200


        # ----------------------------------------------------
        # MESSAGE SAVED BUT EMAIL FAILED
        # ----------------------------------------------------

        print(
            "WARNING: Contact message saved "
            "but email failed."
        )

        print(
            f"Email error: {email_error}"
        )


        return jsonify(
            {
                "success": True,
                "message": (
                    "Your message was received, "
                    "but the email notification "
                    "could not be sent."
                ),
                "message_id": message_id,
                "email_sent": False,
                "email_id": None,
                "email_error": email_error
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


        if username != ADMIN_USERNAME:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid username or password."
                    )
                }
            ), 401


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
        # Store OTP
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


        otp_result = send_email(
            ADMIN_EMAIL,
            otp_subject,
            otp_body
        )


        # ----------------------------------------------------
        # OTP email failure
        # ----------------------------------------------------

        if not otp_result["success"]:

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


            print(
                "OTP email failed:"
            )

            print(
                otp_result.get(
                    "error"
                )
            )


            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Unable to send OTP email."
                    )
                }
            ), 500


        return jsonify(
            {
                "success": True,
                "message": (
                    "OTP sent successfully."
                ),
                "otp_required": True,
                "email_id": (
                    otp_result.get(
                        "email_id"
                    )
                )
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


        if not stored_otp or not expiry_string:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "OTP expired or not found."
                    )
                }
            ), 401


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


        if entered_otp != stored_otp:

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Invalid OTP."
                    )
                }
            ), 401


        session["admin_authenticated"] = True

        session["admin_otp_verified"] = True


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