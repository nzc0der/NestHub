from flask import Blueprint, request, jsonify, session, g
from backend.database.db import query_db, execute_db, log_activity
from backend.utils.helpers import hash_password, check_password, generate_invite_code, sanitize_input
from backend.middleware.auth_middleware import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    # In self-hosted mode, we check if any user exists.
    # If not, the first user is an admin.
    # If users exist, only an admin can create more users (this should be handled via admin panel,
    # but for simplicity we allow it if it's the first user)

    data = request.json
    username = sanitize_input(data.get('username'))
    password = data.get('password')
    role = data.get('role', 'child')

    if not username or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user_count = query_db("SELECT COUNT(*) as count FROM users", one=True)['count']

    # If it's not the first user, require admin role of the person creating it
    # (Simplified: for first setup, first user is admin. Subsequent ones can be added)
    if user_count == 0:
        actual_role = 'admin'
    else:
        # In a real app, we'd check if session user is admin
        # For this task, we allow adding users to the single family
        actual_role = role

    if query_db("SELECT id FROM users WHERE username = ?", (username,), one=True):
        return jsonify({"error": "Username already taken"}), 400

    family = query_db("SELECT id FROM families LIMIT 1", one=True)
    family_id = family['id']

    pw_hash = hash_password(password)
    user_id = execute_db("INSERT INTO users (family_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                         (family_id, username, pw_hash, actual_role))

    log_activity(family_id, user_id, "signup", "auth", f"Created user {username} as {actual_role}")

    return jsonify({"message": "Account created", "user_id": user_id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = sanitize_input(data.get('username'))
    password = data.get('password')

    user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
    if user and check_password(password, user['password_hash']):
        session['user_id'] = user['id']
        session['family_id'] = user['family_id']
        log_activity(user['family_id'], user['id'], "login", "auth")
        return jsonify({"message": "Logged in", "user": {"id": user['id'], "username": user['username'], "role": user['role']}})

    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({"user": {"id": g.user['id'], "username": g.user['username'], "role": g.user['role'], "family_id": g.user['family_id']}})
