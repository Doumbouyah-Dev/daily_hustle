from flask import request
from flask_restful import Resource
from ..models import Booking
from ..schemas.booking import BookingSchema
from app import db

booking_schema = BookingSchema()
booking_list_schema = BookingSchema(many=True)

class BookingResource(Resource):
    def get(self, booking_id):
        booking = Booking.query.get_or_404(booking_id)
        return booking_schema.dump(booking), 200

    def put(self, booking_id):
        booking = Booking.query.get_or_404(booking_id)
        data = request.get_json()
        for field in ["status", "scheduled_date", "scheduled_time", "address", "notes"]:
            setattr(booking, field, data.get(field, getattr(booking, field)))
        db.session.commit()
        return booking_schema.dump(booking), 200

    def delete(self, booking_id):
        booking = Booking.query.get_or_404(booking_id)
        db.session.delete(booking)
        db.session.commit()
        return {"message": "Booking cancelled"}, 204

class BookingListResource(Resource):
    def get(self):
        return booking_list_schema.dump(Booking.query.all()), 200

    def post(self):
        data = request.get_json()
        new_booking = booking_schema.load(data)
        db.session.add(new_booking)
        db.session.commit()
        return booking_schema.dump(new_booking), 201
