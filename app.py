import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta
import os
# =====================
# App Config
# =====================
app = Flask(__name__)
app.secret_key = "secret_key_here"

# Database configuration

uri = os.getenv("DATABASE_URL", "sqlite:///database.db")

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# =====================
# DSA Topics (Global)
# =====================
DSA_TOPICS = [
    "Arrays",
    "Strings",
    "Linked List",
    "Stack",
    "Queue",
    "Recursion",
    "Binary Search",
    "Sorting",
    "Hashing",
    "Trees",
    "Graphs"
]

DEFAULT_QUESTIONS = {
    "Arrays": [
        ("Two Sum", "Easy", "https://leetcode.com/problems/two-sum"),
        ("Best Time to Buy and Sell Stock", "Easy", "https://leetcode.com/problems/best-time-to-buy-and-sell-stock"),
        ("Product of Array Except Self", "Medium", "https://leetcode.com/problems/product-of-array-except-self"),
    ],
    "Strings": [
        ("Valid Palindrome", "Easy", "https://leetcode.com/problems/valid-palindrome"),
        ("Longest Substring Without Repeating Characters", "Medium",
         "https://leetcode.com/problems/longest-substring-without-repeating-characters"),
        ("Valid Anagram", "Easy", "https://leetcode.com/problems/valid-anagram"),
    ],
    "Linked List": [
        ("Reverse Linked List", "Easy", "https://leetcode.com/problems/reverse-linked-list"),
        ("Merge Two Sorted Lists", "Easy", "https://leetcode.com/problems/merge-two-sorted-lists"),
    ],
    "Stack": [
        ("Valid Parentheses", "Easy", "https://leetcode.com/problems/valid-parentheses"),
        ("Min Stack", "Medium", "https://leetcode.com/problems/min-stack"),
    ],
    "Queue": [
        ("Implement Queue using Stacks", "Easy",
         "https://leetcode.com/problems/implement-queue-using-stacks"),
    ],
    "Recursion": [
        ("Fibonacci Number", "Easy", "https://leetcode.com/problems/fibonacci-number"),
    ],
    "Binary Search": [
        ("Binary Search", "Easy", "https://leetcode.com/problems/binary-search"),
        ("Search Insert Position", "Easy", "https://leetcode.com/problems/search-insert-position"),
    ],
    "Sorting": [
        ("Merge Sorted Array", "Easy", "https://leetcode.com/problems/merge-sorted-array"),
    ],
    "Hashing": [
        ("Contains Duplicate", "Easy", "https://leetcode.com/problems/contains-duplicate"),
    ],
    "Trees": [
        ("Maximum Depth of Binary Tree", "Easy",
         "https://leetcode.com/problems/maximum-depth-of-binary-tree"),
    ],
    "Graphs": [
        ("Number of Islands", "Medium", "https://leetcode.com/problems/number-of-islands")
    ]
}

# =====================
# Models
# =====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class DSATopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_email = db.Column(db.String(100), nullable=False)

class DailyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    task = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    user_email = db.Column(db.String(100))

class StudyDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    user_email = db.Column(db.String(100))

class DSAQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50))
    title = db.Column(db.String(200))
    difficulty = db.Column(db.String(20))
    link = db.Column(db.String(300))
    solved = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    user_email = db.Column(db.String(100))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    difficulty = db.Column(db.String(20))
    link = db.Column(db.String(300))
    topic = db.Column(db.String(50))
    solved = db.Column(db.Boolean, default=False)
    user_email = db.Column(db.String(100))

# =====================
# Helper Functions
# =====================
def ensure_topics_for_user(email):
    exists = DSATopic.query.filter_by(user_email=email).first()
    if exists:
        return

    for topic in DSA_TOPICS:
        db.session.add(
            DSATopic(
                topic=topic,
                completed=False,
                user_email=email
            )
        )
    db.session.commit()

def calculate_streak(email):
    days = StudyDay.query.filter_by(user_email=email).all()
    dates = set(d.date for d in days)

    streak = 0
    current = date.today()

    while str(current) in dates:
        streak += 1
        current -= timedelta(days=1)

    return streak

def ensure_questions_for_user(email):
    for topic, questions in DEFAULT_QUESTIONS.items():
        for title, diff, link in questions:
            exists = Question.query.filter_by(
                user_email=email,
                title=title,
                topic=topic
            ).first()

            if not exists:
                q = Question(
                    title=title,
                    difficulty=diff,
                    link=link,
                    topic=topic,
                    user_email=email
                )
                db.session.add(q)
    db.session.commit()

# =====================
# Routes
# =====================
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")

# ---------- Signup ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("signup"))

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        ensure_topics_for_user(email)
        ensure_questions_for_user(email)

        session["user"] = email
        flash("Account created successfully 🎉", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")

# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user"] = email
            flash("Login successful ✅", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password ❌", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

# ---------- Dashboard ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]

    # Topic wise progress
    topics = []
    for t in DSA_TOPICS:
        total = Question.query.filter_by(user_email=email, topic=t).count()
        done = Question.query.filter_by(user_email=email, topic=t, solved=True).count()
        percent = int((done / total) * 100) if total > 0 else 0
        topics.append({
            "name": t,
            "total": total,
            "done": done,
            "percent": percent
        })

    # OVERALL PROGRESS
    all_questions = Question.query.filter_by(user_email=email).all()
    total_q = len(all_questions)
    done_q = len([q for q in all_questions if q.solved])
    progress = int((done_q / total_q) * 100) if total_q > 0 else 0

    # Planner + streak
    today = str(date.today())
    today_plans = DailyPlan.query.filter_by(
        user_email=email,
        date=today
    ).all()
    today_done = len([p for p in today_plans if p.completed])
    today_total = len(today_plans)
    streak = calculate_streak(email)

    return render_template(
        "dashboard.html",
        topics=topics,
        progress=progress,
        today_done=today_done,
        today_total=today_total,
        streak=streak
    )

# ---------- Update Topic ----------
@app.route("/topic/<topic_name>")
def topic_page(topic_name):
    if "user" not in session:
        return redirect(url_for("login"))

    questions = Question.query.filter_by(
        user_email=session["user"],
        topic=topic_name
    ).all()

    total = len(questions)
    done = len([q for q in questions if q.solved])
    percent = int((done / total) * 100) if total > 0 else 0

    return render_template(
        "topic.html",
        questions=questions,
        topic=topic_name,
        total=total,
        done=done,
        percent=percent
    )

# ---------- Planner ----------
@app.route("/planner")
def planner():
    if "user" not in session:
        return redirect(url_for("login"))

    selected_date = request.args.get("date", str(date.today()))
    plans = DailyPlan.query.filter_by(
        user_email=session["user"],
        date=selected_date
    ).all()

    return render_template(
        "planner.html",
        plans=plans,
        selected_date=selected_date
    )

@app.route("/add-plan", methods=["POST"])
def add_plan():
    if "user" not in session:
        return redirect(url_for("login"))

    task = request.form["task"]
    date_selected = request.form["date"]

    plan = DailyPlan(
        task=task,
        date=date_selected,
        user_email=session["user"]
    )

    db.session.add(plan)
    db.session.commit()

    return redirect(url_for("planner", date=date_selected))

@app.route("/toggle-question/<int:id>", methods=["POST"])
def toggle_question(id):
    if "user" not in session:
        return {"error": "login required"}, 401

    q = Question.query.get(id)

    # security check
    if q.user_email != session["user"]:
        return {"error": "unauthorized"}, 403

    q.solved = not q.solved
    db.session.commit()

    return {"status": "ok"}

@app.route("/toggle-plan/<int:id>", methods=["POST"])
def toggle_plan(id):
    if "user" not in session:
        return {"error": "login required"}, 401
    plan = DailyPlan.query.get(id)
    if plan.user_email != session["user"]:
        return {"error": "unauthorized"}, 403
    plan.completed = not plan.completed
    db.session.commit()
    return {"status": "ok"}

# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully 👋", "info")
    return redirect(url_for("login"))

@app.route("/delete-plan", methods=["POST"])
def delete_plan():
    if "user" not in session:
        return redirect(url_for("login"))

    plan_id = request.form["id"]
    plan = DailyPlan.query.get(plan_id)

    if plan.user_email != session["user"]:
        return "Unauthorized", 403

    db.session.delete(plan)
    db.session.commit()

    return redirect(url_for("planner", date=plan.date))

# ==========================
# QUESTIONS SYSTEM
# ==========================
@app.route("/questions/<topic>")
def view_questions(topic):
    if "user" not in session:
        return redirect(url_for("login"))

    questions = Question.query.filter_by(
        user_email=session["user"],
        topic=topic
    ).all()

    return render_template(
        "questions.html",
        topic=topic,
        questions=questions
    )

@app.route("/add-question", methods=["POST"])
def add_question():
    if "user" not in session:
        return redirect(url_for("login"))

    q = Question(
        title=request.form["title"],
        difficulty=request.form["difficulty"],
        link=request.form["link"],
        topic=request.form["topic"],
        user_email=session["user"]
    )

    db.session.add(q)
    db.session.commit()

    return redirect(url_for("view_questions", topic=request.form["topic"]))

@app.route("/delete-question", methods=["POST"])
def delete_question():
    if "user" not in session:
        return "Unauthorized", 401

    qid = request.form["id"]
    q = Question.query.get(qid)

    # Security: ensure user owns this question
    if q.user_email != session["user"]:
        return "Not allowed", 403

    db.session.delete(q)
    db.session.commit()

    return "OK"

# ---------- UPDATE TOPIC PROGRESS ----------
@app.route("/update-topic", methods=["POST"])
def update_topic():
    if "user" not in session:
        return {"progress": 0}

    topic_id = request.form["id"]
    completed = request.form["completed"] == "true"

    topic = DSATopic.query.get(topic_id)

    # security check
    if topic.user_email != session["user"]:
        return {"progress": 0}

    topic.completed = completed
    db.session.commit()

    # Recalculate progress
    topics = DSATopic.query.filter_by(user_email=session["user"]).all()
    total = len(topics)
    done = len([t for t in topics if t.completed])
    progress = int((done / total) * 100) if total else 0

    return {"progress": progress}

@app.route("/init-db")
def init_db():
    db.create_all()
    return "Database tables created successfully!"

# =====================
# Run App
# =====================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
