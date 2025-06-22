# app/routes/admin.py

from flask import Blueprint, render_template, session, redirect, url_for

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    # return render_template('admin_dashboard.html')
    return "<h1>Admin Dashboard</h1>"
