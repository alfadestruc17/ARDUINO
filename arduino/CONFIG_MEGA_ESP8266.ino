// mega_servo.ino  (para cargar en el ATmega Mega)
#include <Servo.h>

Servo myservo;
const int servoPin = 9;      // señal del servo (conectar al cable de señal del servo)

void setup() {
  Serial.begin(115200);    // USB Serial (monitor) - opcional
  Serial3.begin(115200);   // UART que usaremos para hablar con el ESP (TX3/RX3)
  myservo.attach(servoPin);
  myservo.write(90); // posición inicial centrada
  delay(500);
  Serial.println("Mega listo - esperando ángulos en Serial3");
}

void loop() {
  if (Serial3.available()) {
    String line = readLineFromSerial3();
    if (line.length() > 0) {
      bool forced = false;
      if (line.startsWith("F:")) {
        forced = true;
        line = line.substring(2); // quedamos solo con el número
      }

      int angle = line.toInt();
      if (angle < 0) angle = 0;
      if (angle > 180) angle = 180;

      if (forced) {
        myservo.write(angle);
        Serial.println("FORCED override aplicado");
      } else {
        myservo.write(angle);
        Serial.print("Override manual recibido, ángulo: ");
        Serial.println(angle);
      }
    }
  }
  // cualquier otra lógica de peaje que quieras añadir...
}

// ---------------- FUNCIONES AUXILIARES ----------------
String readLineFromSerial3() {
  String s = "";
  while (Serial3.available()) {
    char c = Serial3.read();
    if (c == '\n') break;
    if (c != '\r') s += c;
    if (s.length() > 40) break; // límite de seguridad
  }
  return s;
}
