from marshmallow import Schema, fields, post_load
from ..models import Payment

class PaymentSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    booking_id = fields.Int(required=True)
    amount = fields.Float(required=True)
    payment_method = fields.Str(required=True)
    status = fields.Str(required=True)  # e.g. pending, completed, failed
    transaction_ref = fields.Str()
    created_at = fields.DateTime(dump_only=True)

    @post_load
    def make_payment(self, data, **kwargs):
        return Payment(**data)
