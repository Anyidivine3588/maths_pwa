import os
from functools import wraps
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

import db
import solvers

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

# Set this env var on your host to control who can register as a teacher.
TEACHER_SIGNUP_CODE = os.environ.get("TEACHER_SIGNUP_CODE", "TEACHME123")

with app.app_context():
    db.init_db()


# --------------------------------------------------------------- helpers --

def student_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if not session.get("student_id"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapped


def teacher_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if not session.get("teacher_id"):
            return redirect(url_for("teacher_login"))
        return f(*a, **kw)
    return wrapped


TOPIC_LABELS = {
    "algebra": "Algebra",
    "geometry": "Geometry",
    "graphs": "Graphs",
}


# ------------------------------------------------------------------- home --

@app.route("/")
def index():
    if session.get("student_id"):
        return redirect(url_for("dashboard"))
    if session.get("teacher_id"):
        return redirect(url_for("teacher_dashboard"))
    return render_template("index.html")


# --------------------------------------------------------- student auth --

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        class_name = request.form.get("class_name", "").strip()

        if not full_name or not username or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")

        conn = db.get_db()
        existing = conn.execute("SELECT id FROM students WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash("That username is taken — please choose another.", "error")
            return render_template("register.html")

        conn.execute(
            "INSERT INTO students (full_name, username, password_hash, class_name, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (full_name, username, generate_password_hash(password), class_name, db.now_iso()),
        )
        conn.commit()
        student = conn.execute("SELECT id FROM students WHERE username = ?", (username,)).fetchone()
        conn.close()

        session["student_id"] = student["id"]
        session["student_name"] = full_name
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        conn = db.get_db()
        student = conn.execute("SELECT * FROM students WHERE username = ?", (username,)).fetchone()
        conn.close()
        if student and check_password_hash(student["password_hash"], password):
            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------- teacher auth --

@app.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        code = request.form.get("code", "")

        if code != TEACHER_SIGNUP_CODE:
            flash("Invalid teacher signup code.", "error")
            return render_template("teacher_register.html")
        if not full_name or not username or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("teacher_register.html")

        conn = db.get_db()
        existing = conn.execute("SELECT id FROM teachers WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash("That username is taken — please choose another.", "error")
            return render_template("teacher_register.html")

        conn.execute(
            "INSERT INTO teachers (full_name, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (full_name, username, generate_password_hash(password), db.now_iso()),
        )
        conn.commit()
        teacher = conn.execute("SELECT id FROM teachers WHERE username = ?", (username,)).fetchone()
        conn.close()

        session["teacher_id"] = teacher["id"]
        session["teacher_name"] = full_name
        return redirect(url_for("teacher_dashboard"))

    return render_template("teacher_register.html")


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        conn = db.get_db()
        teacher = conn.execute("SELECT * FROM teachers WHERE username = ?", (username,)).fetchone()
        conn.close()
        if teacher and check_password_hash(teacher["password_hash"], password):
            session["teacher_id"] = teacher["id"]
            session["teacher_name"] = teacher["full_name"]
            return redirect(url_for("teacher_dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("teacher_login.html")


# -------------------------------------------------------- student pages --

@app.route("/dashboard")
@student_required
def dashboard():
    conn = db.get_db()
    sid = session["student_id"]
    attempts = conn.execute(
        "SELECT * FROM attempts WHERE student_id = ? ORDER BY created_at DESC", (sid,)
    ).fetchall()
    conn.close()

    total = len(attempts)
    graded = [a for a in attempts if a["correct"] is not None]
    correct_count = sum(1 for a in graded if a["correct"] == 1)
    success_rate = round(100 * correct_count / len(graded), 1) if graded else None

    topic_counts = Counter(a["topic"] for a in attempts)
    recent = attempts[:15]

    return render_template(
        "student_dashboard.html",
        total=total,
        success_rate=success_rate,
        topic_counts=topic_counts,
        recent=recent,
        topic_labels=TOPIC_LABELS,
    )


@app.route("/solve/<topic>")
@student_required
def solve_page(topic):
    if topic not in TOPIC_LABELS:
        return redirect(url_for("dashboard"))
    return render_template(f"solve_{topic}.html", topic=topic, topic_label=TOPIC_LABELS[topic])


# ------------------------------------------------------------- teacher pages --

@app.route("/teacher/dashboard")
@teacher_required
def teacher_dashboard():
    conn = db.get_db()
    students = conn.execute("SELECT * FROM students ORDER BY full_name").fetchall()
    all_attempts = conn.execute("SELECT * FROM attempts").fetchall()
    conn.close()

    total_students = len(students)
    total_attempts = len(all_attempts)

    active_ids = {a["student_id"] for a in all_attempts}
    active_students = len(active_ids)

    topic_counts = Counter(a["topic"] for a in all_attempts)
    subtopic_counts = Counter(f'{a["topic"]} / {a["subtopic"]}' for a in all_attempts)

    # attempts in the last 7 days, per day, for a simple trend
    last_7 = defaultdict(int)
    cutoff = datetime.utcnow() - timedelta(days=6)
    for a in all_attempts:
        try:
            ts = datetime.fromisoformat(a["created_at"])
        except Exception:
            continue
        if ts >= cutoff.replace(hour=0, minute=0, second=0, microsecond=0):
            last_7[ts.date().isoformat()] += 1
    days = [(cutoff + timedelta(days=i)).date().isoformat() for i in range(7)]
    trend = [{"date": d, "count": last_7.get(d, 0)} for d in days]

    # per-student summary for the roster table
    per_student = defaultdict(lambda: {"attempts": 0, "last_active": None, "topics": set()})
    for a in all_attempts:
        s = per_student[a["student_id"]]
        s["attempts"] += 1
        s["topics"].add(a["topic"])
        if not s["last_active"] or a["created_at"] > s["last_active"]:
            s["last_active"] = a["created_at"]

    roster = []
    for st in students:
        info = per_student.get(st["id"], {"attempts": 0, "last_active": None, "topics": set()})
        roster.append({
            "id": st["id"],
            "full_name": st["full_name"],
            "username": st["username"],
            "class_name": st["class_name"],
            "attempts": info["attempts"],
            "last_active": info["last_active"],
            "topics_covered": len(info["topics"]),
        })
    roster.sort(key=lambda r: r["attempts"], reverse=True)

    least_practiced = sorted(TOPIC_LABELS.keys(), key=lambda t: topic_counts.get(t, 0))

    return render_template(
        "teacher_dashboard.html",
        total_students=total_students,
        total_attempts=total_attempts,
        active_students=active_students,
        topic_counts=topic_counts,
        subtopic_counts=subtopic_counts.most_common(8),
        trend=trend,
        roster=roster,
        topic_labels=TOPIC_LABELS,
        least_practiced=least_practiced,
    )


@app.route("/teacher/student/<int:student_id>")
@teacher_required
def teacher_student_detail(student_id):
    conn = db.get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        conn.close()
        return redirect(url_for("teacher_dashboard"))
    attempts = conn.execute(
        "SELECT * FROM attempts WHERE student_id = ? ORDER BY created_at DESC", (student_id,)
    ).fetchall()
    conn.close()

    topic_counts = Counter(a["topic"] for a in attempts)
    subtopic_counts = Counter(f'{a["topic"]} / {a["subtopic"]}' for a in attempts).most_common(10)

    return render_template(
        "teacher_student_detail.html",
        student=student,
        attempts=attempts,
        topic_counts=topic_counts,
        subtopic_counts=subtopic_counts,
        topic_labels=TOPIC_LABELS,
    )


@app.route("/teacher/logout")
def teacher_logout():
    session.pop("teacher_id", None)
    session.pop("teacher_name", None)
    return redirect(url_for("index"))


# ------------------------------------------------------------- solver API --

@app.route("/api/solve/algebra/<sub>", methods=["POST"])
@student_required
def api_algebra(sub):
    data = request.get_json(force=True)
    sid = session["student_id"]

    if sub == "quadratic":
        res = solvers.solve_quadratic(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "linear":
        res = solvers.solve_linear(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "simultaneous-linear":
        res = solvers.solve_simultaneous_linear(data.get("eq1", ""), data.get("eq2", ""))
        summary = f'{data.get("eq1","")} | {data.get("eq2","")}'
    elif sub == "simultaneous-mixed":
        res = solvers.solve_simultaneous_mixed(data.get("linear", ""), data.get("quad", ""))
        summary = f'{data.get("linear","")} | {data.get("quad","")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "algebra", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/geometry/<sub>", methods=["POST"])
@student_required
def api_geometry(sub):
    data = request.get_json(force=True)
    sid = session["student_id"]

    if sub == "area-perimeter":
        shape = data.get("shape")
        vals = {k: v for k, v in data.items() if k != "shape"}
        res = solvers.area_perimeter(shape, **vals)
        summary = f'{shape}: {vals}'
    elif sub == "pythagoras":
        res = solvers.pythagoras(data.get("mode"), a=data.get("a"), b=data.get("b"), c=data.get("c"))
        summary = f'{data.get("mode")}: a={data.get("a")}, b={data.get("b")}, c={data.get("c")}'
    elif sub == "coordinate":
        res = solvers.coordinate_geometry(data.get("x1"), data.get("y1"), data.get("x2"), data.get("y2"))
        summary = f'({data.get("x1")},{data.get("y1")}) to ({data.get("x2")},{data.get("y2")})'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "geometry", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/graphs/<sub>", methods=["POST"])
@student_required
def api_graphs(sub):
    data = request.get_json(force=True)
    sid = session["student_id"]

    if sub == "table":
        res = solvers.table_of_values(
            data.get("expr", ""), data.get("x_min", -5), data.get("x_max", 5), data.get("step", 1)
        )
        summary = data.get("expr", "")
    elif sub == "plot":
        res = solvers.plot_functions_png(
            data.get("expr", ""), data.get("expr2") or None,
            data.get("x_min", -10), data.get("x_max", 10),
        )
        summary = f'{data.get("expr","")} / {data.get("expr2","")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "graphs", sub, input_summary=summary, correct=None)
    return jsonify(res)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
