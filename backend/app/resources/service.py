from flask import request
from flask_restful import Resource
from ..models import Service # Adjust import path
from ..schemas.service import ServiceSchema
from app import db

service_schema = ServiceSchema()
service_list_schema = ServiceSchema(many=True)


class ServiceResource(Resource):
    def get(self, service_id):
        service = Service.query.get_or_404(service_id)
        return service_schema.dump(service), 200

    def put(self, service_id):
        service = Service.query.get_or_404(service_id)
        data = request.get_json()

        service.name = data.get("name", service.name)
        service.description = data.get("description", service.description)
        service.category_id = data.get("category_id", service.category_id)
        service.pricing_model = data.get("pricing_model", service.pricing_model)
        service.base_price = data.get("base_price", service.base_price)
        service.unit_label = data.get("unit_label", service.unit_label)
        service.estimated_duration = data.get("estimated_duration", service.estimated_duration)
        service.requires_materials = data.get("requires_materials", service.requires_materials)
        service.has_add_ons = data.get("has_add_ons", service.has_add_ons)
        service.is_active = data.get("is_active", service.is_active)

        db.session.commit()
        return service_schema.dump(service), 200

    def delete(self, service_id):
        service = Service.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()
        return {"message": "Service deleted successfully."}, 204


class ServiceListResource(Resource):
    def get(self):
        services = Service.query.all()
        return service_list_schema.dump(services), 200

    def post(self):
        data = request.get_json()
        try:
            new_service = service_schema.load(data)
        except Exception as e:
            return {"message": f"Validation error: {str(e)}"}, 400

        db.session.add(new_service)
        db.session.commit()
        return service_schema.dump(new_service), 201
