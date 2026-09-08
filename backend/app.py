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
# RESEND EMAIL CONFIGURATION
# ============================================================

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY",
    ""
)

RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
).strip()

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    ""
).strip()

OTP_EXPIRY_MINUTES = int(
    os.getenv(
        "OTP_EXPIRY_MINUTES",
        "5"
    )
)


if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# ============================================================
# EMAIL BRANDING
# ============================================================

PORTFOLIO_NAME = "Atul Mahaiskar"
PORTFOLIO_TITLE = "Software Developer • AI/ML • Full Stack"
PORTFOLIO_URL = "https://atul-mahaiskar.vercel.app"

EMAIL_LOGO_TEXT = "AM"


# ============================================================
# EMAIL HELPERS
# ============================================================

def escape_html(value):
    """
    Basic HTML escaping for user-provided content.
    """
    value = str(value)

    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def create_email_layout(
    heading,
    subtitle,
    content_html,
    footer_text="This email was sent from the Atul Mahaiskar portfolio."
):
    """
    Shared professional email layout.
    """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>{escape_html(heading)}</title>

<style>

    body {{
        margin: 0;
        padding: 0;
        background: #f4f7fb;
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Roboto,
            Helvetica,
            Arial,
            sans-serif;
        color: #172033;
    }}

    .wrapper {{
        width: 100%;
        padding: 40px 16px;
        box-sizing: border-box;
    }}

    .container {{
        width: 100%;
        max-width: 620px;
        margin: 0 auto;
        background: #ffffff;
        border-radius: 18px;
        overflow: hidden;
        box-shadow:
            0 12px 40px rgba(15, 23, 42, 0.08);
    }}

    .header {{
        padding: 30px 34px;
        background:
            linear-gradient(
                135deg,
                #111827 0%,
                #1f2937 100%
            );
        color: #ffffff;
    }}

    .brand {{
        display: flex;
        align-items: center;
    }}

    .logo {{
        width: 46px;
        height: 46px;
        border-radius: 12px;
        background: #ffffff;
        color: #111827;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 17px;
        margin-right: 13px;
    }}

    .brand-name {{
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 0.2px;
    }}

    .brand-title {{
        margin-top: 3px;
        color: #cbd5e1;
        font-size: 12px;
    }}

    .body {{
        padding: 34px;
    }}

    .heading {{
        margin: 0;
        font-size: 25px;
        line-height: 1.25;
        color: #111827;
    }}

    .subtitle {{
        margin: 10px 0 26px;
        color: #64748b;
        font-size: 14px;
        line-height: 1.6;
    }}

    .card {{
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
    }}

    .label {{
        display: block;
        margin-bottom: 6px;
        color: #64748b;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.7px;
        text-transform: uppercase;
    }}

    .value {{
        color: #111827;
        font-size: 15px;
        line-height: 1.6;
        word-break: break-word;
    }}

    .email-link {{
        color: #2563eb;
        text-decoration: none;
    }}

    .message-box {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        color: #334155;
        font-size: 14px;
        line-height: 1.75;
        white-space: pre-wrap;
        word-break: break-word;
    }}

    .meta {{
        display: table;
        width: 100%;
        margin-top: 20px;
    }}

    .meta-item {{
        display: table-cell;
        width: 50%;
        vertical-align: top;
        padding-right: 10px;
    }}

    .button {{
        display: inline-block;
        padding: 13px 20px;
        background: #111827;
        color: #ffffff !important;
        text-decoration: none;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 700;
        margin-top: 5px;
    }}

    .divider {{
        height: 1px;
        background: #e5e7eb;
        margin: 28px 0;
    }}

    .footer {{
        padding: 22px 34px;
        background: #f8fafc;
        border-top: 1px solid #e5e7eb;
        text-align: center;
    }}

    .footer-text {{
        margin: 0;
        color: #94a3b8;
        font-size: 11px;
        line-height: 1.6;
    }}

    .footer-link {{
        color: #64748b;
        text-decoration: none;
        font-weight: 600;
    }}

    @media only screen and (max-width: 600px) {{

        .wrapper {{
            padding: 18px 10px;
        }}

        .header {{
            padding: 24px;
        }}

        .body {{
            padding: 26px 22px;
        }}

        .footer {{
            padding: 20px 22px;
        }}

        .heading {{
            font-size: 22px;
        }}

        .meta {{
            display: block;
        }}

        .meta-item {{
            display: block;
            width: 100%;
            padding-right: 0;
            margin-bottom: 15px;
        }}

    }}

</style>
</head>

<body>

<div class="wrapper">

    <div class="container">

        <div class="header">

            <div class="brand">

                <div class="logo">
                    {EMAIL_LOGO_TEXT}
                </div>

                <div>

                    <div class="brand-name">
                        {PORTFOLIO_NAME}
                    </div>

                    <div class="brand-title">
                        {PORTFOLIO_TITLE}
                    </div>

                </div>

            </div>

        </div>

        <div class="body">

            <h1 class="heading">
                {heading}
            </h1>

            <p class="subtitle">
                {subtitle}
            </p>

            {content_html}

        </div>

        <div class="footer">

            <p class="footer-text">
                {escape_html(footer_text)}
                <br><br>

                <a
                    class="footer-link"
                    href="{PORTFOLIO_URL}"
                >
                    Visit Portfolio
                </a>
            </p>

        </div>

    </div>

</div>

</body>
</html>
"""


# ============================================================
# ADMIN CONTACT EMAIL
# ============================================================

def create_admin_contact_email(
    name,
    email,
    message,
    message_id,
    received_at
):

    safe_name = escape_html(name)
    safe_email = escape_html(email)
    safe_message = escape_html(message)
    safe_received = escape_html(received_at)

    content_html = f"""

<div class="card">

    <span class="label">
        From
    </span>

    <div class="value">
        <strong>{safe_name}</strong>
    </div>

</div>


<div class="card">

    <span class="label">
        Email Address
    </span>

    <div class="value">

        <a
            class="email-link"
            href="mailto:{safe_email}"
        >
            {safe_email}
        </a>

    </div>

</div>


<div class="card">

    <span class="label">
        Message
    </span>

    <div class="message-box">
        {safe_message}
    </div>

</div>


<div class="meta">

    <div class="meta-item">

        <span class="label">
            Message ID
        </span>

        <div class="value">
            #{message_id}
        </div>

    </div>

    <div class="meta-item">

        <span class="label">
            Received
        </span>

        <div class="value">
            {safe_received}
        </div>

    </div>

</div>


<div class="divider"></div>

<a
    class="button"
    href="mailto:{safe_email}?subject=Re:%20Your%20message%20to%20Atul%20Mahaiskar"
>
    Reply to {safe_name}
</a>

"""

    return create_email_layout(
        heading="New Contact Message",
        subtitle=(
            f"You received a new message through your "
            f"portfolio contact form."
        ),
        content_html=content_html,
        footer_text=(
            "This is an automated notification from "
            "your portfolio contact system."
        )
    )


# ============================================================
# VISITOR THANK-YOU EMAIL
# ============================================================

def create_visitor_confirmation_email(
    name,
    message_id,
    received_at
):

    safe_name = escape_html(name)
    safe_received = escape_html(received_at)

    content_html = f"""

<div class="card">

    <span class="label">
        Hello
    </span>

    <div class="value">

        <strong>
            {safe_name}
        </strong>

    </div>

</div>


<p
    style="
        margin: 0 0 18px;
        color: #475569;
        font-size: 14px;
        line-height: 1.8;
    "
>
    Thank you for reaching out through my portfolio.
    Your message has been successfully received.
</p>


<p
    style="
        margin: 0 0 18px;
        color: #475569;
        font-size: 14px;
        line-height: 1.8;
    "
>
    I appreciate you taking the time to contact me.
    I will review your message and get back to you
    as soon as possible.
</p>


<div class="card">

    <span class="label">
        Message Reference
    </span>

    <div class="value">

        <strong>
            #{message_id}
        </strong>

        <br>

        <span
            style="
                color: #64748b;
                font-size: 13px;
            "
        >
            Received {safe_received}
        </span>

    </div>

</div>


<div class="divider"></div>


<p
    style="
        margin: 0;
        color: #64748b;
        font-size: 13px;
        line-height: 1.7;
    "
>
    In the meantime, you can explore my portfolio
    and learn more about my projects and technical work.
</p>


<a
    class="button"
    href="{PORTFOLIO_URL}"
>
    Visit My Portfolio
</a>

"""

    return create_email_layout(
        heading="Thanks for reaching out",
        subtitle=(
            "Your message has been received successfully."
        ),
        content_html=content_html,
        footer_text=(
            "Thank you for contacting Atul Mahaiskar."
        )
    )


# ============================================================
# EMAIL SERVICE
# ============================================================

def send_email(
    to_email,
    subject,
    body,
    html_body=None,
    reply_to=None
):

    if not RESEND_API_KEY:

        print("=" * 60)
        print("EMAIL ERROR")
        print("RESEND_API_KEY is missing.")
        print("=" * 60)

        return {
            "success": False,
            "email_id": None,
            "error": "Resend API key is not configured."
        }

    if not to_email:

        print("=" * 60)
        print("EMAIL ERROR")
        print("Recipient email is missing.")
        print("=" * 60)

        return {
            "success": False,
            "email_id": None,
            "error": "Recipient email is missing."
        }

    try:

        print("=" * 60)
        print("RESEND API EMAIL REQUEST")
        print(f"From: {RESEND_FROM_EMAIL}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")

        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": body
        }

        if html_body:
            params["html"] = html_body

        if reply_to:
            params["reply_to"] = reply_to

        result = resend.Emails.send(params)

        print("RESEND API EMAIL ACCEPTED")

        email_id = None

        if isinstance(result, dict):

            email_id = result.get("id")

        else:

            email_id = getattr(
                result,
                "id",
                None
            )

        print(f"Email ID: {email_id}")
        print("=" * 60)

        return {
            "success": True,
            "email_id": email_id,
            "error": None
        }

    except Exception as error:

        print("=" * 60)
        print("RESEND API EMAIL FAILED")
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
        "server": "Flask",
        "email_provider": "Resend API"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "status": "healthy",
        "server": "Flask",
        "database": "SQLite",
        "email": bool(RESEND_API_KEY),
        "email_provider": "Resend API",
        "from_email": RESEND_FROM_EMAIL,
        "admin_email_configured": bool(ADMIN_EMAIL),
        "otp": bool(ADMIN_EMAIL)
    })


# ============================================================
# CONTACT FORM
# ============================================================

@app.route("/api/contact", methods=["POST"])
def contact():

    try:

        data = request.get_json(silent=True) or {}

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
                "message": "Name is required.",
                "email_sent": False
            }), 400

        if not email:

            return jsonify({
                "success": False,
                "message": "Email is required.",
                "email_sent": False
            }), 400

        if (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):

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

        if len(name) > 100:

            return jsonify({
                "success": False,
                "message": "Name is too long.",
                "email_sent": False
            }), 400

        if len(message) > 5000:

            return jsonify({
                "success": False,
                "message": "Message is too long.",
                "email_sent": False
            }), 400

        # ----------------------------------------------------
        # SAVE MESSAGE
        # ----------------------------------------------------

        received_at = datetime.utcnow().isoformat()

        connection = get_db()

        cursor = connection.execute(
            """
            INSERT INTO messages
            (
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
                received_at,
                0
            )
        )

        message_id = cursor.lastrowid

        connection.commit()
        connection.close()

        # ----------------------------------------------------
        # ADMIN EMAIL
        # ----------------------------------------------------

        admin_subject = (
            f"New Portfolio Contact — {name}"
        )

        admin_text = f"""
New contact message from your portfolio.

Name:
{name}

Email:
{email}

Message:
{message}

----------------------------------------

Message ID:
{message_id}

Received:
{received_at}

Reply to:
{email}
"""

        admin_html = create_admin_contact_email(
            name=name,
            email=email,
            message=message,
            message_id=message_id,
            received_at=received_at
        )

        admin_email_result = send_email(
            ADMIN_EMAIL,
            admin_subject,
            admin_text,
            html_body=admin_html,
            reply_to=email
        )

        admin_email_sent = bool(
            admin_email_result.get(
                "success",
                False
            )
        )

        # ----------------------------------------------------
        # VISITOR CONFIRMATION EMAIL
        # ----------------------------------------------------

        visitor_subject = (
            "Thanks for reaching out — Atul Mahaiskar"
        )

        visitor_text = f"""
Hi {name},

Thank you for reaching out through my portfolio.

Your message has been successfully received.

I appreciate you taking the time to contact me.
I will review your message and get back to you
as soon as possible.

Message Reference: #{message_id}
Received: {received_at}

Portfolio:
{PORTFOLIO_URL}

Best regards,

Atul Mahaiskar
Software Developer • AI/ML • Full Stack
"""

        visitor_html = create_visitor_confirmation_email(
            name=name,
            message_id=message_id,
            received_at=received_at
        )

        visitor_email_result = send_email(
            email,
            visitor_subject,
            visitor_text,
            html_body=visitor_html
        )

        visitor_email_sent = bool(
            visitor_email_result.get(
                "success",
                False
            )
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if admin_email_sent:

            print(
                f"Contact message {message_id} "
                "processed successfully."
            )

            return jsonify({
                "success": True,
                "message": (
                    "Your message has been sent successfully."
                ),
                "message_id": message_id,
                "email_sent": True,
                "admin_email_sent": True,
                "confirmation_email_sent": visitor_email_sent,
                "email_id": admin_email_result.get(
                    "email_id"
                )
            }), 200

        # ----------------------------------------------------
        # DATABASE SUCCESS / EMAIL FAILURE
        # ----------------------------------------------------

        print(
            f"Contact message {message_id} saved, "
            "but admin email delivery failed."
        )

        return jsonify({
            "success": False,
            "message": (
                "Your message was received, "
                "but the email notification could not be sent."
            ),
            "message_id": message_id,
            "email_sent": False,
            "admin_email_sent": False,
            "confirmation_email_sent": visitor_email_sent
        }), 502

    except Exception as error:

        print("=" * 60)
        print("CONTACT API ERROR")
        print(
            f"{type(error).__name__}: {error}"
        )
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "Unable to process your message.",
            "email_sent": False
        }), 500


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
# ADMIN LOGIN
# ============================================================

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
                "message": (
                    "Username and password are required."
                )
            }), 400

        if username != ADMIN_USERNAME:

            return jsonify({
                "success": False,
                "message": "Invalid credentials."
            }), 401

        if not ADMIN_PASSWORD_HASH:

            return jsonify({
                "success": False,
                "message": (
                    "Admin password is not configured."
                )
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
            random.randint(
                100000,
                999999
            )
        )

        session["admin_otp"] = otp

        session["admin_otp_expires"] = (
            datetime.utcnow()
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        ).isoformat()

        session["admin_username"] = username
        session.permanent = True

        # ----------------------------------------------------
        # OTP EMAIL
        # ----------------------------------------------------

        otp_subject = (
            "Your Portfolio Admin Login OTP"
        )

        otp_text = f"""
Your Portfolio Admin Login OTP is:

{otp}

This OTP will expire in
{OTP_EXPIRY_MINUTES} minutes.

If you did not request this login,
you can safely ignore this email.

Atul Mahaiskar Portfolio
"""

        otp_html_content = f"""

<div class="card">

    <span class="label">
        Verification Code
    </span>

    <div
        style="
            font-size: 34px;
            font-weight: 800;
            letter-spacing: 8px;
            color: #111827;
            text-align: center;
            padding: 12px 0;
        "
    >
        {otp}
    </div>

</div>


<p
    style="
        margin: 0;
        color: #64748b;
        font-size: 13px;
        line-height: 1.7;
    "
>
    This verification code will expire in
    <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
</p>


<div class="divider"></div>


<p
    style="
        margin: 0;
        color: #94a3b8;
        font-size: 12px;
        line-height: 1.7;
    "
>
    If you did not request this login,
    you can safely ignore this email.
</p>

"""

        otp_html = create_email_layout(
            heading="Admin Login Verification",
            subtitle=(
                "Use the verification code below "
                "to complete your administrator login."
            ),
            content_html=otp_html_content,
            footer_text=(
                "This is a security notification from "
                "your portfolio administration system."
            )
        )

        email_result = send_email(
            ADMIN_EMAIL,
            otp_subject,
            otp_text,
            html_body=otp_html
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
        print(
            f"{type(error).__name__}: {error}"
        )
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": "Login failed."
        }), 500


# ============================================================
# VERIFY OTP
# ============================================================

@app.route(
    "/api/admin/verify-otp",
    methods=["POST"]
)
def verify_otp():

    try:

        data = request.get_json(silent=True) or {}

        entered_otp = str(
            data.get("otp", "")
        ).strip()

        stored_otp = session.get(
            "admin_otp"
        )

        expires_at = session.get(
            "admin_otp_expires"
        )

        if not stored_otp or not expires_at:

            return jsonify({
                "success": False,
                "message": (
                    "OTP expired or unavailable."
                )
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
            "message": (
                "OTP verified successfully."
            )
        }), 200

    except Exception as error:

        print("=" * 60)
        print("OTP VERIFICATION ERROR")
        print(
            f"{type(error).__name__}: {error}"
        )
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": (
                "OTP verification failed."
            )
        }), 500


# ============================================================
# ADMIN STATUS
# ============================================================

@app.route(
    "/api/admin/status",
    methods=["GET"]
)
def admin_status():

    return jsonify({
        "success": True,
        "authenticated": bool(
            session.get(
                "admin_authenticated"
            )
        )
    })


# ============================================================
# GET MESSAGES
# ============================================================

@app.route(
    "/api/messages",
    methods=["GET"]
)
def get_messages():

    if not session.get(
        "admin_authenticated"
    ):

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
        print(
            f"{type(error).__name__}: {error}"
        )
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": (
                "Unable to load messages."
            )
        }), 500


# ============================================================
# MARK MESSAGE AS READ
# ============================================================

@app.route(
    "/api/messages/<int:message_id>/read",
    methods=["PATCH", "POST"]
)
def mark_message_read(message_id):

    if not session.get(
        "admin_authenticated"
    ):

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
            "message": (
                "Message marked as read."
            )
        }), 200

    except Exception as error:

        print("=" * 60)
        print("MARK MESSAGE READ ERROR")
        print(
            f"{type(error).__name__}: {error}"
        )
        print("=" * 60)

        return jsonify({
            "success": False,
            "message": (
                "Unable to update message."
            )
        }), 500


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route(
    "/api/admin/logout",
    methods=["POST"]
)
def admin_logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": (
            "Logged out successfully."
        )
    }), 200


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": (
            "Endpoint not found."
        )
    }), 404


@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "success": False,
        "message": (
            "Internal server error."
        )
    }), 500


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )