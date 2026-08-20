import unittest
import os
import tempfile
from app import create_app
from app.config import Config
from app.database.db import get_db, init_db
from app.database.models import StudentModel

class TestStudents(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path
            
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_create_and_retrieve_student(self):
        with self.app.app_context():
            s_id = StudentModel.create(
                student_id='STU001',
                name='Alice Smith',
                email='alice@test.edu',
                phone='1234567890',
                department='Computer Science',
                semester='Sem 4',
                section='A'
            )
            self.assertIsNotNone(s_id)
            
            student = StudentModel.get_by_student_id('STU001')
            self.assertIsNotNone(student)
            self.assertEqual(student['name'], 'Alice Smith')
            self.assertEqual(student['department'], 'Computer Science')
            self.assertEqual(student['face_label'], 1)

    def test_unique_face_label_increment(self):
        with self.app.app_context():
            StudentModel.create('STU001', 'Alice', 'alice@test.edu', '111', 'CS', 'Sem 1')
            StudentModel.create('STU002', 'Bob', 'bob@test.edu', '222', 'IT', 'Sem 2')
            
            s1 = StudentModel.get_by_student_id('STU001')
            s2 = StudentModel.get_by_student_id('STU002')
            
            self.assertEqual(s1['face_label'], 1)
            self.assertEqual(s2['face_label'], 2)

    def test_update_student(self):
        with self.app.app_context():
            new_id = StudentModel.create('STU003', 'Charlie', 'charlie@test.edu', '333', 'CS', 'Sem 1')
            StudentModel.update(new_id, 'Charlie Brown', 'charlie_new@test.edu', '333444', 'Information Technology', 'Sem 3', 'B')
            
            updated = StudentModel.get_by_id(new_id)
            self.assertEqual(updated['name'], 'Charlie Brown')
            self.assertEqual(updated['department'], 'Information Technology')
            self.assertEqual(updated['semester'], 'Sem 3')
            self.assertEqual(updated['section'], 'B')

    def test_delete_student(self):
        with self.app.app_context():
            new_id = StudentModel.create('STU004', 'David', 'david@test.edu', '444', 'CS', 'Sem 1')
            self.assertIsNotNone(StudentModel.get_by_id(new_id))
            
            StudentModel.delete(new_id)
            self.assertIsNone(StudentModel.get_by_id(new_id))

if __name__ == '__main__':
    unittest.main()
