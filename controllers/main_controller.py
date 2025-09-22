from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_context import db, app_cfg, arduino

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    lista_autos = db.obtener_automoviles()
    return render_template(
        "index.html",
        open_angle=app_cfg.OPEN_ANGLE,
        closed_angle=app_cfg.CLOSED_ANGLE,
        automoviles=lista_autos
    )

@main_bp.route("/send", methods=["POST"])
def send():
    action = request.form.get("action")
    force = request.form.get("force") == "1"
    if action == "open":
        angle = app_cfg.OPEN_ANGLE
    elif action == "close":
        angle = app_cfg.CLOSED_ANGLE
    else:
        flash("Acción inválida", "error")
        return redirect(url_for('main.index'))

    ok = arduino.send_angle(angle, force=force)
    if ok:
        flash(f"Comando enviado: angle={angle} (force={force})", "success")
    else:
        flash("Error enviando comando al ESP", "error")
    return redirect(url_for('main.index'))