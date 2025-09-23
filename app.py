# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, send_file
from config.config import config
from services.arduino_service import ArduinoService
from database.conexion import Conexion
from ultralytics import YOLO
from controllers.car_controller import car_bp

import pytesseract
import re
import io
import logging, os
import cv2
from datetime import datetime

model = YOLO("best.pt")

# configuración básica
env = os.getenv('FLASK_ENV', 'development')
app_cfg = config.get(env, config['default'])
app = Flask(__name__)
app.config.from_object(app_cfg)
logging.basicConfig(level=app_cfg.LOG_LEVEL)

# Registrar el blueprint de cars
app.register_blueprint(car_bp)

arduino = ArduinoService(base_url=app_cfg.BASE_URL)
db = Conexion()   # 👈 instancia la conexión

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
    placa = last_plate_text[:3] if last_plate_text else None
    
    if action == "open":
        # Verificar que haya una placa detectada
        if not placa:
            flash(" No se detectó ninguna placa", "danger")
            return redirect(url_for('index'))
            
        # Verificar que el vehículo esté registrado y tenga saldo suficiente
        automoviles = db.obtener_automoviles()
        auto = next((a for a in automoviles if a['placa'] == placa), None)
        
        if not auto:
            flash(f" El vehículo con placa {placa} no está registrado", "danger")
            return redirect(url_for('index'))
            
        if auto['saldo'] < 10:
            flash(f" Saldo insuficiente. Saldo actual: ${auto['saldo']}", "danger")
            return redirect(url_for('index'))
            
        # Descontar saldo y abrir talanquera
        nuevo_saldo = auto['saldo'] - 10
        db.actualizar_saldo(placa, nuevo_saldo)
        angle = app_cfg.OPEN_ANGLE
        
    elif action == "close":
        angle = app_cfg.CLOSED_ANGLE
    else:
        flash("Acción inválida", "error")
        return redirect(url_for('index'))

    ok = arduino.send_angle(angle, force=force)
    if ok and action == "open":
        flash(f"✅ Talanquera abierta. Se descontaron $10. Saldo restante: ${nuevo_saldo}", "success")
    elif ok:
        flash(f"✅ Talanquera cerrada", "success")
    else:
        flash(" Error enviando comando al ESP", "error")
    return redirect(url_for('index'))

def gen():
    global last_plate_crop, last_plate_text
    cap = cv2.VideoCapture(2)  # cámara (ajusta índice)
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

#  ruta para registrar autos
@app.route("/add_car", methods=["POST"])
def add_car():
    placa = request.form.get("placa_manual", "").strip().upper()
    if len(placa) != 3:
        flash(" La placa debe tener exactamente 3 caracteres.", "danger")
    else:
        try:
            saldo_inicial = 50  # saldo inicial
            costo_registro = 10  # costo de registro
            saldo_final = saldo_inicial - costo_registro
            
            # Registrar con el saldo después del descuento
            db.registrar_automovil(placa, saldo_final)
            flash(f" Automóvil {placa} registrado. Saldo inicial: ${saldo_inicial}, "
                  f"Costo registro: ${costo_registro}, Saldo final: ${saldo_final}", "success")
        except Exception as e:
            flash(f" Error al registrar automóvil: {e}", "danger")
    return redirect(url_for("index"))

# Ruta para recargar saldo
@app.route("/update_saldo", methods=["POST"])
def update_saldo():
    # Redirigir al endpoint del controlador
    return redirect(url_for('car.update_saldo'), code=307)  # Código 307 preserva el método POST


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


@app.route("/dashboard")
def dashboard():
    tarifa = 50.0 
    vehiculos_hoy = 0
    ingresos_totales = 0.0
    promedio_por_hora = 0.0
    hora_pico = "Sin datos"
    max_hora_conteo = 0
    ultima_actualizacion = "Sin datos"
    tiempo_promedio_min = None

    # Obtener lista completa de automóviles para estadísticas
    all_automoviles = db.obtener_automoviles()
    
    # Calcular estadísticas basadas en todos los automóviles
    vehiculos_hoy = len(all_automoviles)
    ingresos_totales = sum(auto['saldo'] for auto in all_automoviles)

    # Promedio por hora (promedio de saldos)
    if all_automoviles:
        promedio_por_hora = ingresos_totales / len(all_automoviles)
    else:
        promedio_por_hora = 0.0

    # Calcular cambios porcentuales basados en datos actuales
    vehiculos_con_saldo = sum(1 for auto in all_automoviles if auto['saldo'] > 0)
    change_vehiculos = (vehiculos_con_saldo / vehiculos_hoy * 100) if vehiculos_hoy > 0 else 0.0

    # Porcentaje de ingresos respecto al saldo inicial posible (50 por vehículo)
    saldo_posible_total = vehiculos_hoy * 50
    change_ingresos = (ingresos_totales / saldo_posible_total * 100) if saldo_posible_total > 0 else 0.0

    # Para promedio: coeficiente de variación (desviación estándar / media * 100)
    if all_automoviles and promedio_por_hora > 0:
        saldos = [auto['saldo'] for auto in all_automoviles]
        mean = sum(saldos) / len(saldos)
        variance = sum((x - mean) ** 2 for x in saldos) / len(saldos)
        std_dev = variance ** 0.5
        change_promedio = (std_dev / mean * 100) if mean > 0 else 0.0
    else:
        change_promedio = 0.0

    # Obtener últimos 10 automóviles para la tabla (ordenados por ID descendente)
    automoviles = all_automoviles[-10:][::-1]  # Últimos 10, ordenados del más reciente al más antiguo
    
    # Derivar métricas visibles en la sección "Estadísticas de Tiempo"
    hora_pico = f"{vehiculos_con_saldo} vehículos"
    max_hora_conteo = vehiculos_con_saldo
    tiempo_promedio_min = promedio_por_hora

    # Datos para el gráfico: saldo por vehículo (últimos 10)
    labels = [auto['placa'] for auto in automoviles]
    data = [auto['saldo'] for auto in automoviles]

    ultima_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ingresos_totales_str = f"${ingresos_totales:,.0f}"

    return render_template(
        "dashboard.html",
        vehiculos_hoy=vehiculos_hoy,
        ingresos_totales_str=ingresos_totales_str,
        promedio_por_hora=promedio_por_hora,
        hora_pico=hora_pico,
        max_hora_conteo=max_hora_conteo,
        tiempo_promedio_min=tiempo_promedio_min,
        ultima_actualizacion=ultima_actualizacion,
        automoviles=automoviles,
        change_vehiculos=change_vehiculos,
        change_ingresos=change_ingresos,
        change_promedio=change_promedio,
        labels=labels,
        data=data
    )


if __name__ == "__main__":
    app.run(debug=app_cfg.DEBUG, host="0.0.0.0", port=5000)
