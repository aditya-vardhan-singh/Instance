# app/routes/admin.py
from app.models import User, ParkingLot, ParkingSpot, ParkingRecord
from app import db
from flask import Blueprint, render_template, session, redirect, url_for,request,flash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# @admin_bp.route('/dashboard')
# def admin_dashboard():
#     if session.get('role') != 'admin':
#         return redirect(url_for('auth.login'))
    
#     all_spots = [
#         {"number": "A101", "level": "1", "is_occupied": True},
#         {"number": "A102", "level": "1", "is_occupied": False},
#         {"number": "B201", "level": "2", "is_occupied": True},
#         {"number": "B202", "level": "2", "is_occupied": False},
#         {"number": "C301", "level": "3", "is_occupied": False},
#     ]

#     from datetime import datetime, timedelta

#     all_bookings = [
#         {
#             "user_email": "alice@example.com",
#             "spot_number": "A101",
#             "start_time": datetime.now() - timedelta(hours=2),
#             "end_time": None  # Ongoing
#         },
#         {
#             "user_email": "bob@example.com",
#             "spot_number": "B201",
#             "start_time": datetime.now() - timedelta(days=1, hours=3),
#             "end_time": datetime.now() - timedelta(days=1)
#         },
#         {
#             "user_email": "charlie@example.com",
#             "spot_number": "A102",
#             "start_time": datetime.now() - timedelta(days=2),
#             "end_time": datetime.now() - timedelta(days=2, hours=-2)
#         },
#     ]
    
#     from datetime import datetime, timedelta

#     # Fake data for 7 days
#     today = datetime.today()
#     daily_labels = [(today - timedelta(days=i)).strftime('%d %b') for i in reversed(range(7))]
#     daily_counts = [2, 4, 1, 3, 0, 5, 6]  # Replace with real count logic

#     daily_booking_data = {
#         'labels': daily_labels,
#         'counts': daily_counts
#     }
    
#     analytics={
#         'total_spots': 100,
#         'occupied_spots': 30,
#         'total_users': 50,
#         'active_bookings': 20
#     }

    
#     return render_template(
#         'admin_dashboard.html',
#         all_spots=all_spots,
#         all_bookings=all_bookings,
#         analytics=analytics,
#         daily_booking_data=daily_booking_data
#     )

@admin_bp.route('/base')
def base():
    return render_template('admin_base.html')

@admin_bp.route('/')
def home():
    lots = ParkingLot.query.all()
    parking_lots = []

    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

        for spot in spots:
            if not spot.is_available:
                # Attach the active (not yet released) parking record
                spot.record = ParkingRecord.query.filter_by(spot_id=spot.id, end_time=None).first()
            else:
                spot.record = None  # Optional: make it consistent

        occupied = sum(1 for s in spots if not s.is_available)

        parking_lots.append({
            'id': lot.id,
            'name': lot.name,
            'spots': spots,
            'occupied_count': occupied,
            'total_spots': len(spots)
        })

    return render_template('admin_home.html', parking_lots=parking_lots)



@admin_bp.route('/users')
def users():
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)


@admin_bp.route('/search', methods=['GET'])
def search():
    search_by = request.args.get('search_by')
    query = request.args.get('query')
    results = None

    if search_by and query:
        if search_by == 'user_id':
            results = ParkingRecord.query.filter_by(user_id=query).all()

        elif search_by == 'parking_lot':
            lots = ParkingLot.query.filter(ParkingLot.name.ilike(f"%{query}%")).all()
            # Include spot stats like dashboard
            results = []
            for lot in lots:
                spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                occupied = sum(1 for s in spots if not s.is_available)
                lot.spots = spots
                lot.occupied_count = occupied
                lot.total_spots = len(spots)
                results.append(lot)

        elif search_by == 'parking_spot':
            spot = ParkingSpot.query.filter_by(id=query).first()
            if spot and not spot.is_available:
                spot.record = ParkingRecord.query.filter_by(spot_id=spot.id, end_time=None).first()
            results = spot

    return render_template("admin_search.html", search_by=search_by, query=query, results=results)


@admin_bp.route('/summary')
def summary():
    lots = ParkingLot.query.all()

    labels = []
    available_data = []
    occupied_data = []
    revenue_data = []

    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        spot_ids = [s.id for s in spots]

        # Stats
        total = len(spots)
        occupied = sum(1 for s in spots if not s.is_available)
        available = total - occupied

        # Revenue from records
        records = ParkingRecord.query.filter(ParkingRecord.spot_id.in_(spot_ids)).all()
        total_revenue = sum((r.estimated_cost or 0) for r in records)
        total_bookings = len(records)

        # Append chart + revenue info
        labels.append(lot.name)
        available_data.append(available)
        occupied_data.append(occupied)
        revenue_data.append({
            'name': lot.name,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue
        })

    return render_template(
        "admin_summary.html",
        labels=labels,
        available_data=available_data,
        occupied_data=occupied_data,
        revenue_data=revenue_data
    )


@admin_bp.route('/edit/<int:lot_id>', methods=['POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    lot.name = request.form['name']
    lot.address = request.form['address']
    lot.pin = request.form['pin']
    lot.rate = float(request.form['rate'])
    lot.total_spots = int(request.form['max_spots'])
    db.session.commit()
    return redirect(url_for('admin.home'))

@admin_bp.route('/add', methods=['POST'])
def add_lot():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    # Extract form data
    name = request.form.get('name')
    address = request.form.get('address')
    pin = request.form.get('pin')
    rate = float(request.form.get('rate'))
    max_spots = int(request.form.get('max_spots'))

    # Step 1: Create the Parking Lot
    new_lot = ParkingLot(name=name, address=address, pin=pin, rate=rate)
    db.session.add(new_lot)
    db.session.commit()

    # Step 2: Auto-create empty parking spots
    for i in range(1, max_spots + 1):
        spot = ParkingSpot(
            lot_id=new_lot.id,
            spot_number=f"S{i:03}",  # Format like S001, S002...
            is_available=True
        )
        db.session.add(spot)

    db.session.commit()
    flash("Parking lot added successfully with empty spots.", "success")
    return redirect(url_for('admin.home'))


@admin_bp.route('/delete-spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if not spot.is_available:
        flash("Cannot delete an occupied spot.", "danger")
        return redirect(url_for('admin.home'))
    
    db.session.delete(spot)
    db.session.commit()
    flash("Parking spot deleted successfully.", "success")
    return redirect(url_for('admin.home'))
