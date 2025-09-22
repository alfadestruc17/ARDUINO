# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from config.config import config
from services.arduino_service import ArduinoService
import logging, os
import cv2

# configuración básica
env = os.getenv('FLASK_ENV', 'development')
app_cfg = config.get(env, config['default'])
app = Flask(__name__)
app.config.from_object(app_cfg)
logging.basicConfig(level=app_cfg.LOG_LEVEL)

arduino = ArduinoService(base_url=app_cfg.BASE_URL)

@app.route("/")
def index():
    return render_template("index.html", open_angle=app_cfg.OPEN_ANGLE, closed_angle=app_cfg.CLOSED_ANGLE)

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
    cap = cv2.VideoCapture(2)  # camera 1 (second camera)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=app_cfg.DEBUG, host="0.0.0.0", port=5000)
