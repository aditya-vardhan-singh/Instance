from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from datetime import datetime, timedelta
from app.models import User, ParkingLot, ParkingSpot, ParkingRecord
from app import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    history = ParkingRecord.query.filter_by(user_id=user_id).order_by(ParkingRecord.start_time.desc()).all()
    
    return render_template('user_home.html', user=user, history=history, parking_lots=None, search_location=None)

# This route is CRITICAL - your JavaScript calls this
@user_bp.route('/available_spot/<int:lot_id>')
def available_spot(lot_id):
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, is_available=True).first()
    if spot:
        return jsonify({"spot_id": spot.id})
    else:
        return jsonify({"spot_id": None, "error": "No available spots"})

@user_bp.route('/reserve_spot', methods=['POST'])
def reserve_spot():
    # Debug: Show what we received
    flash(f"DEBUG: Form data received: {dict(request.form)}", 'info')
    
    if 'user_id' not in session:
        flash('Please login to reserve a spot.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get form data
    spot_id = request.form.get('spot_id')
    lot_id = request.form.get('lot_id')
    user_id = request.form.get('user_id')
    vehicle_no = request.form.get('vehicle_no')
    
    # Debug: Check what we extracted
    flash(f"DEBUG: Extracted - spot_id: {spot_id}, lot_id: {lot_id}, user_id: {user_id}, vehicle_no: {vehicle_no}", 'info')

    # Validate inputs
    if not all([spot_id, lot_id, user_id, vehicle_no]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Convert to integers
    try:
        spot_id = int(spot_id)
        lot_id = int(lot_id)
        user_id = int(user_id)
    except ValueError:
        flash('Invalid data provided.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Check if spot exists and is available
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        flash(f'Spot {spot_id} not found.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    if not spot.is_available:
        flash(f'Spot {spot_id} is not available.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Check if user already has an active reservation
    existing_record = ParkingRecord.query.filter_by(user_id=user_id, status='parked').first()
    if existing_record:
        flash('You already have an active parking reservation.', 'warning')
        return redirect(url_for('user.dashboard'))

    # Create new parking record
    try:
        new_record = ParkingRecord(
            user_id=user_id,
            lot_id=lot_id,
            spot_id=spot_id,
            vehicle_no=vehicle_no,
            start_time=datetime.utcnow(),
            status='parked'
        )

        # Mark spot as unavailable
        spot.is_available = False

        db.session.add(new_record)
        db.session.commit()

        flash(f'SUCCESS: Parking spot {spot_id} reserved successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'ERROR: Failed to reserve spot - {str(e)}', 'danger')
    
    return redirect(url_for('user.dashboard'))

@user_bp.route('/search', methods=['GET'])
def search_parking():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    location = request.args.get('name')
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    parking_lots = ParkingLot.query.filter(ParkingLot.address.ilike(f"%{location}%")).all()

    # Add available spot count
    for lot in parking_lots:
        lot.available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_available=True).count()

    history = ParkingRecord.query.filter_by(user_id=user_id).order_by(ParkingRecord.start_time.desc()).all()

    return render_template('user_home.html', user=user, history=history,
                           parking_lots=parking_lots, search_location=location)

@user_bp.route('/release/<int:record_id>', methods=['POST'])
def release_parking(record_id):
    if 'user_id' not in session:
        flash('Please login to release a spot.', 'danger')
        return redirect(url_for('auth.login'))
    
    record = ParkingRecord.query.get_or_404(record_id)

    # Check ownership
    if record.user_id != session['user_id']:
        flash('You can only release your own parking spots.', 'danger')
        return redirect(url_for('user.dashboard'))

    if record.status == 'released':
        flash("This spot has already been released.", "info")
        return redirect(url_for('user.dashboard'))

    try:
        record.status = 'released'
        record.end_time = datetime.utcnow()

        # Calculate charges
        duration = (record.end_time - record.start_time).total_seconds() / 3600
        lot = ParkingLot.query.get(record.lot_id)
        record.charge = round(duration * lot.rate, 2)

        # Mark spot as available
        spot = ParkingSpot.query.get(record.spot_id)
        spot.is_available = True

        db.session.commit()
        flash(f"Parking spot released successfully. Charge: ₹{record.charge}", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error releasing spot: {str(e)}', 'danger')
    
    return redirect(url_for('user.dashboard'))

@user_bp.route('/summary')
def summary():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    records = ParkingRecord.query.filter_by(user_id=user_id).all()

    daily_data = {}
    for rec in records:
        if rec.status == 'released' and rec.start_time and rec.end_time:
            day = rec.start_time.date().isoformat()
            duration = (rec.end_time - rec.start_time).total_seconds() / 3600
            daily_data[day] = daily_data.get(day, 0) + round(duration, 2)

    chart_labels = list(daily_data.keys())
    chart_data = list(daily_data.values())

    return render_template('user_summary.html', chart_labels=chart_labels, chart_data=chart_data)

# Quick test route to verify basic functionality
@user_bp.route('/test_form', methods=['GET', 'POST'])
def test_form():
    if request.method == 'POST':
        flash(f"Test form received: {dict(request.form)}", 'info')
        return redirect(url_for('user.dashboard'))
    
    return '''
    <form method="POST">
        <input type="text" name="test_field" value="test_value" required>
        <button type="submit">Test Submit</button>
    </form>
    '''