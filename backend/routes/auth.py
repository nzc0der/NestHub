from flask import Blueprint, request, jsonify, session, g
from backend.database.db import query_db, execute_db, log_activity
from backend.utils.helpers import hash_password, check_password, generate_invite_code, sanitize_input
from backend.middleware.auth_middleware import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = sanitize_input(data.get('username'))
    password = data.get('password')
    family_name = sanitize_input(data.get('family_name'))

    if not username or not password or not family_name:
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user exists
    if query_db("SELECT id FROM users WHERE username = ?", (username,), one=True):
        return jsonify({"error": "Username already taken"}), 400

    # Create family
    invite_code = generate_invite_code()
    family_id = execute_db("INSERT INTO families (name, invite_code) VALUES (?, ?)", (family_name, invite_code))

    # Create user as admin
    pw_hash = hash_password(password)
    user_id = execute_db("INSERT INTO users (family_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                         (family_id, username, pw_hash, 'admin'))

    log_activity(family_id, user_id, "signup", "auth", f"Created family {family_name}")

    return jsonify({"message": "Account created", "invite_code": invite_code, "user_id": user_id}), 201

@auth_bp.route('/join', methods=['POST'])
def join():
    data = request.json
    username = sanitize_input(data.get('username'))
    password = data.get('password')
    invite_code = sanitize_input(data.get('invite_code'))
    role = data.get('role', 'child') # default to child

    if not username or not password or not invite_code:
        return jsonify({"error": "Missing required fields"}), 400

    family = query_db("SELECT id FROM families WHERE invite_code = ?", (invite_code,), one=True)
    if not family:
        return jsonify({"error": "Invalid invite code"}), 400

    if query_db("SELECT id FROM users WHERE username = ?", (username,), one=True):
        return jsonify({"error": "Username already taken"}), 400

    pw_hash = hash_password(password)
    user_id = execute_db("INSERT INTO users (family_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                         (family['id'], username, pw_hash, role))

    log_activity(family['id'], user_id, "join", "auth", f"Joined family as {role}")

    return jsonify({"message": "Joined family", "user_id": user_id}), 201

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
