from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ---------------------
# Route: Login
# ---------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'user'
            return redirect(url_for('user.dashboard'))  # Or your desired route
        else:
            return redirect(url_for('auth.login'))  # Retry login if invalid

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
