import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Two modes:
#   - DATABASE_URL is set (production, e.g. a free Neon/Supabase Postgres
#     connection string) -> uses Postgres. Data persists permanently,
#     independent of Render's filesystem, so it survives every redeploy
#     and restart.
#   - DATABASE_URL is NOT set (local development) -> falls back to a local
#     SQLite file, same as before. Fine for testing on your own computer,
#     but NOT persistent on most free hosting tiers.
#
# Everywhere else in the app (app.py) just calls db.get_db(), then uses
# conn.execute(sql, params).fetchone()/.fetchall() and conn.commit() —
# exactly like before. The wrapper below makes Postgres behave the same
# way, so nothing else in the project needs to change.
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    class _PgCursorResult:
        """Wraps a psycopg2 cursor so .fetchone()/.fetchall() behave the
        same as sqlite3's, returning dict-like rows either way."""
        def __init__(self, cursor):
            self._cursor = cursor

        def fetchone(self):
            return self._cursor.fetchone()

        def fetchall(self):
            return self._cursor.fetchall()

    class _PgConnWrapper:
        """Wraps a psycopg2 connection so conn.execute(sql, params) works
        the same way sqlite3.Connection.execute(...) does."""
        def __init__(self, conn):
            self._conn = conn

        def execute(self, query, params=()):
            # sqlite3-style "?" placeholders -> psycopg2-style "%s"
            pg_query = query.replace("?", "%s")
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(pg_query, params)
            return _PgCursorResult(cur)

        def cursor(self):
            return self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        def commit(self):
            self._conn.commit()

        def close(self):
            self._conn.close()

    def get_db():
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return _PgConnWrapper(conn)

    def init_db():
        conn = get_db()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # One row per solver use. correct is 1/0/NULL (NULL = not a graded exercise, e.g. a plot).
        c.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students (id) ON DELETE CASCADE,
                topic TEXT NOT NULL,
                subtopic TEXT NOT NULL,
                input_summary TEXT,
                correct INTEGER,
                created_at TEXT NOT NULL
            )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_attempts_created ON attempts(created_at)")

        conn.commit()
        conn.close()

else:
    import sqlite3

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
