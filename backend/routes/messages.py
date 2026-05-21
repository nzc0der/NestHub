from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db
from backend.middleware.auth_middleware import login_required

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/', methods=['GET'])
@login_required
def get_messages():
    messages = query_db("""
        SELECT m.*, u.username as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.family_id = ?
        ORDER BY m.created_at ASC
    """, (g.user['family_id'],))
    return jsonify([dict(msg) for msg in messages])

@messages_bp.route('/', methods=['POST'])
@login_required
def send_message():
    data = request.json
    content = data.get('content')
    if not content:
        return jsonify({"error": "Content required"}), 400

    msg_id = execute_db(
        "INSERT INTO messages (family_id, sender_id, content, attachment_url) VALUES (?, ?, ?, ?)",
        (g.user['family_id'], g.user['id'], content, data.get('attachment_url'))
    )
    return jsonify({"message": "Message sent", "id": msg_id}), 201
