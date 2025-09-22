# services/arduino_service.py
import requests
import logging
from config.config import Config

logger = logging.getLogger(__name__)

class ArduinoService:
    def __init__(self, base_url: str = None, timeout: float = 3.0):
        # base_url: http://<ip>
        self.base_url = (base_url or Config.BASE_URL).rstrip("/")
        self.timeout = timeout

    def send_angle(self, angle: int, force: bool = False) -> bool:
        """
        Envía un ángulo al ESP que lo reenviará al Mega.
        angle: 0 - 180
        force: si True, indica al ESP que marque esta orden como forzada
        """
        try:
            angle = int(angle)
            if angle < 0 or angle > 180:
                raise ValueError("angle debe estar entre 0 y 180")

            # endpoint: /servo?angle=NN  (añadimos &force=1 si es forzado)
            url = f"{self.base_url}/servo"
            params = {"angle": str(angle)}
            if force:
                params["force"] = "1"

            logger.info(f"Enviando a Arduino (ESP): {url} params={params}")
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()  # lanza excepción si código != 2xx

            # opcional: chequear contenido si quieres
            logger.debug(f"Respuesta ESP: {resp.status_code} - {resp.text}")
            return True

        except Exception as e:
            logger.warning(f"[ArduinoService] Error enviando angle {angle}: {e}")
            return False
