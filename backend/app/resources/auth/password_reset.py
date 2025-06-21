from flask_restful import Resource
from flask import request, jsonify
from app.models import Users
from app.schemas.user import PasswordResetRequestSchema, PasswordResetConfirmSchema
from datetime import datetime, timedelta
import uuid
from app import app # For logging

# Placeholder for email sending function (would use a real email service)
def send_password_reset_email(email, token):
    reset_link = f"http://yourfrontend.com/reset-password?token={token}"
    print(f"DEBUG: Password reset link for {email}: {reset_link}")
    # In a real application, you would use an email sending library/service here
    # e.g., smtplib, Flask-Mail, SendGrid, Mailgun etc.
    app.logger.info(f"Password reset email sent to {email} with token {token}")


class PasswordResetRequestResource(Resource):
    def post(self):
        schema = PasswordResetRequestSchema()
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        user = Users.find_by_email(data["email"])
        if user:
            token = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(hours=1) # Token valid for 1 hour
            user.password_reset_token = token
            user.password_reset_expiration = expiration
            user.save_to_db()
            send_password_reset_email(user.email, token)
        # Always return a generic success message to prevent email enumeration
        return {"message": "If an account with that email exists, a password reset link has been sent."}, 200

class PasswordResetConfirmResource(Resource):
    def post(self):
        schema = PasswordResetConfirmSchema()
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        user = Users.query.filter_by(password_reset_token=data["token"]).first()

        if not user:
            return {"message": "Invalid or expired token."}, 400

        if user.password_reset_expiration < datetime.utcnow():
            user.password_reset_token = None
            user.password_reset_expiration = None
            user.save_to_db()
            return {"message": "Invalid or expired token."}, 400

        user.set_password(data["new_password"])
        user.password_reset_token = None
        user.password_reset_expiration = None
        user.save_to_db()

        return {"message": "Password has been reset successfully."}, 200