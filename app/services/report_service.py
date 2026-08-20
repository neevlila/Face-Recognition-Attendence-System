import os
import pandas as pd
from datetime import datetime
from app.config import Config
from app.database.models import AttendanceModel

class ReportExportService:
    @staticmethod
    def generate_csv(start_date=None, end_date=None, department=None, student_id=None):
        records = AttendanceModel.filter_records(
            start_date=start_date,
            end_date=end_date,
            department=department,
            student_id=student_id,
            limit=50000
        )
        
        data = []
        for r in records:
            data.append({
                'Attendance Date': r['attendance_date'],
                'Attendance Time': r['attendance_time'],
                'Student ID': r['student_id'],
                'Student Name': r['student_name'],
                'Department': r['department'],
                'Semester': r['semester'],
                'Section': r['section'],
                'Status': r['status'],
                'Confidence (%)': f"{r['confidence']:.1f}",
                'Recognition Method': r['recognition_method']
            })
            
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Attendance Date', 'Attendance Time', 'Student ID', 'Student Name',
                'Department', 'Semester', 'Section', 'Status', 'Confidence (%)', 'Recognition Method'
            ])
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"attendance_report_{timestamp}.csv"
        filepath = os.path.join(Config.EXPORTS_DIR, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        return filepath, filename

    @staticmethod
    def generate_excel(start_date=None, end_date=None, department=None, student_id=None):
        records = AttendanceModel.filter_records(
            start_date=start_date,
            end_date=end_date,
            department=department,
            student_id=student_id,
            limit=50000
        )
        
        data = []
        for r in records:
            data.append({
                'Attendance Date': r['attendance_date'],
                'Attendance Time': r['attendance_time'],
                'Student ID': r['student_id'],
                'Student Name': r['student_name'],
                'Department': r['department'],
                'Semester': r['semester'],
                'Section': r['section'],
                'Status': r['status'],
                'Confidence (%)': round(float(r['confidence']), 1),
                'Recognition Method': r['recognition_method']
            })
            
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Attendance Date', 'Attendance Time', 'Student ID', 'Student Name',
                'Department', 'Semester', 'Section', 'Status', 'Confidence (%)', 'Recognition Method'
            ])

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"attendance_report_{timestamp}.xlsx"
        filepath = os.path.join(Config.EXPORTS_DIR, filename)
        
        # Write Excel with formatting
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Attendance Logs', index=False)
            
            # Create a Summary Sheet
            summary_data = {
                'Metric': ['Generated Date', 'Total Records', 'Filter Start Date', 'Filter End Date', 'Department Filter', 'Student Filter'],
                'Value': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    len(df),
                    start_date or 'All Time',
                    end_date or 'All Time',
                    department or 'All Departments',
                    student_id or 'All Students'
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
        return filepath, filename
