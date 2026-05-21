from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db
from backend.middleware.auth_middleware import login_required

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/', methods=['GET'])
@login_required
def get_events():
    events = query_db("SELECT * FROM events WHERE family_id = ?", (g.user['family_id'],))
    return jsonify([dict(event) for event in events])

@calendar_bp.route('/', methods=['POST'])
@login_required
def add_event():
    data = request.json
    title = data.get('title')
    start_time = data.get('start_time')
    if not title or not start_time:
        return jsonify({"error": "Title and start time required"}), 400

    event_id = execute_db(
        "INSERT INTO events (family_id, title, description, start_time, end_time, location, color, category, assigned_to_id, created_by_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (g.user['family_id'], title, data.get('description'), start_time, data.get('end_time'),
         data.get('location'), data.get('color'), data.get('category'), data.get('assigned_to_id'), g.user['id'])
    )
    return jsonify({"message": "Event added", "id": event_id}), 201

@calendar_bp.route('/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    # Only creator, parent or admin can delete
    event = query_db("SELECT created_by_id FROM events WHERE id = ? AND family_id = ?", (event_id, g.user['family_id']), one=True)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event['created_by_id'] != g.user['id'] and g.user['role'] not in ('admin', 'parent'):
        return jsonify({"error": "Permission denied"}), 403

    execute_db("DELETE FROM events WHERE id = ?", (event_id,))
    return jsonify({"message": "Event deleted"})
