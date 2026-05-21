from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db, log_activity
from backend.middleware.auth_middleware import login_required
from datetime import datetime

grocery_bp = Blueprint('grocery', __name__)

@grocery_bp.route('/', methods=['GET'])
@login_required
def get_grocery_items():
    items = query_db("SELECT * FROM grocery_items WHERE family_id = ? AND status != 'archived'", (g.user['family_id'],))
    return jsonify([dict(item) for item in items])

@grocery_bp.route('/', methods=['POST'])
@login_required
def add_grocery_item():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "Name required"}), 400

    item_id = execute_db(
        "INSERT INTO grocery_items (family_id, name, quantity, category, added_by_id) VALUES (?, ?, ?, ?, ?)",
        (g.user['family_id'], name, data.get('quantity'), data.get('category'), g.user['id'])
    )

    execute_db("INSERT INTO grocery_history (grocery_item_id, action, user_id) VALUES (?, ?, ?)",
               (item_id, 'added', g.user['id']))

    log_activity(g.user['family_id'], g.user['id'], "add_grocery", "grocery", f"Added item: {name}")

    return jsonify({"message": "Item added", "id": item_id}), 201

@grocery_bp.route('/<int:item_id>', methods=['PUT'])
@login_required
def update_grocery_item(item_id):
    data = request.json
    item = query_db("SELECT * FROM grocery_items WHERE id = ? AND family_id = ?", (item_id, g.user['family_id']), one=True)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # RESTRICTION: child can mark as collected, but NOT purchased or archived
    new_status = data.get('status')
    if new_status:
        if g.user['role'] == 'child' and new_status in ('purchased', 'archived'):
            return jsonify({"error": "Children cannot mark items as purchased or archive them"}), 403

        if new_status == 'collected':
            execute_db("UPDATE grocery_items SET status = ?, collected_by_id = ?, collected_at = ? WHERE id = ?",
                       (new_status, g.user['id'], datetime.now().isoformat(), item_id))
        elif new_status == 'purchased':
            execute_db("UPDATE grocery_items SET status = ?, purchased_by_id = ?, purchased_at = ? WHERE id = ?",
                       (new_status, g.user['id'], datetime.now().isoformat(), item_id))
        else:
            execute_db("UPDATE grocery_items SET status = ? WHERE id = ?", (new_status, item_id))

        execute_db("INSERT INTO grocery_history (grocery_item_id, action, user_id, details) VALUES (?, ?, ?, ?)",
                   (item_id, 'status_change', g.user['id'], f"changed to {new_status}"))
        log_activity(g.user['family_id'], g.user['id'], "update_grocery", "grocery", f"Item {item_id} status to {new_status}")

    # Name/Quantity/Category updates
    name = data.get('name')
    if name:
         execute_db("UPDATE grocery_items SET name = ?, edited_by_id = ? WHERE id = ?", (name, g.user['id'], item_id))

    return jsonify({"message": "Item updated"})

@grocery_bp.route('/<int:item_id>', methods=['DELETE'])
@login_required
def delete_grocery_item(item_id):
    # RESTRICTION: children cannot permanent delete
    if g.user['role'] == 'child':
        return jsonify({"error": "Children cannot delete items"}), 403

    execute_db("DELETE FROM grocery_items WHERE id = ? AND family_id = ?", (item_id, g.user['family_id']))
    return jsonify({"message": "Item deleted"})
