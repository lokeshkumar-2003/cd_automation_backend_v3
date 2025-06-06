from flask import Flask, jsonify, request, Blueprint
from dbconfig import get_db_connection
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

meter_details_routes = Blueprint("meter_details_routes", __name__)

@meter_details_routes.route("/v1/api/add/meters/<metertype>", methods=['POST'])
def add_main_meter(metertype):
    data = request.get_json()
    metername = data.get('metername')

    if not all([metertype, metername]):
        return jsonify({"message": "Meter type and meter name are required"}), 400

    allowed_metertype = ["Power Meter", "Water Meter"]
    if metertype not in allowed_metertype:
        return jsonify({"error": "Invalid meter type"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO meters (MeterName, MeterType, MeterStatus, ActivationDate, DeactivationDate)
            VALUES (%s, %s, %s, %s, %s)
        """
        now_datetime = datetime.now()
        cursor.execute(query, (metername, metertype, "Active", now_datetime, None))

        conn.commit()
        return jsonify({"message": f"{metername} added successfully to Meters table"}), 201

    except Exception as e:
        print("Error in add_main_meter:", e)
        return jsonify({"message": "Internal Server Error"}), 500

    finally:
        if conn:
            conn.close()

@meter_details_routes.route("/v1/api/add/submeter/<submetername>", methods=['POST'])
def add_submeter(submetername):
    data = request.get_json()
    metername = data.get('metername')

    if not metername:
        return jsonify({"message": "Meter name is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO meters 
            (MeterName, MeterType, MeterStatus, ActivationDate, DeactivationDate, SubMeterName)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        now_datetime = datetime.now()
        cursor.execute(query, (metername, "Power Meter", "Active", now_datetime, None, submetername))

        conn.commit()
        return jsonify({"message": f"{metername} added successfully"}), 201

    except Exception as e:
        print("Error in add_submeter:", e)
        return jsonify({"message": "Internal Server Error"}), 500

    finally:
        if conn:
            conn.close()

@meter_details_routes.route("/v1/api/edit/meters/name", methods=['PUT'])
def edit_meter_name():
    data = request.get_json()
    oldmetername = data.get("oldmetername")
    newmetername = data.get("newmetername")
    metertype = data.get("metertype")
    print(oldmetername, newmetername, metertype)
    if metertype not in ["Power Meter", "Water Meter"]:
        return jsonify({"error": "Invalid meter type"}), 400

    query = """
        UPDATE meters SET MeterName = %s
        WHERE MeterName = %s AND MeterType = %s
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (newmetername, oldmetername, metertype))
        conn.commit()
        return {"message": "Meter updated successfully"}, 200

    except Exception as e:
        print("Error in edit_meter_name: ", e)
        return {"message": "Internal Server Error"}, 500

    finally:
        if conn:
            conn.close()

@meter_details_routes.route("/v1/api/delete/meter/<meterType>/<int:meterId>", methods=['DELETE'])
def delete_meter(meterId, meterType):
    try:
        query = "SELECT * FROM Meters WHERE MeterId = %s AND MeterType = %s"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (meterId, meterType))
        meterData = cursor.fetchone()

        if not meterData:
            return jsonify({"message": "Meter not found"}), 404

        metername = meterData[1]  # Assuming MeterName is the second column

        updatequery = "DELETE FROM Meters WHERE MeterId = %s"
        cursor.execute(updatequery, (meterId,))
        conn.commit()

        return {"message": f"{metername} deleted successfully"}, 200

    except Exception as e:
        print("Error in delete_meter: ", e)
        return jsonify({"message": "Internal Server Error"}), 500

    finally:
        if conn:
            conn.close()

@meter_details_routes.route("/v1/api/update/meter/status/<meterType>/<int:meterId>/<status>", methods=['PUT'])
def meter_state(meterType, meterId, status):
    if status not in ["Activation", "Deactivation"]:
        return {"message": "Invalid meter action"}, 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM Meters WHERE MeterId = %s"
        cursor.execute(query, (meterId,))
        meterdata = cursor.fetchone()

        if not meterdata:
            return jsonify({"message": "Meter not found"}), 404

        now_datetime = datetime.now()
        status_value = "Active" if status == "Activation" else "Inactive"
        date_field = "ActivationDate" if status == "Activation" else "DeactivationDate"

        updationQuery = f"""
            UPDATE Meters SET MeterStatus = %s, {date_field} = %s
            WHERE MeterId = %s AND MeterType = %s
        """
        cursor.execute(updationQuery, (status_value, now_datetime, meterId, meterType))
        conn.commit()

        return {"message": f"Meter status updated to {status_value}"}, 200

    except Exception as e:
        print("Error in meter_state: ", e)
        return jsonify({"message": "Internal Server Error"}), 500

    finally:
        if conn:
            conn.close()

@meter_details_routes.route("/v1/api/meters/<meterType>", methods=['GET'])
def get_meters_by_type(meterType):
    if meterType not in ["Power Meter", "Water Meter"]:
      return jsonify({"error": "Invalid meter type"}), 400

    try:
      query = "SELECT * FROM Meters WHERE MeterType = %s"
      conn = get_db_connection()
      cursor = conn.cursor()

      cursor.execute(query, (meterType,))
      rows = cursor.fetchall()

      result = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
      if(meterType == "Water Meter"):
          return {"data": result}, 200
      else:
          return {"data":[{"MeterName":"Fabric Section"}, {"MeterName":"Conversion"}, {"MeterName":"Power House"}]}

    except Exception as e:
      print("Error in get_meters_by_type: ", e)
      return jsonify({"message": "Internal Server Error"}), 500

@meter_details_routes.route("/v1/api/sub/meters", methods=['GET'])
def get_sub_meters_by_type():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sub_meter_names = ["Power House", "Fabric Section", "Conversion"]

        result_map = {}

        for sub_meter in sub_meter_names:
            query = "SELECT * FROM meters WHERE SubMeterName = %s"
            cursor.execute(query, (sub_meter,))
            rows = cursor.fetchall()
            meters = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
            result_map[sub_meter] = meters

        return jsonify({"data": result_map}), 200

    except Exception as e:
        print("Error in get_sub_meters_by_type:", e)
        return jsonify({"message": "Internal Server Error"}), 500
    
@meter_details_routes.route("/v1/api/sub/meters/<subMeterName>", methods=['GET'])
def get_sub_meters(subMeterName):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM meters WHERE SubMeterName = %s"
        cursor.execute(query, (subMeterName,))
        rows = cursor.fetchall()
        meters = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

        return jsonify({"data": meters}), 200

    except Exception as e:
        print("Error in get_sub_meters:", e)
        return jsonify({"message": "Internal Server Error"}), 500

    finally:
        if 'conn' in locals() and conn:
            conn.close()

@meter_details_routes.route("/v1/api/update/sub/meter/status/<subMeterName>/<int:meterId>/<status>", methods=['PUT'])
def meter_sub_state(subMeterName, meterId, status):
    subMeterName = subMeterName.replace(' ', '')

    if status not in ["Activation", "Deactivation"]:
        return {"message": "Invalid meter action"}, 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM meters WHERE MeterId = %s"
        cursor.execute(query, (meterId,))
        meterdata = cursor.fetchone()

        if not meterdata:
            return jsonify({"message": "Meter not found"}), 404

        now_datetime = datetime.now()
        status_value = "Active" if status == "Activation" else "Inactive"
        date_field = "ActivationDate" if status == "Activation" else "DeactivationDate"

        updationQuery = f"""
            UPDATE meters
            SET MeterStatus = %s, {date_field} = %s
            WHERE MeterId = %s
        """
        cursor.execute(updationQuery, (status_value, now_datetime, meterId))
        conn.commit()
        conn.close()

        return {"message": f"Meter status updated to {status_value}"}, 200

    except Exception as e:
        print("Error in meter_state:", e)
        return jsonify({"message": "Internal Server Error"}), 500

@meter_details_routes.route("/v1/api/delete/sub/meter/<int:meterId>", methods=['DELETE'])
def delete_sub_meter(meterId):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM meters WHERE MeterId = %s"
        cursor.execute(query, (meterId,))
        meterData = cursor.fetchone()
        print(meterData)

        if not meterData:
            return jsonify({"message": "Meter not found"}), 404

        metername = meterData[1] 
        delete_query = "DELETE FROM meters WHERE MeterId = %s"
        cursor.execute(delete_query, (meterId,))
        conn.commit()

        return {"message": f"{metername} deleted successfully"}, 200

    except Exception as e:
        print("Error in delete_meter: ", e)
        return jsonify({"message": "Internal Server Error"}), 500
