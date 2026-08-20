from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from app.routes.auth import login_required
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportExportService
from app.database.models import StudentModel

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    department = request.args.get('department', '').strip()
    
    if start_date and end_date and start_date > end_date:
        end_date = start_date

    summary = AnalyticsService.get_reports_summary(start_date=start_date, end_date=end_date, department=department)

    departments = StudentModel.get_departments()
    
    return render_template(
        'reports/index.html',
        summary=summary,
        departments=departments,
        start_date=start_date,
        end_date=end_date,
        selected_dept=department
    )

@reports_bp.route('/export/csv')
@login_required
def export_csv():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    department = request.args.get('department', '').strip()
    student_id = request.args.get('student_id', '').strip()
    
    filepath, filename = ReportExportService.generate_csv(start_date, end_date, department, student_id)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')

@reports_bp.route('/export/excel')
@login_required
def export_excel():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    department = request.args.get('department', '').strip()
    student_id = request.args.get('student_id', '').strip()
    
    filepath, filename = ReportExportService.generate_excel(start_date, end_date, department, student_id)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
