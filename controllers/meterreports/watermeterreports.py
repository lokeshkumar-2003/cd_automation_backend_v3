from flask import Flask, jsonify, request, Blueprint, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from dbconfig import get_db_connection
from reportlab.lib.pagesizes import letter
import datetime


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

water_meter_readings_report_routes = Blueprint("meter_readings_report_routes", __name__)

@water_meter_readings_report_routes.route("/v1/api/watermeter/reading/report/<metername>", methods=["POST"])
def water_meter_readings_report_route(metername):
    data = request.get_json()

    from_date = data.get('from_date')
    to_date = data.get('to_date')

    if not from_date or not to_date:
        return jsonify({"message": "From and to date are required"}), 400

    if not metername:
        return jsonify({"message": "Meter name is required"}), 400

    query = "SELECT ReadingDate, ReadingValue FROM meterreadings WHERE MeterName = %s AND ReadingDate BETWEEN %s AND %s"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, (metername, from_date, to_date))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": f"Reading not found between {from_date} and {to_date}"}), 404

        readings = []
        for row in rows:
            raw_date = row[0]
            if isinstance(raw_date, str):
                raw_date = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S GMT")
            formatted_date = raw_date.strftime("%d/%m/%Y")

            readings.append({
                "reading_date": formatted_date,
                "reading_value": row[1]
            })

        return jsonify({"readings": readings}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@water_meter_readings_report_routes.route("/v1/api/meter/reading/report/pdf/<meterName>", methods=["POST"])
def generate_pdf_report(meterName):
    data = request.get_json()

    from_date = data.get('from_date')
    to_date = data.get('to_date')

    if not from_date or not to_date:
        return jsonify({"message": "From and to date are required"}), 400

    if not meterName:
        return jsonify({"message": "Meter name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT ReadingDate, MeterName, MeterID, ReadingValue, Username
        FROM meterreadings
        WHERE MeterName = %s AND ReadingDate BETWEEN %s AND %s
        ORDER BY ReadingDate DESC
        """
        cursor.execute(query, (meterName, from_date, to_date))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": f"No readings found between {from_date} and {to_date}"}), 404

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Report header
        pdf.setTitle(f"Water Meter Report - {meterName}")
        pdf.drawString(50, height - 40, "Water Meter Report")
        pdf.drawRightString(width - 50, height - 40, f"Meter Name: {meterName}")
        pdf.drawString(50, height - 60, f"From: {from_date} To: {to_date}")

        # Headers with MeterID
        headers = ["S.NO", "Date", "Meter Name", "Meter ID", "Reading Value", "Username"]
        x_positions = [50, 100, 220, 320, 400, 500]
        y_position = height - 100

        # Draw table headers
        def draw_headers(y):
            for i, header in enumerate(headers):
                pdf.drawString(x_positions[i], y, header)

        draw_headers(y_position)

        # Add data rows
        line_height = 20
        row_y = y_position

        for idx, row in enumerate(rows):
            row_y -= line_height
            if row_y < 50:
                pdf.showPage()
                row_y = height - 50
                draw_headers(row_y)
                row_y -= line_height

            pdf.drawString(x_positions[0], row_y, str(idx + 1))    
            pdf.drawString(x_positions[1], row_y, str(row[0]))      
            pdf.drawString(x_positions[2], row_y, str(row[1]))      
            pdf.drawString(x_positions[3], row_y, str(row[2]))      
            pdf.drawString(x_positions[4], row_y, str(row[3]))      
            pdf.drawString(x_positions[5], row_y, str(row[4]))      

        pdf.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{meterName}_report.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@water_meter_readings_report_routes.route("/v1/api/reports/meter/readings", methods=["POST"])
def get_meter_readings():
    data = request.get_json()

    meter_name = data.get("meterName")
    from_date = data.get("fromdate")
    to_date = data.get("todate")
    print(to_date)
    if not meter_name or not from_date or not to_date:
        return jsonify({"message": "meterName, fromdate, and todate are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
        SELECT ReadingID, ReadingDate, ReadingValue, MeterID, Username, MeterName
        FROM meterreadings
        WHERE MeterName = %s
          AND ReadingDate BETWEEN %s AND %s
        ORDER BY ReadingDate ASC
        """
        cursor.execute(query, (meter_name, from_date, to_date))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "message": f"No readings found for meter: {meter_name} between {from_date} and {to_date}"
            }), 404

        readings = []
        for row in rows:
            readings.append({
                "reading_id": row[0],
                "reading_date": row[1],
                "reading_value": row[2],
                "meter_id": row[3],
                "username": row[4],
                "meter_name": row[5]
            })

        return jsonify(readings), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
