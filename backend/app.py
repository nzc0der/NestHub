import os
import sys
from flask import Flask, send_from_directory, g, session

# Add project root to sys.path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask_cors import CORS
from backend.database.db import init_db, query_db
from backend.routes.auth import auth_bp
from backend.routes.admin import admin_bp
from backend.routes.chores import chores_bp
from backend.routes.calendar import calendar_bp
from backend.routes.grocery import grocery_bp
from backend.routes.meals import meals_bp
from backend.routes.messages import messages_bp
from backend.routes.extra import extra_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(chores_bp, url_prefix='/api/chores')
app.register_blueprint(calendar_bp, url_prefix='/api/calendar')
app.register_blueprint(grocery_bp, url_prefix='/api/grocery')
app.register_blueprint(meals_bp, url_prefix='/api/meals')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(extra_bp, url_prefix='/api/extra')

@app.before_request
def load_user():
    user_id = session.get('user_id')
    if user_id:
        g.user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    else:
        g.user = None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all for SPA routing
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        return {"error": "Not found"}, 404
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        init_db(app)
    app.run(debug=True, port=8000, host='0.0.0.0')
