

from marshmallow import Schema, fields, post_load
from ..models import ServiceCategory


class ServiceCategorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

    @post_load
    def make_category(self, data, **kwargs):
        return ServiceCategory(**data)
