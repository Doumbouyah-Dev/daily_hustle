from flask import Flask, jsonify
from flask_admin import Admin
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_uploads import configure_uploads
from app.libs.image_helper import IMAGE_SET
from config import Config
from datetime import timedelta # Import timedelta for JWT_ACCESS_TOKEN_EXPIRES
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_jwt_extended import JWTManager

jwt = JWTManager()

app = Flask(__name__)
app.config.from_object(Config)
print(f"--- Flask App SECRET_KEY: {app.config['SECRET_KEY']} ---")
api = Api(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)
CORS(app)
configure_uploads(app, IMAGE_SET)



# Import the blacklist for JWT to use
from app.utils.decorators import jwt_blacklist


# Configure JWT to check the blacklist
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jwt_blacklist.is_blocked(jti)

# JWT error handlers (more specific than generic exception)
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"message": "Missing JWT token or token is invalid."}), 401

@jwt.invalid_token_loader
def invalid_token_response(callback):
    print(f"--- Invalid Token Error: jwt_header={jwt_header}, jwt_payload={jwt_payload} ---")
    return jsonify({"message": "Signature verification failed. Invalid token."}), 403

@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return jsonify({"message": "The token has expired.", "error": "token_expired"}), 401

@jwt.revoked_token_loader
def revoked_token_response(jwt_header, jwt_payload):
    return jsonify({"message": "The token has been revoked."}), 401

limiter = Limiter(
    app=app,
    key_func=get_remote_address, # Rate limit by IP address
    default_limits=["200 per day", "50 per hour"] # Default for all routes
)

from app import routes
        # return app
from cli import user_cli
app.cli.add_command(user_cli)
