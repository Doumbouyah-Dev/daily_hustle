from functools import wraps
from flask import request, g, current_app
import jwt

def jwt_required(allowed_roles=None):
    def wrapper(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                return {"message": "Missing token"}, 401
            try:
                # Use current_app.config to get the SECRET_KEY
                data = jwt.decode(token.split()[1], current_app.config["SECRET_KEY"], algorithms=["HS256"])
                if allowed_roles and data["role"] not in allowed_roles:
                    return {"message": "Forbidden for this role"}, 403
                g.user = data
            except jwt.ExpiredSignatureError:
                return {"message": "Token expired"}, 401
            except Exception:
                # This general exception handler is very broad.
                # Consider logging the actual exception for debugging in dev.
                return {"message": "Invalid token"}, 401
            return f(*args, **kwargs)
        return decorator
    return wrapper