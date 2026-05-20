"""
settings.py - Central configuration and utility module.

This module is a pure library. It does NOT start a server, run interactive
prompts, or perform any I/O side-effects at import time. All functions are
safe to call from any context.

Responsibilities:
  - Loading / saving / resetting config.json.
  - SQLite user management (get, add, verify).
  - System-level helpers (is_initialized, path resolution).
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Optional

import bcrypt

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

PROJECT_ROOT: str = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH: str = os.path.join(PROJECT_ROOT, "config.json")

_DEFAULT_DB_PATH: str = os.path.join(PROJECT_ROOT, "data", "family.db")
_DEFAULT_BACKUP_DIR: str = os.path.join(PROJECT_ROOT, "backups")
_DEFAULT_PORT: int = 8000
_DEFAULT_LATITUDE: float = -37.9034
_DEFAULT_LONGITUDE: float = 145.0416
_DEFAULT_CITY: str = "Ormond"

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def load_config() -> dict:
    if not os.path.isfile(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"config.json is malformed: {exc}") from exc


def save_config(data: dict) -> None:
    tmp_path = CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, CONFIG_PATH)
        logger.debug("config.json saved successfully.")
    except OSError as exc:
        logger.error("Failed to save config.json: %s", exc)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def reset_config() -> None:
    if os.path.isfile(CONFIG_PATH):
        os.remove(CONFIG_PATH)
        logger.warning("config.json removed. System will reinitialize on next start.")


def is_initialized() -> bool:
    try:
        cfg = load_config()
        return bool(cfg)
    except ValueError:
        return False


def _db_path() -> str:
    cfg = load_config()
    return cfg.get("db_path", _DEFAULT_DB_PATH)


def _backup_dir() -> str:
    cfg = load_config()
    return cfg.get("backup_dir", _DEFAULT_BACKUP_DIR)


def get_server_port() -> int:
    cfg = load_config()
    return cfg.get("port", _DEFAULT_PORT)


def get_weather_config() -> dict:
    cfg = load_config()
    return {
        "lat": cfg.get("latitude", _DEFAULT_LATITUDE),
        "lon": cfg.get("longitude", _DEFAULT_LONGITUDE),
        "city": cfg.get("city", _DEFAULT_CITY)
    }


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@contextmanager
def _get_db():
    db_path = _db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    with _get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                password_hash TEXT,
                role        TEXT    NOT NULL DEFAULT 'user',
                shopping_permission TEXT NOT NULL DEFAULT 'full',
                status      TEXT    NOT NULL DEFAULT 'Available',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS todos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content     TEXT    NOT NULL,
                done        INTEGER NOT NULL DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title       TEXT    NOT NULL DEFAULT '',
                content     TEXT    NOT NULL DEFAULT '',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS announcements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
                title       TEXT    NOT NULL,
                body        TEXT    NOT NULL DEFAULT '',
                pinned      INTEGER NOT NULL DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bookmarks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                url         TEXT    NOT NULL,
                icon        TEXT    DEFAULT '🌐',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                event_date  DATETIME NOT NULL,
                end_date    DATETIME,
                author_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS shopping_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name   TEXT    NOT NULL,
                added_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS meal_plan (
                day         TEXT PRIMARY KEY,
                meal        TEXT NOT NULL DEFAULT ''
            );
            """
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'Available';")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN shopping_permission TEXT DEFAULT 'full';")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE events ADD COLUMN end_date DATETIME;")
        except sqlite3.OperationalError:
            pass
    logger.info("Database schema verified / created.")


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


def get_users() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, password_hash, role, shopping_permission, status, created_at FROM users ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_user_by_username(username: str) -> Optional[dict]:
    with _get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, shopping_permission, status, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    with _get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, shopping_permission, status, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def add_user(username: str, password: Optional[str], role: str = "user", shopping_permission: str = "full") -> int:
    if get_user_by_username(username) is not None:
        raise ValueError(f"Username '{username}' already exists.")
    password_hash = None
    if password is not None:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    with _get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, role, shopping_permission) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, shopping_permission),
        )
        return cursor.lastrowid


def verify_user(username: str, password: str) -> Optional[dict]:
    user = get_user_by_username(username)
    if not user or not user["password_hash"]:
        return None
    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return user
    return None


def change_password(user_id: int, new_password: str) -> None:
    password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    with _get_db() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def update_user_status(user_id: int, status: str) -> None:
    with _get_db() as conn:
        conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))


def set_shopping_permission(user_id: int, permission: str) -> None:
    with _get_db() as conn:
        conn.execute("UPDATE users SET shopping_permission = ? WHERE id = ?", (permission, user_id))


def delete_user(user_id: int) -> None:
    with _get_db() as conn:
        user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user["role"] == "admin":
            admin_count = conn.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'").fetchone()
            if admin_count["count"] <= 1:
                raise ValueError("Cannot delete the last admin account.")
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------

def get_todos(user_id: int) -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE user_id = ? ORDER BY done ASC, created_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]

def add_todo(user_id: int, content: str) -> int:
    with _get_db() as conn:
        cur = conn.execute("INSERT INTO todos (user_id, content) VALUES (?, ?)", (user_id, content.strip()))
        return cur.lastrowid

def toggle_todo(todo_id: int, user_id: int) -> None:
    with _get_db() as conn:
        conn.execute(
            "UPDATE todos SET done = CASE WHEN done = 0 THEN 1 ELSE 0 END, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (todo_id, user_id)
        )

def delete_todo(todo_id: int, user_id: int) -> None:
    with _get_db() as conn:
        conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id))

def get_notes() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT n.*, u.username as author FROM notes n JOIN users u ON u.id = n.user_id ORDER BY n.updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]

def upsert_note(user_id: int, note_id: Optional[int], title: str, content: str, is_admin: bool = False) -> int:
    with _get_db() as conn:
        if note_id is None:
            cur = conn.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (user_id, title.strip(), content.strip()))
            return cur.lastrowid
        else:
            if is_admin:
                conn.execute("UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (title.strip(), content.strip(), note_id))
            else:
                conn.execute("UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?", (title.strip(), content.strip(), note_id, user_id))
            return note_id

def delete_note(note_id: int, user_id: int, is_admin: bool = False) -> None:
    with _get_db() as conn:
        if is_admin:
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        else:
            conn.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))

def get_announcements() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT a.*, u.username as author FROM announcements a LEFT JOIN users u ON u.id = a.author_id ORDER BY a.pinned DESC, a.created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]

def add_announcement(author_id: int, title: str, body: str, pinned: bool = False) -> int:
    with _get_db() as conn:
        cur = conn.execute("INSERT INTO announcements (author_id, title, body, pinned) VALUES (?, ?, ?, ?)", (author_id, title.strip(), body.strip(), int(pinned)))
        return cur.lastrowid

def delete_announcement(ann_id: int) -> None:
    with _get_db() as conn:
        conn.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))

def toggle_pin(ann_id: int) -> None:
    with _get_db() as conn:
        conn.execute("UPDATE announcements SET pinned = CASE WHEN pinned=0 THEN 1 ELSE 0 END WHERE id = ?", (ann_id,))

def get_bookmarks() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute("SELECT * FROM bookmarks ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

def add_bookmark(title: str, url: str, icon: str = "🌐") -> int:
    with _get_db() as conn:
        cur = conn.execute("INSERT INTO bookmarks (title, url, icon) VALUES (?, ?, ?)", (title.strip(), url.strip(), icon.strip() or "🌐"))
        return cur.lastrowid

def delete_bookmark(bm_id: int) -> None:
    with _get_db() as conn:
        conn.execute("DELETE FROM bookmarks WHERE id = ?", (bm_id,))

def get_events() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute("SELECT e.*, u.username as author FROM events e LEFT JOIN users u ON u.id = e.author_id WHERE e.event_date >= date('now', '-1 day') ORDER BY e.event_date ASC").fetchall()
    return [dict(r) for r in rows]

def get_all_events() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute("SELECT e.*, u.username as author FROM events e LEFT JOIN users u ON u.id = e.author_id ORDER BY e.event_date ASC").fetchall()
    return [dict(r) for r in rows]

def get_event(event_id: int) -> dict | None:
    with _get_db() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return dict(row) if row else None

def add_event(author_id: int, title: str, event_date: str, end_date: str = None) -> int:
    with _get_db() as conn:
        cur = conn.execute("INSERT INTO events (author_id, title, event_date, end_date) VALUES (?, ?, ?, ?)", (author_id, title.strip(), event_date.strip(), end_date.strip() if end_date else None))
        return cur.lastrowid

def delete_event(event_id: int) -> None:
    with _get_db() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

def get_shopping_items() -> list[dict]:
    with _get_db() as conn:
        rows = conn.execute("SELECT s.id, s.item_name as content, s.created_at, u.username as author FROM shopping_items s LEFT JOIN users u ON u.id = s.added_by ORDER BY s.created_at DESC").fetchall()
    return [dict(r) for r in rows]

def get_shopping_item(item_id: int) -> dict | None:
    with _get_db() as conn:
        row = conn.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None

def add_shopping_item(item_name: str, added_by: int) -> int:
    with _get_db() as conn:
        cur = conn.execute("INSERT INTO shopping_items (item_name, added_by) VALUES (?, ?)", (item_name.strip(), added_by))
        return cur.lastrowid

def delete_shopping_item(item_id: int) -> None:
    with _get_db() as conn:
        conn.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))

def get_meal_plan() -> dict:
    with _get_db() as conn:
        rows = conn.execute("SELECT day, meal FROM meal_plan").fetchall()
    return {r["day"]: r["meal"] for r in rows}

def update_meal_plan(day: str, meal: str) -> None:
    with _get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO meal_plan (day, meal) VALUES (?, ?)", (day, meal.strip()))
