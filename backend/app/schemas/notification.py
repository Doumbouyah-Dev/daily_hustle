from marshmallow import Schema, fields, post_load
from ..models import Notifications

class NotificationSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    message = fields.Str(required=True)
    is_read = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

    @post_load
    def make_notification(self, data, **kwargs):
        return Notifications(**data)
