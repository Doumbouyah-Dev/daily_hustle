# from datetime import timedelta
# import os


# baseddir = os.path.abspath(os.path.dirname(__file__))

# class Config(object):
#     DEBUG = True
#     JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "super-secret-jwt-key"
#     # SECRET_KEY = os.environ.get("SECRET_KEY") or "this-is-my-secret-key"
#     SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") \
#         or "sqlite:///" + os.path.join(baseddir, "app.db")
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     PROPAGATE_EXCEPTIONS = True
#     JWT_BLACKLIST_ENABLED = True
#     JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
#     UPLOADED_IMAGES_DEST = os.path.join("static", "images")
#     MAX_CONTENT_LENGTH = 10 * 1024 * 1024
#     JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15) # Short-lived access tokens
#     JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30) # Longer-lived refresh tokens
#     JWT_TOKEN_LOCATION = ["headers"] # Specify where JWT is expected (e.g., 'Authorization: Bearer <token>')
#     JWT_BLACKLIST_ENABLED = True
#     JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]

    
from datetime import timedelta
import os

baseddir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    # TESTING = True if os.environ.get("FLASK_ENV") == "development" else False

    # Use a single SECRET_KEY for both Flask and JWT operations
    SECRET_KEY = os.environ.get("SECRET_KEY") or "this-is-a-strong-default-secret-key"

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") \
        or "sqlite:///" + os.path.join(baseddir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    # JWT configuration, now explicitly using SECRET_KEY for signing/decoding
    # No need for JWT_SECRET_KEY as SECRET_KEY will be used by default if configured correctly
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15) # Short-lived access tokens
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30) # Longer-lived refresh tokens
    JWT_TOKEN_LOCATION = ["headers"] # Specify where JWT is expected (e.g., 'Authorization: Bearer <token>')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]

    UPLOADED_IMAGES_DEST = os.path.join("static", "images")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 # 10 MB limit for uploads
