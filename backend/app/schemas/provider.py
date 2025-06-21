from marshmallow import Schema, fields, post_load, validate
from ..models import Users, UserRole


class ProviderSchema(Schema):
    id = fields.Int(dump_only=True)
    firstname = fields.Str(required=True)
    lastname = fields.Str(required=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str(required=True)
    address = fields.Str()
    gender = fields.Str(validate=validate.OneOf(["Male", "Female", "Other"]))
    is_verified = fields.Bool(dump_only=True)
    is_active = fields.Bool()
    role = fields.Str(dump_only=True)  # Always PROVIDER
    password = fields.Str(load_only=True, required=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_load
    def make_provider(self, data, **kwargs):
        data["role"] = UserRole.PROVIDER  # Enforce provider role
        return Users(**data)
