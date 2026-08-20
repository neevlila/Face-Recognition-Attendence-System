from datetime import datetime, date, timedelta
from app.database.db import query_db
from app.database.models import StudentModel, AttendanceModel

class AnalyticsService:
    @staticmethod
    def get_dashboard_kpis():
        """
        Calculates Total Students, Present Today, Absent Today, and Attendance Rate.
        """
        today = date.today().strftime('%Y-%m-%d')
        
        total_students = StudentModel.count(status='active')
        
        # Present Today
        res_present = query_db(
            'SELECT COUNT(DISTINCT student_id) as cnt FROM attendance WHERE attendance_date = ? AND status = "Present"',
            (today,),
            one=True
        )
        present_today = res_present['cnt'] if res_present else 0
        
        absent_today = max(0, total_students - present_today)
        
        attendance_rate = round((present_today / max(1, total_students)) * 100, 1) if total_students > 0 else 0.0
        
        # Calculate yesterday's rate for trend comparison
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        res_yest = query_db(
            'SELECT COUNT(DISTINCT student_id) as cnt FROM attendance WHERE attendance_date = ? AND status = "Present"',
            (yesterday,),
            one=True
        )
        present_yesterday = res_yest['cnt'] if res_yest else 0
        yest_rate = round((present_yesterday / max(1, total_students)) * 100, 1) if total_students > 0 else 0.0
        trend_diff = round(attendance_rate - yest_rate, 1)
        
        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'attendance_rate': attendance_rate,
            'trend_diff': trend_diff
        }

    @staticmethod
    def get_weekly_trend():
        """
        Returns attendance count for the last 7 days.
        """
        labels = []
        counts = []
        
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            d_str = d.strftime('%Y-%m-%d')
            day_name = d.strftime('%a') # Mon, Tue, etc.
            
            res = query_db('SELECT COUNT(DISTINCT student_id) as cnt FROM attendance WHERE attendance_date = ?', (d_str,), one=True)
            cnt = res['cnt'] if res else 0
            
            labels.append(f"{day_name} ({d.strftime('%m/%d')})")
            counts.append(cnt)
            
        return {
            'labels': labels,
            'data': counts
        }

    @staticmethod
    def get_department_distribution():
        """
        Returns attendance stats grouped by department for today.
        """
        today = date.today().strftime('%Y-%m-%d')
        
        sql = '''
        SELECT 
            s.department,
            COUNT(DISTINCT s.student_id) as total_students,
            COUNT(DISTINCT a.student_id) as present_students
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND a.attendance_date = ?
        WHERE s.status = 'active'
        GROUP BY s.department
        ORDER BY total_students DESC
        '''
        rows = query_db(sql, (today,))
        
        labels = []
        total_data = []
        present_data = []
        percentages = []
        
        for r in rows:
            dept = r['department'] or 'General'
            tot = r['total_students']
            pres = r['present_students']
            pct = round((pres / max(1, tot)) * 100, 1)
            
            labels.append(dept)
            total_data.append(tot)
            present_data.append(pres)
            percentages.append(pct)
            
        return {
            'labels': labels,
            'total': total_data,
            'present': present_data,
            'percentages': percentages
        }

    @staticmethod
    def get_reports_summary(start_date=None, end_date=None, department=None):
        """
        Comprehensive reporting data.
        """
        sql = '''
        SELECT 
            s.student_id,
            s.name,
            s.department,
            s.semester,
            s.section,
            COUNT(a.id) as days_present
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
        '''
        conditions = ["s.status = 'active'"]
        args = []
        
        if start_date:
            conditions.append("(a.attendance_date >= ? OR a.attendance_date IS NULL)")
            args.append(start_date)
        if end_date:
            conditions.append("(a.attendance_date <= ? OR a.attendance_date IS NULL)")
            args.append(end_date)
        if department:
            conditions.append("s.department = ?")
            args.append(department)
            
        sql += " WHERE " + " AND ".join(conditions)
        sql += " GROUP BY s.student_id, s.name, s.department, s.semester, s.section ORDER BY days_present DESC"
        
        rows = query_db(sql, args)
        
        # Calculate total sessions in date range
        date_sql = "SELECT COUNT(DISTINCT attendance_date) as total_sessions FROM attendance WHERE 1=1"
        date_args = []
        if start_date:
            date_sql += " AND attendance_date >= ?"
            date_args.append(start_date)
        if end_date:
            date_sql += " AND attendance_date <= ?"
            date_args.append(end_date)
            
        date_res = query_db(date_sql, date_args, one=True)
        total_sessions = max(1, date_res['total_sessions'] if date_res else 1)
        
        student_reports = []
        for r in rows:
            pres = r['days_present']
            pct = round((pres / total_sessions) * 100, 1)
            if pct > 100.0:
                pct = 100.0
            student_reports.append({
                'student_id': r['student_id'],
                'name': r['name'],
                'department': r['department'],
                'semester': r['semester'],
                'section': r['section'],
                'days_present': pres,
                'total_sessions': total_sessions,
                'percentage': pct,
                'status': 'Eligible' if pct >= 75.0 else 'Shortage Warning'
            })
            
        return {
            'total_sessions': total_sessions,
            'students': student_reports
        }
