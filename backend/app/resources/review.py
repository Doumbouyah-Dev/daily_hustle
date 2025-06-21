from flask import request
from flask_restful import Resource
from ..models import Review
from ..schemas.review import ReviewSchema
from .. import db

review_schema = ReviewSchema()
review_list_schema = ReviewSchema(many=True)

class ReviewListResource(Resource):
    def get(self):
        return review_list_schema.dump(Review.query.all()), 200

    def post(self):
        data = request.get_json()
        new_review = review_schema.load(data)
        db.session.add(new_review)
        db.session.commit()
        return review_schema.dump(new_review), 201


class ReviewResource(Resource):
    def get(self, review_id):
        review = Review.query.get_or_404(review_id)
        return review_schema.dump(review), 200

    def put(self, review_id):
        review = Review.query.get_or_404(review_id)
        data = request.get_json()
        review.rating = data.get("rating", review.rating)
        review.comment = data.get("comment", review.comment)
        db.session.commit()
        return review_schema.dump(review), 200

    def delete(self, review_id):
        review = Review.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        return {"message": "Review deleted"}, 204
