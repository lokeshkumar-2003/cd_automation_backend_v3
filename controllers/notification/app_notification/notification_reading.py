from flask import Flask, jsonify, request, Blueprint, Response
from dbconfig import get_db_connection
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app_notification = Blueprint("app_notification", __name__)

@app_notification.route("/v1/api/app/notifications/<username>", methods=['GET'])
def get_reading_notification(username):
    if not username:
        return jsonify({"message": "Username is required"}), 400

    query_check_status = """
        SELECT NotificationID 
        FROM NotificationReadStatus 
        WHERE IsRead = %s AND AdminUsername = %s
    """
    
    query_get_notification = """
        SELECT ID, Title, Message, CreatedBy, CreatedAt, Status
        FROM Notifications 
        WHERE ID = %s
    """

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query_check_status, (0, username))
        result = cursor.fetchall()
        notification_ids = {row[0] for row in result}

        notifications = []
        for notification_id in notification_ids:
            cursor.execute(query_get_notification, (notification_id,))
            notif_result = cursor.fetchone()
            if notif_result:
                notif_id, title, message, created_by, created_at, status = notif_result
                notifications.append({
                    "ID": notif_id,
                    "Title": title,
                    "Message": message,
                    "CreatedBy": created_by,
                    "Date": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else '',
                    "Status": status
                })

        return jsonify({"notifications": notifications}), 200

    except Exception as e:
        return jsonify({"message": "Error fetching notifications", "error": str(e)}), 500

    finally:
        if conn:
            conn.close()


@app_notification.route("/v1/api/app/notifications/mark-read/<username>/<int:notification_id>", methods=['PUT'])
def mark_notification_as_read(username, notification_id):
    print(username, notification_id)
    if not username or not notification_id:
        return jsonify({"message": "Username and Notification ID are required"}), 400

    update_query = """
        UPDATE NotificationReadStatus
        SET IsRead = %s
        WHERE AdminUsername = %s AND NotificationID = %s
    """

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(update_query, (1, username, notification_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No matching unread notification found"}), 404

        return jsonify({"message": "Notification marked as read successfully"}), 200

    except Exception as e:
        return jsonify({"message": "Failed to mark notification as read", "error": str(e)}), 500

    finally:
        if conn:
            conn.close()
