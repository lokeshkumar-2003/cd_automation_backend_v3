from flask import Flask, jsonify, request, Blueprint
from dbconfig import get_db_connection
from flask_cors import CORS


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

get_users_routes = Blueprint("get_users_routes", __name__)



@get_users_routes.route("/v1/api/auth/get/users/<usertype>", methods=['GET'])
def get_users(usertype):
    allowed_tables = ['regular_users', 'admin_users']
    if usertype not in allowed_tables:
        return jsonify({"message": "Invalid user type"}), 400

    try:
        query = f"SELECT * FROM {usertype}"
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()

        users = [dict(zip(columns, row)) for row in results]

        return jsonify(users), 200

    except Exception as e:
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



@get_users_routes.route("/v1/api/auth/get/user/<usertype>/<userId>", methods=['GET'])
def get_single_users(usertype, userId):
    allowed_tables = ['regular_users', 'admin_users']
    if usertype not in allowed_tables:
        return jsonify({"message": "Invalid user type"}), 400

    try:
        query = f"SELECT * FROM {usertype} WHERE userId = %s"
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query, (userId,))
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()

        users = [dict(zip(columns, row)) for row in results]

        return jsonify(users), 200

    except Exception as e:
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


