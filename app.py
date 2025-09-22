# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, send_file
from config.config import config
from services.arduino_service import ArduinoService
from database.conexion import Conexion

import logging, os
import cv2
from ultralytics import YOLO
import pytesseract
import re
import io

# Ruta al ejecutable de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# configuración básica
env = os.getenv('FLASK_ENV', 'development')
app_cfg = config.get(env, config['default'])
app = Flask(__name__)
app.config.from_object(app_cfg)
logging.basicConfig(level=app_cfg.LOG_LEVEL)

arduino = ArduinoService(base_url=app_cfg.BASE_URL)
db = Conexion()   # 👈 instancia la conexión

model = YOLO("best.pt")

# Variables globales
last_plate_crop = None
last_plate_text = ""

@app.route("/")
def index():
    lista_autos = db.obtener_automoviles()   # 👈 pasa la lista de autos
    return render_template(
        "index.html",
        open_angle=app_cfg.OPEN_ANGLE,
        closed_angle=app_cfg.CLOSED_ANGLE,
        automoviles=lista_autos
    )

@app.route("/send", methods=["POST"])
def send():
    action = request.form.get("action")
    force = request.form.get("force") == "1"
    if action == "open":
        angle = app_cfg.OPEN_ANGLE
    elif action == "close":
        angle = app_cfg.CLOSED_ANGLE
    else:
        flash("Acción inválida", "error")
        return redirect(url_for('index'))

    ok = arduino.send_angle(angle, force=force)
    if ok:
        flash(f"Comando enviado: angle={angle} (force={force})", "success")
    else:
        flash("Error enviando comando al ESP", "error")
    return redirect(url_for('index'))

def gen():
    global last_plate_crop, last_plate_text
    cap = cv2.VideoCapture(1)  # cámara (ajusta índice)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detección YOLO
        results = model(frame, verbose=False)
        annotated_frame = frame.copy()

        for result in results:
            index_plates = (result.boxes.cls == 0).nonzero(as_tuple=True)[0]  # clase placa
            for idx in index_plates:
                conf = result.boxes.conf[idx].item()
                if conf > 0.5:
                    xyxy = result.boxes.xyxy[idx].squeeze().tolist()
                    x1, y1, x2, y2 = map(int, xyxy)

                    # Recorte de la placa
                    plate_crop = frame[max(0, y1-15):y2+15, max(0, x1-15):x2+15]
                    if plate_crop.size > 0:
                        last_plate_crop = plate_crop
                        # Save for debugging
                        cv2.imwrite("debug_plate.jpg", plate_crop)

                        # OCR with Tesseract
                        text = pytesseract.image_to_string(plate_crop, lang='eng')
                        logging.info(f"OCR text: {text}")
                        # Clean the text: keep only alphanumeric, uppercase
                        cleaned_text = re.sub(r'[^A-Z0-9]', '', text.upper())
                        if cleaned_text:  # Only update if OCR found text
                            last_plate_text = cleaned_text
                        logging.info(f"Final plate text: {last_plate_text}")

                    # Dibujar sobre el frame
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, last_plate_text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # Codificar frame para enviar al navegador
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 🚀 Nueva ruta para registrar autos
@app.route("/add_car", methods=["POST"])
def add_car():
    placa = request.form.get("placa", "").strip().upper()
    if len(placa) != 3:
        flash("❌ La placa debe tener exactamente 3 caracteres.", "danger")
    else:
        try:
            db.registrar_automovil(placa, 50)  # saldo inicial 50
            flash(f"✅ Automóvil {placa} registrado con saldo inicial de 50.", "success")
        except Exception as e:
            flash(f"❌ Error al registrar automóvil: {e}", "danger")
    return redirect(url_for("index"))




@app.route("/get_plate_text")
def get_plate_text():
    """Devuelve el texto de la placa en JSON para actualizar input en frontend"""
    return jsonify({"text": last_plate_text})

@app.route("/get_plate_crop")
def get_plate_crop():
    global last_plate_crop
    if last_plate_crop is None:
        return ("", 204)  # No Content si aún no hay placas

    # Convertir el recorte a JPG en memoria
    _, buffer = cv2.imencode('.jpg', last_plate_crop)
    io_buf = io.BytesIO(buffer)
    return send_file(io_buf, mimetype='image/jpeg')


if __name__ == "__main__":
    app.run(debug=app_cfg.DEBUG, host="0.0.0.0", port=5000)
