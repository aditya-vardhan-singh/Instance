# app/models/parking_lot.py

from app import db
from datetime import datetime

class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    pin = db.Column(db.String(6), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    total_spots = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-many relationship
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')
    
    @property
    def available_spots(self):
        return sum(1 for spot in self.spots if spot.is_available)
    
    @property
    def occupied_spots(self):
        return self.total_spots - self.available_spots
