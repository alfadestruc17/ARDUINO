from flask import Blueprint, request, redirect, url_for, flash
import time
from app_context import db, arduino, app_cfg

car_bp = Blueprint('car', __name__)

@car_bp.route("/add_car", methods=["POST"])
def add_car():
    placa = request.form.get("placa_manual", "").strip().upper()
    if len(placa) != 3:
        flash(" La placa debe tener exactamente 3 caracteres.", "danger")
    else:
        try:
            db.registrar_automovil(placa, 50)  # saldo inicial 50
            flash(f"✅ Automóvil {placa} registrado con saldo inicial de 50.", "success")
            # Abrir barrera
            ok_open = arduino.send_angle(app_cfg.OPEN_ANGLE)
            if ok_open:
                time.sleep(15)
                ok_close = arduino.send_angle(app_cfg.CLOSED_ANGLE)
                if ok_close:
                    flash("Barrera abierta y cerrada correctamente.", "success")
                else:
                    flash("Error cerrando barrera.", "error")
            else:
                flash("Error abriendo barrera.", "error")
        except Exception as e:
            flash(f" Error al registrar automóvil: {e}", "danger")
    return redirect(url_for("main.index"))

@car_bp.route("/update_saldo", methods=["POST"])
def update_saldo():
    placa = request.form.get("placa", "").strip().upper()
    try:
        monto_recarga = float(request.form.get("nuevo_saldo", 0))
        if monto_recarga <= 0:
            flash(" El monto de recarga debe ser mayor a 0.", "danger")
            return redirect(url_for("main.index"))

        # Obtener el saldo actual
        automoviles = db.obtener_automoviles()
        auto = next((a for a in automoviles if a['placa'] == placa), None)
        if auto is None:
            flash(" No se encontró el vehículo con esa placa.", "danger")
            return redirect(url_for("main.index"))
        nuevo_saldo = auto['saldo'] + monto_recarga
        db.actualizar_saldo(placa, nuevo_saldo)
        flash(f"✅ Recarga exitosa para {placa}: +${monto_recarga}. Nuevo saldo: ${nuevo_saldo}", "success")
    except ValueError:
        flash(" El monto debe ser un número válido.", "danger")
    except Exception as e:
        flash(f" Error al recargar saldo: {e}", "danger")
    return redirect(url_for("main.index"))