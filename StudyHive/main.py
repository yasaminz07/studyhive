from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from database import get_db_connection, init_db

# Load .env ONLY locally
if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "studyhive-secret-key")
CORS(app)  # allow frontend requests

# Safe DB init
@app.before_first_request
def setup_database():
    init_db()

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
    conn.close()

    # ---------------- SEND EMAILS (SENDGRID) ----------------
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

        # Email to admin
        admin_email = Mail(
            from_email=os.environ.get("MAIL_FROM"),
            to_emails=os.environ.get("MAIL_TO"),
            subject="New StudyHive Support Report",
            html_content=f"""
            <h2>New Support Report</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {user_email}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
            """
        )

        # Confirmation email to user
        user_email_msg = Mail(
            from_email=os.environ.get("MAIL_FROM"),
            to_emails=user_email,
            subject="We’ve received your report – StudyHive",
            html_content=f"""
            <p>Hi {name},</p>
            <p>We’ve received your support request and will get back to you shortly.</p>
            <p><strong>Your message:</strong></p>
            <p>{message}</p>
            <br>
            <p>– StudyHive Support Team</p>
            """
        )

        sg.send(admin_email)
        sg.send(user_email_msg)

        print("SENDGRID EMAILS SENT SUCCESSFULLY")

    except Exception as e:
        # Email failure must NOT break the app
        print("SENDGRID EMAIL ERROR (ignored):", e)

    # ---------------- FINAL RESPONSE ----------------
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
    app.run(debug=os.getenv("FLASK_ENV") != "production")

