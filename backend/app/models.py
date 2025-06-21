# This is the models in app/models.py:
from typing import List
from datetime import datetime, date, timedelta, time
# from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import pytz
import moment
from app import app, db # Assuming 'app' and 'db' are initialized correctly in app/__init__.py
import enum


# -------------------- Enums --------------------

class UserRole(enum.Enum):
    CUSTOMER = "customer" # Represents a standard user who books services.
    PROVIDER = "provider" # Represents a service provider.
    ADMIN = "admin"       # Represents an administrator with full control.
    B2B_CLIENT = "b2b_client" # Represents a business client.

class PricingModel(enum.Enum):
    FIXED = "fixed"
    HOURLY = "hourly"
    AREA_BASED = "area_based"

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class VerificationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class NotificationType(enum.Enum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_UPDATE = "booking_update"
    PAYMENT_REMINDER = "payment_reminder"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    REVIEW_REQUEST = "review_request"
    SYSTEM_MESSAGE = "system_message"
    PROVIDER_VERIFICATION = "provider_verification"


class Users(db.Model):
    __tablename__ = 'users' # Explicitly set table name for clarity
    id = db.Column(db.Integer, primary_key=True, index=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    gender = db.Column(db.String(10))
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True) # For soft delete
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20), unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True) # New field for last login timestamp
    email_verification_token = db.Column(db.String(255), nullable=True) # New field for email verification token
    email_verified_at = db.Column(db.DateTime, nullable=True) # New field for email verification timestamp
    phone_verification_token = db.Column(db.String(255), nullable=True) # New field for phone verification token
    phone_verified_at = db.Column(db.DateTime, nullable=True) # New field for phone verification timestamp
    password_reset_token = db.Column(db.String(255), nullable=True) # New field for password reset token
    password_reset_expiration = db.Column(db.DateTime, nullable=True) # New field for password reset token expiration

    provider = db.relationship('Provider', backref='user', uselist=False, lazy='joined', cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='customer', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    notifications = db.relationship('Notifications', backref='user', lazy='dynamic')


    def __init__(self, **kwargs):
        super(Users, self).__init__(**kwargs)
        if 'password' in kwargs:
            # Use bcrypt by explicitly specifying the method
            self.set_password(kwargs['password'])

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        # Soft delete for Users model
        if self.__tablename__ == 'users':
            self.is_active = False
            db.session.add(self)
        else:
            db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_phone(cls, phone):
        return cls.query.filter_by(phone=phone).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class Provider(db.Model):
    __tablename__ = 'providers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    bio = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Float, default=5.0)
    is_available = db.Column(db.Boolean, default=True)
    service_radius = db.Column(db.Float, nullable=True) # e.g., in miles or kilometers
    service_area_description = db.Column(db.String(255), nullable=True) # e.g., "Serves all of NYC", "Zip Codes: 10001, 10002"
    verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
    verification_document_url = db.Column(db.String(255), nullable=True) # URL to uploaded verification document

    bookings = db.relationship('Booking', backref='provider', lazy='dynamic')
    reviews_received = db.relationship('Review', backref='provider', lazy='dynamic')
    services_offered = db.relationship('ProviderService', backref='provider', lazy='dynamic', cascade="all, delete-orphan")
    schedules = db.relationship('ProviderSchedule', backref='provider', lazy='dynamic', cascade="all, delete-orphan")
    specializations = db.relationship('ProviderSpecialization', backref='provider', lazy='dynamic', cascade="all, delete-orphan")


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).first()


class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    services = db.relationship('Service', backref='category', lazy='dynamic')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id', ondelete='SET NULL'), nullable=True)
    pricing_model = db.Column(db.Enum(PricingModel), default=PricingModel.FIXED, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    unit_label = db.Column(db.String(50), nullable=True) # e.g., "per hour", "per sq meter", "fixed"
    estimated_duration = db.Column(db.Integer, nullable=True) # in minutes
    requires_materials = db.Column(db.Boolean, default=False)
    has_add_ons = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True) # Allows deactivating a service
    image_url = db.Column(db.String(255), nullable=True) # New field for service image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    add_ons = db.relationship('ServiceAddOn', backref='service', lazy='dynamic', cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='service', lazy='dynamic')
    providers = db.relationship('ProviderService', backref='service', lazy='dynamic', cascade="all, delete-orphan")
    availability_slots = db.relationship('ServiceAvailability', backref='service', lazy='dynamic', cascade="all, delete-orphan")
    area_pricing_rules = db.relationship('AreaPricingRule', backref='service', lazy='dynamic', cascade="all, delete-orphan")


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()


class ServiceAddOn(db.Model):
    __tablename__ = 'service_add_ons'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True) # New field for add-on description
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True) # Allows deactivating an add-on

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class ServiceAvailability(db.Model):
    __tablename__ = 'service_availability'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False) # 0 for Monday, 6 for Sunday
    start_time = db.Column(db.Time, nullable=False) # e.g., time(9, 0) for 9:00 AM
    end_time = db.Column(db.Time, nullable=False) # e.g., time(17, 0) for 5:00 PM

    __table_args__ = (db.UniqueConstraint('service_id', 'day_of_week', name='_service_day_uc'),)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class AreaPricingRule(db.Model):
    __tablename__ = 'area_pricing_rules'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    min_area = db.Column(db.Float, nullable=True)
    max_area = db.Column(db.Float, nullable=True)
    price_per_unit = db.Column(db.Float, nullable=False) # Price per sq foot/meter
    base_fee = db.Column(db.Float, default=0.0) # Optional fixed fee for area-based services

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class ProviderService(db.Model):
    __tablename__ = 'provider_services'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    # Could add specific pricing for this provider-service combination if needed
    # price = db.Column(db.Float, nullable=True)

    # Ensures a provider offers a specific service only once
    __table_args__ = (db.UniqueConstraint('provider_id', 'service_id', name='_provider_service_uc'),)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class ProviderSchedule(db.Model):
    __tablename__ = 'provider_schedules'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False)
    available_date = db.Column(db.Date, nullable=False) # The specific date the provider is available
    start_time = db.Column(db.Time, nullable=False) # Start time of availability slot
    end_time = db.Column(db.Time, nullable=False) # End time of availability slot

    # Ensures a provider doesn't have overlapping schedules for a given date
    __table_args__ = (db.UniqueConstraint('provider_id', 'available_date', 'start_time', 'end_time', name='_provider_schedule_uc'),)


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class ProviderSpecialization(db.Model):
    __tablename__ = 'provider_specializations'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=True) # Can be NULL if specialization is general
    specialization_description = db.Column(db.String(255), nullable=False) # e.g., "Pipe repair", "Boiler installation"

    __table_args__ = (db.UniqueConstraint('provider_id', 'service_id', 'specialization_description', name='_provider_spec_uc'),)


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id', ondelete='SET NULL'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='SET NULL'), nullable=False)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    # Structured location fields
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total_cost = db.Column(db.Float, nullable=False)
    cancellation_reason = db.Column(db.String(255), nullable=True) # New field for cancellation reason
    cancellation_fee = db.Column(db.Float, nullable=True) # New field for cancellation fee
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payment = db.relationship('Payment', backref='booking', uselist=False, lazy='joined', cascade="all, delete-orphan")
    review = db.relationship('Review', backref='booking', uselist=False, lazy='joined', cascade="all, delete-orphan")

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=True) # e.g., "credit_card", "paypal", "cash"
    status = db.Column(db.String(20), default="pending", nullable=False) # e.g., "pending", "completed", "failed", "refunded"
    transaction_ref = db.Column(db.String(100), unique=True, nullable=True) # Payment gateway transaction reference
    refund_amount = db.Column(db.Float, nullable=True) # New field for refund amount
    refund_status = db.Column(db.String(20), nullable=True) # New field for refund status (e.g., 'initiated', 'completed', 'failed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_booking_id(cls, booking_id):
        return cls.query.filter_by(booking_id=booking_id).first()


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    rating = db.Column(db.Integer, nullable=False) # e.g., 1 to 5 stars
    comment = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=False) # New field for moderation
    moderation_notes = db.Column(db.String(255), nullable=True) # New field for moderation notes
    provider_reply = db.Column(db.Text, nullable=True) # New field for provider's reply
    provider_reply_at = db.Column(db.DateTime, nullable=True) # New field for provider reply timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class Notifications(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=True) # Changed to use NotificationType enum
    status = db.Column(db.String(20), default="sent", nullable=False) # e.g., "sent", "delivered", "failed"
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all_for_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

