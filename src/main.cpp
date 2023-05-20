/*
References:
  https://randomnerdtutorials.com/esp32-web-server-spiffs-spi-flash-file-system/
*/
#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <PubSubClient.h>
#include <SPIFFS.h>
#include <WiFi.h>

/*
  CREDENTIALS
*/
// Network
const char* ssid = "CHANGE_ME";
const char* password = "CHANGE_ME";
// MQTT
const char* mqttServer = "CHANGE_ME";
const int mqttPort = "CHANGE_ME";
const char* mqttUser = "CHANGE_ME";
const char* mqttPassword = "CHANGE_ME";
const char* mqttTopicRead = "CHANGE_ME";
const char* mqttTopicPublish = "CHANGE_ME";

/*
  SERVER/CLIENT DECLARATION
*/
// Create PubSubClient
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

/*
  PORT CONFIGURATION
*/
// Set LED GPIO
const int pumpPin = 27;
const int boardLedPin = 2;

/*
  STATIC IP
*/
// Set your Static IP address
IPAddress local_IP(192, 168, 0, 69);
// Set your Gateway IP address
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);    // optional
IPAddress secondaryDNS(8, 8, 4, 4);  // optional

/*
  VARIABLES DECLARATION
*/
// Stores LED state
String ledState;
// Variable to store the HTTP request
String requestFromClient;

// Replaces placeholder with LED state value
String processor(const String& var) {
  Serial.println(var);
  if (var == "STATE") {
    if (digitalRead(pumpPin)) {
      ledState = "ON";
    } else {
      ledState = "OFF";
    }
    Serial.print(ledState);
    return ledState;
  }
  return String();
}

void setup_mqtt() {
  // Loop until we're reconnected
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP32Client-IrrigaTOP";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (mqttClient.connect(clientId.c_str(), mqttUser, mqttPassword)) {
      Serial.println("connected");
      mqttClient.subscribe(mqttTopicRead);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setPump(String status) {
  Serial.println();
  Serial.print("Pump Status:");
  Serial.println(status);
  if (status == "ON") {
    Serial.print("--- Turnin Pump ON ---");
    digitalWrite(pumpPin, HIGH);
  } else if (status == "OFF") {
    Serial.print("--- Turnin Pump OFF ---");
    digitalWrite(pumpPin, LOW);
  }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("-------New message from Broker-----");
  Serial.print("channel:");
  Serial.println(topic);
  Serial.print("data:");
  Serial.write(payload, length);
  String messageTemp;
  for (int i = 0; i < length; i++) {
    messageTemp += (char)payload[i];
  }
  setPump(messageTemp);
  Serial.println();
}

void publishPumpStatus() {
  const char* pumpStatus;
  if (digitalRead(pumpPin)) {
    pumpStatus = "ON";
  }
  else {
    pumpStatus = "OFF";
  }

  if (!mqttClient.connected()) {
    setup_mqtt();
  }
  mqttClient.publish(mqttTopicPublish, pumpStatus);
}

void setup_asyncWebServerRoutes() {
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
    digitalWrite(pumpPin, HIGH);
    request->send(SPIFFS, "/index.html", String(), false, processor);
  });

  // Route to set GPIO to LOW
  server.on("/off", HTTP_GET, [](AsyncWebServerRequest* request) {
    digitalWrite(pumpPin, LOW);
    request->send(SPIFFS, "/index.html", String(), false, processor);
  });

  // Start server
  Serial.println("Starting server");
  server.begin();
}

void setup_spiffs() {
  // Initialize SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
}

void setup_wifi() {
  delay(10);
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

  // Print local IP address
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  Serial.println("########################");
  Serial.println("# SETUP");
  Serial.println("########################");

  // Initialize the output variables as outputs
  pinMode(boardLedPin, OUTPUT);
  pinMode(pumpPin, OUTPUT);
  // Set outputs to LOW
  digitalWrite(pumpPin, LOW);

  setup_spiffs();
  setup_wifi();
  setup_asyncWebServerRoutes();
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setCallback(mqtt_callback);
  setup_mqtt();
  publishPumpStatus();
}

void loop() {
  mqttClient.loop();
  // put your main code here, to run repeatedly:
  digitalWrite(boardLedPin, HIGH);
  // Serial.println("LED is on");
  delay(1000);
  digitalWrite(boardLedPin, LOW);
  // Serial.println("LED is off");
  delay(1000);
}
