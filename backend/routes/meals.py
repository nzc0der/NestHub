from flask import Blueprint, request, jsonify, g
from backend.database.db import query_db, execute_db
from backend.middleware.auth_middleware import login_required

meals_bp = Blueprint('meals', __name__)

@meals_bp.route('/', methods=['GET'])
@login_required
def get_meals():
    meals = query_db("SELECT * FROM meals WHERE family_id = ?", (g.user['family_id'],))
    return jsonify([dict(meal) for meal in meals])

@meals_bp.route('/', methods=['POST'])
@login_required
def add_meal():
    data = request.json
    day = data.get('day_of_week')
    meal_type = data.get('meal_type')
    if not day or not meal_type:
        return jsonify({"error": "Day and meal type required"}), 400

    meal_id = execute_db(
        "INSERT INTO meals (family_id, day_of_week, meal_type, description, recipe_url) VALUES (?, ?, ?, ?, ?)",
        (g.user['family_id'], day, meal_type, data.get('description'), data.get('recipe_url'))
    )
    return jsonify({"message": "Meal added", "id": meal_id}), 201

@meals_bp.route('/<int:meal_id>', methods=['PUT'])
@login_required
def update_meal(meal_id):
    data = request.json
    execute_db(
        "UPDATE meals SET day_of_week = ?, meal_type = ?, description = ?, recipe_url = ? WHERE id = ? AND family_id = ?",
        (data.get('day_of_week'), data.get('meal_type'), data.get('description'), data.get('recipe_url'), meal_id, g.user['family_id'])
    )
    return jsonify({"message": "Meal updated"})

@meals_bp.route('/<int:meal_id>', methods=['DELETE'])
@login_required
def delete_meal(meal_id):
    execute_db("DELETE FROM meals WHERE id = ? AND family_id = ?", (meal_id, g.user['family_id']))
    return jsonify({"message": "Meal deleted"})
