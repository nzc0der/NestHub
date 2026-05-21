from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db, log_activity
from backend.middleware.auth_middleware import login_required, parent_or_admin

chores_bp = Blueprint('chores', __name__)

@chores_bp.route('/', methods=['GET'])
@login_required
def get_chores():
    chores = query_db("SELECT * FROM chores WHERE family_id = ?", (g.user['family_id'],))
    return jsonify([dict(chore) for chore in chores])

@chores_bp.route('/', methods=['POST'])
@login_required
def add_chore():
    data = request.json
    title = data.get('title')
    if not title:
        return jsonify({"error": "Title required"}), 400

    chore_id = execute_db(
        "INSERT INTO chores (family_id, title, description, assigned_to_id, points, due_date, priority, created_by_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (g.user['family_id'], title, data.get('description'), data.get('assigned_to_id'),
         data.get('points', 0), data.get('due_date'), data.get('priority', 'medium'), g.user['id'])
    )
    log_activity(g.user['family_id'], g.user['id'], "add_chore", "chores", f"Added chore: {title}")
    return jsonify({"message": "Chore added", "id": chore_id}), 201

@chores_bp.route('/<int:chore_id>/status', methods=['PUT'])
@login_required
def update_chore_status(chore_id):
    data = request.json
    new_status = data.get('status')
    if new_status not in ('pending', 'in_progress', 'completed', 'approved'):
        return jsonify({"error": "Invalid status"}), 400

    # Security: ensure chore belongs to family
    chore = query_db("SELECT * FROM chores WHERE id = ? AND family_id = ?", (chore_id, g.user['family_id']), one=True)
    if not chore:
        return jsonify({"error": "Chore not found"}), 404

    # Logic for approval
    if new_status == 'approved' and g.user['role'] not in ('admin', 'parent'):
        return jsonify({"error": "Approval required by parent or admin"}), 403

    execute_db("UPDATE chores SET status = ?, approved_by_id = ? WHERE id = ?",
               (new_status, g.user['id'] if new_status == 'approved' else None, chore_id))
    log_activity(g.user['family_id'], g.user['id'], "update_chore", "chores", f"Chore {chore_id} status to {new_status}")
    return jsonify({"message": "Status updated"})

@chores_bp.route('/<int:chore_id>', methods=['DELETE'])
@login_required
@parent_or_admin
def delete_chore(chore_id):
    execute_db("DELETE FROM chores WHERE id = ? AND family_id = ?", (chore_id, g.user['family_id']))
    return jsonify({"message": "Chore deleted"})
