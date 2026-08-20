import unittest
import os
import tempfile
from datetime import date, datetime
from app import create_app
from app.config import Config
from app.database.db import get_db, init_db
from app.database.models import StudentModel, AttendanceModel

class TestAttendance(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = self.db_path
            
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()
            # Seed test students
            StudentModel.create('STU101', 'Mahek Chavda', 'mahek@test.edu', '111', 'Computer Science', 'Sem 6')
            StudentModel.create('STU102', 'Drashti Bambharoliya', 'drashti@test.edu', '222', 'Information Technology', 'Sem 6')

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_mark_attendance_success(self):
        with self.app.app_context():
            res = AttendanceModel.mark_present('STU101', 94.5, recognition_method='OpenCV-LBPH')
            self.assertEqual(res['status'], 'marked')
            self.assertIsNotNone(res['id'])
            
            # Verify record exists
            records = AttendanceModel.get_today_records()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['student_id'], 'STU101')
            self.assertEqual(records[0]['student_name'], 'Mahek Chavda')
            self.assertEqual(records[0]['confidence'], 94.5)

    def test_prevent_duplicate_attendance_same_day(self):
        with self.app.app_context():
            # First mark
            res1 = AttendanceModel.mark_present('STU101', 92.0)
            self.assertEqual(res1['status'], 'marked')
            
            # Second mark attempt on same day
            res2 = AttendanceModel.mark_present('STU101', 95.0)
            self.assertEqual(res2['status'], 'already_marked')
            
            # Verify only 1 record exists in DB
            records = AttendanceModel.get_today_records()
            self.assertEqual(len(records), 1)

    def test_filter_attendance_by_department(self):
        with self.app.app_context():
            AttendanceModel.mark_present('STU101', 90.0) # CS
            AttendanceModel.mark_present('STU102', 88.0) # IT
            
            cs_records = AttendanceModel.filter_records(department='Computer Science')
            it_records = AttendanceModel.filter_records(department='Information Technology')
            
            self.assertEqual(len(cs_records), 1)
            self.assertEqual(cs_records[0]['student_id'], 'STU101')
            self.assertEqual(len(it_records), 1)
            self.assertEqual(it_records[0]['student_id'], 'STU102')

    def test_student_attendance_percentage_calculation(self):
        with self.app.app_context():
            # Mark STU101 on 2 distinct dates
            AttendanceModel.mark_present('STU101', 90.0, date_str='2026-08-01')
            AttendanceModel.mark_present('STU101', 92.0, date_str='2026-08-02')
            # Mark STU102 on only 1 date
            AttendanceModel.mark_present('STU102', 85.0, date_str='2026-08-01')
            
            stats1 = AttendanceModel.get_student_stats('STU101')
            stats2 = AttendanceModel.get_student_stats('STU102')
            
            self.assertEqual(stats1['total_present'], 2)
            self.assertEqual(stats1['percentage'], 100.0) # 2/2 = 100%
            
            self.assertEqual(stats2['total_present'], 1)
            self.assertEqual(stats2['percentage'], 50.0) # 1/2 = 50%

if __name__ == '__main__':
    unittest.main()
