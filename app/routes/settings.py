from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.auth import login_required
from app.database.models import SettingsModel, AdminModel, ActivityLogModel

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_settings':
            conf_thresh = request.form.get('confidence_threshold', '70.0').strip()
            cooldown = request.form.get('cooldown_minutes', '60').strip()
            cam_idx = request.form.get('camera_index', '0').strip()
            samples = request.form.get('samples_per_student', '30').strip()
            inst_name = request.form.get('institution_name', '').strip()
            
            SettingsModel.set('confidence_threshold', conf_thresh)
            SettingsModel.set('cooldown_minutes', cooldown)
            SettingsModel.set('camera_index', cam_idx)
            SettingsModel.set('samples_per_student', samples)
            if inst_name:
                SettingsModel.set('institution_name', inst_name)
                
            ActivityLogModel.log('SETTINGS_UPDATED', 'System operational parameters updated')
            flash('System parameters updated successfully.', 'success')
            return redirect(url_for('settings.index'))
            
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '').strip()
            new_pw = request.form.get('new_password', '').strip()
            confirm_pw = request.form.get('confirm_password', '').strip()
            
            from flask import g
            if not AdminModel.verify_password(g.admin['username'], current_pw):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('settings.index'))
                
            if len(new_pw) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return redirect(url_for('settings.index'))
                
            if new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('settings.index'))
                
            AdminModel.update_password(g.admin['id'], new_pw)
            ActivityLogModel.log('PASSWORD_CHANGED', 'Administrator password updated')
            flash('Password changed successfully.', 'success')
            return redirect(url_for('settings.index'))
            
    settings = SettingsModel.get_all()
    return render_template('settings/index.html', settings=settings)
