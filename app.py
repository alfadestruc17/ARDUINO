# app.py
from flask import Flask
from config.config import config
from services.arduino_service import ArduinoService
from database.conexion import Conexion
from database.car_repository import CarRepository
from services.video_service import VideoService
import os
import logging

# Set up app context
import app_context

# configuración básica
env = os.getenv('FLASK_ENV', 'development')
app_cfg = config.get(env, config['default'])
app = Flask(__name__)
app.config.from_object(app_cfg)
logging.basicConfig(level=app_cfg.LOG_LEVEL)

arduino = ArduinoService(base_url=app_cfg.BASE_URL)
db = Conexion()
car_repo = CarRepository(db)
video_service = VideoService()

# Set context
app_context.db = db
app_context.arduino = arduino
app_context.app_cfg = app_cfg
app_context.car_repo = car_repo
app_context.video_service = video_service

# Import and register blueprints
from controllers.main_controller import main_bp
from controllers.car_controller import car_bp
from controllers.video_controller import video_bp
from controllers.dashboard_controller import dashboard_bp

app.register_blueprint(main_bp)
app.register_blueprint(car_bp)
app.register_blueprint(video_bp)
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    app.run(debug=app_cfg.DEBUG, host="0.0.0.0", port=5000)
