from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
from database import get_db_connection, init_db
from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage
import uuid
from functools import wraps
from werkzeug.utils import secure_filename

# Environment & secrets
# Load .env ONLY locally
if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "studyhive-secret-key")

# IMPORTANT for session cookies from frontend fetch():
# - supports_credentials=True lets browsers send/receive cookies

# CORS / session cookie config
CORS(app, supports_credentials=True)

# Upload config
UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads", "profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

POST_UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads", "posts")
os.makedirs(POST_UPLOAD_DIR, exist_ok=True)

POST_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
POST_MAX_MB = 8  # change if you want

app.config["MAX_CONTENT_LENGTH"] = POST_MAX_MB * 1024 * 1024

# Upload helpers - Nafis
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_post_image(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in POST_ALLOWED_EXTENSIONS

# Auth helpers
def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_logged_in"):
            return redirect("/")
        return view_func(*args, **kwargs)

    return wrapped

# Database bootstrap
def safe_init_db():
    try:
        init_db()
    except Exception as e:
        print("DB init skipped:", e)


def time_ago(dt):
    """
    Robust time_ago for timestamps that may be:
    - naive (no tzinfo)
    - timezone-aware (Postgres can return aware timestamps depending on config)
    """
    if dt is None:
        return ""

    # Convert to UTC aware
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)

    now_utc = datetime.now(timezone.utc)
    seconds = int((now_utc - dt_utc).total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        return f"{seconds // 60} minutes ago"
    elif seconds < 86400:
        return f"{seconds // 3600} hours ago"
    else:
        return f"{seconds // 86400} days ago"

# Pages
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
@login_required
def home():
    return render_template(
        "home.html",
        user_name=session.get("user_name")
    )

@app.route("/about")
def about():
    return render_template("about.html", user_name=session.get("user_name"))

@app.route("/explore")
def explore():
    return render_template("explore.html", user_name=session.get("user_name"))

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

@app.route("/profile")
@login_required
def profile():
    conn = get_db_connection()
    cur = conn.cursor()

    user_id = session["user_id"]

    cur.execute(
        """
        SELECT id, username, first_name, last_name, profile_image, user_type
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )
    user = cur.fetchone()

    cur.execute(
        """
        SELECT id, title, body, created_at, image_url
        FROM posts
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    posts_rows = cur.fetchall()

    cur.close()
    conn.close()

    if not user:
        return "User not found", 404

    posts = []
    for p in posts_rows:
        posts.append((p[0], p[1], p[2], time_ago(p[3]), p[4]))

    return render_template(
        "profile.html",
        profile_user={
            "id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "profile_image": user[4],
        },
        user_type=user[5],
        posts=posts,
        user_name=session.get("user_name"),
    )

# Admin login/dashboard/support - Yasamin
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, full_name FROM admins WHERE username = %s AND password = %s",
            (username, password),
        )

        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_name"] = admin[1]
            return redirect("/admin/dashboard")

        return render_template("admin-login.html", error="Invalid username or password")

    return render_template("admin-login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM support_reports")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM support_reports WHERE resolved = FALSE")
    unresolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM support_reports WHERE resolved = TRUE")
    resolved = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT name, message, resolved, created_at
        FROM support_reports
        ORDER BY created_at DESC
        LIMIT 5
        """
    )
    latest_reports = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin-dashboard.html",
        admin=session.get("admin_name"),
        total=total,
        unresolved=unresolved,
        resolved=resolved,
        latest_reports=latest_reports,
    )

@app.route("/admin/support")
def admin_support():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, email, message, resolved, created_at
        FROM support_reports
        ORDER BY created_at DESC
        """
    )
    reports = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin-support.html", reports=reports)

@app.route("/admin/support/resolve/<int:report_id>", methods=["POST"])
def resolve_report(report_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE support_reports SET resolved = %s WHERE id = %s",
        (True, report_id),
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin/support")

# Support form (DB + email) - Yasamin
@app.route("/support", methods=["POST"])
def support():
    data = request.get_json(silent=True) or {}

    user_email = data.get("email")
    name = data.get("name")
    message = data.get("message")

    if not user_email or not name or not message:
        return jsonify(success=False), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO support_reports (name, email, message, resolved)
        VALUES (%s, %s, %s, %s)
        """,
        (name, user_email, message, False),
    )

    conn.commit()
    cursor.close()
    conn.close()

    try:
        mail_from = os.environ.get("MAIL_FROM")
        mail_to = os.environ.get("MAIL_TO") or os.environ.get("SMTP_USER")

        if not mail_from:
            raise ValueError("MAIL_FROM is missing")
        if not mail_to:
            raise ValueError("MAIL_TO is missing (set MAIL_TO or SMTP_USER)")

        # Admin email
        admin_msg = EmailMessage()
        admin_msg["Subject"] = "New StudyHive Support Report"
        admin_msg["From"] = mail_from
        admin_msg["To"] = mail_to
        admin_msg.set_content(
            f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                <h2>New Support Report</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                </body>
                </html>
                """,
            subtype="html",
        )

        # User confirmation
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
                </html>
                """,
            subtype="html",
        )

        # User copy
        user_copy = EmailMessage()
        user_copy["Subject"] = "Copy of your StudyHive support report"
        user_copy["From"] = mail_from
        user_copy["To"] = user_email
        user_copy.set_content(
            f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                <h2>Your Support Report Copy</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                <br>
                <p>– StudyHive Support Team</p>
                </body>
                </html>
                """,
            subtype="html",
        )

        with smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))) as smtp:
            smtp.starttls()
            smtp.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
            smtp.send_message(admin_msg)
            smtp.send_message(user_msg)
            smtp.send_message(user_copy)

    except Exception as e:
        print("EMAIL ERROR (ignored):", e)

    return jsonify(success=True)

# Auth - Yasamin

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    first_name = data.get("firstName")
    last_name = data.get("lastName")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    user_type = (data.get("userType") or "").strip().lower()

    if not first_name or not last_name or not username or not email or not password:
        return jsonify(success=False, error="Missing fields")

    if user_type not in ("student", "tutor"):
        return jsonify(success=False, error="Please choose Student or Tutor")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, first_name, last_name, email, password, user_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (username, first_name, last_name, email, password, user_type)
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
    data = request.get_json(silent=True) or {}
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
        (username, password),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session.clear()  # IMPORTANT: clears old user's session keys
        session["user_logged_in"] = True
        session["user_id"] = user[0]
        session["user_name"] = f"{user[1]} {user[2]}".strip()
        return jsonify(success=True)

    return jsonify(success=False)

# Forgot/reset password - Yasamin

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        return jsonify(success=False, error="Email is required")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify(success=True)

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)

    cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))
    cursor.execute(
        """
        INSERT INTO password_resets (email, token, expires_at)
        VALUES (%s, %s, %s)
        """,
        (email, token, expires_at),
    )

    conn.commit()
    cursor.close()
    conn.close()

    reset_link = f"http://127.0.0.1:5000/reset-password/{token}"
    print("RESET LINK:", reset_link)

    try:
        msg = EmailMessage()
        msg["Subject"] = "StudyHive Password Reset"
        msg["From"] = os.environ.get("MAIL_FROM")
        msg["To"] = email
        msg.set_content(
            f"Click the link below to reset your password:\n{reset_link}\n\nThis link is valid for 24 hours."
        )

        with smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT"))) as smtp:
            smtp.starttls()
            smtp.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
            smtp.send_message(msg)

        print("RESET EMAIL SENT")
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
        (token,),
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return "Invalid or expired reset link"

    email, expires_at = row

    if datetime.utcnow() > expires_at:
        cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))
        conn.commit()
        cursor.close()
        conn.close()
        return "This reset link has expired"

    if request.method == "GET":
        cursor.close()
        conn.close()
        return render_template("reset-password.html", token=token)

    data = request.get_json(silent=True) or {}
    new_password = data.get("password")

    if not new_password:
        cursor.close()
        conn.close()
        return jsonify(success=False), 400

    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
    cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)

# User profile API
@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    if not session.get("user_logged_in"):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, first_name, last_name
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (user_id,))
    followers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
    following = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT 1 FROM follows
        WHERE follower_id = %s AND following_id = %s
        """,
        (session["user_id"], user_id),
    )
    is_following = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return jsonify(
        {
            "id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "followers": followers,
            "following": following,
            "is_following": is_following,
        }
    )


@app.route("/api/posts", methods=["GET"])
def api_posts():
    page = int(request.args.get("page", 1))
    limit = 5
    offset = (page - 1) * limit

    # Optional filter: show posts from only one user (for profile page)
    user_id_filter = request.args.get("user_id")

    conn = get_db_connection()
    cur = conn.cursor()

    if user_id_filter:
        # PROFILE MODE: only this user's posts
        cur.execute(
            """
            SELECT
                posts.id, posts.title, posts.body, posts.created_at, posts.image_url,
                users.id, users.first_name, users.last_name, users.profile_image
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.user_id = %s
            ORDER BY posts.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id_filter, limit, offset),
        )
    else:
        # NORMAL FEED MODE: all posts
        cur.execute(
            """
            SELECT
                posts.id, posts.title, posts.body, posts.created_at, posts.image_url,
                users.id, users.first_name, users.last_name, users.profile_image
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    posts = []
    for r in rows:
        post_id = r[0]
        title = r[1]
        body = r[2]
        created_at = r[3]
        image_url = r[4]

        user_id = r[5]
        first = r[6] or ""
        last = r[7] or ""
        profile_image = r[8]

        if first and last:
            initials = (first[0] + last[0]).upper()
        elif first:
            initials = first[0].upper()
        else:
            initials = "U"

        posts.append({
            "id": post_id,
            "title": title,
            "body": body,
            "created_at": time_ago(created_at),
            "image_url": image_url,
            "user_id": user_id,
            "author": f"{first} {last}".strip(),
            "initials": initials,
            "profile_image": profile_image,
        })

    return jsonify(posts)

# Post creation + post image upload - Nafis,Ismaeel 
@app.route("/api/posts", methods=["POST"])
@login_required
def create_post():
    title = ""
    body = ""

    image_url = None

    if request.content_type and request.content_type.startswith("multipart/form-data"):
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()

        file = request.files.get("image")
        if file and file.filename:
            if not allowed_post_image(file.filename):
                return jsonify({"error": "Unsupported image type"}), 400

            ext = file.filename.rsplit(".", 1)[1].lower()
            safe_name = secure_filename(file.filename.rsplit(".", 1)[0])[:40] or "post"
            fname = f"post_{session['user_id']}_{uuid.uuid4().hex}_{safe_name}.{ext}"

            save_path = os.path.join(POST_UPLOAD_DIR, fname)
            file.save(save_path)

            image_url = f"/static/uploads/posts/{fname}"

    else:
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        body = (data.get("body") or "").strip()

    if not title:
        return jsonify({"error": "Missing title"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO posts (user_id, title, body, image_url)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (session["user_id"], title, body, image_url),
    )

    post_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"success": True, "post_id": post_id, "image_url": image_url})


@app.route("/dev/create-test-posts")
def create_test_posts():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, first_name FROM users LIMIT 6")
    users = cur.fetchall()

    if len(users) < 6:
        cur.close()
        conn.close()
        return "You need at least 6 users in the database!"

    for user in users:
        user_id = user[0]
        name = user[1] or "User"

        for i in range(1, 4):
            cur.execute(
                """
                INSERT INTO posts (user_id, title, body, image_url)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, f"{name}'s Post #{i}", f"This is a test post #{i} by {name}.", None),
            )

    conn.commit()
    cur.close()
    conn.close()

    return "Created 3 posts for each of 6 users (18 posts total)."

# Other users' profile page
@app.route("/profile/<int:user_id>")
@login_required
def profile_dynamic(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, first_name, last_name, profile_image
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return "User not found", 404

    # follower counts
    try:
        cur.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (user_id,))
        followers = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
        following = cur.fetchone()[0]
    except Exception:
        followers = 0
        following = 0

    cur.execute(
        """
        SELECT 1 FROM follows
        WHERE follower_id = %s AND following_id = %s
        """,
        (session["user_id"], user_id),
    )
    is_following = cur.fetchone() is not None

    cur.execute(
        """
        SELECT id, title, body, created_at, image_url
        FROM posts
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    posts_rows = cur.fetchall()

    cur.close()
    conn.close()

    posts = []
    for p in posts_rows:
        posts.append((p[0], p[1], p[2], time_ago(p[3]), p[4]))

    return render_template(
        "profile-other.html",
        profile_user={
            "id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "profile_image": user[4],
            "followers": followers,
            "following": following,
        },
        posts=posts,
        is_following=is_following,
        user_name=session.get("user_name"),
    )

# Follow / Following
@app.route("/api/toggle-follow", methods=["POST"])
def toggle_follow():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    target_user_id = int(data.get("user_id"))
    follower_id = session["user_id"]

    if follower_id == target_user_id:
        return jsonify({"error": "You can't follow yourself"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1 FROM follows
        WHERE follower_id = %s AND following_id = %s
        """,
        (follower_id, target_user_id),
    )
    exists = cur.fetchone()

    if exists:
        cur.execute(
            """
            DELETE FROM follows
            WHERE follower_id = %s AND following_id = %s
            """,
            (follower_id, target_user_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "unfollowed"})

    cur.execute(
        """
        INSERT INTO follows (follower_id, following_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (follower_id, target_user_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "followed"})


@app.route("/api/following/<int:user_id>")
def get_following(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT users.id, users.first_name, users.last_name, users.username
        FROM follows
        JOIN users ON users.id = follows.following_id
        WHERE follows.follower_id = %s
        """,
        (user_id,),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(
        [
            {"id": r[0], "name": f"{r[1]} {r[2]}".strip(), "username": r[3]}
            for r in rows
        ]
    )

# Comments - Nafis
@app.route("/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT c.id, u.first_name, u.last_name, u.profile_image, c.content, c.created_at
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = %s AND c.is_deleted = FALSE
        ORDER BY c.created_at ASC
        """,
        (post_id,),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(
        [
            {
                "id": r[0],
                "username": f"{r[1]} {r[2]}".strip(),
                "profile_image": r[3],
                "content": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
            }
            for r in rows
        ]
    )


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    if not session.get("user_logged_in") or not session.get("user_id"):
        return jsonify(success=False, error="Not logged in"), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify(success=False, error="Missing content"), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        return jsonify(success=False, error="Post not found"), 404

    user_id = session["user_id"]

    cur.execute(
        """
        INSERT INTO comments (post_id, user_id, content, is_deleted, created_at)
        VALUES (%s, %s, %s, FALSE, NOW())
        RETURNING id, created_at
        """,
        (post_id, user_id, content),
    )

    new_row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(
        success=True,
        comment_id=new_row[0],
        created_at=new_row[1].isoformat() if new_row[1] else None,
    )


@app.route("/admin/comments/delete/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    if not session.get("admin_logged_in"):
        return jsonify(success=False, error="Admin not logged in"), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE comments
        SET is_deleted = TRUE
        WHERE id = %s
        """,
        (comment_id,),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(success=True)

# Profile edit + upload pfp - Nafis
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
    cur.execute("UPDATE users SET profile_image=%s WHERE id=%s", (public_path, user_id))
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

    if request.method == "GET":
        cur.execute(
            """
            SELECT first_name, last_name, username, email, profile_image
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify(success=False), 404

        return jsonify(
            {
                "success": True,
                "first_name": row[0],
                "last_name": row[1],
                "username": row[2],
                "email": row[3],
                "profile_image": row[4],
            }
        )

    data = request.get_json(silent=True) or {}
    first = data.get("first_name")
    last = data.get("last_name")
    username = data.get("username")
    email = data.get("email")
    user_type = (data.get("user_type") or "").strip().lower()

    cur.execute(
        """
        UPDATE users
        SET first_name=%s,
            last_name=%s,
            username=%s,
            email=%s,
            user_type=%s
        WHERE id=%s
        """,
        (first, last, username, email, user_type, session["user_id"]),
    )

    conn.commit()
    cur.close()
    conn.close()

    session["user_name"] = f"{first} {last}"

    return jsonify(success=True)

@app.context_processor
def inject_nav_user():
    if not session.get("user_logged_in") or not session.get("user_id"):
        return {"nav_profile_image": None}

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT profile_image FROM users WHERE id=%s", (session["user_id"],))
    row = cur.fetchone()
    cur.close()
    conn.close()

    return {"nav_profile_image": row[0] if row else None}

# Search - Juzer
@app.route("/api/search", methods=["GET"])
def api_search_all():
    q = (request.args.get("q") or "").strip()

    if not q:
        return jsonify({"users": [], "posts": [], "subjects": []})

    like = f"%{q}%"

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # --- People ---
        cur.execute(
            """
            SELECT id, username, first_name, last_name, profile_image
            FROM users
            WHERE username ILIKE %s
               OR first_name ILIKE %s
               OR last_name ILIKE %s
            ORDER BY id DESC
            LIMIT 8
            """,
            (like, like, like),
        )
        people_rows = cur.fetchall()

        # --- Posts ---
        cur.execute(
            """
            SELECT p.id, p.title, p.body, u.first_name, u.last_name
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.title ILIKE %s OR p.body ILIKE %s
            ORDER BY p.created_at DESC
            LIMIT 8
            """,
            (like, like),
        )
        post_rows = cur.fetchall()

        people = []
        for r in people_rows:
            uid, username, first, last, profile_image = r
            name = f"{first or ''} {last or ''}".strip() or username or "User"
            people.append(
                {
                    "id": uid,
                    "name": name,
                    "username": username,
                    "profile_image": profile_image,
                }
            )

        posts = []
        for r in post_rows:
            pid, title, body, first, last = r
            author = f"{first or ''} {last or ''}".strip() or "User"
            posts.append(
                {
                    "id": pid,
                    "title": title,
                    "body": body,
                    "author": author,
                }
            )

        return jsonify({"users": people, "posts": posts, "subjects": []})

    finally:
        cur.close()
        conn.close()

# Mutuals - Ismaeel
@app.route("/api/friends")
@login_required
def get_friends():
    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT u.id, u.first_name, u.last_name, u.username, u.profile_image
        FROM follows f1
        JOIN follows f2
          ON f1.following_id = f2.follower_id
         AND f1.follower_id = f2.following_id
        JOIN users u
          ON u.id = f1.following_id
        WHERE f1.follower_id = %s
        """,
        (user_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "name": f"{r[1]} {r[2]}".strip(),
            "username": r[3],
            "profile_image": r[4],
        }
        for r in rows
    ])

if __name__ == "__main__":
    safe_init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
