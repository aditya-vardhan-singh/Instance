# app/models/reservation.py

from app import db
from datetime import datetime

class Reservation(db.Model):
    __tablename__ = 'reservation'

    reservation_id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.spot_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
