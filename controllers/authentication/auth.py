from flask import Flask, jsonify, request, Blueprint
from dbconfig import get_db_connection
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/v1/api/auth/login", methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("Username", "").strip()
    password = data.get("Password", "").strip()
    usertype = data.get("Usertype", "").strip()
    
    if not all([username, password, usertype]):
        return jsonify({"error": "Missing username, password"}), 400

    allowed_usertypes = ["admin_users", "regular_users"]
    if usertype not in allowed_usertypes:
        return jsonify({"error": "Invalid user type"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) 
        query = f"SELECT * FROM {usertype} WHERE Username = %s AND Password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            device_uuid = user["Device_uuid"]
            device_active = user["IsDeviceActive"]
            print(device_active)
            return jsonify({
                "message": "Login successful",
                "device_uuid": device_uuid,
                "device_active": device_active
            }), 200
        else:
            return jsonify({"error": "Incorrect username or password or user not exist"}), 404

    except Exception as e:
        print(e)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@auth_routes.route("/v1/api/auth/user/deviceid", methods=['POST'])
def get_device_uuid():
    data = request.get_json()
    username = data.get("Username")
    usertype = data.get("Usertype")

    if not all([username, usertype]):
        return jsonify({"error": "Missing username or usertype"}), 400

    allowed_usertypes = ["admin_users", "regular_users"]
    if usertype not in allowed_usertypes:
        return jsonify({"error": "Invalid user type"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"SELECT Device_uuid, IsDeviceActive FROM {usertype} WHERE Username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result is None:
            return jsonify({"message": "User not found. Please ensure you are registered."}), 404

        device_uuid, is_device_active = result

        print(is_device_active)

        return jsonify({
            "Device_uuid": device_uuid,
            "IsDeviceActive": is_device_active
        }), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

@auth_routes.route("/v1/api/auth/device_id_activate/<usertype>/<username>", methods=['PUT'])
def device_id_activate(usertype, username):
    allowed_usertypes = ["admin_users", "regular_users"]
    if usertype not in allowed_usertypes:
        return jsonify({"error": "Invalid user type"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"UPDATE {usertype} SET IsDeviceActive = 1 WHERE Username = %s"
        cursor.execute(query, (username,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "User not found or already active."}), 404

        return jsonify({"message": f"Device activated successfully for user {username}."}), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()
