import logging, logging.handlers, os, shutil, signal, subprocess, sys, threading, time, markdown
from datetime import datetime
from functools import wraps
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path: sys.path.insert(0, PROJECT_ROOT)
import settings
from flask import (Flask, abort, flash, redirect, render_template, request, session, url_for, jsonify, send_from_directory)

def create_app() -> Flask:
    cfg = settings.load_config()
    app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, "templates"))
    app.secret_key = cfg.get("secret_key", os.urandom(32).hex())
    @app.template_filter('markdown')
    def render_markdown(text):
        if not text: return ""
        return markdown.markdown(text, extensions=['extra', 'nl2br'])
    _register_routes(app)
    return app

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session: return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin": abort(403)
        return f(*args, **kwargs)
    return decorated

def _register_routes(app: Flask) -> None:
    @app.before_request
    def check_ui():
        if "ui_mode" not in session: session.update({"ui_mode": "pc", "ui_mode_selected": False})
    @app.route("/set_ui_mode/<mode>")
    def set_ui_mode(mode):
        if mode in ["pc", "mobile"]: session.update({"ui_mode": mode, "ui_mode_selected": True})
        return redirect(request.referrer or url_for("index"))
    @app.route("/")
    def index(): return redirect(url_for("dashboard"))
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "user_id" in session: return redirect(url_for("dashboard"))
        if request.method == "POST":
            u, p = request.form.get("username", "").strip().lower(), request.form.get("password", "")
            if u == "guest":
                guest = settings.get_user_by_username("guest")
                if guest:
                    session.update({"user_id": guest["id"], "username": "guest", "role": "guest", "shopping_permission": "read"})
                    return redirect(url_for("dashboard"))
            user = settings.verify_user(u, p)
            if user:
                session.update({"user_id": user["id"], "username": user["username"], "role": user["role"], "shopping_permission": user["shopping_permission"]})
                return redirect(url_for("dashboard"))
            flash("Invalid credentials.", "danger")
        return render_template("login.html", users=[u for u in settings.get_users() if u["username"] != "guest"])
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))
    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html", todos=settings.get_todos(session["user_id"]), notes=settings.get_notes(), announcements=settings.get_announcements()[:3], bookmarks=settings.get_bookmarks(), events=settings.get_events(), all_users=settings.get_users(), meal_plan=settings.get_meal_plan(), weather_cfg=settings.get_weather_config(), now=datetime.now())
    @app.route("/todos/add", methods=["POST"])
    @login_required
    def todo_add():
        c = request.form.get("content", "").strip()
        if c: settings.add_todo(session["user_id"], c)
        return redirect(url_for("dashboard"))
    @app.route("/todos/toggle/<int:id>", methods=["POST"])
    @login_required
    def todo_toggle(id):
        settings.toggle_todo(id, session["user_id"])
        return redirect(url_for("dashboard"))
    @app.route("/todos/clear_completed", methods=["POST"])
    @login_required
    def todo_clear_completed():
        for t in settings.get_todos(session["user_id"]):
            if t["done"]: settings.delete_todo(t["id"], session["user_id"])
        return redirect(url_for("dashboard"))
    @app.route("/notes/save", methods=["POST"])
    @login_required
    def note_save():
        nid = request.form.get("note_id")
        settings.upsert_note(session["user_id"], int(nid) if nid and nid.isdigit() else None, request.form.get("title", "").strip(), request.form.get("content", "").strip(), session.get("role") == "admin")
        return redirect(url_for("notes_list"))
    @app.route("/notes")
    @login_required
    def notes_list(): return render_template("notes.html", notes=settings.get_notes())
    @app.route("/profile/status", methods=["POST"])
    @login_required
    def update_status():
        s = request.form.get("status", "Available").strip()
        if s: settings.update_user_status(session["user_id"], s)
        return redirect(request.referrer or url_for("dashboard"))

if __name__ == "__main__":
    if not settings.is_initialized():
        subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, "setup.py")])
        sys.exit(0)
    settings.init_schema()
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
