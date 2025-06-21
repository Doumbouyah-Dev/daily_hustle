# # File: app/resources/user.py

# from flask import request
# from flask_restful import Resource
# from ..models import Users, UserRole

# from app import db
# from werkzeug.security import generate_password_hash, check_password_hash
# from ..utils.decorators import admin_required
# from app.schemas.user import UserProfileUpdateSchema, UserAdminUpdateSchema # Need a new schema for admin updates
# from app.utils.decorators import jwt_required_wrapper, role_required, UserRole # Import new decorator



# user_list_schema = UserSchema(many=True)

# role_change_schema = RoleChangeRequestSchema()


# class UserResource(Resource):
#     @jwt_required_wrapper
#     def get(self, user_id):
#         user = Users.find_by_id(user_id)
#         if not user:
#             return {"message": "User not found"}, 404

#         # Authorization: User can only view their own profile, or admin can view any
#         if g.user.id != user.id and g.user.role != UserRole.ADMIN:
#             return {"message": "Unauthorized access"}, 403

#         schema = UserProfileUpdateSchema() # Using this for dumping too, for now
#         return schema.dump(user), 200

#     @jwt_required_wrapper
#     def put(self, user_id):
#         user = Users.find_by_id(user_id)
#         if not user:
#             return {"message": "User not found"}, 404

#         # Determine which schema to use based on role and target user
#         if g.user.role == UserRole.ADMIN:
#             schema = UserAdminUpdateSchema(partial=True) # Allows partial updates, including is_active/role
#         elif g.user.id == user.id:
#             schema = UserProfileUpdateSchema(partial=True) # Standard user can update their profile
#         else:
#             return {"message": "Unauthorized access"}, 403

#         try:
#             data = schema.load(request.get_json(), partial=True) # partial=True for PUT
#         except Exception as err:
#             return {"message": str(err)}, 400

#         # Prevent non-admins from changing their own role or is_active status
#         if g.user.role != UserRole.ADMIN:
#             if "role" in data or "is_active" in data:
#                 return {"message": "Unauthorized to modify role or account status"}, 403

#         # Apply updates
#         for key, value in data.items():
#             if hasattr(user, key):
#                 if key == "password": # Handle password hashing if provided
#                     user.set_password(value)
#                 elif key == "role": # Convert string role to UserRole enum
#                     user.role = UserRole(value)
#                 else:
#                     setattr(user, key, value)

#         user.save_to_db()
#         return {"message": "User updated successfully", "user": UserProfileUpdateSchema().dump(user)}, 200

#     # Note: The original `delete_from_db` on Users model was modified for soft delete.
#     # This delete method here will now trigger the soft delete.
#     @role_required(UserRole.ADMIN) # Only admin can "delete" (soft-delete) users
#     def delete(self, user_id):
#         user = Users.find_by_id(user_id)
#         if not user:
#             return {"message": "User not found"}, 404

#         if not user.is_active:
#             return {"message": "User is already deactivated"}, 400

#         user.delete_from_db() # This will now set is_active=False
#         return {"message": "User deactivated successfully"}, 200

# # class UserRegisterResource(Resource):
# #     def post(self):
# #         data = request.get_json()
# #         user = user_schema.load(data)
# #         user.set_password(data["password"])
# #         user.save_to_db()
# #         return user_schema.dump(user), 201

# class UserLoginResource(Resource):
#     def post(self):
#         data = request.get_json()
#         user = Users.find_by_email(data.get("email"))
#         if user and user.check_password(data.get("password")):
#             return {"message": "Login successful", "user": user_schema.dump(user)}, 200
#         return {"message": "Invalid credentials"}, 401

# class UserListResource(Resource):
#     def get(self):
#         users = Users.query.all()
#         return user_list_schema.dump(users), 200


#UserDetailResource, UserProfileUpdateResource
# class UserRoleRequestResource(Resource):
#     def post(self, user_id):
#         user = Users.query.get_or_404(user_id)
#         user.role = UserRole.PENDING_PROVIDER
#         db.session.commit()
#         return {"message": "Provider request submitted and pending admin approval."}, 200

# UserRoleApprovalResource
# ProviderProfileResource
# UserRoleRequestResource
# UserResource
# UserListResource

# class UserRoleApprovalResource(Resource):
#     @admin_required
#     def put(self, user_id):
#         user = Users.query.get_or_404(user_id)
#         if user.role == UserRole.PENDING_PROVIDER:
#             user.role = UserRole.PROVIDER
#             db.session.commit()
#             return {"message": "User role updated to PROVIDER."}, 200
#         return {"message": "No pending provider request."}, 400

# app/resources/user.py
from flask_restful import Resource
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
    def post(self):
        user = g.user
        if user.role != UserRole.CUSTOMER:
            return {"message": "Only customers can request a role change."}, 400

        schema = UserRoleRequestSchema()
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        if not isinstance(data, dict) or "requested_role" not in data:
            return {"message": "Invalid input data: 'requested_role' is required."}, 400
        requested_role_enum = UserRole(data["requested_role"])

        # Check if they are already requesting or are already that role
        if user.role == requested_role_enum:
            return {"message": f"You are already a {requested_role_enum.value}."}, 400

        # In a real application, you would save this request to a 'RoleChangeRequest' model
        # and an admin would review it. For now, we'll simulate it directly or add a placeholder.
        # For this example, let's just create the provider profile immediately if requested
        # and set the user's role to pending verification for provider.

        if requested_role_enum == UserRole.PROVIDER:
            # Check if provider profile already exists
            existing_provider = Provider.find_by_user_id(user.id)
            if existing_provider:
                return {"message": "You already have a provider profile."}, 400

            # Create a new Provider entry for the user
            # Ensure 'data' is a dict and use correct Provider model parameters
            bio = data["message"] if isinstance(data, dict) and "message" in data else "New provider registration."
            provider = Provider(user=user, description=bio)
            # If your Provider model supports setting verification status after creation:
            provider.verification_status = VerificationStatus.PENDING
            try:
                provider.save_to_db()
                user.role = UserRole.PROVIDER # Set their role immediately (or change to a PENDING_PROVIDER role if exists)
                user.is_verified = False # Provider needs to be verified
                user.save_to_db()
                return {"message": f"Provider profile created and status set to {provider.verification_status.value}. Please complete verification."}, 201
            except Exception as e:
                return {"message": f"Error creating provider profile: {str(e)}"}, 500
        else:
            return {"message": "Role change requests are only supported for Provider role at this time."}, 400

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