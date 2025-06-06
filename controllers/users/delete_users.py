import re
from flask_cors import CORS
from dbconfig import get_db_connection
from flask import Flask, jsonify, request, Blueprint

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

delete_users_routes = Blueprint("delete_users_routes", __name__)

@delete_users_routes.route("/v1/api/auth/delete/<usertype>/<userId>", methods=['DELETE'])
def delete_user(usertype, userId):
    print(f"Received userId for deletion: {userId}")  # Debugging userId
    
    try:
        valid_tables = ['admin_users', 'regular_users']
        if usertype not in valid_tables:
            return jsonify({"message": "Invalid user type."}), 400

        # Strip any potential whitespace from userId
        userId = userId.strip()

        query = f"""
            DELETE FROM {usertype} 
            WHERE userId = %s
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        # Debugging query and userId
        print(f"Executing query: {query} with params: {userId}")

        cursor.execute(query, (userId,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": f"No user found with userId {userId}"}), 404

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
