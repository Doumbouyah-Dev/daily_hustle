from marshmallow import Schema, fields, post_load
from ..models import ServiceAddOn


class ServiceAddOnSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    price = fields.Float(required=True)
    service_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_load
    def make_addon(self, data, **kwargs):
        return ServiceAddOn(**data)
