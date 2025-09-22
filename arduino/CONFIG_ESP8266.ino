// esp_config.ino  (para cargar en el ESP8266)
// Asegúrate de seleccionar en Arduino IDE: Board -> "NodeMCU 1.0 (ESP-12E Module)" u otra correspondiente

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid     = "POLUX1";
const char* password = "@YECOWI79851521@";

ESP8266WebServer server(80);

void handleRoot() {
  server.send(200, "text/plain", "ESP8266 listo. Usa /servo?angle=ANG");
}

void handleServo() {
  if (!server.hasArg("angle")) { server.send(400,"text/plain","missing"); return; }
  String sAngle = server.arg("angle");
  int angle = sAngle.toInt();
  bool force = server.hasArg("force") && server.arg("force") == "1";
  if (force) {
    Serial.printf("F:%d\n", angle);
  } else {
    Serial.printf("%d\n", angle);
  }
  server.send(200, "text/plain", "ok");
}


void setup() {
  Serial.begin(115200); // velocidad con la que ESP hablará con Mega (asegúrate concordar en Mega)
  delay(100);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 15000UL) {
    delay(300);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi connected, IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("WiFi no conectado");
  }

  server.on("/", handleRoot);
  server.on("/servo", handleServo);
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}
