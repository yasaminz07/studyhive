from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
from database import get_db_connection, init_db
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import uuid
from functools import wraps


# Load .env ONLY locally
if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "studyhive-secret-key")
CORS(app)  # allow frontend requests

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_logged_in"):
            return redirect("/")
        return view_func(*args, **kwargs)
    return wrapped


def safe_init_db():
    try:
        init_db()
    except Exception as e:
        print("DB init skipped:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT posts.id, posts.title, posts.body, posts.created_at,
               users.id, users.first_name, users.last_name
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
        LIMIT 20
    """)

    rows = cur.fetchall()
    conn.close()

    posts = []
    for r in rows:
        posts.append({
            "id": r[0],
            "title": r[1],
            "body": r[2],
            "created_at": time_ago(r[3]),
            "user_id": r[4],
            "author": f"{r[5]} {r[6]}",
            "initials": (r[5][0] + r[6][0]).upper()
        })

    return render_template(
        "home.html",
        user_name=session.get("user_name"),
        posts=posts
    )


@app.route("/about")
def about():
    return render_template("about.html", user_name=session.get("user_name"))

@app.route("/explore")
def explore():
    return render_template("explore.html", user_name=session.get("user_name"))

@app.route("/profile")
@login_required
def profile():
    conn = get_db_connection()
    cur = conn.cursor()

    user_id = session["user_id"]

    # Get your own user info
    cur.execute("""
        SELECT id, username, first_name, last_name, profile_image
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cur.fetchone()

    # Get your posts
    cur.execute("""
        SELECT id, title, body, created_at
        FROM posts
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    posts = cur.fetchall()

    conn.close()

    return render_template(
        "profile.html",
        profile_user={
            "id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "profile_image": user[4]
        },
        posts=posts,
        user_name=session.get("user_name")
    )

@app.route("/messages")
def messages():
    return render_template("messages.html", user_name=session.get("user_name"))

@app.route("/subject-english")
def subject_english():
    return render_template("subject-english.html", user_name=session.get("user_name"))

@app.route("/subject-maths")
def subject_maths():
    return render_template("subject-maths.html", user_name=session.get("user_name"))

@app.route("/subject-science")
def subject_science():
    return render_template("subject-science.html", user_name=session.get("user_name"))

@app.route("/support", methods=["GET"])
def support_page():
    return render_template("support.html", user_name=session.get("user_name"))

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

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    if not session.get("user_logged_in"):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user basic info
    cursor.execute("""
        SELECT id, username, first_name, last_name
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Get follower counts
    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (user_id,))
    followers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
    following = cursor.fetchone()[0]

    # Check if current user follows this profile
    cursor.execute("""
        SELECT 1 FROM follows
        WHERE follower_id = %s AND following_id = %s
    """, (session["user_id"], user_id))
    is_following = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return jsonify({
        "id": user[0],
        "username": user[1],
        "first_name": user[2],
        "last_name": user[3],
        "followers": followers,
        "following": following,
        "is_following": is_following
    })

#post route

@app.route("/api/posts")
def api_posts():
    page = int(request.args.get("page", 1))
    limit = 5
    offset = (page - 1) * limit

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT posts.id, posts.title, posts.body, posts.created_at,
            users.id, users.first_name, users.last_name, users.profile_image
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))

    rows = cur.fetchall()
    conn.close()

    posts = []
    for r in rows:
        first = r[5]
        last = r[6]

        if first and last:
            initials = (first[0] + last[0]).upper()
        elif first:
            initials = first[0].upper()
        else:
            initials = "U"

        posts.append({
            "id": r[0],
            "title": r[1],
            "body": r[2],
            "created_at": time_ago(r[3]),
            "user_id": r[4],
            "author": f"{first or ''} {last or ''}".strip(),
            "initials": initials,
            "profile_image": r[7]
        })

    return jsonify(posts)

@app.route("/dev/create-test-posts")
def create_test_posts():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get first 6 users
    cur.execute("SELECT id, first_name FROM users LIMIT 6")
    users = cur.fetchall()

    if len(users) < 6:
        return "You need at least 6 users in the database!"

    # For each user, create 3 posts
    for user in users:
        user_id = user[0]
        name = user[1]

        for i in range(1, 4):
            cur.execute("""
                INSERT INTO posts (user_id, title, body, image_url)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                f"{name}'s Post #{i}",
                f"This is a test post #{i} by {name}.",
                None
            ))

    conn.commit()
    conn.close()

    return "Created 3 posts for each of 6 users (18 posts total)."

def time_ago(dt):
    seconds = int((datetime.utcnow() - dt).total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        return f"{seconds // 60} minutes ago"
    elif seconds < 86400:
        return f"{seconds // 3600} hours ago"
    else:
        return f"{seconds // 86400} days ago"

# profle-other account access
@app.route("/profile/<int:user_id>")
@login_required
def profile_dynamic(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get user info
    cur.execute("""
        SELECT id, username, first_name, last_name, profile_image
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return "User not found", 404

    # Get follower counts (if you already have follows table)
    try:
        cur.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (user_id,))
        followers = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
        following = cur.fetchone()[0]
    except:
        followers = 0
        following = 0

    # Check if current user follows this profile
    cur.execute("""
        SELECT 1 FROM follows
        WHERE follower_id = %s AND following_id = %s
    """, (session["user_id"], user_id))

    is_following = cur.fetchone() is not None

    # Get this user's posts
    cur.execute("""
        SELECT id, title, body, created_at
        FROM posts
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    posts = cur.fetchall()

    conn.close()

    return render_template(
        "profile-other.html",
        profile_user={
            "id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "profile_image": user[4],
            "followers": followers,
            "following": following
        },
        posts=posts,
        is_following=is_following,
        user_name=session.get("user_name")
    )

#Follow/Unfollow
@app.route("/api/toggle-follow", methods=["POST"])
def toggle_follow():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    target_user_id = int(data.get("user_id"))
    follower_id = session["user_id"]

    if follower_id == target_user_id:
        return jsonify({"error": "You can't follow yourself"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if already following
    cur.execute("""
        SELECT 1 FROM follows
        WHERE follower_id = %s AND following_id = %s
    """, (follower_id, target_user_id))

    exists = cur.fetchone()

    if exists:
        # UNFOLLOW
        cur.execute("""
            DELETE FROM follows
            WHERE follower_id = %s AND following_id = %s
        """, (follower_id, target_user_id))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "unfollowed"})

    else:
        # FOLLOW (safe insert)
        cur.execute("""
            INSERT INTO follows (follower_id, following_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (follower_id, target_user_id))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "followed"})
    
@app.route("/api/following/<int:user_id>")
def get_following(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT users.id, users.first_name, users.last_name, users.username
        FROM follows
        JOIN users ON users.id = follows.following_id
        WHERE follows.follower_id = %s
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "name": f"{r[1]} {r[2]}",
            "username": r[3]
        }
        for r in rows
    ])

# Nafis's work
# ==========================================
#                  COMMENTS
# ==========================================

@app.route("/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, u.first_name, u.last_name, u.profile_image, c.content, c.created_at
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = %s AND c.is_deleted = FALSE
        ORDER BY c.created_at ASC
    """, (post_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "username": f"{r[1]} {r[2]}",
            "profile_image": r[3],
            "content": r[4],
            "created_at": r[5].isoformat() if r[5] else None
        }
        for r in rows
    ])


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    # must be logged in
    if not session.get("user_logged_in") or not session.get("user_id"):
        return jsonify(success=False, error="Not logged in"), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify(success=False, error="Missing content"), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # (Optional but recommended) ensure post exists
    cur.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        return jsonify(success=False, error="Post not found"), 404

    user_id = session["user_id"]

    cur.execute("""
        INSERT INTO comments (post_id, user_id, content, is_deleted, created_at)
        VALUES (%s, %s, %s, FALSE, NOW())
        RETURNING id, created_at
    """, (post_id, user_id, content))

    new_row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(
        success=True,
        comment_id=new_row[0],
        created_at=new_row[1].isoformat() if new_row[1] else None
    )

@app.route("/api/me/profile-image", methods=["POST"])
def upload_profile_image():
    if not session.get("user_logged_in") or not session.get("user_id"):
        return jsonify(success=False, error="Not authenticated"), 401

    if "image" not in request.files:
        return jsonify(success=False, error="No file uploaded"), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify(success=False, error="No selected file"), 400

    if not allowed_file(file.filename):
        return jsonify(success=False, error="Unsupported file type"), 400

    user_id = session["user_id"]
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"user_{user_id}.{ext}"

    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    public_path = f"/static/uploads/profiles/{filename}"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET profile_image=%s WHERE id=%s",
        (public_path, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    session["profile_image"] = public_path

    return jsonify(success=True, profile_image=public_path)

@app.route("/api/me", methods=["GET", "POST"])
def me():
    if not session.get("user_logged_in") or not session.get("user_id"):
        return jsonify(success=False), 401

    conn = get_db_connection()
    cur = conn.cursor()

    # =========================
    # GET → return user info
    # =========================
    if request.method == "GET":
        cur.execute("""
            SELECT first_name, last_name, username, email, profile_image
            FROM users
            WHERE id = %s
        """, (session["user_id"],))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify(success=False), 404

        return jsonify({
            "success": True,
            "first_name": row[0],
            "last_name": row[1],
            "username": row[2],
            "email": row[3],
            "profile_image": row[4]
        })

    # =========================
    # POST → update user info
    # =========================
    data = request.get_json()

    first = data.get("first_name")
    last = data.get("last_name")
    username = data.get("username")
    email = data.get("email")

    cur.execute("""
        UPDATE users
        SET first_name=%s, last_name=%s, username=%s, email=%s
        WHERE id=%s
    """, (first, last, username, email, session["user_id"]))

    conn.commit()
    cur.close()
    conn.close()

    session["user_name"] = f"{first} {last}"

    return jsonify(success=True)

@app.route("/posts/<int:post_id>/comments/count")
def comments_count(post_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM comments
        WHERE post_id = %s AND is_deleted = FALSE
    """, (post_id,))

    count = cur.fetchone()[0]
    conn.close()

    return jsonify({"count": count})

@app.route("/admin/comments/delete/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    # IMPORTANT: stop random users deleting comments
    if not session.get("admin_logged_in"):
        return jsonify(success=False, error="Admin not logged in"), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE comments
        SET is_deleted = TRUE
        WHERE id = %s
    """, (comment_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(success=True)

UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads", "profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    safe_init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)