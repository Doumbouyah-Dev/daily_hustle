from flask_restful import Resource
from ..models import Users, UserRole
from ..models import Booking
from ..models import Service
from app import db
from .auth.utils import jwt_required

class AdminStatsResource(Resource):
    @jwt_required(allowed_roles=["ADMIN"])
    def get(self):
        return {
            "total_users": Users.query.count(),
            "total_providers": Users.query.filter_by(role=UserRole.PROVIDER).count(),
            "total_bookings": Booking.query.count(),
            "active_services": Service.query.filter_by(is_active=True).count(),
        }, 200
