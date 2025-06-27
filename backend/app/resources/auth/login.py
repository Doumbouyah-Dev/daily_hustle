from flask_restful import Resource
from datetime import datetime, timedelta
from flask import g
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from app.models import Users, UserRole # Assuming UserRole is defined
from app.schemas.user import UserLoginSchema
from app.utils.decorators import jwt_blacklist # Import the blacklist for revocation

class UserLoginResource(Resource):
    def post(self):
        schema = UserLoginSchema()
        try:
            user_data = schema.load(request.get_json())
        except Exception as err: # Use specific validation error if using Marshmallow's ValidationError
            return {"message": str(err)}, 400

        user = Users.find_by_email(user_data["email"]) or Users.find_by_username(user_data["username"])

        if user and user.check_password(user_data["password"]):
            # Ensure user is active for login
            if not user.is_active:
                return {"message": "Account is inactive. Please contact support."}, 403

            # Update last login timestamp
            user.last_login_at = datetime.utcnow()
            user.save_to_db()

            # Create access and refresh tokens
            # We can add custom claims like user role here
            additional_claims = {"role": user.role.value}
            # access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
            # refresh_token = create_refresh_token(identity=user.id)
            access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
            refresh_token = create_refresh_token(identity=str(user.id))

            return {
                "message": "Logged in successfully",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.id,
                "role": user.role.value
            }, 200
        return {"message": "Invalid credentials"}, 401

class TokenRefreshResource(Resource):
    @jwt_required(refresh=True) # This decorator verifies the refresh token
    def post(self):
        current_user_id = get_jwt_identity()
        user = Users.find_by_id(current_user_id)
        if not user:
            return jsonify({"message": "User not found for refresh token."}), 404

        # Ensure the user is still active before issuing new tokens
        if not user.is_active:
            return {"message": "Account is inactive. Cannot refresh token."}, 403

        # Create a new access token
        additional_claims = {"role": user.role.value}
        new_access_token = create_access_token(identity=current_user_id, additional_claims=additional_claims)
        return {"access_token": new_access_token}, 200

class UserLogoutResource(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"] # Get the JTI (JWT ID) of the current token
        jwt_blacklist.add(jti) # Add it to the blacklist
        return {"message": "Successfully logged out"}, 200