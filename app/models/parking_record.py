from datetime import datetime
from app import db

class ParkingRecord(db.Model):
    __tablename__ = 'parking_record'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'))
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    vehicle_no = db.Column(db.String(20))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='parked')  # parked, released, cancelled
    charge = db.Column(db.Float, default=0.0)

    # Relationships
    lot = db.relationship('ParkingLot', backref='records')
    user = db.relationship('User', backref='parking_records')

    @property
    def duration(self):
        if self.end_time:
            return round((self.end_time - self.start_time).total_seconds() / 3600, 2)
        return None

    @property
    def is_active(self):
        return self.status == 'parked'
        return self.status == 'parked'
