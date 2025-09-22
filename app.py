# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from config.config import config
from services.arduino_service import ArduinoService
from database.conexion import Conexion

import logging, os
import cv2
from ultralytics import YOLO


# configuración básica
env = os.getenv('FLASK_ENV', 'development')
app_cfg = config.get(env, config['default'])
app = Flask(__name__)
app.config.from_object(app_cfg)
logging.basicConfig(level=app_cfg.LOG_LEVEL)

arduino = ArduinoService(base_url=app_cfg.BASE_URL)
db = Conexion()   # 👈 instancia la conexión

model = YOLO("yolo11n.pt")  


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


if __name__ == "__main__":
    app.run(debug=app_cfg.DEBUG, host="0.0.0.0", port=5000)
