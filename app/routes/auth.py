from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
import re
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# python
# web dev - overview (manager) functionality
# 


# ---------------------
# Route: Login
# ---------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Validation
        if not (6 <= len(password) <= 12):
            flash('Password must be between 6 and 12 characters.', 'error')
            return render_template('login.html')

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Invalid email address.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin.base'))  # You need to define this route
            else:
                return redirect(url_for('user.dashboard'))

        flash('Incorrect email or password!', 'error')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


# ---------------------
# Route: Signup
# ---------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Validation: username length
        if not (4 <= len(username) <= 20):
            return render_template("signup.html",message="Username is required!")
            # flash('Username must be between 4 and 20 characters.', 'error')
            return render_template('signup.html')

        # Validation: password length
        if not (6 <= len(password) <= 12):
            flash('Password must be between 6 and 12 characters.', 'error')
            return render_template('signup.html')

        # Validation: email format
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Invalid email address.', 'error')
            return render_template('signup.html')

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('signup.html')

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.login'))

    return render_template('signup.html')


# ---------------------
# Route: Logout
# ---------------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.homepage'))
