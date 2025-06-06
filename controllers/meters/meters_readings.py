from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
from datetime import datetime
from dbconfig import get_db_connection

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

meter_readings_routes = Blueprint("meter_readings_routes", __name__)

@meter_readings_routes.route("/v1/api/check/meter/status/<metername>/<metertype>", methods=['GET'])
def check_meter_status(metername, metertype):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        check_query = "SELECT MeterStatus, MeterType FROM meters WHERE MeterName = %s"
        cursor.execute(check_query, (metername,))
        result = cursor.fetchone()

        if not result:
            return jsonify({
                "message": f"No meter found with the name {metername}"
            }), 404

        meter_status, meter_type = result
        meter_type = meter_type.replace(" ", "")

        if meter_type.lower() != metertype.lower():
            return jsonify({
                "message": f"Meter {metername} is of type '{meter_type}', not '{metertype}'."
            }), 404

        if meter_status == "Inactive":
            return jsonify({
                "message": f"Readings cannot be added for the {meter_type} meter {metername} as it is currently inactive."
            }), 400

        return jsonify({
            "message": f"Meter {metername} is active and ready for readings.",
            "meterType": meter_type
        }), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            "message": "An internal error occurred."
        }), 500

    finally:
        if conn:
            conn.close()


@meter_readings_routes.route("/v1/api/add/readings/watermeter/<metername>", methods=['POST'])
def add_water_meter_reading_value(metername):
    try:
        data = request.get_json()

        if not data:
            return jsonify({"message": "Request body is missing"}), 400

        username = data.get("username")
        reading_value = data.get("readingValue")

        if not metername:
            return jsonify({"message": "Meter name is required"}), 400

        if username is None:
            return jsonify({"message": "Username is required"}), 400

        if reading_value is None:
            return jsonify({"message": "readingValue is required"}), 400
        
        

        # Convert reading_value to float and validate range (if needed)
        try:
            reading_value = float(reading_value)
        except (ValueError, TypeError):
            return jsonify({"message": "readingValue must be a valid number"}), 400

        # Optional: add range validation if your DB limits are known
        # For example, if ReadingValue is a FLOAT(10,2), limit accordingly
        if not (-1e10 < reading_value < 1e10):
            return jsonify({"message": "readingValue is out of acceptable range"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        check_query = "SELECT MeterName, MeterStatus, MeterID FROM Meters WHERE MeterName = %s"
        cursor.execute(check_query, (metername,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "Meter not found"}), 404

        meter_name, meter_status, meter_id = result

        if meter_status.lower() == "inactive":
            return jsonify({"message": f"{meter_name} is currently inactive"}), 400

        insert_query = """
            INSERT INTO meterreadings (MeterID, MeterName, ReadingDate, ReadingValue, Username)
            VALUES (%s, %s, %s, %s, %s)
        """
        now_date = datetime.now().date()
        exist_readings_query = "SELECT * FROM meterreadings WHERE MeterName = %s AND ReadingDate = %s"
        cursor.execute(exist_readings_query, (metername, now_date,))
        exist_reading = cursor.fetchall()

        if len(exist_reading) > 0:  
            return jsonify({"message": "Reading for today already exists"}), 400

        reading_date = datetime.now().date()
        cursor.execute(insert_query, (meter_id, metername, reading_date, reading_value, username))
        conn.commit()

        return jsonify({
            "message": "Reading added successfully",
            "data": {
                "meter_id": meter_id,
                "meter_name": metername,
                "reading_value": reading_value,
                "reading_date": str(reading_date),
                "username": username
            }
        }), 200

    except Exception as e:
        print("Error in add_water_meter_reading_value:", e)
        return jsonify({"message": "Internal server error"}), 500

    finally:
        if 'conn' in locals() and conn:
            conn.close()

@meter_readings_routes.route("/v1/api/get/readings/watermeter/<int:meterId>", methods=['GET'])
def get_water_meter_reading_value(meterId):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM meterreadings WHERE MeterID = %s"
        cursor.execute(query, (meterId,))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": "No readings found for this meter ID"}), 404

        result = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

        return jsonify({"data": result}), 200

    except Exception as e:
        print("Error in get_water_meter_reading_value:", e)
        return jsonify({"message": "Internal server error"}), 500

    finally:
        if 'conn' in locals() and conn:
            conn.close()


@meter_readings_routes.route("/v1/api/watermeter/reading/recent/<meterName>", methods=["GET"])
def water_meter_readings_recent_route(meterName):
    if not meterName:
        return jsonify({"message": "Meter Name is required"}), 400

    query = """
        SELECT ReadingDate, ReadingValue
        FROM meterreadings 
        WHERE MeterName = %s 
        ORDER BY ReadingDate DESC
        LIMIT 30
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, (meterName,))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": "No recent readings found"}), 404

        readings = [
            {"reading_date": str(row[0]), "reading_value": row[1]}
            for row in rows
        ]

        return jsonify({"readings": readings}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
