import cv2
import logging
from ultralytics import YOLO
import pytesseract
from utils.ocr_utils import clean_plate_text

class VideoService:
    def __init__(self):
        self.model = YOLO("best.pt")
        self.last_plate_crop = None
        self.last_plate_text = ""

    def gen(self):
        cap = cv2.VideoCapture(0)  # cámara (ajusta índice)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detección YOLO
            results = self.model(frame, verbose=False)
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
                            self.last_plate_crop = plate_crop
                            # Save for debugging
                            cv2.imwrite("debug_plate.jpg", plate_crop)

                            # OCR with Tesseract
                            text = pytesseract.image_to_string(plate_crop, lang='eng')
                            logging.info(f"OCR text: {text}")
                            # Clean the text
                            cleaned_text = clean_plate_text(text)
                            if cleaned_text:  # Only update if OCR found text
                                self.last_plate_text = cleaned_text
                            logging.info(f"Final plate text: {self.last_plate_text}")

                        # Dibujar sobre el frame
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, self.last_plate_text, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            # Codificar frame para enviar al navegador
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def get_last_plate_text(self):
        return self.last_plate_text

    def get_last_plate_crop(self):
        return self.last_plate_crop