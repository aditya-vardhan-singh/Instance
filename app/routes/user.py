# app/routes/user.py

from flask import Blueprint, render_template

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/')
def user_dashboard():
    return "<h1>User Dashboard</h1>"
