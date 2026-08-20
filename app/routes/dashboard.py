from flask import Blueprint, render_template, jsonify
from app.routes.auth import login_required
from app.services.analytics_service import AnalyticsService
from app.services.face_recognition import face_recognizer
from app.database.models import AttendanceModel, ActivityLogModel

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    kpis = AnalyticsService.get_dashboard_kpis()
    today_records = AttendanceModel.get_today_records(limit=10)
    recent_logs = ActivityLogModel.get_recent(limit=8)
    weekly_trend = AnalyticsService.get_weekly_trend()
    dept_distribution = AnalyticsService.get_department_distribution()
    
    system_status = {
        'model_trained': face_recognizer.is_trained,
        'last_trained': face_recognizer.last_trained_time or 'Never',
        'registered_faces': len(face_recognizer.labels_map),
        'status_text': 'System Online' if face_recognizer.is_trained else 'Model Needs Training'
    }
    
    return render_template(
        'dashboard/index.html',
        kpis=kpis,
        today_records=today_records,
        recent_logs=recent_logs,
        weekly_trend=weekly_trend,
        dept_distribution=dept_distribution,
        system_status=system_status
    )

@dashboard_bp.route('/api/stats')
@login_required
def get_stats_api():
    kpis = AnalyticsService.get_dashboard_kpis()
    weekly = AnalyticsService.get_weekly_trend()
    dept = AnalyticsService.get_department_distribution()
    return jsonify({
        'kpis': kpis,
        'weekly': weekly,
        'department': dept
    })
