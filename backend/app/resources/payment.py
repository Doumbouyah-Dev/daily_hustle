from flask import request
from flask_restful import Resource
from ..models import Payment
from ..schemas.payment import PaymentSchema
from .. import db

payment_schema = PaymentSchema()
payment_list_schema = PaymentSchema(many=True)

class PaymentListResource(Resource):
    def get(self):
        payments = Payment.query.all()
        return payment_list_schema.dump(payments), 200

    def post(self):
        data = request.get_json()
        try:
            new_payment = payment_schema.load(data)
        except Exception as e:
            return {"message": f"Validation Error: {str(e)}"}, 400

        db.session.add(new_payment)
        db.session.commit()
        return payment_schema.dump(new_payment), 201


class PaymentResource(Resource):
    def get(self, payment_id):
        payment = Payment.query.get_or_404(payment_id)
        return payment_schema.dump(payment), 200

    def put(self, payment_id):
        payment = Payment.query.get_or_404(payment_id)
        data = request.get_json()

        payment.status = data.get("status", payment.status)
        payment.transaction_ref = data.get("transaction_ref", payment.transaction_ref)
        db.session.commit()
        return payment_schema.dump(payment), 200

    def delete(self, payment_id):
        payment = Payment.query.get_or_404(payment_id)
        db.session.delete(payment)
        db.session.commit()
        return {"message": "Payment deleted"}, 204
