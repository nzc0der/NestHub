import sqlite3
import os
from flask import g

DB_PATH = os.environ.get('DATABASE_URL', 'data/nestboard.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db(app):
    if not os.path.exists('data'):
        os.makedirs('data')

    with app.app_context():
        db = get_db()
        with app.open_resource('database/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())

        # Ensure a default family exists for self-hosted single-family use
        existing_family = db.execute("SELECT id FROM families LIMIT 1").fetchone()
        if not existing_family:
            db.execute("INSERT INTO families (name, invite_code) VALUES (?, ?)", ('Our Home', 'SELF_HOSTED'))

        # Ensure 'purchased' is not used anymore, instead use 'archived' if we want to hide it
        # Or just keep it as is.

        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

def log_activity(family_id, user_id, action, category=None, details=None):
    execute_db(
        "INSERT INTO activity_logs (family_id, user_id, action, category, details) VALUES (?, ?, ?, ?, ?)",
        (family_id, user_id, action, category, details)
    )
