# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from config.config import config
from services.arduino_service import ArduinoService
import logging, os

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

if __name__ == "__main__":
    app.run(debug=app_cfg.DEBUG, host="0.0.0.0", port=5000)
