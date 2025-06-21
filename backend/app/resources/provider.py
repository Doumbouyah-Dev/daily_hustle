from flask import request
from flask_restful import Resource
from ..models import Users, UserRole
from ..schemas.user import UserSchema
from app import db

provider_schema = UserSchema()
provider_list_schema = UserSchema(many=True)

class ProviderListResource(Resource):
    def get(self):
        providers = Users.query.filter_by(role=UserRole.PROVIDER).all()
        return provider_list_schema.dump(providers), 200

    def post(self):
        data = request.get_json()
        data["role"] = UserRole.PROVIDER.name  # Force role to PROVIDER
        new_provider = provider_schema.load(data)
        db.session.add(new_provider)
        db.session.commit()
        return provider_schema.dump(new_provider), 201


class ProviderResource(Resource):
    def get(self, provider_id):
        provider = Users.query.filter_by(id=provider_id, role=UserRole.PROVIDER).first_or_404()
        return provider_schema.dump(provider), 200

    def put(self, provider_id):
        provider = Users.query.filter_by(id=provider_id, role=UserRole.PROVIDER).first_or_404()
        data = request.get_json()
        for field in ["firstname", "lastname", "email", "phone", "address"]:
            setattr(provider, field, data.get(field, getattr(provider, field)))
        db.session.commit()
        return provider_schema.dump(provider), 200

    def delete(self, provider_id):
        provider = Users.query.filter_by(id=provider_id, role=UserRole.PROVIDER).first_or_404()
        db.session.delete(provider)
        db.session.commit()
        return {"message": "Provider deleted successfully"}, 204
