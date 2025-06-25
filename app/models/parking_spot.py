# app/models/parking_spot.py

from app import db

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.String(20))
    is_available = db.Column(db.Boolean, default=True)
    rate_per_hour = db.Column(db.Float, default=10.0)

    # One-to-one with reservation (optional)
    reservation = db.relationship('Reservation', backref='spot', uselist=False)
