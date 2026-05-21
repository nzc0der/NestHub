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

if __name__ == '__main__':
    unittest.main()
