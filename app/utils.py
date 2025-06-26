# app/utils.py
from datetime import datetime

def calculate_duration(start, end):
    """Returns duration in hours (float)."""
    return round((end - start).total_seconds() / 3600, 2)

def calculate_charges(duration, rate_per_hour):
    return round(duration * rate_per_hour, 2)

def get_user_history(user_id, ParkingRecord):
    return ParkingRecord.query.filter_by(user_id=user_id).order_by(ParkingRecord.start_time.desc()).all()

def get_parking_summary(user_id, ParkingRecord):
    summary = {}
    records = ParkingRecord.query.filter_by(user_id=user_id, status='released').all()
    for rec in records:
        date_str = rec.start_time.date().isoformat()
        duration = calculate_duration(rec.start_time, rec.end_time)
        summary[date_str] = summary.get(date_str, 0) + duration
    return summary

def auto_allot_spot(ParkingSpot, lot_id):
    return ParkingSpot.query.filter_by(id=lot_id, is_available=True).first()
