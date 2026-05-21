import os
import psutil
import platform
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db
from backend.middleware.auth_middleware import login_required, admin_only

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/logs', methods=['GET'])
@login_required
@admin_only
def get_logs():
    logs = query_db("SELECT * FROM activity_logs WHERE family_id = ? ORDER BY timestamp DESC", (g.user['family_id'],))
    return jsonify([dict(log) for log in logs])

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_only
def get_users():
    users = query_db("SELECT id, username, role, first_name, last_name, avatar_url FROM users WHERE family_id = ?", (g.user['family_id'],))
    return jsonify([dict(user) for user in users])

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@login_required
@admin_only
def update_user_role(user_id):
    data = request.json
    new_role = data.get('role')
    if new_role not in ('admin', 'parent', 'child', 'guest'):
        return jsonify({"error": "Invalid role"}), 400

    execute_db("UPDATE users SET role = ? WHERE id = ? AND family_id = ?", (new_role, user_id, g.user['family_id']))
    return jsonify({"message": "Role updated"})

@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_only
def get_stats():
    # Simple stats for now
    user_count = query_db("SELECT COUNT(*) as count FROM users WHERE family_id = ?", (g.user['family_id'],), one=True)['count']
    chore_count = query_db("SELECT COUNT(*) as count FROM chores WHERE family_id = ?", (g.user['family_id'],), one=True)['count']
    grocery_count = query_db("SELECT COUNT(*) as count FROM grocery_items WHERE family_id = ? AND status='active'", (g.user['family_id'],), one=True)['count']

    return jsonify({
        "user_count": user_count,
        "chore_count": chore_count,
        "grocery_count": grocery_count
    })

@admin_bp.route('/diagnostics', methods=['GET'])
@login_required
@admin_only
def get_diagnostics():
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return jsonify({
        "os": platform.system(),
        "os_release": platform.release(),
        "cpu_usage": f"{cpu_usage}%",
        "memory_used": f"{memory.percent}%",
        "memory_total": f"{memory.total // (1024*1024)} MB",
        "disk_free": f"{disk.free // (1024*1024*1024)} GB",
        "uptime": f"{datetime.now().isoformat()}", # simplified
        "python_version": platform.python_version()
    })
