from flask import Blueprint, request, redirect, url_for, flash
import time
from app_context import db, arduino, app_cfg
from dataclasses import dataclass
from typing import Optional, Tuple

car_bp = Blueprint('car', __name__)

@dataclass
class CarRegistration:
    placa: str
    saldo_inicial: float = 50.0
    costo_registro: float = 10.0

    def validar_placa(self) -> Tuple[bool, Optional[str]]:
        """Valida el formato de la placa"""
        if not self.placa:
            return False, "La placa no puede estar vacía."
        if len(self.placa) != 3:
            return False, "La placa debe tener exactamente 3 caracteres."
        return True, None

    def calcular_saldo_final(self) -> float:
        """Calcula el saldo final después del costo de registro"""
        return self.saldo_inicial - self.costo_registro

    def validar_saldo(self) -> Tuple[bool, Optional[str]]:
        """Valida si hay saldo suficiente para el registro"""
        saldo_final = self.calcular_saldo_final()
        if saldo_final < 0:
            return False, f"Saldo insuficiente. Se requiere mínimo ${self.costo_registro}"
        return True, None

@car_bp.route("/add_car", methods=["POST"])
def add_car():
    try:
        # Obtener y validar datos de registro
        placa = request.form.get("placa_manual", "").strip().upper()
        registro = CarRegistration(placa=placa)
        
        # Validar formato de placa
        valid_placa, error_msg = registro.validar_placa()
        if not valid_placa:
            flash(f" {error_msg}", "danger")
            return redirect(url_for("main.index"))
        
        # Verificar si el vehículo ya existe y procesar el paso
        automoviles = db.obtener_automoviles()
        auto_existente = next((auto for auto in automoviles if auto['placa'] == placa), None)
        
        if auto_existente:
            # Vehículo existente - procesar paso
            costo_paso = 10  # Costo por paso
            if auto_existente['saldo'] < costo_paso:
                flash(f" Saldo insuficiente para el vehículo {placa}. Saldo actual: ${auto_existente['saldo']}", "danger")
                return redirect(url_for("main.index"))
                
            nuevo_saldo = auto_existente['saldo'] - costo_paso
            db.actualizar_saldo(placa, nuevo_saldo)
            flash(f" Paso registrado para {placa}. Cobrado: ${costo_paso}. Nuevo saldo: ${nuevo_saldo}", "success")
            
            # Abrir barrera para vehículo existente
            ok_open = arduino.send_angle(app_cfg.OPEN_ANGLE)
            if not ok_open:
                flash(" Error abriendo barrera.", "error")
                return redirect(url_for("main.index"))
            
            time.sleep(15)
            ok_close = arduino.send_angle(app_cfg.CLOSED_ANGLE)
            if ok_close:
                flash(" Barrera operada correctamente.", "success")
            else:
                flash(" Error cerrando barrera.", "error")
            
            return redirect(url_for("main.index"))
        
        # Validar saldo
        valid_saldo, error_saldo = registro.validar_saldo()
        if not valid_saldo:
            flash(f" {error_saldo}", "danger")
            return redirect(url_for("main.index"))
        
        # Calcular saldo final y registrar
        saldo_final = registro.calcular_saldo_final()
        db.registrar_automovil(placa, saldo_final)
        
        # Mensaje de éxito con detalles
        flash(
            f" Automóvil {placa} registrado:\n"
            f"Saldo inicial: ${registro.saldo_inicial}\n"
            f"Costo registro: ${registro.costo_registro}\n"
            f"Saldo final: ${saldo_final}",
            "success"
        )
        
        # Controlar barrera
        ok_open = arduino.send_angle(app_cfg.OPEN_ANGLE)
        if not ok_open:
            flash(" Error abriendo barrera.", "error")
            return redirect(url_for("main.index"))
        
        time.sleep(15)
        ok_close = arduino.send_angle(app_cfg.CLOSED_ANGLE)
        if ok_close:
            flash(" Barrera operada correctamente.", "success")
        else:
            flash(" Error cerrando barrera.", "error")
            
    except Exception as e:
        flash(f" Error en el registro: {str(e)}", "danger")
        
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
        flash(f" Recarga exitosa para {placa}: +${monto_recarga}. Nuevo saldo: ${nuevo_saldo}", "success")
    except ValueError:
        flash(" El monto debe ser un número válido.", "danger")
    except Exception as e:
        flash(f" Error al recargar saldo: {e}", "danger")
    return redirect(url_for("main.index"))