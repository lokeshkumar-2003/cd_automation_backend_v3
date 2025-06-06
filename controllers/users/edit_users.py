import re
from flask_cors import CORS
from dbconfig import get_db_connection
from util.IsValidEmailId import is_valid_email
from flask import Flask, jsonify, request, Blueprint

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

edit_users_routes = Blueprint("edit_users_routes", __name__)
IMEI_REGEX = r'^\d{15}$'

@edit_users_routes.route("/v1/api/auth/update/<usertype>/<userId>", methods=['PUT'])
def update_user(usertype, userId):
    request_data = request.get_json()
    name = request_data.get("Name")
    emailId = request_data.get('EmailId')
    phoneno = request_data.get('Phoneno')
    username = request_data.get('Username')
    Device_uuid = request_data.get('Device_uuid')
    Password = request_data.get('Password')
    isDeviceActive = request_data.get('IsDeviceActive')
    
    # Input validation
    if not all([emailId, phoneno, username, Device_uuid, Password, name]):
        return jsonify({"message": "All fields must be filled"}), 400

    if not is_valid_email(emailId):
        return jsonify({"message": "Please enter a valid email address."}), 400

    phoneno_str = str(phoneno)
    if not phoneno_str.isdigit() or len(phoneno_str) != 10:
        return jsonify({"message": "Phone number must be 10 digits."}), 400

    try:
        valid_tables = ['admin_users', 'regular_users']
        if usertype not in valid_tables:
            return jsonify({"message": "Invalid user type."}), 400
        userId = userId.strip()
        query = f"""
            UPDATE {usertype} 
            SET Name = %s, EmailId = %s, Phoneno = %s, Username = %s, Device_uuid = %s, Password = %s, IsDeviceActive = %s
            WHERE userId = %s
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query, (name, emailId, phoneno_str, username, Device_uuid, Password, isDeviceActive, userId))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": f"No user found with userId {userId}"}), 404

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        print('Error in edit_user: ', e)
        return jsonify({"message": "Internal server error"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()