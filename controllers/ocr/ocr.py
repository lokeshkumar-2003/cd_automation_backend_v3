import os
import re
import uuid
import cv2
import traceback
from flask import Blueprint, request, jsonify
from paddleocr import PaddleOCR

ocr_routes = Blueprint('ocr_routes', __name__)
ocr = PaddleOCR(use_angle_cls=False, lang="en")

def preprocess_image(image_path: str) -> str:
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to read image at {image_path}")

    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    _, binary_inv = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
    preprocessed_path = f"preprocessed_{uuid.uuid4().hex}.jpg"
    cv2.imwrite(preprocessed_path, binary_inv)
    return preprocessed_path

@ocr_routes.route('/v1/api/ocr', methods=['POST'])
def run_ocr():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    filename = None
    preprocessed_path = None

    try:
        filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
        file.save(filename)

        preprocessed_path = preprocess_image(filename)

        results = ocr.ocr(preprocessed_path, cls=False)

        detected_text = ""
        if results:
            for result in results:
                if result:
                    for line in result:
                        detected_text += line[1][0] + " "

        digits_only = " ".join(re.findall(r'\d+', detected_text))
        print("digits", digits_only)
        return jsonify({"digits": digits_only.strip()}), 200

    except Exception as e:
        print(f"OCR error: {e}")
        traceback.print_exc()
        return jsonify({"message": f"OCR failed: {str(e)}"}), 500

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        if preprocessed_path and os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
