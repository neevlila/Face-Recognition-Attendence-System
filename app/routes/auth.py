import functools
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from app.database.models import AdminModel, ActivityLogModel

auth_bp = Blueprint('auth', __name__)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('admin_id') is None:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view

@auth_bp.before_app_request
def load_logged_in_admin():
    admin_id = session.get('admin_id')
    if admin_id is None:
        g.admin = None
    else:
        g.admin = AdminModel.get_by_id(admin_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.admin is not None:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('auth/login.html')
            
        admin = AdminModel.verify_password(username, password)
        if admin:
            session.clear()
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_name'] = admin['full_name']
            
            AdminModel.update_last_login(admin['id'])
            ActivityLogModel.log('ADMIN_LOGIN', f"Admin '{username}' logged in successfully.", ip_address=request.remote_addr)
            flash(f"Welcome back, {admin['full_name']}!", 'success')
            
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('http'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            ActivityLogModel.log('FAILED_LOGIN', f"Failed login attempt for username '{username}'.", ip_address=request.remote_addr)
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    username = session.get('admin_username', 'Admin')
    ActivityLogModel.log('ADMIN_LOGOUT', f"Admin '{username}' logged out.", ip_address=request.remote_addr)
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))
