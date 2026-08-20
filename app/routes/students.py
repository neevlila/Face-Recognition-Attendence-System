import os
import shutil
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from app.config import Config
from app.routes.auth import login_required
from app.database.models import StudentModel, AttendanceModel, ActivityLogModel
from app.services.face_recognition import face_recognizer


students_bp = Blueprint('students', __name__, url_prefix='/students')

@students_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    semester = request.args.get('semester', '').strip()
    status = request.args.get('status', '').strip()
    page = int(request.args.get('page', 1))
    limit = 20
    offset = (page - 1) * limit
    
    students = StudentModel.get_all(search=search, department=department, semester=semester, status=status, limit=limit, offset=offset)
    total_count = StudentModel.count(search=search, department=department, semester=semester, status=status)
    total_pages = max(1, (total_count + limit - 1) // limit)
    departments = StudentModel.get_departments()
    
    # Check sample files on disk for each student
    students_with_meta = []
    for s in students:
        s_dict = dict(s)
        s_dir = os.path.join(Config.DATASET_DIR, str(s['student_id']))
        has_samples = os.path.exists(s_dir) and len(os.listdir(s_dir)) > 0
        s_dict['has_dataset'] = has_samples
        students_with_meta.append(s_dict)
        
    return render_template(
        'students/index.html',
        students=students_with_meta,
        departments=departments,
        search=search,
        selected_dept=department,
        selected_sem=semester,
        selected_status=status,
        current_page=page,
        total_pages=total_pages,
        total_students=total_count
    )

@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        section = request.form.get('section', 'A').strip()
        
        if not student_id or not name or not department or not semester:
            flash('Please provide Student ID, Full Name, Department, and Semester.', 'danger')
            return render_template('students/add_edit.html', mode='add')
            
        # Check uniqueness
        existing_sid = StudentModel.get_by_student_id(student_id)
        if existing_sid:
            flash(f"Student ID '{student_id}' is already registered.", 'danger')
            return render_template('students/add_edit.html', mode='add')
            
        new_id = StudentModel.create(student_id, name, email, phone, department, semester, section)
        ActivityLogModel.log('STUDENT_REGISTERED', f"Registered student '{name}' (ID: {student_id})", student_id=student_id)
        flash(f"Student '{name}' added successfully! Now capture face dataset.", 'success')
        return redirect(url_for('students.profile', id=new_id, capture='true'))
        
    return render_template('students/add_edit.html', mode='add')

@students_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = StudentModel.get_by_id(id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        section = request.form.get('section', 'A').strip()
        status = request.form.get('status', 'active').strip()
        
        if not name or not department or not semester:
            flash('Name, Department, and Semester are required.', 'danger')
            return render_template('students/add_edit.html', mode='edit', student=student)
            
        StudentModel.update(id, name, email, phone, department, semester, section, status=status)
        ActivityLogModel.log('STUDENT_UPDATED', f"Updated details for student '{name}' (ID: {student['student_id']})", student_id=student['student_id'])
        flash(f"Student '{name}' updated successfully.", 'success')
        return redirect(url_for('students.profile', id=id))
        
    return render_template('students/add_edit.html', mode='edit', student=student)

@students_bp.route('/profile/<int:id>')
@login_required
def profile(id):
    student = StudentModel.get_by_id(id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))
        
    stats = AttendanceModel.get_student_stats(student['student_id'])
    history = AttendanceModel.get_student_history(student['student_id'], limit=20)
    
    # Dataset files
    s_dir = os.path.join(Config.DATASET_DIR, str(student['student_id']))
    sample_images = []
    if os.path.exists(s_dir):
        sample_images = [f for f in os.listdir(s_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != 'profile.jpg']
        sample_images.sort()
        
    trigger_capture = request.args.get('capture') == 'true'
    
    return render_template(
        'students/profile.html',
        student=student,
        stats=stats,
        history=history,
        sample_images=sample_images,
        samples_count=len(sample_images),
        trigger_capture=trigger_capture
    )

@students_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = StudentModel.get_by_id(id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))
        
    student_id = student['student_id']
    name = student['name']
    
    # Remove dataset folder
    s_dir = os.path.join(Config.DATASET_DIR, str(student_id))
    if os.path.exists(s_dir):
        try:
            shutil.rmtree(s_dir)
        except Exception as e:
            print(f"Error removing dataset folder: {e}")
            
    StudentModel.delete(id)
    
    # Auto-synchronize and retrain/clear face recognition model
    try:
        face_recognizer.train_model()
    except Exception as e:
        print(f"Error syncing model after deletion: {e}")

    ActivityLogModel.log('STUDENT_DELETED', f"Deleted student '{name}' (ID: {student_id})", student_id=student_id)
    flash(f"Student '{name}' and face dataset deleted successfully.", 'info')
    return redirect(url_for('students.index'))


@students_bp.route('/dataset_image/<student_id>/<filename>')
@login_required
def dataset_image(student_id, filename):
    s_dir = os.path.join(Config.DATASET_DIR, str(student_id))
    return send_from_directory(s_dir, filename)

@students_bp.route('/api/check_id/<student_id>')
@login_required
def check_id_exists(student_id):
    existing = StudentModel.get_by_student_id(student_id)
    return jsonify({'exists': existing is not None})
