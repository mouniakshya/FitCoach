import sqlite3
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

_DB_PATH = str(Path(__file__).parent.parent.parent / "data.db")


@st.cache_resource
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exercises (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT    NOT NULL,
                reps          INTEGER NOT NULL DEFAULT 0,
                sets          INTEGER NOT NULL DEFAULT 0,
                time          INTEGER NOT NULL DEFAULT 0,
                calories      REAL    NOT NULL DEFAULT 0.0,
                form_score    REAL    NOT NULL DEFAULT 100.0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id           INTEGER PRIMARY KEY REFERENCES users(id),
                weight_kg         REAL    DEFAULT 70.0,
                daily_goal_reps   INTEGER DEFAULT 50,
                coach_personality TEXT    DEFAULT 'Motivational',
                voice_enabled     INTEGER DEFAULT 1
            )
            """
        )

        # Migration helper for existing databases missing new columns
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(exercises)")
        exercise_cols = [row["name"] for row in cursor.fetchall()]

        if "calories" not in exercise_cols:
            cursor.execute("ALTER TABLE exercises ADD COLUMN calories REAL DEFAULT 0.0")
        if "form_score" not in exercise_cols:
            cursor.execute("ALTER TABLE exercises ADD COLUMN form_score REAL DEFAULT 100.0")


def get_user(username: str) -> sqlite3.Row:
    conn = _get_connection()
    return conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()


def create_user(username: str) -> sqlite3.Row:
    conn = _get_connection()
    with conn:
        conn.execute(
            "INSERT INTO users (username) VALUES (?)", (username,)
        )
        user = get_user(username)
        if user:
            conn.execute(
                """
                INSERT OR IGNORE INTO user_profiles (user_id, weight_kg, daily_goal_reps, coach_personality, voice_enabled)
                VALUES (?, 70.0, 50, 'Motivational', 1)
                """,
                (user["id"],)
            )
    return user


def get_or_create_user(username: str) -> sqlite3.Row:
    user = get_user(username)
    if user is None:
        user = create_user(username)
    else:
        # Ensure profile exists
        conn = _get_connection()
        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO user_profiles (user_id, weight_kg, daily_goal_reps, coach_personality, voice_enabled)
                VALUES (?, 70.0, 50, 'Motivational', 1)
                """,
                (user["id"],)
            )
    return user


def get_user_profile(user_id: int) -> dict:
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()

    if row:
        return {
            "weight_kg": float(row["weight_kg"]),
            "daily_goal_reps": int(row["daily_goal_reps"]),
            "coach_personality": str(row["coach_personality"]),
            "voice_enabled": bool(row["voice_enabled"])
        }
    return {
        "weight_kg": 70.0,
        "daily_goal_reps": 50,
        "coach_personality": "Motivational",
        "voice_enabled": True
    }


def save_user_profile(user_id: int, weight_kg: float, daily_goal_reps: int, coach_personality: str, voice_enabled: bool) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO user_profiles (user_id, weight_kg, daily_goal_reps, coach_personality, voice_enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                weight_kg = excluded.weight_kg,
                daily_goal_reps = excluded.daily_goal_reps,
                coach_personality = excluded.coach_personality,
                voice_enabled = excluded.voice_enabled
            """,
            (user_id, weight_kg, daily_goal_reps, coach_personality, 1 if voice_enabled else 0)
        )


def add_exercise(user_id, exercise_name, reps, sets, time_taken, calories=0.0, form_score=100.0):
    conn = _get_connection()

    with conn:
        existing = conn.execute("""
            SELECT * FROM exercises 
            WHERE user_id = ? AND exercise_name = ? AND Date(created_at) = Date('now')
        """, (user_id, exercise_name)).fetchone()

        if existing:
            # Weighted average for form score
            existing_reps = existing["reps"]
            total_reps = existing_reps + reps
            combined_score = round(
                ((existing["form_score"] * existing_reps) + (form_score * reps)) / max(1, total_reps),
                1
            )
            conn.execute("""
                UPDATE exercises 
                SET reps = reps + ?, sets = sets + ?, time = time + ?, calories = calories + ?, form_score = ?
                WHERE id = ?
            """, (reps, sets, int(time_taken), round(float(calories), 2), combined_score, existing['id']))
        else:
            conn.execute("""
                INSERT INTO exercises (user_id, exercise_name, sets, reps, time, calories, form_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, exercise_name, sets, reps, int(time_taken), round(float(calories), 2), round(float(form_score), 1)))


def get_users_exercises(user_id):
    conn = _get_connection()
    return conn.execute("""
        SELECT * FROM exercises 
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()


def get_user_stats(user_id: int) -> dict:
    conn = _get_connection()
    rows = conn.execute("""
        SELECT 
            COUNT(*) as session_count,
            COALESCE(SUM(reps), 0) as total_reps,
            COALESCE(SUM(sets), 0) as total_sets,
            COALESCE(SUM(time), 0) as total_time,
            COALESCE(SUM(calories), 0.0) as total_calories,
            COALESCE(AVG(form_score), 100.0) as avg_form_score
        FROM exercises
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    # Calculate streak (consecutive active days)
    date_rows = conn.execute("""
        SELECT DISTINCT Date(created_at) as workout_date
        FROM exercises
        WHERE user_id = ?
        ORDER BY workout_date DESC
    """, (user_id,)).fetchall()

    streak = 0
    if date_rows:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        dates = [datetime.strptime(r["workout_date"], "%Y-%m-%d").date() for r in date_rows]

        # Check if active today or yesterday
        if dates[0] == today or dates[0] == yesterday:
            expected = dates[0]
            for d in dates:
                if d == expected:
                    streak += 1
                    expected -= timedelta(days=1)
                else:
                    break

    # Today's reps
    today_row = conn.execute("""
        SELECT COALESCE(SUM(reps), 0) as today_reps
        FROM exercises
        WHERE user_id = ? AND Date(created_at) = Date('now')
    """, (user_id,)).fetchone()

    return {
        "session_count": rows["session_count"] if rows else 0,
        "total_reps": int(rows["total_reps"]) if rows else 0,
        "total_sets": int(rows["total_sets"]) if rows else 0,
        "total_time": int(rows["total_time"]) if rows else 0,
        "total_calories": round(float(rows["total_calories"]), 1) if rows else 0.0,
        "avg_form_score": round(float(rows["avg_form_score"]), 1) if rows else 100.0,
        "streak_days": streak,
        "today_reps": int(today_row["today_reps"]) if today_row else 0
    }


def get_user_personal_records(user_id: int) -> list:
    conn = _get_connection()
    rows = conn.execute("""
        SELECT 
            exercise_name,
            MAX(reps) as max_reps,
            MAX(sets) as max_sets,
            MAX(time) as max_duration,
            MAX(calories) as max_calories
        FROM exercises
        WHERE user_id = ?
        GROUP BY exercise_name
        ORDER BY max_reps DESC
    """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


def delete_user_history(user_id: int) -> None:
    conn = _get_connection()
    with conn:
        conn.execute("DELETE FROM exercises WHERE user_id = ?", (user_id,))
