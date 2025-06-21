from marshmallow import Schema, fields, post_load
from ..models import Booking

class BookingSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    provider_id = fields.Int(required=True)
    service_id = fields.Int(required=True)
    status = fields.Str(required=True)
    scheduled_date = fields.Date(required=True)
    scheduled_time = fields.Time(required=True)
    address = fields.Str(required=True)
    notes = fields.Str()
    total_price = fields.Float()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_load
    def make_booking(self, data, **kwargs):
        return Booking(**data)
