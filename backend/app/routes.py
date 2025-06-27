from flask import jsonify
from marshmallow import ValidationError
from app import app, api
from flask_jwt_extended import jwt_required


from app.resources.notification import NotificationResource
from app.resources.category import ServiceCategoryListResource, ServiceCategoryResource
from app.resources.booking import BookingListResource, BookingResource
from app.resources.user import UserListResource, UserRoleApprovalResource, UserDetailResource, UserProfileUpdateResource, UserRoleRequestResource, ProviderProfileResource
from app.resources.provider import ProviderListResource, ProviderResource
from app.resources.payment import PaymentListResource, PaymentResource
from app.resources.service import ServiceListResource, ServiceResource
from app.resources.review import ReviewListResource, ReviewResource
from app.resources.notification import NotificationListResource
from .resources.auth.register import UserRegisterResource 
from app.resources.admin import AdminStatsResource
from app.resources.auth.login import UserLoginResource, TokenRefreshResource, UserLogoutResource



# Users
api.add_resource(UserListResource, "/all_users")
api.add_resource(UserDetailResource, "/users/<int:user_id>")
api.add_resource(UserProfileUpdateResource, "/update")
api.add_resource(UserRoleRequestResource, "/user/request-role")
api.add_resource(UserRoleApprovalResource, "/users/<int:user_id>/approve-role")
api.add_resource(ProviderListResource, "/providers")
api.add_resource(ProviderResource, "/providers/<int:provider_id>")
api.add_resource(ProviderProfileResource, "/provider/profile")

# Categories
api.add_resource(ServiceCategoryListResource, "/categories")
api.add_resource(ServiceCategoryResource, "/categories/<int:category_id>")

# Bookings
api.add_resource(BookingListResource, "/bookings")
api.add_resource(BookingResource, "/bookings/<int:booking_id>")

#Payment
api.add_resource(PaymentListResource, "/payments")
api.add_resource(PaymentResource, "/payments/<int:payment_id>")

# Services
api.add_resource(ServiceListResource, "/services")
api.add_resource(ServiceResource, "/services/<int:service_id>")



# Reviews
api.add_resource(ReviewListResource, "/reviews")
api.add_resource(ReviewResource, "/reviews/<int:review_id>")

# Notifications
api.add_resource(NotificationListResource, "/notifications")
api.add_resource(NotificationResource, "/notifications/<int:notification_id>")


# User Protection
api.add_resource(UserRegisterResource, "/auth/v1/register")
api.add_resource(AdminStatsResource, "/admin/v1/stats")
api.add_resource(UserLoginResource, '/auth/v1/login')
api.add_resource(TokenRefreshResource, '/auth/v1/refresh')
api.add_resource(UserLogoutResource, '/auth/v1/logout')




@app.route('/')
def root_info():
    return jsonify({
        "message": "Welcome to your Flask Restful API!",
        "available_endpoints": {
            "/auth/register": "POST - Register a new user",
            # Add other endpoints you have or plan to have
        }
    }), 200 