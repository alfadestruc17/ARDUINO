import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de datos
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_DATABASE = os.getenv('DB_DATABASE', 'arduino')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Arduino/ESP por IP
    ARDUINO_IP = os.getenv('ARDUINO_IP', '192.168.101.72')
    BASE_URL = f"http://{ARDUINO_IP}".rstrip("/")

    # Comportamiento del servo
    OPEN_ANGLE = int(os.getenv('OPEN_ANGLE', '0'))    # angulo "abrir"
    CLOSED_ANGLE = int(os.getenv('CLOSED_ANGLE', '180')) # angulo "cerrar"

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE  = os.getenv('LOG_FILE', 'app.log')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
