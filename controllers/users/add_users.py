import re
import uuid
from flask import jsonify, Blueprint, request, Flask
from dbconfig import get_db_connection
from flask_cors import CORS
from util.IsValidEmailId import is_valid_email

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

add_user_routes = Blueprint("add_user_routes", __name__)

PASSWORD_REGEX = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

# List of allowed tables to avoid SQL injection
ALLOWED_USER_TYPES = ['admin_users', 'regular_users']

@add_user_routes.route("/v1/api/auth/add/<usertype>", methods=['POST'])
def add_user(usertype):
    try:
        # Validate table name
        if usertype not in ALLOWED_USER_TYPES:
            return jsonify({"message": "Invalid user type"}), 400

        data = request.get_json(force=True)
        print(data)

        emailId = str(data.get('EmailId', '')).strip()
        phoneno = str(data.get('Phoneno', '')).strip()
        username = str(data.get('Username', '')).strip()
        password = str(data.get('Password', '')).strip()
        userdeviceid = str(data.get('UserdeviceId', '')).strip()
        name = str(data.get('Name', '')).strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Corrected query and parameter passing
        check_exist_query = f"SELECT Username FROM {usertype} WHERE Username = %s"
        cursor.execute(check_exist_query, (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"message": "User already exists"}), 409

        # Validation checks
        if not all([emailId, phoneno, username, password, userdeviceid, name]):
            return jsonify({"message": "All fields must be filled"}), 400

        if not is_valid_email(emailId):
            return jsonify({"message": "Please enter a valid email address."}), 400

        if not phoneno.isdigit() or len(phoneno) != 10:
            return jsonify({"message": "Phone number must be 10 digits."}), 400

        if not re.match(PASSWORD_REGEX, password):
            return jsonify({
                "message": "Password must be at least 8 characters long, contain at least one uppercase letter, one digit, and one special character."
            }), 400

        user_id = str(uuid.uuid4())
        user_role = "Admin" if usertype == "admin_users" else "User"

        insert_query = f"""
            INSERT INTO {usertype} 
            (UserId, EmailId, Phoneno, Username, Password, Usertype, Device_uuid, Name) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (user_id, emailId, phoneno, username, password, user_role, userdeviceid, name))
        conn.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        print("Error in Add_Users:", e)
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
