from flask import Blueprint, jsonify, request
from dbconfig import get_db_connection

fcm_token_routes = Blueprint("fcm_token_routes", __name__)

@fcm_token_routes.route("/v1/api/fcm/token/<username>", methods=['POST'])
def store_fcm_token(username):
    data = request.get_json()
    fcm_token = data.get('fcm_token')

    if not fcm_token:
        return jsonify({"message": "FCM token is required"}), 400

    if not username:
        return jsonify({"message": "Username is required"}), 400

    query_get_token = "SELECT fcm_token FROM admin_users WHERE Username = %s"
    query_update_token = "UPDATE admin_users SET fcm_token = %s WHERE Username = %s"

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query_get_token, (username,))
        row = cursor.fetchone()

        if row is None:
            return jsonify({"message": f"No user found with username {username}"}), 404

        existing_token = row[0]

        if existing_token != fcm_token:
            cursor.execute(query_update_token, (fcm_token, username))
            conn.commit()
            return jsonify({"message": "FCM token updated successfully", "fcmtoken": existing_token}), 200
        else:
            return jsonify({"message": "FCM token is already up-to-date"}), 200

    except Exception as e:
        print("Error in fcm_token endpoint:", e)
        return jsonify({"message": "Something went wrong", "error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
