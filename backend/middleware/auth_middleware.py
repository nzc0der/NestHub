from functools import wraps
from flask import request, jsonify, g, session
from backend.database.db import query_db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.user = user
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user:
                 return jsonify({"error": "Authentication required"}), 401
            if g.user['role'] not in roles:
                return jsonify({"error": "Permission denied"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def admin_only(f):
    return roles_required('admin')(f)

def parent_or_admin(f):
    return roles_required('admin', 'parent')(f)
