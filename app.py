import os
import re
import signal
import time
import hmac
import hashlib
import secrets
from urllib.parse import urlparse
from functools import wraps
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

import db
import solvers
import frac_numeric as fnum
import frac_algebra as falg
import stats_solvers as stats
import topics

app = Flask(__name__)

# --- secret key: never a publicly-known default ---------------------------
_key = os.environ.get("SECRET_KEY", "").strip()
if not _key:
    _dburl = os.environ.get("DATABASE_URL", "")
    if _dburl:
        # Stable, private fallback derived from the DB password so logins
        # survive restarts even if SECRET_KEY was never set. Set SECRET_KEY
        # on Render for best security.
        _key = hashlib.sha256(("maths-assist|" + _dburl).encode()).hexdigest()
    else:
        _key = secrets.token_hex(32)  # local testing only
app.secret_key = _key

_IS_PROD = bool(os.environ.get("DATABASE_URL")) or bool(os.environ.get("RENDER"))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=_IS_PROD,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=256 * 1024,
)

# Who may register as a teacher. NO default: if unset, teacher sign-up is closed.
TEACHER_SIGNUP_CODE = os.environ.get("TEACHER_SIGNUP_CODE", "").strip()

MIN_PASSWORD_LEN = 8
_USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,30}$")

# --- login throttling (per IP + username, in memory) -----------------------
_FAILS = defaultdict(list)
_MAX_FAILS = 5
_WINDOW = 15 * 60


def _client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() if fwd else request.remote_addr) or "?"


def _throttle_key(kind, username):
    return f"{kind}|{_client_ip()}|{username}"


def _is_locked(key):
    now = time.time()
    _FAILS[key] = [t for t in _FAILS[key] if now - t < _WINDOW]
    return len(_FAILS[key]) >= _MAX_FAILS


def _record_fail(key):
    _FAILS[key].append(time.time())


def _clear_fails(key):
    _FAILS.pop(key, None)


@app.before_request
def _csrf_origin_check():
    """Block cross-site POSTs: if the browser says the request came from a
    different website, refuse it."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        src = request.headers.get("Origin") or request.headers.get("Referer")
        if src:
            host = urlparse(src).netloc
            if host and host != request.host:
                return ("Blocked: cross-site request.", 403)


@app.after_request
def _security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if _IS_PROD:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.path.startswith(("/teacher", "/dashboard", "/api", "/login", "/register")):
        resp.headers["Cache-Control"] = "no-store"
    return resp

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


@app.route("/teacher/db-status")
@teacher_required
def db_status():
    """Teacher-only diagnostic. Shows no secrets."""
    lines = [
        f"Permanent database (DATABASE_URL) in use: {bool(os.environ.get('DATABASE_URL'))}",
        f"Teacher signup code is set: {bool(TEACHER_SIGNUP_CODE)}",
        f"SECRET_KEY is set: {bool(os.environ.get('SECRET_KEY'))}",
    ]
    try:
        conn = db.get_db()
        row = conn.execute("SELECT COUNT(*) AS n FROM students").fetchone()
        conn.close()
        lines.append(f"Database connected. Students: {row['n'] if row else '?'}")
    except Exception:
        lines.append("Database connection FAILED (see Render logs).")
    return "<pre>" + "\n".join(lines) + "</pre>"


# A runaway calculation (a huge number, a monstrous expression) must never freeze the
# site for everybody, so each solver call is cut off after a few seconds.
class _SolveTimeout(Exception):
    pass


def limited(seconds=8):
    def deco(f):
        @wraps(f)
        def wrapped(*a, **kw):
            def _handler(signum, frame):
                raise _SolveTimeout()
            try:
                old = signal.signal(signal.SIGALRM, _handler)
                signal.setitimer(signal.ITIMER_REAL, seconds)
            except (ValueError, AttributeError):  # not the main thread / no SIGALRM
                return f(*a, **kw)
            try:
                return f(*a, **kw)
            except _SolveTimeout:
                return jsonify({"ok": False, "error": "That problem took too long to solve. "
                                                      "Try smaller numbers or a simpler expression."})
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old)
        return wrapped
    return deco


TOPIC_LABELS = topics.TOPIC_LABELS
topics._load()


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
        if not _USERNAME_RE.match(username):
            flash("Username must be 3-30 characters: letters, numbers, . _ - only.", "error")
            return render_template("register.html")
        if len(password) < MIN_PASSWORD_LEN:
            flash(f"Password must be at least {MIN_PASSWORD_LEN} characters.", "error")
            return render_template("register.html")
        full_name = full_name[:100]
        class_name = class_name[:50]

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

        session.clear()
        session.permanent = True
        session["student_id"] = student["id"]
        session["student_name"] = full_name
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        tkey = _throttle_key("student", username)
        if _is_locked(tkey):
            flash("Too many failed attempts. Please wait 15 minutes and try again.", "error")
            return render_template("login.html"), 429
        conn = db.get_db()
        student = conn.execute("SELECT * FROM students WHERE username = ?", (username,)).fetchone()
        conn.close()
        if student and check_password_hash(student["password_hash"], password):
            _clear_fails(tkey)
            session.clear()
            session.permanent = True
            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]
            return redirect(url_for("dashboard"))
        _record_fail(tkey)
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

        tkey = _throttle_key("tsignup", "-")
        if _is_locked(tkey):
            flash("Too many failed attempts. Please wait 15 minutes and try again.", "error")
            return render_template("teacher_register.html"), 429
        if not TEACHER_SIGNUP_CODE or not hmac.compare_digest(code.encode(), TEACHER_SIGNUP_CODE.encode()):
            _record_fail(tkey)
            flash("Invalid teacher signup code.", "error")
            return render_template("teacher_register.html")
        if not full_name or not username or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("teacher_register.html")
        if not _USERNAME_RE.match(username):
            flash("Username must be 3-30 characters: letters, numbers, . _ - only.", "error")
            return render_template("teacher_register.html")
        if len(password) < 10:
            flash("Teacher password must be at least 10 characters.", "error")
            return render_template("teacher_register.html")
        full_name = full_name[:100]

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

        session.clear()
        session.permanent = True
        session["teacher_id"] = teacher["id"]
        session["teacher_name"] = full_name
        return redirect(url_for("teacher_dashboard"))

    return render_template("teacher_register.html")


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        tkey = _throttle_key("teacher", username)
        if _is_locked(tkey):
            flash("Too many failed attempts. Please wait 15 minutes and try again.", "error")
            return render_template("teacher_login.html"), 429
        conn = db.get_db()
        teacher = conn.execute("SELECT * FROM teachers WHERE username = ?", (username,)).fetchone()
        conn.close()
        if teacher and check_password_hash(teacher["password_hash"], password):
            _clear_fails(tkey)
            session.clear()
            session.permanent = True
            session["teacher_id"] = teacher["id"]
            session["teacher_name"] = teacher["full_name"]
            return redirect(url_for("teacher_dashboard"))
        _record_fail(tkey)
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
    if topic in topics.SPECS:
        return render_template("solve_generic.html", topic=topic, topic_label=TOPIC_LABELS[topic], spec=topics.SPECS[topic])
    return render_template(f"solve_{topic}.html", topic=topic, topic_label=TOPIC_LABELS[topic])


@app.route("/topics")
@student_required
def topics_page():
    groups = {}
    for key, label, desc, group in topics.TOPIC_INFO:
        if key in topics.SPECS or os.path.exists(os.path.join(app.root_path, "templates", f"solve_{key}.html")):
            groups.setdefault(group, []).append((key, label, desc))
    return render_template("topics.html", groups=list(groups.items()))


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
    session.clear()
    return redirect(url_for("index"))


# ------------------------------------------------------------- solver API --

@app.route("/api/solve/algebra/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_algebra(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "quadratic":
        res = solvers.solve_quadratic(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "quadratic-factorisation":
        res = solvers.solve_quadratic_factorisation(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "quadratic-completing-square":
        res = solvers.solve_quadratic_completing_square(data.get("expr", ""))
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
@limited(10)
def api_geometry(sub):
    data = (request.get_json(force=True, silent=True) or {})
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
@limited(10)
def api_graphs(sub):
    data = (request.get_json(force=True, silent=True) or {})
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
            data.get("y_min") or None, data.get("y_max") or None,
            data.get("x_scale") or None, data.get("y_scale") or None,
        )
        summary = f'{data.get("expr","")} / {data.get("expr2","")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "graphs", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/sequences/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_sequences(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "ap-solve":
        res = solvers.ap_solve(data.get("a") or None, data.get("d") or None,
                                data.get("n") or None, data.get("Tn") or None, data.get("Sn") or None)
        summary = f'a={data.get("a")}, d={data.get("d")}, n={data.get("n")}, Tn={data.get("Tn")}, Sn={data.get("Sn")}'
    elif sub == "ap-terms":
        res = solvers.ap_list_terms(data.get("a"), data.get("d"), data.get("start"), data.get("end"))
        summary = f'a={data.get("a")}, d={data.get("d")}, terms {data.get("start")}-{data.get("end")}'
    elif sub == "gp-solve":
        res = solvers.gp_solve(data.get("a") or None, data.get("r") or None,
                                data.get("n") or None, data.get("Tn") or None, data.get("Sn") or None)
        summary = f'a={data.get("a")}, r={data.get("r")}, n={data.get("n")}, Tn={data.get("Tn")}, Sn={data.get("Sn")}'
    elif sub == "gp-terms":
        res = solvers.gp_list_terms(data.get("a"), data.get("r"), data.get("start"), data.get("end"))
        summary = f'a={data.get("a")}, r={data.get("r")}, terms {data.get("start")}-{data.get("end")}'
    elif sub == "gp-sum-infinity":
        res = solvers.gp_sum_infinity(data.get("a"), data.get("r"))
        summary = f'a={data.get("a")}, r={data.get("r")}'
    elif sub == "general":
        res = solvers.general_sequence(data.get("terms", ""), data.get("find_upto") or None)
        summary = f'terms={data.get("terms")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "sequences", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/sets/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_sets(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "operations":
        res = solvers.set_operations(data.get("set_a", ""), data.get("set_b", ""), data.get("universal") or None)
        summary = f'A={data.get("set_a")}, B={data.get("set_b")}'
    elif sub == "venn2":
        res = solvers.venn_two_set(
            n_u=data.get("n_u") or None, n_a=data.get("n_a") or None,
            n_b=data.get("n_b") or None, n_both=data.get("n_both") or None,
            n_neither=data.get("n_neither") or None,
        )
        summary = f'U={data.get("n_u")}, A={data.get("n_a")}, B={data.get("n_b")}, both={data.get("n_both")}, neither={data.get("n_neither")}'
    elif sub == "venn2-elements":
        res = solvers.venn_two_set_elements(data.get("set_a", ""), data.get("set_b", ""), data.get("universal", ""))
        summary = f'A={data.get("set_a")}, B={data.get("set_b")}, U={data.get("universal")}'
    elif sub == "venn3":
        res = solvers.venn_three_set(
            n_u=data.get("n_u") or None, n_a=data.get("n_a") or None,
            n_b=data.get("n_b") or None, n_c=data.get("n_c") or None,
            n_ab=data.get("n_ab") or None, n_ac=data.get("n_ac") or None,
            n_bc=data.get("n_bc") or None, n_abc=data.get("n_abc") or None,
        )
        summary = "3-set Venn problem"
    elif sub == "venn3-elements":
        res = solvers.venn_three_set_elements(data.get("set_a", ""), data.get("set_b", ""),
                                               data.get("set_c", ""), data.get("universal", ""))
        summary = "3-set Venn (elements) problem"
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "sets", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/trigonometry/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_trigonometry(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "right-triangle":
        res = solvers.right_triangle(
            opposite=data.get("opposite") or None, adjacent=data.get("adjacent") or None,
            hypotenuse=data.get("hypotenuse") or None, angle=data.get("angle") or None,
        )
        summary = f'opp={data.get("opposite")}, adj={data.get("adjacent")}, hyp={data.get("hypotenuse")}, angle={data.get("angle")}'
    elif sub == "sine-rule":
        res = solvers.sine_rule(
            a=data.get("a") or None, A=data.get("A") or None,
            b=data.get("b") or None, B=data.get("B") or None,
            c=data.get("c") or None, C=data.get("C") or None,
        )
        summary = "Sine rule"
    elif sub == "cosine-rule":
        res = solvers.cosine_rule(
            a=data.get("a") or None, b=data.get("b") or None,
            c=data.get("c") or None, C=data.get("C") or None,
        )
        summary = "Cosine rule"
    elif sub == "elevation":
        res = solvers.angle_of_elevation(
            height=data.get("height") or None, distance=data.get("distance") or None,
            angle=data.get("angle") or None,
        )
        summary = f'height={data.get("height")}, distance={data.get("distance")}, angle={data.get("angle")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "trigonometry", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/indices/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_indices(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "multiply":
        res = solvers.indices_law_multiply(data.get("base", ""), data.get("m"), data.get("n"))
        summary = f'a={data.get("base")}, m={data.get("m")}, n={data.get("n")}'
    elif sub == "divide":
        res = solvers.indices_law_divide(data.get("base", ""), data.get("m"), data.get("n"))
        summary = f'a={data.get("base")}, m={data.get("m")}, n={data.get("n")}'
    elif sub == "power":
        res = solvers.indices_law_power(data.get("base", ""), data.get("m"), data.get("n"))
        summary = f'a={data.get("base")}, m={data.get("m")}, n={data.get("n")}'
    elif sub == "evaluate":
        res = solvers.indices_evaluate(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "solve":
        res = solvers.indices_solve_equation(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "equal-base":
        res = solvers.indices_solve_equal_base(data.get("expr", ""))
        summary = data.get("expr", "")
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "indices", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/logarithms/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_logarithms(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "evaluate":
        res = solvers.log_evaluate(data.get("expr", ""), data.get("base") or None)
        summary = f'{data.get("expr")}, base={data.get("base")}'
    elif sub == "change-of-base":
        res = solvers.log_change_of_base(data.get("value"), data.get("from_base"), data.get("to_base") or 10)
        summary = f'value={data.get("value")}, from={data.get("from_base")}, to={data.get("to_base")}'
    elif sub == "laws":
        res = solvers.log_laws_simplify(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "solve":
        res = solvers.log_solve_equation(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "tables":
        res = solvers.log_evaluate_tables(data.get("number", ""))
        summary = data.get("number", "")
    elif sub == "antilog":
        res = solvers.log_antilog(data.get("value", ""))
        summary = data.get("value", "")
    elif sub == "calculate":
        res = solvers.log_calculate(data.get("expr", ""))
        summary = data.get("expr", "")
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "logarithms", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/surds/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_surds(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "simplify":
        res = solvers.surd_simplify(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "arithmetic":
        res = solvers.surd_arithmetic(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "rationalize":
        res = solvers.surd_rationalize(data.get("expr", ""))
        summary = data.get("expr", "")
    elif sub == "equation":
        res = solvers.surd_solve_equation(data.get("expr", ""))
        summary = data.get("expr", "")
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "surds", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/bearings/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_bearings(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "convert":
        res = solvers.bearing_convert(data.get("bearing", ""))
        summary = data.get("bearing", "")
    elif sub == "back":
        res = solvers.bearing_back(data.get("bearing", ""))
        summary = data.get("bearing", "")
    elif sub == "journey":
        res = solvers.bearing_journey(data.get("d1"), data.get("b1"), data.get("d2"), data.get("b2"))
        summary = f'd1={data.get("d1")}, b1={data.get("b1")}, d2={data.get("d2")}, b2={data.get("b2")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "bearings", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/solve/earthgeo/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_earthgeo(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]

    if sub == "meridian":
        res = solvers.earth_distance_meridian(
            data.get("lat1"), data.get("lat2"), data.get("R") or None,
            data.get("unit") or "km", data.get("pi_val") or None,
        )
        summary = f'lat1={data.get("lat1")}, lat2={data.get("lat2")}, unit={data.get("unit")}'
    elif sub == "parallel":
        res = solvers.earth_distance_parallel(
            data.get("lat"), data.get("long1"), data.get("long2"),
            data.get("R") or None, data.get("unit") or "km", data.get("pi_val") or None,
        )
        summary = f'lat={data.get("lat")}, long1={data.get("long1")}, long2={data.get("long2")}, unit={data.get("unit")}'
    elif sub == "radius":
        res = solvers.earth_radius_of_parallel(data.get("lat"), data.get("R") or None)
        summary = f'lat={data.get("lat")}, R={data.get("R")}'
    elif sub == "speed":
        res = solvers.earth_distance_speed_time(
            data.get("distance") or None, data.get("speed") or None, data.get("time") or None,
            data.get("distance_unit") or "km", data.get("time_unit") or "hours",
        )
        summary = f'distance={data.get("distance")}, speed={data.get("speed")}, time={data.get("time")}'
    elif sub == "find-meridian":
        res = solvers.earth_find_point_meridian(
            data.get("lat1"), data.get("distance"), data.get("direction"),
            data.get("R") or None, data.get("unit") or "km", data.get("pi_val") or None,
        )
        summary = f'lat1={data.get("lat1")}, distance={data.get("distance")}, direction={data.get("direction")}'
    elif sub == "find-parallel":
        res = solvers.earth_find_point_parallel(
            data.get("lat"), data.get("long1"), data.get("distance"), data.get("direction"),
            data.get("R") or None, data.get("unit") or "km", data.get("pi_val") or None,
        )
        summary = f'lat={data.get("lat")}, long1={data.get("long1")}, distance={data.get("distance")}, direction={data.get("direction")}'
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400

    db.log_attempt(sid, "earthgeo", sub, input_summary=summary, correct=None)
    return jsonify(res)


# --------------------------------------------- fractions & statistics API --

def _s(data, key, maxlen=600):
    v = data.get(key, "")
    return str(v if v is not None else "")[:maxlen]


@app.route("/api/solve/fractions/<sub>", methods=["POST"])
@student_required
@limited(8)
def api_fractions(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]
    text = _s(data, "text")
    if sub == "lcm-hcf":
        want = _s(data, "want", 10) or "both"
        if fnum.has_letters(text):
            res = falg.alg_lcm_hcf(text, want)
        elif "/" in text:
            res = fnum.lcm_hcf_fractions(text, want)
        else:
            res = fnum.lcm_hcf_numbers(text, want, _s(data, "method", 12) or "prime", _s(data, "unit", 30))
    elif sub == "types":
        res = falg.alg_types(text) if fnum.has_letters(text) else fnum.fraction_types(text)
    elif sub == "simplify":
        if fnum.has_letters(text):
            res = falg.alg_expression(text)
        elif fnum.re.fullmatch(r"\s*-?\d+\s*/\s*-?\d+\s*", text):
            res = fnum.simplify_fraction(text)
        else:
            res = fnum.numeric_expression(text)
    elif sub == "operations":
        res = falg.alg_expression(text) if fnum.has_letters(text) else fnum.numeric_expression(text)
    elif sub == "compare":
        res = fnum.compare_fractions(text, _s(data, "order", 12) or "ascending")
    elif sub == "convert":
        kind = _s(data, "kind", 12)
        fn = {"frac2dec": fnum.fraction_to_decimal, "dec2frac": fnum.decimal_to_fraction,
              "frac2pct": fnum.fraction_to_percent, "pct2frac": fnum.percent_to_fraction}.get(kind)
        res = fn(text) if fn else {"ok": False, "error": "Unknown conversion."}
    elif sub == "word":
        kind = _s(data, "kind", 12)
        res = fnum.fraction_word(
            kind, fraction=_s(data, "fraction", 40), quantity=_s(data, "quantity", 30), a=_s(data, "a", 30),
            b=_s(data, "b", 30), part=_s(data, "part", 30), total=_s(data, "total", 30),
            fractions=_s(data, "fractions", 200), basis=_s(data, "basis", 12), direction=_s(data, "direction", 12))
    elif sub == "alg-factorise":
        res = falg.alg_factorise(text)
    elif sub == "alg-solve":
        res = falg.alg_solve(text, _s(data, "var", 2) or None)
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400
    db.log_attempt(sid, "fractions", sub, input_summary=text[:200], correct=None)
    return jsonify(res)


@app.route("/api/solve/statistics/<sub>", methods=["POST"])
@student_required
@limited(8)
def api_statistics(sub):
    data = (request.get_json(force=True, silent=True) or {})
    sid = session["student_id"]
    g = lambda k, n=600: _s(data, k, n)
    if sub == "ungrouped":
        res = stats.stats_ungrouped(g("values", 3000), g("freq", 3000), g("want", 12) or "all")
        summary = g("values", 100)
    elif sub == "grouped":
        res = stats.stats_grouped(g("classes"), g("freq"), g("want", 12) or "all", g("assumed", 20), g("percentile", 10))
        summary = g("classes", 100)
    elif sub == "chart":
        res = stats.stats_chart(g("kind", 12), classes=g("classes"), freq=g("freq"), labels=g("labels"),
                                values=g("values", 3000), title=g("title", 80), read_value=g("read_value", 20),
                                read_percentile=g("read_percentile", 10))
        summary = g("kind", 12)
    elif sub == "mean":
        res = stats.mean_problem(g("kind", 20), values=g("values"), freqs=g("freqs"), mean=g("mean", 30), n1=g("n1", 20),
                                 m1=g("m1", 20), n2=g("n2", 20), m2=g("m2", 20), n=g("n", 20), value=g("value", 20),
                                 action=g("action", 10), weights=g("weights"))
        summary = g("kind", 20)
    elif sub == "prob-simple":
        res = stats.prob_simple(g("favourable", 20), g("total", 20))
        summary = f'{g("favourable", 20)}/{g("total", 20)}'
    elif sub == "prob-combined":
        res = stats.prob_combined(g("pa", 20), g("pb", 20), g("relation", 12) or "independent", g("pab", 20))
        summary = "combined events"
    elif sub == "prob-draw":
        res = stats.prob_draw(g("items"), g("draws", 3) or 2, g("replacement", 5), g("sequence", 100))
        summary = g("items", 100)
    elif sub == "prob-dice":
        res = stats.prob_dice_coins(g("kind", 12), g("event", 20), g("value", 10), g("n", 5) or "2")
        summary = g("kind", 12)
    elif sub == "perm-comb":
        res = stats.perm_comb(g("kind", 12), g("n", 6), g("r", 6))
        summary = f'{g("kind", 12)} n={g("n", 6)} r={g("r", 6)}'
    elif sub == "arrangements":
        res = stats.arrangements(g("word", 20), g("condition", 12) or "none", g("letters", 20))
        summary = g("word", 20)
    else:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400
    db.log_attempt(sid, "statistics", sub, input_summary=summary, correct=None)
    return jsonify(res)


@app.route("/api/g/<topic>/<sub>", methods=["POST"])
@student_required
@limited(10)
def api_generic(topic, sub):
    handler = topics.HANDLERS.get(topic, {}).get(sub)
    if handler is None:
        return jsonify({"ok": False, "error": "Unknown solver."}), 400
    raw = request.get_json(force=True, silent=True) or {}
    if not isinstance(raw, dict):
        raw = {}
    data = {str(k)[:40]: str(v if v is not None else "")[:600] for k, v in raw.items()}
    try:
        res = handler(data)
    except _SolveTimeout:
        raise
    except Exception:
        app.logger.exception("solver %s/%s crashed", topic, sub)
        res = {"ok": False, "steps": [], "result": None,
               "error": "Sorry, something went wrong with that problem. Please check what you typed and try again."}
    summary = " | ".join(v for v in data.values() if v)[:200]
    db.log_attempt(session["student_id"], topic, sub, input_summary=summary, correct=None)
    return jsonify(res)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
