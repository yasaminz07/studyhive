from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from database import get_db_connection, init_db
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
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
            "SELECT id FROM admins WHERE username = %s AND password = %s",
            (username, password)
        )

        admin = cursor.fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_username"] = username
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

    # ---------------- SEND EMAILS (SENDGRID) ----------------
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

        # =========================
        # EMAIL 1: ADMIN REPORT
        # =========================
        admin_email = Mail(
            from_email=os.environ.get("MAIL_FROM"),
            to_emails=os.environ.get("MAIL_TO"),
            subject="New StudyHive Support Report",

            plain_text_content=f"""
            New Support Report

            Name: {name}
            Email: {user_email}

            Message:
            {message}
            """,

            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>New Support Report</h2>
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>User Email:</strong> {user_email}</p>
                    <p><strong>Message:</strong></p>
                    <p>{message}</p>
                </body>
            </html>
            """
        )

        # =========================
        # EMAIL 2: USER CONFIRMATION (YOUR ORIGINAL MESSAGE)
        # =========================
        confirmation_email = Mail(
            from_email=os.environ.get("MAIL_FROM"),
            to_emails=user_email,
            subject="We’ve received your report – StudyHive",

            plain_text_content=f"""
            Hi {name},

            We’ve received your support request and will get back to you as soon as possible.

            Your message:
            {message}

            – StudyHive Support Team
            """,

            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Thank you for contacting StudyHive</h2>
                    <p>Hi {name},</p>
                    <p>We’ve received your support request and will get back to you as soon as possible.</p>
                    <p><strong>Your message:</strong></p>
                    <p>{message}</p>
                    <br>
                    <p>– StudyHive Support Team</p>
                </body>
            </html>
            """
        )

        sg.send(admin_email)
        sg.send(confirmation_email)

        print("SENDGRID EMAILS SENT SUCCESSFULLY")

    except Exception as e:
        # Email issues should NOT break the app
        print("SENDGRID EMAIL ERROR (ignored):", e)

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
        admin=session.get("admin_username"),
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

if __name__ == "__main__":
    safe_init_db()
    app.run(debug=os.getenv("FLASK_ENV") != "production")

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
        return jsonify(success=False, error="No account with that email")

    # Generate token
    import uuid
    token = str(uuid.uuid4())

    # Delete old tokens for this email
    cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))

    # Insert new token
    cursor.execute(
        "INSERT INTO password_resets (email, token) VALUES (%s, %s)",
        (email, token)
    )

    conn.commit()
    conn.close()

    reset_link = f"http://127.0.0.1:5000/reset-password/{token}"

    try:
        message = Mail(
            from_email=os.environ.get("MAIL_FROM"),
            to_emails=email,
            subject="StudyHive Password Reset",
            html_content=f"""
            <h2>Password Reset</h2>
            <p>Click this link to reset your password:</p>
            <a href="{reset_link}">{reset_link}</a>
            """
        )

        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        sg.send(message)

        return jsonify(success=True)

    except Exception as e:
        print("EMAIL ERROR:", e)
        return jsonify(success=False, error="Failed to send email")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT email FROM password_resets WHERE token = %s",
        (token,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Invalid or expired reset link"

    email = row[0]

    if request.method == "GET":
        conn.close()
        return render_template("reset-password.html", token=token)

    # POST → update password
    data = request.get_json()
    new_password = data.get("password")

    if not new_password:
        return jsonify(success=False)

    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (new_password, email)
    )

    # Delete token after use
    cursor.execute(
        "DELETE FROM password_resets WHERE token = %s",
        (token,)
    )

    conn.commit()
    conn.close()

    return jsonify(success=True)

