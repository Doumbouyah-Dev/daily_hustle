from flask_restful import Resource
from ..models import Users, UserRole
from ..models import Booking
from ..models import Service
from app import db
from app.utils.decorators import role_required # or jwt_required_wrapper


class AdminStatsResource(Resource):
    @role_required(UserRole.ADMIN) # Use role_required from app.utils.decorators
    def get(self):
        return {
            "total_users": Users.query.count(),
            "total_providers": Users.query.filter_by(role=UserRole.PROVIDER).count(),
            "total_bookings": Booking.query.count(),
            "active_services": Service.query.filter_by(is_active=True).count(),
        }, 200
