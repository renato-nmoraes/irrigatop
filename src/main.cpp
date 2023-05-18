/*
References:
  https://randomnerdtutorials.com/esp32-web-server-spiffs-spi-flash-file-system/
*/
#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <SPIFFS.h>
#include <WiFi.h>

// Replace with your network credentials
const char* ssid = "acougue_2.4G";
const char* password = "BomDi@159";

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

// Variable to store the HTTP request
String requestFromClient;

// Set LED GPIO
const int ledPin = 27;
const int boardLedPin = 2;
// Stores LED state
String ledState;

// Set your Static IP address
IPAddress local_IP(192, 168, 0, 69);
// Set your Gateway IP address
IPAddress gateway(192, 168, 0, 1);

IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);    // optional
IPAddress secondaryDNS(8, 8, 4, 4);  // optional

// Replaces placeholder with LED state value
String processor(const String& var) {
  Serial.println(var);
  if (var == "STATE") {
    if (digitalRead(ledPin)) {
      ledState = "ON";
    } else {
      ledState = "OFF";
    }
    Serial.print(ledState);
    return ledState;
  }
  return String();
}

void setup() {
  Serial.begin(115200);
  Serial.println("########################");
  Serial.println("# SETUP");
  Serial.println("########################");

  // Initialize the output variables as outputs
  pinMode(boardLedPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  // Set outputs to LOW
  digitalWrite(ledPin, LOW);

  // Initialize SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }

  // Configures static IP address
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("STA Failed to configure");
  }

  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // Route for root / web page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest* request) {
    request->send(SPIFFS, "/index.html", String(), false, processor);
  });

  // Route to load style.css file
  server.on("/style.css", HTTP_GET, [](AsyncWebServerRequest* request) {
    request->send(SPIFFS, "/style.css", "text/css");
  });

  // Route to set GPIO to HIGH
  server.on("/on", HTTP_GET, [](AsyncWebServerRequest* request) {
    digitalWrite(ledPin, HIGH);
    request->send(SPIFFS, "/index.html", String(), false, processor);
  });

  // Route to set GPIO to LOW
  server.on("/off", HTTP_GET, [](AsyncWebServerRequest* request) {
    digitalWrite(ledPin, LOW);
    request->send(SPIFFS, "/index.html", String(), false, processor);
  });

  // Start server
  Serial.println("Starting server");
  server.begin();
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(boardLedPin, HIGH);
  // Serial.println("LED is on");
  delay(1000);
  digitalWrite(boardLedPin, LOW);
  // Serial.println("LED is off");
  delay(1000);
}
