from flask import request
from flask_restful import Resource
from ...models import Users, UserRole 
from app import db
from werkzeug.security import generate_password_hash
from ...schemas.user import UserRegisterSchema, UserSchema

user_schema = UserSchema()

import uuid # For generating tokens
from datetime import timedelta
from app import app # Assuming app instance is available for config access

class UserRegisterResource(Resource):
    def post(self):
        schema = UserRegisterSchema()
        try:
            user_data = schema.load(request.get_json())
            # If user_data is a list (e.g., when many=True), get the first item
            if isinstance(user_data, list):
                user_data = user_data[0]
        except Exception as err: # Use ValidationError if using Marshmallow's ValidationError
            return {"message": str(err)}, 400
        if not user_data:
            return {"message": "Invalid input data"}, 400

        if Users.find_by_username(user_data["username"]):
            return {"message": "Username already exists"}, 409
        if Users.find_by_email(user_data["email"]):
            return {"message": "Email already exists"}, 409
        if Users.find_by_phone(user_data.get("phone")):
            return {"message": "Phone number already exists"}, 409

        user = Users(
            firstname=user_data.get("firstname"),
            lastname=user_data.get("lastname"),
            username=user_data["username"],
            email=user_data["email"],
            gender=user_data.get("gender"),
            phone=user_data.get("phone"),
            password=user_data["password"], # This calls set_password
            is_verified=False # New users are not verified by default
        )

        # Generate email verification token
        user.email_verification_token = str(uuid.uuid4())
        # For a real app, send this token to the user's email address
        # e.g., send_verification_email(user.email, user.email_verification_token)

        try:
            user.save_to_db()
            return {"message": "User created successfully. Please check your email to verify your account."}, 201
        except Exception as e:
            app.logger.error(f"Error creating user: {e}")
            return {"message": "Internal server error"}, 500
