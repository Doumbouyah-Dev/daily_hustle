from flask import request
from flask_restful import Resource
from ..models import Notifications
from ..schemas.notification import NotificationSchema
from .. import db

notification_schema = NotificationSchema()
notification_list_schema = NotificationSchema(many=True)

class NotificationListResource(Resource):
    def get(self):
        return notification_list_schema.dump(Notifications.query.all()), 200

    def post(self):
        data = request.get_json()
        new_notification = notification_schema.load(data)
        db.session.add(new_notification)
        db.session.commit()
        return notification_schema.dump(new_notification), 201


class NotificationResource(Resource):
    def get(self, notification_id):
        notification = Notifications.query.get_or_404(notification_id)
        return notification_schema.dump(notification), 200

    def put(self, notification_id):
        notification = Notifications.query.get_or_404(notification_id)
        data = request.get_json()
        notification.message = data.get("message", notification.message)
        notification.is_read = data.get("is_read", notification.is_read)
        db.session.commit()
        return notification_schema.dump(notification), 200

    def delete(self, notification_id):
        notification = Notifications.query.get_or_404(notification_id)
        db.session.delete(notification)
        db.session.commit()
        return {"message": "Notification deleted"}, 204
