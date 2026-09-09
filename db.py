import sqlite3
import os
from datetime import datetime

# In production (Render, etc.), set DATABASE_PATH to a file on a persistent
# disk — e.g. "/var/data/maths_assist.db" — so student accounts and progress
# survive redeploys and restarts. Without it, this falls back to a file next
# to this script, which is fine for local development but NOT persistent on
# most free hosting tiers (their filesystem resets on every restart).
DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "maths_assist.db"),
)


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            class_name TEXT,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # One row per solver use. correct is 1/0/NULL (NULL = not a graded exercise, e.g. a plot).
    c.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            subtopic TEXT NOT NULL,
            input_summary TEXT,
            correct INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_attempts_created ON attempts(created_at)")

    conn.commit()
    conn.close()


def now_iso():
    return datetime.utcnow().isoformat()


def log_attempt(student_id, topic, subtopic, input_summary=None, correct=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO attempts (student_id, topic, subtopic, input_summary, correct, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, topic, subtopic, input_summary, correct, now_iso()),
    )
    conn.commit()
    conn.close()
