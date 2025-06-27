from functools import wraps
from flask import request, jsonify, g
# Import jwt_required, get_jwt_identity, get_jwt directly from flask_jwt_extended
from flask_jwt_extended import jwt_required as flask_jwt_required, get_jwt_identity, get_jwt
from app.models import Users, UserRole

# A simple in-memory blacklist for demonstration. For production, use a database.
# This class needs to be imported and used by the @jwt.token_in_blocklist_loader
# function in your app/__init__.py file.
class TokenBlacklist:
    def __init__(self):
        self.blocked_tokens = set()

    def add(self, jti):
        self.blocked_tokens.add(jti)

    def is_blocked(self, jti):
        return jti in self.blocked_tokens

jwt_blacklist = TokenBlacklist() # This instance should be imported into app/__init__.py

def role_required(required_role: UserRole):
    """
    Decorator to ensure the authenticated user has a specific role.

    Args:
        required_role (UserRole): The UserRole enum value required to access the endpoint.
    """
    def decorator(fn):
        @wraps(fn)
        @flask_jwt_required() # Ensures a valid JWT is present and not blacklisted
        def wrapper(*args, **kwargs):
            # --- ADD THESE LINES TO DEBUG THE INCOMING REQUEST AND TOKEN ---
            print(f"--- Incoming Authorization Header: {request.headers.get('Authorization')} ---")
            claims = get_jwt()
            print(f"--- Decoded JWT Claims (Payload): {claims} ---")
            # -----------------------------------------------------------

            user_role_str = claims.get('role')

            if not user_role_str:
                return jsonify({"message": "Role not found in token claims."}), 403

            try:
                user_role = UserRole(user_role_str)
            except ValueError:
                return jsonify({"message": "Invalid role in token claims."}), 403

            # Check if the user's role matches the required role
            if user_role != required_role:
                return jsonify({"message": f"{required_role.value.capitalize()} privileges required"}), 403

            # Fetch the user object and attach to Flask's g object for easy access
            user_id = get_jwt_identity()
            g.user = Users.find_by_id(user_id)
            if not g.user:
                return jsonify({"message": "User not found."}), 404

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# This wrapper is functionally equivalent to @flask_jwt_required() but
# also ensures g.user is set. You can use @flask_jwt_required() directly
# if you prefer to handle g.user assignment within your resource methods.
def jwt_required_wrapper(fn):
    """
    Decorator to ensure a valid JWT is present and attach the user object to g.user.
    """
    @wraps(fn)
    @flask_jwt_required() # Ensures valid JWT and automatically handles blacklisting check
    def wrapper(*args, **kwargs):
        # --- ADD THESE LINES TO DEBUG THE INCOMING REQUEST AND TOKEN ---
        print(f"--- Incoming Authorization Header (jwt_required_wrapper): {request.headers.get('Authorization')} ---")
        claims = get_jwt()
        print(f"--- Decoded JWT Claims (Payload - jwt_required_wrapper): {claims} ---")
        # 
        user_id = get_jwt_identity()
        g.user = Users.find_by_id(user_id)
        if not g.user:
            return jsonify({"message": "User not found."}), 404
        return fn(*args, **kwargs)
    return wrapper

# Remove app/resources/auth/utils.py entirely as its functionality is now
# covered by Flask-JWT-Extended and these decorators.
