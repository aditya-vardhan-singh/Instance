# app/routes/admin.py

from flask import Blueprint, render_template, session, redirect, url_for

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    all_spots = [
        {"number": "A101", "level": "1", "is_occupied": True},
        {"number": "A102", "level": "1", "is_occupied": False},
        {"number": "B201", "level": "2", "is_occupied": True},
        {"number": "B202", "level": "2", "is_occupied": False},
        {"number": "C301", "level": "3", "is_occupied": False},
    ]

    from datetime import datetime, timedelta

    all_bookings = [
        {
            "user_email": "alice@example.com",
            "spot_number": "A101",
            "start_time": datetime.now() - timedelta(hours=2),
            "end_time": None  # Ongoing
        },
        {
            "user_email": "bob@example.com",
            "spot_number": "B201",
            "start_time": datetime.now() - timedelta(days=1, hours=3),
            "end_time": datetime.now() - timedelta(days=1)
        },
        {
            "user_email": "charlie@example.com",
            "spot_number": "A102",
            "start_time": datetime.now() - timedelta(days=2),
            "end_time": datetime.now() - timedelta(days=2, hours=-2)
        },
    ]
    
    from datetime import datetime, timedelta

    # Fake data for 7 days
    today = datetime.today()
    daily_labels = [(today - timedelta(days=i)).strftime('%d %b') for i in reversed(range(7))]
    daily_counts = [2, 4, 1, 3, 0, 5, 6]  # Replace with real count logic

    daily_booking_data = {
        'labels': daily_labels,
        'counts': daily_counts
    }
    
    analytics={
        'total_spots': 100,
        'occupied_spots': 30,
        'total_users': 50,
        'active_bookings': 20
    }

    
    return render_template(
        'admin_dashboard.html',
        all_spots=all_spots,
        all_bookings=all_bookings,
        analytics=analytics,
        daily_booking_data=daily_booking_data
    )



@admin_bp.route('/add-spot')
def add_spot():
    return "<h1>Add spot</h1>"

@admin_bp.route('/remove-spot')
def remove_spot():
    return "<h1>Remove spot</h1>"
