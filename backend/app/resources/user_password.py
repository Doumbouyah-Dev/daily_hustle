from flask_restful import Resource
from flask import request, jsonify, g
from app.models import Users
from app.schemas.user import UserPasswordChangeSchema
from app.utils.decorators import jwt_required_wrapper, jwt_blacklist # Import the blacklist for revocation

class UserPasswordChangeResource(Resource):
    @jwt_required_wrapper
    def post(self):
        schema = UserPasswordChangeSchema()
        try:
            data = schema.load(request.get_json())
        except Exception as err:
            return {"message": str(err)}, 400

        user = g.user # User object from JWT context
        if not user.check_password(data["old_password"]):
            return {"message": "Incorrect old password."}, 401

        user.set_password(data["new_password"])
        user.save_to_db()

        # Revoke all existing tokens for this user after password change
        # This requires a more sophisticated JWT invalidation strategy (e.g., storing jti in DB per user)
        # For simplicity, here we'll just indicate that tokens should be invalidated.
        # In a real system, you'd mark ALL tokens for this user as invalid in your blocklist DB table.
        # For this quick demo, we just inform the client to re-login.
        # A more robust solution might involve updating a 'password_last_changed_at' timestamp
        # in the user model and checking it in the token_in_blocklist_loader.
        jti = get_jwt()["jti"] # Only revoke the current token. More comprehensive revocation needed.
        jwt_blacklist.add(jti)


        return {"message": "Password changed successfully. Please log in again with your new password."}, 200