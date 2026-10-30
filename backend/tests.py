import unittest
import json
import os
import sys
import sqlite3
import uuid

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app
from backend.database import db as db_module

class NestBoardTestCase(unittest.TestCase):
    def setUp(self):
        self.db_name = f'test_{uuid.uuid4().hex}.db'
        db_module.DB_PATH = self.db_name

        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db_module.init_db(app)
        # Setup initial family and users
        db_module.execute_db("INSERT INTO families (name, invite_code) VALUES (?, ?)", ('Test Family', str(uuid.uuid4())))
        # Admin
        db_module.execute_db("INSERT INTO users (family_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                   (1, f'admin_{uuid.uuid4().hex}', 'xxx', 'admin'))
        # Child
        db_module.execute_db("INSERT INTO users (family_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                   (1, f'child_{uuid.uuid4().hex}', 'yyy', 'child'))

    def tearDown(self):
        self.app_context.pop()
        if os.path.exists(self.db_name):
             os.remove(self.db_name)

    def login(self, role):
        user = db_module.query_db("SELECT id, family_id FROM users WHERE role = ?", (role,), one=True)
        with self.client.session_transaction() as sess:
            sess['user_id'] = user['id']
            sess['family_id'] = user['family_id']

    def test_grocery_child_restriction(self):
        """Test that children cannot delete or mark as purchased."""
        self.login('child')

        # Add item
        res = self.client.post('/api/grocery/', json={'name': 'Apples'})
        item_id = res.get_json()['id']

        # Try to mark as purchased (should fail)
        res = self.client.put(f'/api/grocery/{item_id}', json={'status': 'purchased'})
        self.assertEqual(res.status_code, 403)

        # Try to delete (should fail)
        res = self.client.delete(f'/api/grocery/{item_id}')
        self.assertEqual(res.status_code, 403)

        # Try to mark as collected (should succeed)
        res = self.client.put(f'/api/grocery/{item_id}', json={'status': 'collected'})
        self.assertEqual(res.status_code, 200)

    def test_photo_approval_logic(self):
        """Test that child uploads are pending, admin uploads are approved."""
        # Child upload
        self.login('child')
        res = self.client.post('/api/extra/photos', json={'image_url': 'http://test.com/1.jpg'})
        self.assertEqual(res.get_json()['status'], 'pending')

        # Admin upload
        self.login('admin')
        res = self.client.post('/api/extra/photos', json={'image_url': 'http://test.com/2.jpg'})
        self.assertEqual(res.get_json()['status'], 'approved')

    def test_tv_summary_endpoint(self):
        """Test the TV companion summary endpoint returns aggregate family data."""
        # Insert sample events and chores for family 1
        db_module.execute_db(
            "INSERT INTO events (family_id, title, start_time, location) VALUES (?, ?, ?, ?)",
            (1, "Family Dinner", "2025-12-01 19:00", "Dining Room")
        )
        db_module.execute_db(
            "INSERT INTO chores (family_id, title, priority, status) VALUES (?, ?, ?, ?)",
            (1, "Feed the dog", "high", "pending")
        )
        db_module.execute_db(
            "INSERT INTO meals (family_id, day_of_week, meal_type, description) VALUES (?, ?, ?, ?)",
            (1, "Monday", "Dinner", "Spaghetti Bolognese")
        )
        db_module.execute_db(
            "INSERT INTO grocery_items (family_id, name, status) VALUES (?, ?, ?)",
            (1, "Milk", "active")
        )

        res = self.client.get('/api/tv/summary')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['configured'])
        self.assertEqual(data['family']['name'], 'Test Family')
        self.assertGreaterEqual(len(data['calendar']), 1)
        self.assertEqual(data['calendar'][0]['title'], 'Family Dinner')
        self.assertGreaterEqual(len(data['chores']), 1)
        self.assertEqual(data['chores'][0]['title'], 'Feed the dog')
        self.assertGreaterEqual(len(data['meals']), 1)
        self.assertGreaterEqual(len(data['grocery']), 1)

    def test_tv_weather_endpoint(self):
        """Test the weather proxy and fallback/cache logic."""
        res = self.client.get('/api/tv/weather')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('current', data)
        self.assertIn('temperature', data['current'])
        self.assertIn('forecast', data)
        self.assertEqual(data['location'], 'Ormond, Melbourne')

    def test_tv_dashboard_routes(self):
        """Test that /dashboard and /tv static files are served properly."""
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'NestHub | TV Companion Dashboard', res.data)

        res_slash = self.client.get('/dashboard/')
        self.assertEqual(res_slash.status_code, 200)

        res_css = self.client.get('/tv/dashboard.css')
        self.assertEqual(res_css.status_code, 200)

        res_js = self.client.get('/tv/dashboard.js')
        self.assertEqual(res_js.status_code, 200)

    def test_phone_interface_intact(self):
        """Test that existing index.html and phone routes remain intact."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'NestBoard | Premium Family Dashboard', res.data)

if __name__ == '__main__':
    unittest.main()
