from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime, timedelta
from app.models import User, ParkingLot, ParkingSpot, ParkingRecord
from app import db
from collections import namedtuple

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)

    # Fetch parking history
    history = ParkingRecord.query.filter_by(user_id=user_id).order_by(ParkingRecord.start_time.desc()).all()
    print("User ID from session:", user_id)
    print("User from DB:", user)


    return render_template('user_home.html', user=user, history=history, parking_lots=None, search_location=None)

@user_bp.route('/search', methods=['GET'])
def search_parking():
    location = request.args.get('name')
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    parking_lots = ParkingLot.query.filter(ParkingLot.address.ilike(f"%{location}%")).all()

    # Dynamically attach available spot count
    for lot in parking_lots:
        lot.available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_available=True).count()

    history = ParkingRecord.query.filter_by(user_id=user_id).order_by(ParkingRecord.start_time.desc()).all()

    return render_template('user_home.html', user=user, history=history,
                           parking_lots=parking_lots, search_location=location)
    
    
@user_bp.route('/available_spot/<int:lot_id>')
def available_spot(lot_id):
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='available').first()
    if spot:
        return jsonify({'spot_id': spot.id})
    return jsonify({'spot_id': None})
    

@user_bp.route('/reserve_spot', methods=['POST'])
def reserve_spot():
    spot_id = request.form.get('spot_id')
    lot_id = request.form.get('lot_id')
    user_id = request.form.get('user_id')
    vehicle_no = request.form.get('vehicle_no')

    spot = ParkingSpot.query.get(spot_id)
    if not spot or not spot.is_available:
        flash('Spot is not available. Please try another one.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Create new parking record
    new_record = ParkingRecord(
        user_id=user_id,
        lot_id=lot_id,
        spot_id=spot_id,
        vehicle_no=vehicle_no,
        status='parked'
    )
    
    print('Spot ID:', spot_id)
    print('Spot exists:', bool(spot))
    print('Is available:', spot.is_available if spot else 'N/A')


    # Mark the spot as unavailable
    spot.is_available = False

    db.session.add(new_record)
    db.session.commit()

    flash('Parking spot reserved successfully!', 'success')
    return redirect(url_for('user_home.html'))


@user_bp.route('/book/<int:lot_id>', methods=['POST'])
def book_spot(lot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    spot = ParkingSpot.query.filter_by(lot_id=lot.id, is_available=True).first()

    if not spot:
        flash('No spots available in this lot.', 'warning')
        return redirect(url_for('user.dashboard'))

    vehicle_no = request.form.get('vehicle_no')

    if not vehicle_no:
        flash('Vehicle number is required.', 'danger')
        return redirect(url_for('user.dashboard'))

    spot.is_available = False

    new_record = ParkingRecord(
        user_id=session['user_id'],
        lot_id=lot.id,
        spot_id=spot.id,
        vehicle_no=vehicle_no,
        start_time=datetime.utcnow(),
        status='parked'
    )

    db.session.add(new_record)
    db.session.commit()

    flash('Spot booked successfully!', 'success')
    return redirect(url_for('user.user_home'))



# @user_bp.route('/release/<int:id>')
# def release_spot(id):
#     if 'user_id' not in session:
#         return redirect(url_for('auth.login'))
    
#     record = ParkingRecord.query.get_or_404(id)

#     if record.status != 'parked':
#         flash('This spot is already released.', 'info')
#         return redirect(url_for('user.dashboard'))

#     record.end_time = datetime.utcnow()
#     record.status = 'released'

#     # Mark the spot as available again
#     spot = ParkingSpot.query.get(record.spot_id)
#     spot.is_available = True

#     # Calculate charge (for demo purposes, ₹10 per hour)
#     duration_hours = max((record.end_time - record.start_time).total_seconds() / 3600, 1)
#     record.charge = round(duration_hours * spot.rate_per_hour, 2)

#     db.session.commit()

#     flash(f'Spot released. Charge: ₹{record.charge}', 'success')
#     return redirect(url_for('user.dashboard'))


@user_bp.route('/release/<int:record_id>', methods=['POST'])
def release_parking(record_id):
    record = ParkingRecord.query.get_or_404(record_id)

    if record.status == 'released':
        flash("This spot has already been released.", "info")
        return redirect(url_for('user.user_dashboard'))

    record.status = 'released'
    record.end_time = datetime.utcnow()

    # Calculate charges (example: hourly rate * hours)
    duration = (record.end_time - record.start_time).total_seconds() / 3600
    lot = ParkingLot.query.get(record.lot_id)
    record.charge = round(duration * lot.rate, 2)

    # Mark spot as available again
    spot = ParkingSpot.query.get(record.spot_id)
    spot.is_available = True

    db.session.commit()
    flash("Parking spot released successfully.", "success")
    return redirect(url_for('user.user_home'))


@user_bp.route('/summary')
def summary():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    records = ParkingRecord.query.filter_by(user_id=user_id).all()

    # Build chart data: hours parked per day
    daily_data = {}
    for rec in records:
        if rec.status == 'released' and rec.start_time and rec.end_time:
            day = rec.start_time.date().isoformat()
            duration = (rec.end_time - rec.start_time).total_seconds() / 3600
            daily_data[day] = daily_data.get(day, 0) + round(duration, 2)

    chart_labels = list(daily_data.keys())
    chart_data = list(daily_data.values())

    return render_template('user_summary.html', chart_labels=chart_labels, chart_data=chart_data)
