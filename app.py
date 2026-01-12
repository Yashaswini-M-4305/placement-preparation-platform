from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

# =====================
# App Config
# =====================
app = Flask(__name__)
app.secret_key = "secret_key_here"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

def ensure_topics_for_user(email):
    existing = DSATopic.query.filter_by(user_email=email).first()

    if existing:
        return  # topics already exist

    for topic in DSA_TOPICS:
        db.session.add(
            DSATopic(
                topic=topic,
                completed=False,
                user_email=email
            )
        )

    db.session.commit()

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

# =====================
# Home
# =====================
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")

# =====================
# Signup
# =====================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        # Check existing email
        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("signup"))

        # Create user
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        # Auto add DSA topics
        for topic in DSA_TOPICS:
            db.session.add(
                DSATopic(
                    topic=topic,
                    completed=False,
                    user_email=email
                )
            )
        db.session.commit()

        # Auto login
        session["user"] = email
        flash("Account created successfully 🎉", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")

# =====================
# Login
# =====================
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

# =====================
# Dashboard
# =====================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # 🔥 FIX FOR OLD USERS
    ensure_topics_for_user(session["user"])

    topics = DSATopic.query.filter_by(
        user_email=session["user"]
    ).all()

    total = len(topics)
    done = len([t for t in topics if t.completed])
    progress = int((done / total) * 100) if total > 0 else 0

    return render_template(
        "dashboard.html",
        topics=topics,
        progress=progress
    )


# =====================
# Update Topic (AJAX)
# =====================
@app.route("/update-topic", methods=["POST"])
def update_topic():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401

    topic_id = request.form["id"]
    completed = request.form["completed"] == "true"

    topic = DSATopic.query.get(topic_id)
    topic.completed = completed
    db.session.commit()

    # 🔢 recalculate progress
    topics = DSATopic.query.filter_by(
        user_email=session["user"]
    ).all()

    total = len(topics)
    done = len([t for t in topics if t.completed])
    progress = int((done / total) * 100) if total > 0 else 0

    return {"progress": progress}



# =====================
# Logout
# =====================
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully 👋", "info")
    return redirect(url_for("login"))

# =====================
# Run App
# =====================
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

@app.route("/toggle-plan", methods=["POST"])
def toggle_plan():
    plan_id = request.form["id"]
    plan = DailyPlan.query.get(plan_id)
    plan.completed = not plan.completed
    db.session.commit()
    return "OK"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


