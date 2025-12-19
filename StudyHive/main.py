from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib
import os
from database import get_db_connection, init_db


load_dotenv()

app = Flask(__name__)
app.secret_key = "studyhive-secret-key"  # required for sessions
CORS(app)  # allow frontend requests


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

        if (
            username == os.getenv("ADMIN_USERNAME") and
            password == os.getenv("ADMIN_PASSWORD")
        ):
            session["admin_logged_in"] = True
            session["admin_username"] = username.title()
            return redirect("/admin/dashboard")

        return render_template(
            "admin-login.html",
            error="Invalid admin credentials"
        )

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

    if not user_email or not name or not message:
        return jsonify(success=False), 400
    
    # -------- SAVE TO DATABASE --------
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO support_reports (name, email, message, resolved) VALUES (?, ?, ?, 0)",
        (name, user_email, message)
    )

    conn.commit()
    conn.close()


    # =========================
    # EMAIL 1: SUPPORT REPORT
    # =========================
    support_email = EmailMessage()
    support_email["Subject"] = "New StudyHive Support Report"
    support_email["From"] = os.getenv("MAIL_USERNAME")
    support_email["To"] = os.getenv("MAIL_TO")
    support_email["CC"] = user_email
    support_email["Reply-To"] = user_email

    support_email.set_content("This email requires HTML support.")
    support_email.add_alternative(f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>New Support Report</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>User Email:</strong> {user_email}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
        </body>
    </html>
    """, subtype="html")

    # =========================
    # EMAIL 2: AUTO-CONFIRMATION
    # =========================
    confirmation_email = EmailMessage()
    confirmation_email["Subject"] = "We’ve received your report – StudyHive"
    confirmation_email["From"] = os.getenv("MAIL_USERNAME")
    confirmation_email["To"] = user_email

    confirmation_email.set_content("This email requires HTML support.")
    confirmation_email.add_alternative(f"""
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
    """, subtype="html")

    try:
        with smtplib.SMTP(
            os.environ["MAIL_SERVER"],
            int(os.environ["MAIL_PORT"])
        ) as server:
            server.starttls()
            server.login(
                os.environ["MAIL_USERNAME"],
                os.environ["MAIL_PASSWORD"]
            )

            server.send_message(support_email)
            server.send_message(confirmation_email)

        print("EMAILS SENT SUCCESSFULLY")

    except Exception as e:
        print("EMAIL ERROR:", e)
        return jsonify(success=False), 500

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

    cursor.execute("SELECT COUNT(*) FROM support_reports WHERE resolved = 0")
    unresolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM support_reports WHERE resolved = 1")
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
        "UPDATE support_reports SET resolved = 1 WHERE id = ?",
        (report_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/support")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
