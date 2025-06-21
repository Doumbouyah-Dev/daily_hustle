from marshmallow import Schema, fields, validate, post_load, ValidationError
from app.models import UserRole, VerificationStatus # Import enums from models


# Base User Schema - defines common fields for dumping/loading user data
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.String(required=True, validate=validate.Length(min=4, max=50))
    email = fields.Email(required=True)
    firstname = fields.String(validate=validate.Length(max=50))
    lastname = fields.String(validate=validate.Length(max=50))
    gender = fields.String(validate=validate.OneOf(["Male", "Female", "Other"]))
    phone = fields.String(validate=validate.Regexp(r'^\+?[0-9]{7,15}$')) # Basic phone number validation
    role = fields.String(dump_only=True, validate=validate.OneOf([e.value for e in UserRole])) # Role should be dumped as string
    is_verified = fields.Boolean(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    address = fields.String(validate=validate.Length(max=200))
    timestamp = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    last_login_at = fields.DateTime(dump_only=True)
    email_verified_at = fields.DateTime(dump_only=True)
    phone_verified_at = fields.DateTime(dump_only=True)

    class Meta:
        # Explicitly define fields here to ensure they are available for inheritance
        fields = (
            "id", "username", "email", "firstname", "lastname", "gender", "phone",
            "role", "is_verified", "is_active", "address", "timestamp", "updated_at",
            "last_login_at", "email_verified_at", "phone_verified_at"
        )


# Schema for user registration
class UserRegisterSchema(UserSchema):
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    confirm_password = fields.String(required=True, load_only=True)

    class Meta(UserSchema.Meta):
        # Extend fields from UserSchema.Meta and add password-related fields
        # Ensure 'password' and 'confirm_password' are load_only
        fields = UserSchema.Meta.fields + ("password", "confirm_password")

    @post_load
    def validate_passwords(self, data, **kwargs):
        if data["password"] != data["confirm_password"]:
            raise ValidationError("Passwords do not match.", "confirm_password")
        data.pop("confirm_password") # Remove confirm_password before loading into model
        return data


# Schema for user login
class UserLoginSchema(Schema):
    username = fields.String(load_only=True, validate=validate.Length(min=4, max=50))
    email = fields.Email(load_only=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))

    @post_load
    def require_username_or_email(self, data, **kwargs):
        if not data.get("username") and not data.get("email"):
            raise ValidationError("Username or email is required.", "username")
        return data


# Schema for updating a user's own profile (non-admin)
class UserProfileUpdateSchema(Schema):
    firstname = fields.String(validate=validate.Length(max=50))
    lastname = fields.String(validate=validate.Length(max=50))
    email = fields.Email()
    gender = fields.String(validate=validate.OneOf(["Male", "Female", "Other"]))
    address = fields.String(validate=validate.Length(max=200))
    phone = fields.String(validate=validate.Regexp(r'^\+?[0-9]{7,15}$'))

    @post_load
    def ensure_update_data(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided for update.", "_schema")
        return data


# Schema for admin updating a user (includes role and active status)
class UserAdminUpdateSchema(UserProfileUpdateSchema):
    role = fields.String(validate=validate.OneOf([e.value for e in UserRole]))
    is_active = fields.Boolean()
    is_verified = fields.Boolean() # Admin can toggle verification status


# Schema for user to change their password
class UserPasswordChangeSchema(Schema):
    old_password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    new_password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    confirm_new_password = fields.String(required=True, load_only=True)

    @post_load
    def validate_passwords(self, data, **kwargs):
        if data["new_password"] != data["confirm_new_password"]:
            raise ValidationError("New password and confirmation do not match.", "confirm_new_password")
        return data


# Schema for requesting a password reset (providing email)
class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True)


# Schema for confirming password reset with token and new password
class PasswordResetConfirmSchema(Schema):
    token = fields.String(required=True)
    new_password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    confirm_new_password = fields.String(required=True, load_only=True)

    @post_load
    def validate_passwords(self, data, **kwargs):
        if data["new_password"] != data["confirm_new_password"]:
            raise ValidationError("New password and confirmation do not match.", "confirm_new_password")
        return data


# Schema for a user requesting a role change (e.g., customer to provider)
class UserRoleRequestSchema(Schema):
    # Only allow requesting Provider or B2B_CLIENT roles, not Admin
    requested_role = fields.String(required=True, validate=validate.OneOf([UserRole.PROVIDER.value, UserRole.B2B_CLIENT.value]))
    # Optional message for the admin reviewing the request
    message = fields.String(validate=validate.Length(max=500))


# Schema for admin to approve/reject a role change request
class RoleChangeApprovalSchema(Schema):
    action = fields.String(required=True, validate=validate.OneOf(["approve", "reject"]))
    # Optional notes from admin
    admin_notes = fields.String(validate=validate.Length(max=500))


# Schema for Provider-specific profile fields
class ProviderProfileSchema(Schema):
    bio = fields.String(validate=validate.Length(max=500))
    is_available = fields.Boolean()
    service_radius = fields.Float()
    service_area_description = fields.String(validate=validate.Length(max=255))
    # Admin can update verification status
    verification_status = fields.String(validate=validate.OneOf([e.value for e in VerificationStatus]))
    verification_document_url = fields.URL() # Assuming this is a URL to a document
    rating = fields.Float(dump_only=True) # Rating is aggregated, not directly set via schema

    class Meta:
        fields = (
            "bio", "is_available", "service_radius", "service_area_description",
            "verification_status", "verification_document_url", "rating"
        )


class UserUpdateSchema(Schema):
    firstname = fields.Str()
    lastname = fields.Str()
    email = fields.Email()
    address = fields.Str()
    phone = fields.Str()
    gender = fields.Str()
    # role = fields.Str(validate=validate.OneOf([e.value for e in UserRole]))