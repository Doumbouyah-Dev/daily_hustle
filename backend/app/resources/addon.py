from flask import request
from flask_restful import Resource
from ..models import ServiceAddOn
from ..schemas.addon import ServiceAddOnSchema
from app import db

addon_schema = ServiceAddOnSchema()
addon_list_schema = ServiceAddOnSchema(many=True)


class ServiceAddOnResource(Resource):
    def get(self, addon_id):
        addon = ServiceAddOn.query.get_or_404(addon_id)
        return addon_schema.dump(addon), 200

    def put(self, addon_id):
        addon = ServiceAddOn.query.get_or_404(addon_id)
        data = request.get_json()

        addon.name = data.get("name", addon.name)
        addon.description = data.get("description", addon.description)
        addon.price = data.get("price", addon.price)
        addon.service_id = data.get("service_id", addon.service_id)

        db.session.commit()
        return addon_schema.dump(addon), 200

    def delete(self, addon_id):
        addon = ServiceAddOn.query.get_or_404(addon_id)
        db.session.delete(addon)
        db.session.commit()
        return {"message": "Add-on deleted successfully"}, 204


class ServiceAddOnListResource(Resource):
    def get(self):
        addons = ServiceAddOn.query.all()
        return addon_list_schema.dump(addons), 200

    def post(self):
        data = request.get_json()
        try:
            new_addon = addon_schema.load(data)
        except Exception as e:
            return {"message": f"Validation error: {str(e)}"}, 400

        db.session.add(new_addon)
        db.session.commit()
        return addon_schema.dump(new_addon), 201
