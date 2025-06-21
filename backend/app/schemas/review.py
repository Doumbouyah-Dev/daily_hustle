from marshmallow import Schema, fields, post_load
from ..models import Review

class ReviewSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    provider_id = fields.Int(required=True)
    booking_id = fields.Int(required=True)
    rating = fields.Int(required=True)
    comment = fields.Str()
    created_at = fields.DateTime(dump_only=True)

    @post_load
    def make_review(self, data, **kwargs):
        return Review(**data)
