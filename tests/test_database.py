import unittest
import os
import tempfile
import sqlite3
from app import create_app
from app.config import Config
from app.database.db import get_db, init_db, query_db

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path
            
        self.app = create_app(TestConfig)
        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_tables_created(self):
        with self.app.app_context():
            tables = query_db("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [t['name'] for t in tables]
            self.assertIn('admins', table_names)
            self.assertIn('students', table_names)
            self.assertIn('attendance', table_names)
            self.assertIn('system_settings', table_names)
            self.assertIn('activity_logs', table_names)

    def test_default_admin_seeded(self):
        with self.app.app_context():
            admin = query_db("SELECT * FROM admins WHERE username='admin'", one=True)
            self.assertIsNotNone(admin)
            self.assertEqual(admin['username'], 'admin')

    def test_default_settings_seeded(self):
        with self.app.app_context():
            thresh = query_db("SELECT value FROM system_settings WHERE key='confidence_threshold'", one=True)
            self.assertIsNotNone(thresh)
            self.assertEqual(thresh['value'], '70.0')

if __name__ == '__main__':
    unittest.main()
