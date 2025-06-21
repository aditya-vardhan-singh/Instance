# app/models/parking_spot.py

from app import db

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'

    spot_id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.lot_id'), nullable=False)
    status = db.Column(db.String(1), default='A', nullable=False)  # A = Available, O = Occupied

    # One-to-one with reservation (optional)
    reservation = db.relationship('Reservation', backref='spot', uselist=False)
