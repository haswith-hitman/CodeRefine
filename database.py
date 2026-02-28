"""
CodeRefine — Database Module
SQLite-backed user auth, review history, snippets, and statistics.
"""

import sqlite3
import hashlib
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coderefine.db")

COMPLEXITY_SCORE_MAP = {
    "O(1)":       100,
    "O(log n)":   88,
    "O(n)":       72,
    "O(n log n)": 58,
    "O(n²)":      35,
    "O(n³)":      18,
    "O(2^n)":     8,
    "O(n!)":      2,
}

def complexity_to_score(notation: str) -> int:
    if not notation:
        return 50
    notation = notation.strip()
    if notation in COMPLEXITY_SCORE_MAP:
        return COMPLEXITY_SCORE_MAP[notation]
    for key, val in COMPLEXITY_SCORE_MAP.items():
        if key.lower() in notation.lower():
            return val
    return 50


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            theme         TEXT DEFAULT 'dark',
            accent_color  TEXT DEFAULT 'indigo',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                 INTEGER NOT NULL,
            language                TEXT NOT NULL,
            original_code           TEXT NOT NULL,
            review_json             TEXT,
            rewritten_code          TEXT,
            bugs_count              INTEGER DEFAULT 0,
            perf_score              INTEGER DEFAULT 0,
            security_count          INTEGER DEFAULT 0,
            complexity              INTEGER DEFAULT 0,
            confidence              INTEGER DEFAULT 0,
            orig_time_complexity    TEXT    DEFAULT '',
            rw_time_complexity      TEXT    DEFAULT '',
            orig_complexity_score   INTEGER DEFAULT 50,
            rw_complexity_score     INTEGER DEFAULT 50,
            orig_space_complexity   TEXT    DEFAULT '',
            rw_space_complexity     TEXT    DEFAULT '',
            created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            language    TEXT NOT NULL,
            code        TEXT NOT NULL,
            tags        TEXT DEFAULT '[]',
            is_favorite INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS challenge_attempts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            challenge_key TEXT NOT NULL,
            language      TEXT NOT NULL,
            user_code     TEXT NOT NULL,
            score         INTEGER DEFAULT 0,
            passed        INTEGER DEFAULT 0,
            feedback      TEXT DEFAULT '',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Migrate existing DBs
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(reviews)").fetchall()}
    review_migrations = {
        "orig_time_complexity":   "TEXT DEFAULT ''",
        "rw_time_complexity":     "TEXT DEFAULT ''",
        "orig_complexity_score":  "INTEGER DEFAULT 50",
        "rw_complexity_score":    "INTEGER DEFAULT 50",
        "orig_space_complexity":  "TEXT DEFAULT ''",
        "rw_space_complexity":    "TEXT DEFAULT ''",
    }
    for col, definition in review_migrations.items():
        if col not in existing_cols:
            c.execute(f"ALTER TABLE reviews ADD COLUMN {col} {definition}")

    user_cols = {row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()}
    user_migrations = {
        "theme": "TEXT DEFAULT 'dark'",
        "accent_color": "TEXT DEFAULT 'indigo'",
    }
    for col, definition in user_migrations.items():
        if col not in user_cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")

    conn.commit()
    conn.close()


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def create_user(username: str, email: str, password: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, hash_password(password))
        )
        conn.commit()
        return True, "Account created!"
    except sqlite3.IntegrityError as e:
        msg = "Username already taken." if "username" in str(e) else "Email already registered."
        return False, msg
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, email, theme, accent_color, created_at FROM users "
            "WHERE username=? AND password_hash=?",
            (username, hash_password(password))
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user_settings(user_id: int, theme: str, accent_color: str):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET theme=?, accent_color=? WHERE id=?",
            (theme, accent_color, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def save_review(
    user_id, language, original_code, review_json,
    rewritten_code="", bugs=0, perf=0, sec=0, complexity=0, confidence=0,
    orig_time_complexity="", rw_time_complexity="",
    orig_complexity_score=50, rw_complexity_score=50,
    orig_space_complexity="", rw_space_complexity="",
):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO reviews
              (user_id, language, original_code, review_json, rewritten_code,
               bugs_count, perf_score, security_count, complexity, confidence,
               orig_time_complexity, rw_time_complexity,
               orig_complexity_score, rw_complexity_score,
               orig_space_complexity, rw_space_complexity)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id, language, original_code[:800], review_json,
            rewritten_code[:3000], bugs, perf, sec, complexity, confidence,
            orig_time_complexity, rw_time_complexity,
            orig_complexity_score, rw_complexity_score,
            orig_space_complexity, rw_space_complexity,
        ))
        conn.commit()
    finally:
        conn.close()


# ── Snippets ──────────────────────────────────────────────────────────────────

def save_snippet(user_id: int, title: str, description: str, language: str, code: str, tags: list) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO snippets (user_id, title, description, language, code, tags) VALUES (?,?,?,?,?,?)",
            (user_id, title, description, language, code, json.dumps(tags))
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_snippets(user_id: int, search: str = "", language: str = "") -> list:
    conn = get_connection()
    try:
        query = "SELECT * FROM snippets WHERE user_id=?"
        params = [user_id]
        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR code LIKE ?)"
            params += [f"%{search}%", f"%{search}%", f"%{search}%"]
        if language:
            query += " AND language=?"
            params.append(language)
        query += " ORDER BY is_favorite DESC, updated_at DESC"
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["tags"] = json.loads(d.get("tags", "[]"))
            except Exception:
                d["tags"] = []
            result.append(d)
        return result
    finally:
        conn.close()


def get_snippet(snippet_id: int, user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snippets WHERE id=? AND user_id=?",
            (snippet_id, user_id)
        ).fetchone()
        if row:
            d = dict(row)
            try:
                d["tags"] = json.loads(d.get("tags", "[]"))
            except Exception:
                d["tags"] = []
            return d
        return None
    finally:
        conn.close()


def update_snippet(snippet_id: int, user_id: int, title: str, description: str, language: str, code: str, tags: list):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE snippets SET title=?, description=?, language=?, code=?, tags=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
            (title, description, language, code, json.dumps(tags), snippet_id, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def toggle_snippet_favorite(snippet_id: int, user_id: int):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE snippets SET is_favorite = 1 - is_favorite WHERE id=? AND user_id=?",
            (snippet_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_snippet(snippet_id: int, user_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM snippets WHERE id=? AND user_id=?", (snippet_id, user_id))
        conn.commit()
    finally:
        conn.close()


# ── Challenges ────────────────────────────────────────────────────────────────

def save_challenge_attempt(user_id: int, challenge_key: str, language: str, user_code: str, score: int, passed: bool, feedback: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO challenge_attempts (user_id, challenge_key, language, user_code, score, passed, feedback) VALUES (?,?,?,?,?,?,?)",
            (user_id, challenge_key, language, user_code, score, int(passed), feedback)
        )
        conn.commit()
    finally:
        conn.close()


def get_challenge_stats(user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT COUNT(*) as total_attempts,
                   SUM(passed) as total_passed,
                   COALESCE(AVG(score), 0) as avg_score,
                   MAX(score) as best_score
            FROM challenge_attempts WHERE user_id=?
        """, (user_id,)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_user_history(user_id, limit=8):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT language, original_code, bugs_count, perf_score,
                   security_count, complexity, confidence,
                   orig_time_complexity, rw_time_complexity,
                   orig_complexity_score, rw_complexity_score,
                   orig_space_complexity, rw_space_complexity,
                   created_at
            FROM reviews WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_user_stats(user_id):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*)                          AS total_reviews,
                COALESCE(SUM(bugs_count),0)       AS total_bugs,
                COALESCE(SUM(security_count),0)   AS total_security,
                COALESCE(AVG(perf_score),0)       AS avg_perf,
                COALESCE(AVG(complexity),0)       AS avg_complexity,
                COALESCE(AVG(confidence),0)       AS avg_confidence,
                COALESCE(AVG(orig_complexity_score),50) AS avg_orig_tc_score,
                COALESCE(AVG(rw_complexity_score),50)   AS avg_rw_tc_score
            FROM reviews WHERE user_id=?
        """, (user_id,)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_language_breakdown(user_id):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT language, COUNT(*) as cnt
            FROM reviews WHERE user_id=?
            GROUP BY language ORDER BY cnt DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent_trend(user_id, limit=15):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT
                perf_score, bugs_count, complexity,
                orig_time_complexity, rw_time_complexity,
                orig_complexity_score, rw_complexity_score,
                orig_space_complexity, rw_space_complexity,
                created_at
            FROM reviews WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


init_db()
