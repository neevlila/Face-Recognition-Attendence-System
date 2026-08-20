import unittest
import os
import tempfile
from app import create_app
from app.config import Config
from app.database.db import get_db, init_db

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path
            SECRET_KEY = 'test-secret-key'
            
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AuraPass', response.data)

    def test_valid_login(self):
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard Overview', response.data)

    def test_invalid_login(self):
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_protected_route_redirects_anonymous_user(self):
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_logout(self):
        # Login first
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AuraPass', response.data)


if __name__ == '__main__':
    unittest.main()
