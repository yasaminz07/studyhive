from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
from database import get_db_connection, init_db
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import uuid

# Load .env ONLY locally
if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "studyhive-secret-key")
CORS(app)  # allow frontend requests

def safe_init_db():
    try:
        init_db()
    except Exception as e:
        print("DB init skipped:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/profile-friend")
def profile_friend():
    return render_template("profile-friend.html")

@app.route("/profile-other")
def profile_other():
    return render_template("profile-other.html")

@app.route("/messages")
def messages():
    return render_template("messages.html")

@app.route("/subject-english")
def subject_english():
    return render_template("subject-english.html")

@app.route("/subject-maths")
def subject_maths():
    return render_template("subject-maths.html")

@app.route("/subject-science")
def subject_science():
    return render_template("subject-science.html")

@app.route("/support", methods=["GET"])
def support_page():
    return render_template("support.html")

# ---------------- ADMIN LOGIN -------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, full_name FROM admins WHERE username = %s AND password = %s",
            (username, password)
        )

        admin = cursor.fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_name"] = admin[1] 
            return redirect("/admin/dashboard")

        # Login failed
        return render_template("admin-login.html", error="Invalid username or password")

    # GET request - show login page
    return render_template("admin-login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")

# ---------------- SUPPORT FORM (EMAIL) ----------------

@app.route("/support", methods=["POST"])
def support():
    data = request.get_json()

    user_email = data.get("email")
    name = data.get("name")
    message = data.get("message")

    # ---------------- VALIDATION ----------------
    if not user_email or not name or not message:
        return jsonify(success=False), 400

    # ---------------- SAVE TO DATABASE ----------------
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO support_reports (name, email, message, resolved)
        VALUES (%s, %s, %s, %s)
        """,
        (name, user_email, message, False)
    )

    conn.commit()
    cursor.close()
    conn.close()

    # ---------------- SEND EMAILS (GMAIL) ----------------
    try:
        mail_from = os.environ.get("MAIL_FROM")
        mail_to = os.environ.get("MAIL_TO") or os.environ.get("SMTP_USER")

        if not mail_to:
            raise ValueError("MAIL_TO is missing (set MAIL_TO in .env)")

        # ===== EMAIL 1: ADMIN REPORT (to your StudyHive inbox) =====
        admin_msg = EmailMessage()
        admin_msg["Subject"] = "New StudyHive Support Report"
        admin_msg["From"] = mail_from
        admin_msg["To"] = mail_to
        admin_msg.set_content(f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Support Report</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
            </body>
            </html>""", subtype="html")

        # ===== EMAIL 2: USER CONFIRMATION =====
        user_msg = EmailMessage()
        user_msg["Subject"] = "We’ve received your report – StudyHive"
        user_msg["From"] = mail_from
        user_msg["To"] = user_email
        user_msg.set_content(
            f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Thank you for contacting StudyHive</h2>
                <p>Hi {name},</p>
                <p>We’ve received your support request and will get back to you as soon as possible.</p>
                <p>– StudyHive Support Team</p>
            </body>
            </html>""", subtype="html")

        # ===== EMAIL 3: USER COPY OF REPORT =====
        user_copy = EmailMessage()
        user_copy["Subject"] = "Copy of your StudyHive support report"
        user_copy["From"] = mail_from
        user_copy["To"] = user_email
        user_copy.set_content(f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Your Support Report Copy</h2>
                <p><strong>Name:<strong> {name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                <br>
                <p>– StudyHive Support Team</p>
            </body>
            </html>""", subtype="html")

        with smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))) as smtp:
            smtp.starttls()
            smtp.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
            smtp.send_message(admin_msg)
            smtp.send_message(user_msg)
            smtp.send_message(user_copy)

        print("SUPPORT EMAILS SENT USING GMAIL SMTP (admin + confirmation + copy)")

    except Exception as e:
        print("EMAIL ERROR (ignored):", e)

    return jsonify(success=True)

@app.route("/admin/support")
def admin_support():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, message, resolved, created_at
        FROM support_reports
        ORDER BY created_at DESC
    """)

    reports = cursor.fetchall()
    conn.close()

    return render_template("admin-support.html", reports=reports)

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Counts
    cursor.execute("SELECT COUNT(*) FROM support_reports")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM support_reports WHERE resolved = FALSE")
    unresolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM support_reports WHERE resolved = TRUE")
    resolved = cursor.fetchone()[0]

    # Latest 5 reports
    cursor.execute("""
        SELECT name, message, resolved, created_at
        FROM support_reports
        ORDER BY created_at DESC
        LIMIT 5
    """)
    latest_reports = cursor.fetchall()

    conn.close()

    return render_template(
        "admin-dashboard.html",
        admin=session.get("admin_name"),
        total=total,
        unresolved=unresolved,
        resolved=resolved,
        latest_reports=latest_reports
    )


@app.route("/admin/support/resolve/<int:report_id>", methods=["POST"])
def resolve_report(report_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE support_reports SET resolved = %s WHERE id = %s",
        (True, report_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/support")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    first_name = data.get("firstName")
    last_name = data.get("lastName")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not first_name or not last_name or not username or not email or not password:
        return jsonify(success=False, error="Missing fields")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, first_name, last_name, email, password)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, first_name, last_name, email, password)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify(success=False, error="Username or email already exists")

    conn.close()
    return jsonify(success=True)

@app.route("/login-user", methods=["POST"])
def login_user():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, first_name, last_name
        FROM users
        WHERE username = %s AND password = %s
        """,
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_logged_in"] = True
        session["user_id"] = user[0]
        session["user_name"] = user[1] + " " + user[2]
        return jsonify(success=True)

    return jsonify(success=False)

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify(success=False, error="Email is required")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check user exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        # For security, still return success
        return jsonify(success=True)

    # Generate token
    token = str(uuid.uuid4())

    # Expiry time = 24 hours from now
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Delete old tokens for this email
    cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))

    # Insert new token
    cursor.execute(
        """
        INSERT INTO password_resets (email, token, expires_at)
        VALUES (%s, %s, %s)
        """,
        (email, token, expires_at)
    )

    conn.commit()
    conn.close()

    reset_link = f"http://127.0.0.1:5000/reset-password/{token}"
    print("RESET LINK:", reset_link)

    try:
        msg = EmailMessage()
        msg["Subject"] = "StudyHive Password Reset"
        msg["From"] = os.environ.get("MAIL_FROM")
        msg["To"] = email
        msg.set_content(f"""Click the link below to reset your password: {reset_link} This link is valid for 24 hours.""")

        with smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))) as smtp:
            smtp.starttls()
            smtp.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
            smtp.send_message(msg)

        print("EMAIL SENT USING GMAIL SMTP")

        return jsonify(success=True)

    except Exception as e:
        print("EMAIL ERROR:", e)
        return jsonify(success=False, error="Failed to send email")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT email, expires_at 
        FROM password_resets 
        WHERE token = %s
        """,
        (token,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Invalid or expired reset link"

    email, expires_at = row

    # Check if expired
    if datetime.utcnow() > expires_at:
        cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))
        conn.commit()
        conn.close()
        return "This reset link has expired"

    # Show reset form
    if request.method == "GET":
        conn.close()
        return render_template("reset-password.html", token=token)

    # POST → update password
    data = request.get_json()
    new_password = data.get("password")

    if not new_password:
        conn.close()
        return jsonify(success=False)

    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (new_password, email)
    )

    # Delete token AFTER success
    cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))

    conn.commit()
    conn.close()

    return jsonify(success=True)

if __name__ == "__main__":
    safe_init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)