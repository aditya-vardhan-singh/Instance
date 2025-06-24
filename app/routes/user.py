# app/routes/user.py

from flask import Blueprint, render_template

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/')
def user_dashboard():
    # fetch these data from database
    available_spots = [
        {"number": 7, "level": 0},
        {"number": 32, "level": 5},
        {"number": 53, "level": 7},
        {"number": 54, "level": 7},
        {"number": 55, "level": 7}
    ]
    current_booking = {"spot_number": "04", "start_time": "12:32 PM"}
    booking_history = [
        {"spot_number":"04", "start_time": "12:32 PM", "end_time": "01:45 PM"},
        {"spot_number":"43", "start_time": "2:30 PM", "end_time": "01:40 PM"},
        {"spot_number":"12", "start_time": "12:15 PM", "end_time": "01:32 PM"}
    ]
    
    return render_template(
        'user_dashboard.html',
        available_spots=available_spots,        # list of dicts or objects with `.number`, `.level`
        current_booking=current_booking,        # object or None with `.spot_number`, `.start_time`
        booking_history=booking_history         # list of bookings with `.spot_number`, `.start_time`, `.end_time`
    )


@user_bp.route('/user/bookspot')
def user_bookspot():
    return render_template("<h1>Booking spot for parking</h1>")

@user_bp.route('/user/release-spot')
def release_spot():
    return render_template("<h1>Releasing booked spot</h1>")