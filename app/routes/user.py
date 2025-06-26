from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime, timedelta
from app.models import User, ParkingLot, ParkingSpot, ParkingRecord
from app import db
from collections import namedtuple

user_bp = Blueprint('user', __name__, url_prefix='/user')


# Define mock structure
Lot = namedtuple('Lot', ['location'])
Record = namedtuple('Record', ['id', 'lot', 'vehicle_no', 'start_time', 'status', 'spot_id', 'charge'])

@user_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Sample user
    user = {
        'id': 1,
        'name': 'Aditya'
    }

    # Sample records
    history = [
        Record(
            id=101,
            lot=Lot(location='Chatori Gali'),
            vehicle_no='UP32FZ0001',
            start_time=datetime.now() - timedelta(hours=2),
            status='parked',
            spot_id='A303-126',
            charge=None
        ),
        Record(
            id=102,
            lot=Lot(location='Cyber Hub'),
            vehicle_no='DL8CAF7865',
            start_time=datetime.now() - timedelta(days=1, hours=3),
            status='released',
            spot_id='A404-011',
            charge=40.00
        )
    ]
    
    return render_template(
        'user_home.html',
        user=user,
        history=history,
        parking_lots=None,
    )

@user_bp.route('/search')
def search_parking():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    location = request.args.get('location')
    user = User.query.get(session['user_id'])
    history = ParkingRecord.query.filter_by(user_id=user.id).order_by(ParkingRecord.start_time.desc()).all()
    
    parking_lots = ParkingLot.query.filter(ParkingLot.location.ilike(f'%{location}%')).all()

    return render_template('user_home.html', user=user, history=history, parking_lots=parking_lots, search_location=location)



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
    return redirect(url_for('user.dashboard'))



@user_bp.route('/release/<int:id>')
def release_spot(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    record = ParkingRecord.query.get_or_404(id)

    if record.status != 'parked':
        flash('This spot is already released.', 'info')
        return redirect(url_for('user.dashboard'))

    record.end_time = datetime.utcnow()
    record.status = 'released'

    # Mark the spot as available again
    spot = ParkingSpot.query.get(record.spot_id)
    spot.is_available = True

    # Calculate charge (for demo purposes, ₹10 per hour)
    duration_hours = max((record.end_time - record.start_time).total_seconds() / 3600, 1)
    record.charge = round(duration_hours * spot.rate_per_hour, 2)

    db.session.commit()

    flash(f'Spot released. Charge: ₹{record.charge}', 'success')
    return redirect(url_for('user.dashboard'))


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
