import sqlite3
from werkzeug.security import generate_password_hash
from app.database.db import get_db

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT DEFAULT 'Administrator',
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    department TEXT NOT NULL,
    semester TEXT NOT NULL,
    section TEXT DEFAULT 'A',
    profile_image TEXT,
    face_label INTEGER UNIQUE,
    face_samples_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    attendance_date TEXT NOT NULL,
    attendance_time TEXT NOT NULL,
    status TEXT DEFAULT 'Present',
    confidence REAL DEFAULT 0.0,
    recognition_method TEXT DEFAULT 'OpenCV-LBPH',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE(student_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT,
    student_id TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date_student ON attendance(attendance_date, student_id);
CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department);
CREATE INDEX IF NOT EXISTS idx_students_face_label ON students(face_label);
"""

def create_schema():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()

def seed_initial_data():
    db = get_db()
    admin = db.execute('SELECT id FROM admins WHERE username = ?', ('admin',)).fetchone()
    if not admin:
        default_hash = generate_password_hash('admin123', method='scrypt')
        db.execute(
            'INSERT INTO admins (username, password_hash, full_name, email) VALUES (?, ?, ?, ?)',
            ('admin', default_hash, 'System Administrator', 'admin@faceattend.edu')
        )
    
    default_settings = [
        ('confidence_threshold', '70.0', 'Minimum confidence percentage required for auto-marking attendance'),
        ('cooldown_minutes', '60', 'Minutes before student recognition triggers duplicate status vs new session'),
        ('camera_index', '0', 'Default hardware camera device index (0 for default webcam)'),
        ('samples_per_student', '30', 'Target face crop samples collected per student enrollment'),
        ('institution_name', 'University Department of Computer Science & Engineering', 'Organization / College Name'),
        ('system_mode', 'active', 'Live recognition operational mode (active/testing/maintenance)')
    ]
    
    for key, value, desc in default_settings:
        db.execute(
            'INSERT OR IGNORE INTO system_settings (key, value, description) VALUES (?, ?, ?)',
            (key, value, desc)
        )
    db.commit()
