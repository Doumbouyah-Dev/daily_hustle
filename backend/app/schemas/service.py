from marshmallow import Schema, fields, validate, post_load
from ..models import Service, PricingModel


class ServiceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    category_id = fields.Int(required=True)
    pricing_model = fields.Str(validate=validate.OneOf([e.name for e in PricingModel]))
    base_price = fields.Float(required=True)
    unit_label = fields.Str()
    estimated_duration = fields.Int()
    requires_materials = fields.Bool()
    has_add_ons = fields.Bool()
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_load
    def make_service(self, data, **kwargs):
        return Service(**data)
