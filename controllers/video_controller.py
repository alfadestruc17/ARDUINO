from flask import Blueprint, Response, jsonify, send_file
import io
import cv2
from app_context import video_service

video_bp = Blueprint('video', __name__)

@video_bp.route('/video_feed')
def video_feed():
    # Assuming video_service.gen() is available
    return Response(video_service.gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@video_bp.route("/get_plate_text")
def get_plate_text():
    """Devuelve el texto de la placa en JSON para actualizar input en frontend"""
    return jsonify({"text": video_service.get_last_plate_text()})

@video_bp.route("/get_plate_crop")
def get_plate_crop():
    plate_crop = video_service.get_last_plate_crop()
    if plate_crop is None:
        return ("", 204)  # No Content si aún no hay placas

    # Convertir el recorte a JPG en memoria
    _, buffer = cv2.imencode('.jpg', plate_crop)
    io_buf = io.BytesIO(buffer)
    return send_file(io_buf, mimetype='image/jpeg')