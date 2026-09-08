import os
import random
import sqlite3
import time
from datetime import datetime, timedelta
from urllib.parse import quote

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
# FLASK APPLICATION
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
).strip()

CORS(
    app,
    origins=[FRONTEND_ORIGIN],
    supports_credentials=True
)


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    connection = sqlite3.connect(
        DATABASE_PATH
    )

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
            is_read INTEGER DEFAULT 0,
            ip_address TEXT,
            user_agent TEXT
        )
        """
    )

    connection.commit()

    # --------------------------------------------------------
    # Backward compatibility for existing database
    # --------------------------------------------------------

    existing_columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(messages)"
        ).fetchall()
    }

    if "ip_address" not in existing_columns:
        connection.execute(
            "ALTER TABLE messages ADD COLUMN ip_address TEXT"
        )

    if "user_agent" not in existing_columns:
        connection.execute(
            "ALTER TABLE messages ADD COLUMN user_agent TEXT"
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
).strip()

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
# PORTFOLIO BRANDING
# ============================================================

PORTFOLIO_NAME = "Atul Mahaiskar"

PORTFOLIO_TITLE = (
    "Software Developer • AI/ML • Full Stack"
)

PORTFOLIO_URL = (
    "https://atul-mahaiskar.vercel.app"
)

EMAIL_LOGO_TEXT = "AM"


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
).strip()

ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    ""
).strip()


# ============================================================
# SIMPLE RATE LIMITING
# ============================================================

RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv(
        "CONTACT_RATE_LIMIT_SECONDS",
        "60"
    )
)

RATE_LIMIT_MAX_REQUESTS = int(
    os.getenv(
        "CONTACT_RATE_LIMIT_MAX_REQUESTS",
        "3"
    )
)

contact_rate_limits = {}


def is_rate_limited(ip_address):

    now = time.time()

    requests_for_ip = contact_rate_limits.get(
        ip_address,
        []
    )

    requests_for_ip = [
        timestamp
        for timestamp in requests_for_ip
        if now - timestamp < RATE_LIMIT_WINDOW_SECONDS
    ]

    if len(requests_for_ip) >= RATE_LIMIT_MAX_REQUESTS:

        contact_rate_limits[ip_address] = requests_for_ip

        return True

    requests_for_ip.append(now)

    contact_rate_limits[ip_address] = requests_for_ip

    return False


# ============================================================
# HTML ESCAPING
# ============================================================

def escape_html(value):

    value = str(value)

    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


# ============================================================
# EMAIL LAYOUT
# ============================================================

def create_email_layout(
    heading,
    subtitle,
    content_html,
    footer_text=(
        "This email was sent from the "
        "Atul Mahaiskar portfolio."
    )
):

    safe_heading = escape_html(
        heading
    )

    safe_subtitle = escape_html(
        subtitle
    )

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="color-scheme"
    content="light"
>

<title>
    {safe_heading}
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    padding: 0;

    background: #eef2f7;

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

table {{
    border-collapse: collapse;
}}

a {{
    text-decoration: none;
}}

.email-wrapper {{
    width: 100%;

    padding:
        42px 15px;
}}

.email-container {{
    width: 100%;
    max-width: 650px;

    margin: 0 auto;

    background: #ffffff;

    border-radius: 22px;

    overflow: hidden;

    border: 1px solid #e5e7eb;

    box-shadow:
        0 20px 60px
        rgba(15, 23, 42, 0.10);
}}


/* =========================================================
   HEADER
========================================================= */

.header {{
    position: relative;

    padding:
        34px 36px;

    background:
        linear-gradient(
            135deg,
            #05070c 0%,
            #111827 50%,
            #1e293b 100%
        );

    color: #ffffff;
}}

.header-glow {{
    position: absolute;

    width: 190px;
    height: 190px;

    right: -80px;
    top: -95px;

    border-radius: 50%;

    background:
        rgba(255,255,255,0.055);
}}

.header-line {{
    position: absolute;

    left: 36px;
    right: 36px;
    bottom: 0;

    height: 1px;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,0.20),
            transparent
        );
}}

.brand {{
    position: relative;

    display: flex;

    align-items: center;

    gap: 15px;

    z-index: 2;
}}

.logo {{
    width: 56px;
    height: 56px;

    min-width: 56px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 16px;

    background:
        linear-gradient(
            145deg,
            #ffffff,
            #e5e7eb
        );

    color: #0f172a;

    font-size: 18px;

    font-weight: 900;

    letter-spacing: -2px;

    box-shadow:
        0 9px 25px
        rgba(0,0,0,0.25);
}}

.brand-name {{
    margin: 0;

    color: #ffffff;

    font-size: 19px;

    font-weight: 800;

    letter-spacing: -0.3px;
}}

.brand-title {{
    margin-top: 5px;

    color: #aeb8c8;

    font-size: 11px;

    line-height: 1.4;

    letter-spacing: 0.3px;
}}

.brand-status {{
    display: inline-block;

    margin-top: 8px;

    padding:
        4px 9px;

    border-radius: 999px;

    background:
        rgba(255,255,255,0.06);

    border:
        1px solid
        rgba(255,255,255,0.10);

    color: #cbd5e1;

    font-size: 9px;

    font-weight: 800;

    letter-spacing: 0.8px;

    text-transform: uppercase;
}}


/* =========================================================
   BODY
========================================================= */

.body {{
    padding:
        39px 36px 36px;
}}

.eyebrow {{
    margin-bottom: 9px;

    color: #64748b;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 1.5px;

    text-transform: uppercase;
}}

.heading {{
    margin: 0;

    color: #0f172a;

    font-size: 28px;

    line-height: 1.2;

    font-weight: 850;

    letter-spacing: -0.8px;
}}

.subtitle {{
    margin:
        11px 0 29px;

    color: #64748b;

    font-size: 14px;

    line-height: 1.7;
}}


/* =========================================================
   STATUS BADGE
========================================================= */

.message-status {{
    display: inline-block;

    margin-bottom: 18px;

    padding:
        6px 10px;

    border-radius: 999px;

    background: #f1f5f9;

    border:
        1px solid #e2e8f0;

    color: #475569;

    font-size: 9px;

    font-weight: 800;

    letter-spacing: 0.9px;

    text-transform: uppercase;
}}


/* =========================================================
   CARDS
========================================================= */

.card {{
    margin-bottom: 16px;

    padding: 20px;

    background: #f8fafc;

    border:
        1px solid #e7ebf0;

    border-radius: 15px;
}}

.label {{
    display: block;

    margin-bottom: 7px;

    color: #64748b;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 1px;

    text-transform: uppercase;
}}

.value {{
    color: #172033;

    font-size: 15px;

    line-height: 1.65;

    word-break: break-word;
}}

.email-link {{
    color: #334155;

    font-weight: 650;

    border-bottom:
        1px solid #cbd5e1;
}}

.message-box {{
    padding: 18px;

    background: #ffffff;

    border:
        1px solid #e2e8f0;

    border-radius: 12px;

    color: #334155;

    font-size: 14px;

    line-height: 1.8;

    white-space: pre-wrap;

    word-break: break-word;
}}


/* =========================================================
   META
========================================================= */

.meta {{
    width: 100%;

    margin-top: 20px;
}}

.meta-item {{
    width: 50%;

    vertical-align: top;

    padding-right: 10px;
}}

.meta-item:last-child {{
    padding-right: 0;

    padding-left: 10px;
}}

.meta-label {{
    display: block;

    margin-bottom: 5px;

    color: #94a3b8;

    font-size: 9px;

    font-weight: 800;

    letter-spacing: 0.9px;

    text-transform: uppercase;
}}

.meta-value {{
    color: #475569;

    font-size: 11px;

    font-weight: 650;
}}


/* =========================================================
   BUTTON
========================================================= */

.button-wrapper {{
    margin-top: 27px;
}}

.button {{
    display: inline-block;

    padding:
        13px 21px;

    border-radius: 11px;

    background: #111827;

    color: #ffffff !important;

    font-size: 13px;

    font-weight: 750;

    letter-spacing: 0.1px;

    box-shadow:
        0 8px 20px
        rgba(15,23,42,0.16);
}}


/* =========================================================
   DIVIDER
========================================================= */

.divider {{
    height: 1px;

    margin:
        30px 0;

    background: #e5e7eb;
}}


/* =========================================================
   FOOTER
========================================================= */

.footer {{
    padding:
        25px 36px;

    background: #f8fafc;

    border-top:
        1px solid #e5e7eb;

    text-align: center;
}}

.footer-brand {{
    margin-bottom: 7px;

    color: #334155;

    font-size: 12px;

    font-weight: 750;
}}

.footer-text {{
    margin: 0;

    color: #94a3b8;

    font-size: 10px;

    line-height: 1.7;
}}

.footer-link {{
    display: inline-block;

    margin-top: 10px;

    color: #475569;

    font-size: 11px;

    font-weight: 750;
}}

.footer-mark {{
    margin-top: 13px;

    color: #cbd5e1;

    font-size: 9px;

    font-weight: 750;

    letter-spacing: 1.5px;

    text-transform: uppercase;
}}


/* =========================================================
   MOBILE
========================================================= */

@media only screen and (max-width: 600px) {{

    .email-wrapper {{
        padding:
            18px 8px;
    }}

    .email-container {{
        border-radius: 17px;
    }}

    .header {{
        padding:
            27px 22px;
    }}

    .header-line {{
        left: 22px;
        right: 22px;
    }}

    .logo {{
        width: 48px;
        height: 48px;

        min-width: 48px;
    }}

    .brand-name {{
        font-size: 16px;
    }}

    .brand-title {{
        font-size: 10px;
    }}

    .body {{
        padding:
            29px 20px;
    }}

    .heading {{
        font-size: 23px;
    }}

    .subtitle {{
        font-size: 13px;
    }}

    .meta-item {{
        display: block;

        width: 100%;

        padding:
            0 0 15px 0;
    }}

    .meta-item:last-child {{
        padding-left: 0;
    }}

    .footer {{
        padding:
            22px 20px;
    }}

}}

</style>

</head>


<body>

<div class="email-wrapper">

<div class="email-container">


<!-- =======================================================
     PREMIUM AM HEADER
======================================================== -->

<div class="header">

    <div class="header-glow"></div>

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

            <div class="brand-status">
                Portfolio Communication
            </div>

        </div>

    </div>

    <div class="header-line"></div>

</div>


<!-- =======================================================
     MAIN CONTENT
======================================================== -->

<div class="body">

    <div class="eyebrow">
        ATUL MAHAISKAR • PORTFOLIO
    </div>

    <h1 class="heading">
        {safe_heading}
    </h1>

    <p class="subtitle">
        {safe_subtitle}
    </p>

    {content_html}

</div>


<!-- =======================================================
     FOOTER
======================================================== -->

<div class="footer">

    <div class="footer-brand">
        Atul Mahaiskar
    </div>

    <p class="footer-text">
        {escape_html(footer_text)}
    </p>

    <a
        class="footer-link"
        href="{PORTFOLIO_URL}"
    >
        Visit Portfolio ↗
    </a>

    <div class="footer-mark">
        AM • SOFTWARE • AI • FULL STACK
    </div>

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
    safe_message_id = escape_html(message_id)
    safe_received_at = escape_html(received_at)

    reply_subject = quote(
        "Re: Your message to Atul Mahaiskar"
    )

    content = f"""

    <div class="message-status">
        NEW MESSAGE
    </div>


    <div class="card">

        <span class="label">
            From
        </span>

        <div class="value">
            {safe_name}
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


    <table class="meta">

        <tr>

            <td class="meta-item">

                <span class="meta-label">
                    Message ID
                </span>

                <span class="meta-value">
                    #{safe_message_id}
                </span>

            </td>


            <td class="meta-item">

                <span class="meta-label">
                    Received
                </span>

                <span class="meta-value">
                    {safe_received_at}
                </span>

            </td>

        </tr>

    </table>


    <div class="divider"></div>


    <div class="button-wrapper">

        <a
            class="button"
            href="mailto:{safe_email}?subject={reply_subject}"
        >
            Reply to {safe_name}
        </a>

    </div>

    """

    return create_email_layout(
        heading="New Contact Message",
        subtitle=(
            "A new visitor message has been received "
            "through your portfolio contact form."
        ),
        content_html=content,
        footer_text=(
            "You received this notification because "
            "your portfolio contact system received "
            "a new message."
        )
    )


# ============================================================
# VISITOR CONFIRMATION EMAIL
# ============================================================

def create_visitor_confirmation_email(
    name,
    message_id
):

    safe_name = escape_html(
        name
    )

    safe_message_id = escape_html(
        message_id
    )

    content = f"""

    <div class="message-status">
        MESSAGE RECEIVED
    </div>


    <div class="card">

        <span class="label">
            Hello
        </span>

        <div class="value">
            Hi {safe_name},
        </div>

    </div>


    <div class="card">

        <div class="value">

            Thank you for reaching out through
            the Atul Mahaiskar portfolio.

            <br><br>

            Your message has been successfully
            received. I appreciate you taking the
            time to get in touch.

        </div>

    </div>


    <div class="card">

        <span class="label">
            Message Reference
        </span>

        <div class="value">
            #{safe_message_id}
        </div>

    </div>


    <div class="button-wrapper">

        <a
            class="button"
            href="{PORTFOLIO_URL}"
        >
            Visit My Portfolio ↗
        </a>

    </div>

    """

    return create_email_layout(
        heading="Thanks for reaching out",
        subtitle=(
            "Your message is now safely in my inbox."
        ),
        content_html=content,
        footer_text=(
            "This is an automated confirmation. "
            "Please do not reply to this email."
        )
    )


# ============================================================
# OTP EMAIL
# ============================================================

def create_otp_email(
    otp
):

    safe_otp = escape_html(
        otp
    )

    content = f"""

    <div class="message-status">
        SECURITY VERIFICATION
    </div>


    <div class="card">

        <span class="label">
            Your verification code
        </span>

        <div
            style="
                font-size: 32px;
                font-weight: 850;
                letter-spacing: 8px;
                color: #0f172a;
                padding: 12px 0;
            "
        >
            {safe_otp}
        </div>

        <div
            style="
                color: #64748b;
                font-size: 12px;
                line-height: 1.6;
            "
        >
            This code expires in
            {OTP_EXPIRY_MINUTES} minutes.
        </div>

    </div>


    <div class="card">

        <div class="value">

            If you did not attempt to sign in
            to the portfolio administration panel,
            you can safely ignore this email.

        </div>

    </div>

    """

    return create_email_layout(
        heading="Admin Verification Code",
        subtitle=(
            "Use the verification code below "
            "to complete your administrator login."
        ),
        content_html=content,
        footer_text=(
            "Security notification from the "
            "Atul Mahaiskar portfolio."
        )
    )


# ============================================================
# RESEND EMAIL SERVICE
# ============================================================

def send_email(
    to_email,
    subject,
    body,
    html_body=None,
    reply_to=None
):

    if not RESEND_API_KEY:

        print(
            "RESEND API KEY IS NOT CONFIGURED"
        )

        return {
            "success": False,
            "error": "Email service is not configured."
        }

    if not to_email:

        return {
            "success": False,
            "error": "Recipient email is missing."
        }

    try:

        print(
            "======================================"
        )

        print(
            "RESEND API EMAIL REQUEST"
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

        result = resend.Emails.send(
            params
        )

        email_id = None

        if isinstance(result, dict):

            email_id = result.get(
                "id"
            )

        else:

            email_id = getattr(
                result,
                "id",
                None
            )

        print(
            "RESEND API EMAIL SENT"
        )

        print(
            f"Email ID: {email_id}"
        )

        print(
            "======================================"
        )

        return {
            "success": True,
            "email_id": email_id
        }

    except Exception as error:

        print(
            "======================================"
        )

        print(
            "RESEND API EMAIL FAILED"
        )

        print(
            f"Error type: {type(error).__name__}"
        )

        print(
            f"Error: {error}"
        )

        print(
            "======================================"
        )

        return {
            "success": False,
            "error": str(error)
        }


# ============================================================
# ROOT
# ============================================================

@app.route("/", methods=["GET"])
def root():

    return jsonify({
        "success": True,
        "service": "Atul Mahaiskar Portfolio Backend",
        "server": "Flask",
        "database": "SQLite",
        "email_provider": "Resend API",
        "email": bool(RESEND_API_KEY),
        "admin_email_configured": bool(ADMIN_EMAIL),
        "otp": True,
        "rate_limiting": True,
        "status": "online"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    database_status = "SQLite"

    return jsonify({
        "success": True,
        "status": "healthy",
        "server": "Flask",
        "database": database_status,
        "email": bool(RESEND_API_KEY),
        "email_provider": "Resend API",
        "from_email": RESEND_FROM_EMAIL,
        "admin_email_configured": bool(
            ADMIN_EMAIL
        ),
        "otp": True,
        "rate_limiting": True
    })


# ============================================================
# CONTACT API
# ============================================================

@app.route(
    "/api/contact",
    methods=["POST", "OPTIONS"]
)
def contact():

    if request.method == "OPTIONS":

        return jsonify({
            "success": True
        })


    # --------------------------------------------------------
    # NEW FEATURE: RATE LIMITING
    # --------------------------------------------------------

    ip_address = (
        request.headers.get(
            "X-Forwarded-For",
            request.remote_addr
        )
        or "unknown"
    )

    ip_address = ip_address.split(",")[0].strip()

    if is_rate_limited(
        ip_address
    ):

        return jsonify({
            "success": False,
            "message": (
                "Too many messages. "
                "Please wait a moment and try again."
            )
        }), 429


    # --------------------------------------------------------
    # READ REQUEST
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request data."
        }), 400


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


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not name:

        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400

    if len(name) > 100:

        return jsonify({
            "success": False,
            "message": "Name is too long."
        }), 400


    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400


    if "@" not in email or "." not in email:

        return jsonify({
            "success": False,
            "message": "Please enter a valid email."
        }), 400


    if len(email) > 180:

        return jsonify({
            "success": False,
            "message": "Email is too long."
        }), 400


    if not message:

        return jsonify({
            "success": False,
            "message": "Message is required."
        }), 400


    if len(message) < 5:

        return jsonify({
            "success": False,
            "message": (
                "Please enter a more detailed message."
            )
        }), 400


    if len(message) > 5000:

        return jsonify({
            "success": False,
            "message": (
                "Message must be under 5000 characters."
            )
        }), 400


    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    received_at = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


    # --------------------------------------------------------
    # USER AGENT
    # --------------------------------------------------------

    user_agent = (
        request.headers.get(
            "User-Agent",
            ""
        )[:500]
    )


    # --------------------------------------------------------
    # SAVE MESSAGE
    # --------------------------------------------------------

    connection = get_db()

    cursor = connection.execute(
        """
        INSERT INTO messages
        (
            name,
            email,
            message,
            created_at,
            is_read,
            ip_address,
            user_agent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            email,
            message,
            received_at,
            0,
            ip_address,
            user_agent
        )
    )

    message_id = cursor.lastrowid

    connection.commit()

    connection.close()


    print(
        f"Contact message {message_id} saved."
    )


    # --------------------------------------------------------
    # ADMIN EMAIL
    # --------------------------------------------------------

    admin_email_sent = False

    admin_email_id = None

    if ADMIN_EMAIL:

        admin_html = create_admin_contact_email(
            name=name,
            email=email,
            message=message,
            message_id=message_id,
            received_at=received_at
        )

        admin_text = f"""
New contact message from {name}

Email:
{email}

Message:
{message}

Message ID:
#{message_id}

Received:
{received_at}
"""

        admin_result = send_email(
            to_email=ADMIN_EMAIL,
            subject=(
                f"New Portfolio Contact Message "
                f"from {name}"
            ),
            body=admin_text,
            html_body=admin_html,
            reply_to=email
        )

        admin_email_sent = (
            admin_result.get("success")
            is True
        )

        admin_email_id = (
            admin_result.get("email_id")
        )


    # --------------------------------------------------------
    # VISITOR CONFIRMATION
    # --------------------------------------------------------

    visitor_email_sent = False

    visitor_email_id = None

    visitor_html = create_visitor_confirmation_email(
        name=name,
        message_id=message_id
    )

    visitor_text = f"""
Hi {name},

Thank you for contacting Atul Mahaiskar.

Your message has been received successfully.

Message reference:
#{message_id}

Portfolio:
{PORTFOLIO_URL}

Regards,
Atul Mahaiskar
Software Developer • AI/ML • Full Stack
"""

    visitor_result = send_email(
        to_email=email,
        subject=(
            "Thanks for contacting Atul Mahaiskar"
        ),
        body=visitor_text,
        html_body=visitor_html
    )

    visitor_email_sent = (
        visitor_result.get("success")
        is True
    )

    visitor_email_id = (
        visitor_result.get("email_id")
    )


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    if not admin_email_sent:

        print(
            f"Contact message {message_id} saved, "
            "but admin email delivery failed."
        )

        return jsonify({
            "success": False,
            "message": (
                "Your message was saved, "
                "but email delivery failed. "
                "Please try again later."
            ),
            "message_id": message_id,
            "email_sent": False,
            "admin_email_sent": False,
            "confirmation_email_sent": (
                visitor_email_sent
            )
        }), 502


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
        "confirmation_email_sent": (
            visitor_email_sent
        ),
        "email_id": admin_email_id,
        "visitor_email_id": visitor_email_id
    }), 200


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/api/admin/login",
    methods=["POST"]
)
def admin_login():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400


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

        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401


    if not ADMIN_PASSWORD_HASH:

        return jsonify({
            "success": False,
            "message": (
                "Admin password is not configured."
            )
        }), 500


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
            "message": "Invalid username or password."
        }), 401


    # --------------------------------------------------------
    # GENERATE OTP
    # --------------------------------------------------------

    otp = str(
        random.randint(
            100000,
            999999
        )
    )

    session["admin_otp"] = otp

    session["admin_otp_expires"] = (
        time.time()
        +
        (OTP_EXPIRY_MINUTES * 60)
    )

    session["admin_authenticated"] = False

    session.permanent = True


    # --------------------------------------------------------
    # SEND OTP
    # --------------------------------------------------------

    if not ADMIN_EMAIL:

        return jsonify({
            "success": False,
            "message": (
                "Admin email is not configured."
            )
        }), 500


    otp_html = create_otp_email(
        otp
    )

    otp_text = f"""
Atul Mahaiskar Portfolio
Admin Verification Code

Your OTP is:

{otp}

This code expires in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this code,
ignore this email.
"""

    result = send_email(
        to_email=ADMIN_EMAIL,
        subject=(
            "Admin Verification Code • "
            "Atul Mahaiskar Portfolio"
        ),
        body=otp_text,
        html_body=otp_html
    )


    if not result.get("success"):

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
            "message": (
                "Unable to send verification code."
            )
        }), 502


    return jsonify({
        "success": True,
        "message": (
            "Verification code sent successfully."
        ),
        "expires_in": (
            OTP_EXPIRY_MINUTES * 60
        )
    }), 200


# ============================================================
# VERIFY OTP
# ============================================================

@app.route(
    "/api/admin/verify-otp",
    methods=["POST"]
)
def verify_otp():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400


    submitted_otp = str(
        data.get(
            "otp",
            ""
        )
    ).strip()

    stored_otp = session.get(
        "admin_otp"
    )

    expiry = session.get(
        "admin_otp_expires"
    )


    if not stored_otp or not expiry:

        return jsonify({
            "success": False,
            "message": (
                "No active verification code."
            )
        }), 401


    if time.time() > float(expiry):

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
            "message": (
                "Verification code has expired."
            )
        }), 401


    if submitted_otp != stored_otp:

        return jsonify({
            "success": False,
            "message": (
                "Invalid verification code."
            )
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
            "Administrator authentication successful."
        )
    }), 200


# ============================================================
# ADMIN STATUS
# ============================================================

@app.route(
    "/api/admin/status",
    methods=["GET"]
)
def admin_status():

    authenticated = (
        session.get(
            "admin_authenticated",
            False
        )
        is True
    )

    return jsonify({
        "success": True,
        "authenticated": authenticated
    })


# ============================================================
# AUTHENTICATION HELPER
# ============================================================

def require_admin():

    return (
        session.get(
            "admin_authenticated",
            False
        )
        is True
    )


# ============================================================
# GET MESSAGES
# ============================================================

@app.route(
    "/api/messages",
    methods=["GET"]
)
def get_messages():

    if not require_admin():

        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401


    connection = get_db()

    rows = connection.execute(
        """
        SELECT
            id,
            name,
            email,
            message,
            created_at,
            is_read,
            ip_address,
            user_agent
        FROM messages
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()


    messages = []

    for row in rows:

        messages.append({
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "message": row["message"],
            "created_at": row["created_at"],
            "is_read": bool(
                row["is_read"]
            ),
            "ip_address": row["ip_address"],
            "user_agent": row["user_agent"]
        })


    return jsonify({
        "success": True,
        "messages": messages,
        "count": len(messages)
    }), 200


# ============================================================
# MARK MESSAGE AS READ
# ============================================================

@app.route(
    "/api/messages/<int:message_id>/read",
    methods=["PATCH", "POST"]
)
def mark_message_read(
    message_id
):

    if not require_admin():

        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401


    connection = get_db()

    cursor = connection.execute(
        """
        UPDATE messages
        SET is_read = 1
        WHERE id = ?
        """,
        (message_id,)
    )

    connection.commit()

    updated = (
        cursor.rowcount > 0
    )

    connection.close()


    if not updated:

        return jsonify({
            "success": False,
            "message": "Message not found."
        }), 404


    return jsonify({
        "success": True,
        "message": (
            "Message marked as read."
        )
    }), 200


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
        "message": "Logged out successfully."
    }), 200


# ============================================================
# 404 HANDLER
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "Endpoint not found."
    }), 404


# ============================================================
# 500 HANDLER
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

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
        debug=True
    )