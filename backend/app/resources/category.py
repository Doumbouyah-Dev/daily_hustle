from flask import request
from flask_restful import Resource
from ..schemas.category import ServiceCategorySchema
from app import db
from ..models import ServiceCategory


category_schema = ServiceCategorySchema()

category_list_schema = ServiceCategorySchema(many=True)

class ServiceCategoryResource(Resource):
    def get(self, category_id):
        category = ServiceCategory.query.get_or_404(category_id)
        return category_schema.dump(category), 200

    def put(self, category_id):
        category = ServiceCategory.query.get_or_404(category_id)
        data = request.get_json()
        category.name = data.get("name", category.name)
        db.session.commit()
        return category_schema.dump(category), 200

    def delete(self, category_id):
        category = ServiceCategory.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return {"message": "Category deleted"}, 204

class ServiceCategoryListResource(Resource):
    def get(self):
        return category_list_schema.dump(ServiceCategory.query.all()), 200

    def post(self):
        data = request.get_json()
        new_category = category_schema.load(data)
        db.session.add(new_category)
        db.session.commit()
        return category_schema.dump(new_category), 201
