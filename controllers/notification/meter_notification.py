from flask import Blueprint, jsonify
from dbconfig import get_db_connection
from datetime import datetime
from controllers.notification.util.Email_handler import send_email
from controllers.notification.Notification_handler import send_app_notification

meter_notification_routes = Blueprint("meter_notification_routes", __name__)

@meter_notification_routes.route("/v1/api/notification/admins/meter/<adminName>/<meterName>/<meterType>/<state>", methods=['GET'])
def meter_notification(adminName, meterName, meterType, state):
    if not all([adminName, meterName, meterType, state]):
        return jsonify({"message": "All fields are required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT Name, Username, EmailId, emailPassword, fcm_token FROM admin_users")
        admins = cursor.fetchall()

        sender = None
        receivers = []

        for name, username, email, password, token in admins:
            if username == adminName:
                sender = {"name": name, "email": email, "password": password}
            else:
                receivers.append({
                    "username": username,
                    "email": email,
                    "fcm_token": token
                })

        if not sender or not sender["email"] or not sender["password"]:
            return jsonify({"message": "Sender admin details not found or incomplete"}), 404

        current_date = datetime.now().strftime("%d-%m-%Y")
        notification_title = f"Meter {state} – {meterName}"
        notification_message = (
            f"Hello Admin,\n\n"
            f"The meter '{meterName}' has been {state} by '{adminName}' on {current_date}.\n"
            f"Type: {meterType}\n"
            f"Please review this action in the admin panel."
        )

        db_message = f"The meter '{meterName}' of type '{meterType}' was {state} by {adminName} on {current_date}."
        now_data = datetime.now()

        cursor.execute("""
            INSERT INTO Notifications (Title, Message, CreatedBy, CreatedAt, Status)
            VALUES (%s, %s, %s, %s, %s)
        """, (notification_title, db_message, adminName, now_data, "Normal"))
        conn.commit()

        notification_id = cursor.lastrowid

        for admin in receivers:
            cursor.execute("""
                INSERT INTO NotificationReadStatus (NotificationID, AdminUsername, IsRead)
                VALUES (%s, %s, %s)
            """, (notification_id, admin["username"], 0))

            send_email(
                sender_email=sender["email"],
                sender_password=sender["password"],
                recipient_email=admin["email"],
                subject=notification_title,
                body=notification_message
            )

            if admin.get("fcm_token"):
                send_app_notification(
                    device_token=admin["fcm_token"],
                    title=notification_title,
                    message=notification_message
                )

        conn.commit()
        return jsonify({"message": "Notification sent to other admins successfully"}), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"message": "Failed to send notification", "error": str(e)}), 500

    finally:
        if conn:
            conn.close()
