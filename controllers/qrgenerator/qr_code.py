import qrcode
import io
from flask_cors import CORS
from flask import Flask, request, Blueprint, send_file

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

qr_generator_routes = Blueprint("qr_generator_routes", __name__)

@qr_generator_routes.route('/v1/api/generate_qr/meter', methods=['POST'])
def generate_qr():
    data = request.get_json()
    meter_name = data.get('meter_name') if data else None
    if not meter_name:
        return 'meter_name is required', 400

    qr = qrcode.make(meter_name)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')