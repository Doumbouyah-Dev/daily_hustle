from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, jwt_required as flask_jwt_required, get_jwt
from app.models import Users, UserRole
# from app import jwt_blacklist # Assuming you'll add this to app/__init__.py or a separate jwt_manager

# A simple in-memory blacklist for demonstration. For production, use a database.
# This should ideally be managed by a JWT extension setup in app/__init__.py
# For now, let's assume `app.jwt_blacklist` is a set.
# In a real app, you'd use Flask-JWT-Extended's token_in_blocklist_loader.
class TokenBlacklist:
    def __init__(self):
        self.blocked_tokens = set()

    def add(self, jti):
        self.blocked_tokens.add(jti)

    def is_blocked(self, jti):
        return jti in self.blocked_tokens

jwt_blacklist = TokenBlacklist() # This would typically be initialized in __init__.py or similar


def role_required(required_role: UserRole):
    def decorator(fn):
        @wraps(fn)
        @flask_jwt_required() # Ensure JWT is present and valid
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role_str = claims.get('role')
            if not user_role_str:
                return jsonify({"message": "Role not found in token claims."}), 403

            try:
                user_role = UserRole(user_role_str)
            except ValueError:
                return jsonify({"message": "Invalid role in token claims."}), 403

            # Convert roles to a comparable format for checking hierarchy if needed
            # For now, a direct match is assumed, or specific hierarchy logic can be added
            # Example for hierarchical roles:
            # role_hierarchy = {
            #     UserRole.CUSTOMER: 0,
            #     UserRole.PROVIDER: 1,
            #     UserRole.ADMIN: 2
            # }
            # if role_hierarchy.get(user_role, -1) < role_hierarchy.get(required_role, 99):

            if user_role != required_role: # For exact role match
                return jsonify({"message": f"{required_role.value.capitalize()} privileges required"}), 403

            # Optionally, fetch the user object and attach to Flask's g object for easy access
            user_id = get_jwt_identity()
            g.user = Users.find_by_id(user_id)
            if not g.user:
                return jsonify({"message": "User not found."}), 404

            # Check if the token is blacklisted (for logout)
            jti = get_jwt()["jti"]
            if jwt_blacklist.is_blocked(jti):
                return jsonify({"message": "Token has been revoked."}), 401

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Generic JWT required decorator (can be replaced by flask_jwt_required directly)
def jwt_required_wrapper(fn):
    @wraps(fn)
    @flask_jwt_required()
    def wrapper(*args, **kwargs):
        # Attach user to g object for easy access in resources
        user_id = get_jwt_identity()
        g.user = Users.find_by_id(user_id)
        if not g.user:
            return jsonify({"message": "User not found."}), 404

        # Check if the token is blacklisted (for logout)
        jti = get_jwt()["jti"]
        if jwt_blacklist.is_blocked(jti):
            return jsonify({"message": "Token has been revoked."}), 401
        return fn(*args, **kwargs)
    return wrapper

# Original admin_required is replaced by role_required(UserRole.ADMIN)
# The old admin_required relied on X-User-ID, which is insecure with JWT.
# You should remove the old admin_required function.