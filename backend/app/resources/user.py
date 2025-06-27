
# app/resources/user.py
from flask_restful import Resource, reqparse
from flask import request, jsonify, g
from app.models import Users, UserRole, Provider, VerificationStatus # Import Provider model
from app.schemas.user import (
    UserSchema,
    UserProfileUpdateSchema,
    UserAdminUpdateSchema,
    UserRoleRequestSchema,    # Corrected: for user's role request
    RoleChangeApprovalSchema, # Corrected: for admin's approval of role change
    ProviderProfileSchema,
    UserUpdateSchema     # Added for provider profile updates
)
from app import db
from flask_jwt_extended import jwt_required
from app.utils.decorators import jwt_required_wrapper, role_required
from app.utils.decorators import jwt_blacklist # Assuming this is available if needed for token revocation

user_schema = UserSchema()
user_update_schema = UserUpdateSchema()
requested_role_enum = UserRoleRequestSchema()


class UserDetailResource(Resource):
    def get(self, user_id):
        user = Users.query.get_or_404(user_id)
        return user_schema.dump(user), 200

    def delete(self, user_id):
        user = Users.query.get_or_404(user_id)
        user.delete_from_db()
        return {"message": "User deleted"}, 204

class UserProfileUpdateResource(Resource):
    def put(self, user_id):
        user = Users.query.get_or_404(user_id)
        data = user_update_schema.load(request.get_json(), partial=True)
        if not isinstance(data, dict):
            return {"message": "Invalid input data."}, 400
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        return user_schema.dump(user), 200

# Resource for listing all users (Admin only) or self (jwt_required_wrapper handles G.user context)
class UserListResource(Resource):
    @role_required(UserRole.ADMIN)
    def get(self):
        users = Users.query.all()
        # Exclude sensitive fields like password hash from schema dump
        return UserSchema(many=True).dump(users), 200


# Resource for a single user (GET, PUT, DELETE)
class UserResource(Resource):
    @jwt_required_wrapper
    def get(self, user_id):
        user = Users.find_by_id(user_id)
        if not user:
            return {"message": "User not found"}, 404

        # Authorization: User can only view their own profile, or admin can view any
        if g.user.id != user.id and g.user.role != UserRole.ADMIN:
            return {"message": "Unauthorized access"}, 403

        # Use UserSchema for dumping data
        return UserSchema().dump(user), 200

    @jwt_required_wrapper
    def put(self, user_id):
        user = Users.find_by_id(user_id)
        if not user:
            return {"message": "User not found"}, 404

        # Determine which schema to use based on role and target user
        if g.user.role == UserRole.ADMIN:
            schema = UserAdminUpdateSchema(partial=True) # Allows partial updates, including is_active/role
        elif g.user.id == user.id:
            schema = UserProfileUpdateSchema(partial=True) # Standard user can update their profile
        else:
            return {"message": "Unauthorized access"}, 403

        try:
            data = schema.load(request.get_json()) # partial=True is set in schema init
        except Exception as err: # Catch Marshmallow ValidationError specifically if possible
            return {"message": str(err)}, 400

        # Prevent non-admins from changing their own role or is_active status
        if g.user.role != UserRole.ADMIN:
            if isinstance(data, dict) and ("role" in data or "is_active" in data or "is_verified" in data):
                return {"message": "Unauthorized to modify role, account status, or verification status"}, 403

        # Apply updates
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(user, key):
                    if key == "password": # This case is now handled by UserPasswordChangeResource
                        pass # Do nothing here, password changes should go to dedicated endpoint
                    elif key == "role": # Convert string role to UserRole enum
                        user.role = UserRole(value)
                    else:
                        setattr(user, key, value)
        else:
            return {"message": "Invalid input data."}, 400

        user.save_to_db()
        return {"message": "User updated successfully", "user": UserSchema().dump(user)}, 200

    @role_required(UserRole.ADMIN) # Only admin can "delete" (soft-delete) users
    def delete(self, user_id):
        user = Users.find_by_id(user_id)
        if not user:
            return {"message": "User not found"}, 404

        if not user.is_active:
            return {"message": "User is already deactivated"}, 400

        user.delete_from_db() # This will now set is_active=False
        return {"message": "User deactivated successfully"}, 200


# Resource for a user to request a role change (e.g., to Provider)

class UserRoleRequestResource(Resource):
    @jwt_required_wrapper
    def post(self): # Note: No user_id is needed in the method signature
        user = g.user # The user is the one making the request, from the JWT
        if user.role != UserRole.CUSTOMER:
            return {"message": "Only customers can request a role change."}, 400

        schema = UserRoleRequestSchema()
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        # Note: The original code used data["message"] for the bio, which is a bit odd.
        # A more explicit field in the schema like "bio" would be better, but we will follow the original logic.
        bio_message = data.get("message", "New provider registration.") 

        # Check if they are requesting to be a provider
        requested_role_enum = UserRole(data["requested_role"])
        if requested_role_enum != UserRole.PROVIDER:
            return {"message": "Role change requests are only supported for the Provider role at this time."}, 400

        # Check if a provider profile already exists
        if Provider.find_by_user_id(user.id):
            return {"message": "You already have a provider profile."}, 400

        # --- THIS IS THE CRITICAL LOGIC THAT WAS MISSING ---
        # Create a new Provider entry for the user
        provider = Provider(
            user_id=user.id, 
            bio=bio_message, 
            verification_status=VerificationStatus.PENDING
        )
        
        try:
            # Change the user's role and save both the user and new provider profile
            user.role = UserRole.PROVIDER
            db.session.add(provider)
            db.session.commit()
            
            # On success, return 201 Created
            return {"message": f"Provider profile created and is pending verification."}, 201

        except Exception as e:
            db.session.rollback() # Rollback the transaction on error
            app.logger.error(f"Error creating provider profile: {e}") # Log the error
            return {"message": "An internal error occurred while creating the provider profile."}, 500
        

# Resource for Admin to approve or reject role change requests
class UserRoleApprovalResource(Resource):
    @role_required(UserRole.ADMIN)
    def post(self, user_id):
        user = Users.find_by_id(user_id)
        if not user:
            return {"message": "User not found"}, 404

        schema = RoleChangeApprovalSchema() # Corrected: using RoleChangeApprovalSchema
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        if not isinstance(data, dict):
            return {"message": "Invalid input data."}, 400
        action = data.get("action")
        admin_notes = data.get("admin_notes")

        if action == "approve":
            # Assuming the role change was already initiated and user.role is e.g. UserRole.PROVIDER (pending verification)
            # This endpoint now handles the approval of the *verification* for a provider.
            if user.role == UserRole.PROVIDER:
                provider = Provider.find_by_user_id(user.id)
                if provider:
                    provider.verification_status = VerificationStatus.APPROVED
                    provider.save_to_db()
                    user.is_verified = True # Mark user as verified as well
                    user.save_to_db()
                    return {"message": f"User {user.username} (Provider) has been approved and verified."}, 200
                else:
                    return {"message": "Provider profile not found for this user."}, 404
            else:
                return {"message": "User is not a provider or not pending verification for a role."}, 400

        elif action == "reject":
            # If a provider's verification is rejected, you might set their status back or mark them as unverified
            if user.role == UserRole.PROVIDER:
                provider = Provider.find_by_user_id(user.id)
                if provider:
                    provider.verification_status = VerificationStatus.REJECTED
                    provider.save_to_db()
                    user.is_verified = False # Mark user as unverified
                    user.save_to_db()
                    return {"message": f"User {user.username} (Provider) verification has been rejected."}, 200
                else:
                    return {"message": "Provider profile not found for this user."}, 404
            else:
                return {"message": "Cannot reject role change for non-provider or unrequested role."}, 400
        else:
            return {"message": "Invalid action specified."}, 400


# Resource for Providers to update their specific profile fields
class ProviderProfileResource(Resource):
    @role_required(UserRole.PROVIDER) # Only a provider can update their provider profile
    def put(self):
        user = g.user # The authenticated user is the provider
        provider = Provider.find_by_user_id(user.id)

        if not provider:
            return {"message": "Provider profile not found for this user."}, 404

        schema = ProviderProfileSchema(partial=True)
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(provider, key):
                    if key == "verification_status": # Prevent providers from changing their own verification status
                        return {"message": "Unauthorized to modify verification status."}, 403
                    setattr(provider, key, value)
        else:
            return {"message": "Invalid input data."}, 400

        provider.save_to_db()
        return {"message": "Provider profile updated successfully", "provider": ProviderProfileSchema().dump(provider)}, 200

    @role_required(UserRole.PROVIDER)
    def get(self):
        user = g.user
        provider = Provider.find_by_user_id(user.id)
        if not provider:
            return {"message": "Provider profile not found."}, 404
        return ProviderProfileSchema().dump(provider), 200