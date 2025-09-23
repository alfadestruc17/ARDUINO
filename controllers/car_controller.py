from flask import Blueprint, request, redirect, url_for, flash
import time
from app_context import db, arduino, app_cfg
from database.car_repository import CarRepository
from services.car_service import CarService

car_bp = Blueprint('car', __name__)
car_repository = CarRepository(db)
car_service = CarService(car_repository)

@car_bp.route("/add_car", methods=["POST"])
def add_car():
    placa = request.form.get("placa_manual", "")
    try:
        # Registrar el vehículo con validaciones y descuento
        result = car_service.register_car(placa)
        
        flash(f"✅ Automóvil {result['placa']} registrado. "
              f"Saldo inicial: ${result['saldo_inicial']}, "
              f"Costo registro: ${result['costo_registro']}, "
              f"Saldo final: ${result['saldo_final']}", "success")
              
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
    except ValueError as e:
        flash(f" {str(e)}", "danger")
    except Exception as e:
        flash(f" Error al registrar automóvil: {e}", "danger")
    return redirect(url_for("main.index"))

@car_bp.route("/update_saldo", methods=["POST"])
def update_saldo():
    placa = request.form.get("placa", "")
    try:
        monto_recarga = float(request.form.get("nuevo_saldo", 0))
        result = car_service.update_balance(placa, monto_recarga)
        flash(f"✅ Recarga exitosa para {result['placa']}: "
              f"+${result['monto_recarga']}. Nuevo saldo: ${result['nuevo_saldo']}", "success")
    except ValueError as e:
        flash(f" {str(e)}", "danger")
    except Exception as e:
        flash(f" Error al recargar saldo: {e}", "danger")
    return redirect(url_for("main.index"))