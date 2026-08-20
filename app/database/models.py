import sqlite3
from datetime import datetime, date
from werkzeug.security import check_password_hash, generate_password_hash
from app.database.db import get_db, query_db, execute_db

class AdminModel:
    @staticmethod
    def get_by_username(username):
        return query_db('SELECT * FROM admins WHERE username = ?', (username,), one=True)
    
    @staticmethod
    def get_by_id(admin_id):
        return query_db('SELECT * FROM admins WHERE id = ?', (admin_id,), one=True)
    
    @staticmethod
    def verify_password(username, password):
        admin = AdminModel.get_by_username(username)
        if admin and check_password_hash(admin['password_hash'], password):
            return admin
        return None
    
    @staticmethod
    def update_last_login(admin_id):
        execute_db('UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (admin_id,))
    
    @staticmethod
    def update_password(admin_id, new_password):
        pw_hash = generate_password_hash(new_password, method='scrypt')
        execute_db('UPDATE admins SET password_hash = ? WHERE id = ?', (pw_hash, admin_id))


class StudentModel:
    @staticmethod
    def get_all(search=None, department=None, semester=None, status=None, limit=100, offset=0):
        sql = 'SELECT * FROM students WHERE 1=1'
        args = []
        if search:
            sql += ' AND (name LIKE ? OR student_id LIKE ? OR email LIKE ?)'
            term = f'%{search}%'
            args.extend([term, term, term])
        if department:
            sql += ' AND department = ?'
            args.append(department)
        if semester:
            sql += ' AND semester = ?'
            args.append(semester)
        if status:
            sql += ' AND status = ?'
            args.append(status)
        sql += ' ORDER BY id DESC LIMIT ? OFFSET ?'
        args.extend([limit, offset])
        return query_db(sql, args)
    
    @staticmethod
    def count(search=None, department=None, semester=None, status=None):
        sql = 'SELECT COUNT(*) as total FROM students WHERE 1=1'
        args = []
        if search:
            sql += ' AND (name LIKE ? OR student_id LIKE ? OR email LIKE ?)'
            term = f'%{search}%'
            args.extend([term, term, term])
        if department:
            sql += ' AND department = ?'
            args.append(department)
        if semester:
            sql += ' AND semester = ?'
            args.append(semester)
        if status:
            sql += ' AND status = ?'
            args.append(status)
        res = query_db(sql, args, one=True)
        return res['total'] if res else 0

    @staticmethod
    def get_by_id(id_val):
        return query_db('SELECT * FROM students WHERE id = ?', (id_val,), one=True)

    @staticmethod
    def get_by_student_id(student_id):
        return query_db('SELECT * FROM students WHERE student_id = ?', (student_id,), one=True)

    @staticmethod
    def get_by_face_label(face_label):
        return query_db('SELECT * FROM students WHERE face_label = ?', (face_label,), one=True)

    @staticmethod
    def get_next_face_label():
        res = query_db('SELECT MAX(face_label) as max_label FROM students', one=True)
        if res and res['max_label'] is not None:
            return res['max_label'] + 1
        return 1

    @staticmethod
    def create(student_id, name, email, phone, department, semester, section='A', profile_image=None):
        face_label = StudentModel.get_next_face_label()
        sql = '''INSERT INTO students 
                 (student_id, name, email, phone, department, semester, section, profile_image, face_label) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        new_id = execute_db(sql, (student_id, name, email, phone, department, semester, section, profile_image, face_label))
        return new_id

    @staticmethod
    def update(id_val, name, email, phone, department, semester, section='A', profile_image=None, status='active'):
        if profile_image:
            sql = '''UPDATE students 
                     SET name = ?, email = ?, phone = ?, department = ?, semester = ?, section = ?, profile_image = ?, status = ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?'''
            execute_db(sql, (name, email, phone, department, semester, section, profile_image, status, id_val))
        else:
            sql = '''UPDATE students 
                     SET name = ?, email = ?, phone = ?, department = ?, semester = ?, section = ?, status = ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?'''
            execute_db(sql, (name, email, phone, department, semester, section, status, id_val))

    @staticmethod
    def update_samples_count(student_id, count):
        execute_db('UPDATE students SET face_samples_count = ?, updated_at = CURRENT_TIMESTAMP WHERE student_id = ?', (count, student_id))

    @staticmethod
    def delete(id_val):
        execute_db('DELETE FROM students WHERE id = ?', (id_val,))

    @staticmethod
    def get_departments():
        rows = query_db('SELECT DISTINCT department FROM students ORDER BY department')
        return [r['department'] for r in rows if r['department']]


class AttendanceModel:
    @staticmethod
    def mark_present(student_id, confidence, recognition_method='OpenCV-LBPH', date_str=None, time_str=None):
        now = datetime.now()
        att_date = date_str or now.strftime('%Y-%m-%d')
        att_time = time_str or now.strftime('%H:%M:%S')
        
        # Verify student exists in students table before inserting to prevent foreign key failure
        st = query_db('SELECT id FROM students WHERE student_id = ?', (student_id,), one=True)
        if not st:
            return {'status': 'not_found', 'message': f'Student ID {student_id} not registered'}

        # Check if already marked for today
        existing = query_db(
            'SELECT id, attendance_time FROM attendance WHERE student_id = ? AND attendance_date = ?',
            (student_id, att_date),
            one=True
        )
        if existing:
            return {'status': 'already_marked', 'time': existing['attendance_time'], 'id': existing['id']}
        
        try:
            sql = '''INSERT INTO attendance (student_id, attendance_date, attendance_time, status, confidence, recognition_method)
                     VALUES (?, ?, ?, 'Present', ?, ?)'''
            new_id = execute_db(sql, (student_id, att_date, att_time, confidence, recognition_method))
            return {'status': 'marked', 'time': att_time, 'id': new_id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def is_marked_today(student_id, date_str=None):
        att_date = date_str or date.today().strftime('%Y-%m-%d')
        row = query_db('SELECT id, attendance_time FROM attendance WHERE student_id = ? AND attendance_date = ?', (student_id, att_date), one=True)
        return row is not None


    @staticmethod
    def get_today_records(limit=50):
        today = date.today().strftime('%Y-%m-%d')
        sql = '''SELECT a.*, s.name as student_name, s.department, s.semester, s.section, s.profile_image
                 FROM attendance a
                 JOIN students s ON a.student_id = s.student_id
                 WHERE a.attendance_date = ?
                 ORDER BY a.attendance_time DESC
                 LIMIT ?'''
        return query_db(sql, (today, limit))

    @staticmethod
    def filter_records(start_date=None, end_date=None, student_id=None, department=None, limit=500, offset=0):
        sql = '''SELECT a.*, s.name as student_name, s.department, s.semester, s.section, s.email, s.phone
                 FROM attendance a
                 JOIN students s ON a.student_id = s.student_id
                 WHERE 1=1'''
        args = []
        if start_date:
            sql += ' AND a.attendance_date >= ?'
            args.append(start_date)
        if end_date:
            sql += ' AND a.attendance_date <= ?'
            args.append(end_date)
        if student_id:
            sql += ' AND a.student_id = ?'
            args.append(student_id)
        if department:
            sql += ' AND s.department = ?'
            args.append(department)
        sql += ' ORDER BY a.attendance_date DESC, a.attendance_time DESC LIMIT ? OFFSET ?'
        args.extend([limit, offset])
        return query_db(sql, args)

    @staticmethod
    def get_student_history(student_id, limit=30):
        sql = '''SELECT * FROM attendance WHERE student_id = ? ORDER BY attendance_date DESC, attendance_time DESC LIMIT ?'''
        return query_db(sql, (student_id, limit))

    @staticmethod
    def get_student_stats(student_id):
        total_present = query_db('SELECT COUNT(*) as cnt FROM attendance WHERE student_id = ? AND status = "Present"', (student_id,), one=True)['cnt']
        total_dates_row = query_db('SELECT COUNT(DISTINCT attendance_date) as cnt FROM attendance', one=True)
        total_days = total_dates_row['cnt'] if total_dates_row and total_dates_row['cnt'] > 0 else 1
        percentage = round((total_present / max(1, total_days)) * 100, 1)
        if percentage > 100.0:
            percentage = 100.0
        return {
            'total_present': total_present,
            'total_days': total_days,
            'percentage': percentage
        }

    @staticmethod
    def delete_record(record_id):
        execute_db('DELETE FROM attendance WHERE id = ?', (record_id,))


class SettingsModel:
    @staticmethod
    def get_all():
        rows = query_db('SELECT * FROM system_settings')
        return {r['key']: r['value'] for r in rows}

    @staticmethod
    def get(key, default=None):
        row = query_db('SELECT value FROM system_settings WHERE key = ?', (key,), one=True)
        return row['value'] if row else default

    @staticmethod
    def set(key, value, description=None):
        if description:
            execute_db('INSERT INTO system_settings (key, value, description, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value, description = excluded.description, updated_at = CURRENT_TIMESTAMP', (key, str(value), description))
        else:
            execute_db('INSERT INTO system_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP', (key, str(value)))


class ActivityLogModel:
    @staticmethod
    def log(action, details=None, student_id=None, ip_address=None):
        sql = '''INSERT INTO activity_logs (action, details, student_id, ip_address) VALUES (?, ?, ?, ?)'''
        execute_db(sql, (action, details, student_id, ip_address))

    @staticmethod
    def get_recent(limit=20):
        return query_db('SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?', (limit,))
