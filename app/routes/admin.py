# app/routes/admin.py
from app.models import User, ParkingLot, ParkingSpot, ParkingRecord
from app import db
from flask import Blueprint, render_template, session, redirect, url_for,request,flash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/base')
def base():
    return render_template('admin_base.html')



@admin_bp.route('/')
def home():
    lots = ParkingLot.query.all()
    parking_lots = []

    for lot in lots:
        # Get all spots related to this lot
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

        # Add parking record reference if the spot is occupied
        for spot in spots:
            if not spot.is_available:
                spot.record = ParkingRecord.query.filter_by(spot_id=spot.id, end_time=None).first()
            else:
                spot.record = None

        # Add extra computed values directly to the model
        lot.spots = spots
        lot.occupied_count = sum(1 for s in spots if not s.is_available)
        lot.total_spots = len(spots)

        # Append the full lot object
        parking_lots.append(lot)

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

    # Get form values
    new_name = request.form['name']
    new_address = request.form['address']
    new_pin = request.form['pin']
    new_rate = float(request.form['rate'])
    new_total_spots = int(request.form['max_spots'])

    # Update basic fields
    lot.name = new_name
    lot.address = new_address
    lot.pin = new_pin
    lot.rate = new_rate

    # Adjust parking spots
    current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    current_count = len(current_spots)

    if new_total_spots > current_count:
        # Add new empty spots
        for i in range(current_count + 1, new_total_spots + 1):
            new_spot = ParkingSpot(
                lot_id=lot.id,
                spot_number=f"S{i:03}",
                is_available=True
            )
            db.session.add(new_spot)
    elif new_total_spots < current_count:
        # Remove extra spots (only if available)
        removable_spots = [s for s in current_spots if s.is_available]
        to_remove = current_count - new_total_spots

        if len(removable_spots) < to_remove:
            flash("Cannot reduce max spots — too many spots are occupied.", "danger")
            return redirect(url_for('admin.home'))

        for spot in removable_spots[:to_remove]:
            db.session.delete(spot)

    # Finally update total_spots
    lot.total_spots = new_total_spots

    db.session.commit()
    flash("Parking lot updated successfully.", "success")
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


@admin_bp.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    # Check for occupied spots (optional)
    occupied = any(not spot.is_available for spot in lot.spots)
    if occupied:
        flash("Cannot delete lot with occupied spots.", "danger")
        return redirect(url_for('admin.home'))

    db.session.delete(lot)
    db.session.commit()
    flash("Parking lot deleted successfully.", "success")
    return redirect(url_for('admin.home'))


@admin_bp.route('/delete-spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    db.session.delete(spot)
    db.session.commit()
    return redirect(url_for('admin.home'))
