from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db
from backend.middleware.auth_middleware import login_required, parent_or_admin
from datetime import datetime

extra_bp = Blueprint('extra', __name__)

# --- Photo Gallery ---

@extra_bp.route('/photos', methods=['GET'])
@login_required
def get_photos():
    # Only show approved photos, or all if parent/admin
    if g.user['role'] in ('admin', 'parent'):
        photos = query_db("SELECT * FROM photos WHERE family_id = ? ORDER BY uploaded_at DESC", (g.user['family_id'],))
    else:
        photos = query_db("SELECT * FROM photos WHERE family_id = ? AND status = 'approved' ORDER BY uploaded_at DESC", (g.user['family_id'],))
    return jsonify([dict(photo) for photo in photos])

@extra_bp.route('/photos', methods=['POST'])
@login_required
def upload_photo():
    data = request.json
    image_url = data.get('image_url')
    if not image_url:
        return jsonify({"error": "Image URL required"}), 400

    # Child uploads start as pending
    status = 'approved' if g.user['role'] in ('admin', 'parent') else 'pending'

    photo_id = execute_db(
        "INSERT INTO photos (family_id, title, image_url, uploaded_by, status) VALUES (?, ?, ?, ?, ?)",
        (g.user['family_id'], data.get('title'), image_url, g.user['id'], status)
    )
    return jsonify({"message": "Photo uploaded", "id": photo_id, "status": status}), 201

@extra_bp.route('/photos/<int:photo_id>/approve', methods=['PUT'])
@login_required
@parent_or_admin
def approve_photo(photo_id):
    execute_db("UPDATE photos SET status = 'approved' WHERE id = ? AND family_id = ?", (photo_id, g.user['family_id']))
    return jsonify({"message": "Photo approved"})

# --- Sticky Notes ---

@extra_bp.route('/notes', methods=['GET'])
@login_required
def get_notes():
    notes = query_db("SELECT * FROM notes WHERE family_id = ? ORDER BY updated_at DESC", (g.user['family_id'],))
    return jsonify([dict(note) for note in notes])

@extra_bp.route('/notes', methods=['POST'])
@login_required
def add_note():
    data = request.json
    note_id = execute_db(
        "INSERT INTO notes (family_id, title, content, color, updated_by) VALUES (?, ?, ?, ?, ?)",
        (g.user['family_id'], data.get('title'), data.get('content'), data.get('color'), g.user['id'])
    )
    return jsonify({"message": "Note added", "id": note_id}), 201

@extra_bp.route('/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    data = request.json
    execute_db(
        "UPDATE notes SET title = ?, content = ?, color = ?, updated_by = ?, updated_at = ? WHERE id = ? AND family_id = ?",
        (data.get('title'), data.get('content'), data.get('color'), g.user['id'], datetime.now().isoformat(), note_id, g.user['family_id'])
    )
    return jsonify({"message": "Note updated"})

# --- Pet Care ---

@extra_bp.route('/pet_care', methods=['GET'])
@login_required
def get_pet_care():
    logs = query_db("SELECT * FROM pet_care WHERE family_id = ? ORDER BY timestamp DESC LIMIT 50", (g.user['family_id'],))
    return jsonify([dict(log) for log in logs])

@extra_bp.route('/pet_care', methods=['POST'])
@login_required
def log_pet_care():
    data = request.json
    pet_name = data.get('pet_name')
    action = data.get('action')
    if not pet_name or not action:
        return jsonify({"error": "Pet name and action required"}), 400

    log_id = execute_db(
        "INSERT INTO pet_care (family_id, pet_name, pet_type, action, status, logged_by_id) VALUES (?, ?, ?, ?, ?, ?)",
        (g.user['family_id'], pet_name, data.get('pet_type'), action, data.get('status'), g.user['id'])
    )
    return jsonify({"message": "Pet care logged", "id": log_id}), 201

# --- Emergency Contacts ---

@extra_bp.route('/emergency_contacts', methods=['GET'])
@login_required
def get_emergency_contacts():
    contacts = query_db("SELECT * FROM emergency_contacts WHERE family_id = ?", (g.user['family_id'],))
    return jsonify([dict(contact) for contact in contacts])

@extra_bp.route('/emergency_contacts', methods=['POST'])
@login_required
@parent_or_admin
def add_emergency_contact():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "Name required"}), 400

    contact_id = execute_db(
        "INSERT INTO emergency_contacts (family_id, name, relationship, phone, email, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (g.user['family_id'], name, data.get('relationship'), data.get('phone'), data.get('email'), data.get('notes'))
    )
    return jsonify({"message": "Contact added", "id": contact_id}), 201
