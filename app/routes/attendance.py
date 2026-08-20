from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.routes.auth import login_required
from app.database.models import AttendanceModel, StudentModel, ActivityLogModel

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
@login_required
def index():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    department = request.args.get('department', '').strip()
    student_id = request.args.get('student_id', '').strip()
    page = int(request.args.get('page', 1))
    limit = 25
    offset = (page - 1) * limit
    
    # Default to today if no dates specified
    if not start_date and not end_date and not student_id and not department:
        start_date = date.today().strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
    elif start_date and end_date and start_date > end_date:
        end_date = start_date

        
    records = AttendanceModel.filter_records(
        start_date=start_date,
        end_date=end_date,
        student_id=student_id,
        department=department,
        limit=limit,
        offset=offset
    )
    
    departments = StudentModel.get_departments()
    
    return render_template(
        'attendance/index.html',
        records=records,
        departments=departments,
        start_date=start_date,
        end_date=end_date,
        selected_dept=department,
        student_id=student_id,
        current_page=page
    )

@attendance_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_record(id):
    AttendanceModel.delete_record(id)
    ActivityLogModel.log('ATTENDANCE_RECORD_DELETED', f'Deleted attendance record ID {id}')
    flash('Attendance record removed.', 'info')
    return redirect(request.referrer or url_for('attendance.index'))
