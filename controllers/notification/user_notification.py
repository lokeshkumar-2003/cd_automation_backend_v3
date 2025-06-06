from flask import Flask, jsonify, Blueprint
from flask_cors import CORS
from datetime import datetime
from dbconfig import get_db_connection
from controllers.notification.util.Email_handler import send_email
from controllers.notification.Notification_handler import send_app_notification

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

user_notification_routes = Blueprint("user_notification_routes", __name__)

@user_notification_routes.route("/v1/api/notification/admins/user/<adminName>/<username>/<role>/<state>", methods=['GET'])
def user_notification(adminName, username, role, state):
    if not all([adminName, username, role, state]):
        return jsonify({"message": "All fields are required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        
        cursor.execute("SELECT Name, Username, EmailId, emailPassword, fcm_token FROM admin_users")
        result = cursor.fetchall()
        
        sender = None
        receivers = []

        for name, uname, email, password, fcm_token in result:
            if uname == adminName:
                print("Sender", uname)
                sender = {"name": name, "email": email, "password": password}
            else:
                print("Receiver", uname)
                receivers.append({
                    "username": uname,
                    "email": email,
                    "fcm_token": fcm_token
                })

        if not sender or not sender["email"] or not sender["password"]:
            return jsonify({"message": "Sender admin details not found or incomplete"}), 404

        current_date = datetime.now().strftime("%d-%m-%Y")
        notification_title = f"User Account {state} – {username}"

        detailed_message = f"""Hello Admin,

The user '{username}' has been {state} by '{adminName}' on {current_date}.
Role: {role}
Please review this action in the admin panel."""

        db_message = f"The user '{username}' with role '{role}' was {state} by {adminName} on {current_date}."
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
                body=detailed_message
            )

            
            if admin.get("fcm_token"):
                send_app_notification(
                    device_token=admin["fcm_token"],
                    title=notification_title,
                    message=detailed_message
                )

        conn.commit()
        return jsonify({"message": "Notification sent to other admins successfully"}), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"message": "Failed to send notification", "error": str(e)}), 500

    finally:
        if conn:
            conn.close()
