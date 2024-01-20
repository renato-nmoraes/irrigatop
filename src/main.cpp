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
const char* ssid = "acougue_2.4G";
const char* password = "BomDi@159";
// MQTT
const char* mqttServer = "34.42.244.45";
const int mqttPort = 59687;
const char* mqttUser = "irrigatop";
const char* mqttPassword = "irrigatop";
const char* mqttTopicReadAction = "irrigation/action";
const char* mqttTopicReadIntensity = "irrigation/intensity";
const char* mqttTopicReadPump = "irrigation/pump";
const char* mqttTopicPublishAction = "irrigation/status/action";
const char* mqttTopicPublishIntensity = "irrigation/status/intensity";
const char* mqttTopicPublishPump = "irrigation/status/pump";

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
const int pump1Pin = 27;
const int pump2Pin = 33;
const int pwmPin = 16;
const int boardLedPin = 2;
int pumpPin = pump1Pin;

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
// PWM
const int pwmFreq = 1000;
const int pwmChannel = 0;
const int pwmResolution = 8;
const char* pumpStatus;
char intensityChar[3];
char idChar[1];

// Stores LED state
String ledState;
// Variable to store the HTTP request
String requestFromClient;

// Replaces placeholder with LED state value
String processor(const String& var) {
  Serial.println(var);
  if (var == "STATE") {
    if (digitalRead(pumpPin)) {
      ledState = "OFF";
    } else {
      ledState = "ON";
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
      mqttClient.subscribe(mqttTopicReadAction);
      mqttClient.subscribe(mqttTopicReadIntensity);
      mqttClient.subscribe(mqttTopicReadPump);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void publishPumpStatus(bool pulse) {
  if (digitalRead(pumpPin)) {
    pumpStatus = "OFF";
  } else {
    pumpStatus = "ON";
  }

  if (pulse) {
    pumpStatus = "PULSE";
  }

  if (!mqttClient.connected()) {
    setup_mqtt();
  }
  mqttClient.publish(mqttTopicPublishAction, pumpStatus);
}

void publishPumpIntensity(const int intensity) {
  itoa(intensity, intensityChar, 10);
  if (!mqttClient.connected()) {
    setup_mqtt();
  }
  mqttClient.publish(mqttTopicPublishIntensity, intensityChar);
}

void publishPumpId(const int id) {
  itoa(id, idChar, 10);
  if (!mqttClient.connected()) {
    setup_mqtt();
  }
  mqttClient.publish(mqttTopicPublishPump, idChar);
}

void setPump(String status) {
  bool pulse = false;
  Serial.println();
  Serial.print("Pump Status:");
  Serial.println(status);
  if (status == "ON") {
    Serial.print("--- Turning Pump ON ---");
    digitalWrite(pumpPin, LOW);
  } else if (status == "OFF") {
    Serial.print("--- Turning Pump OFF ---");
    digitalWrite(pumpPin, HIGH);
  } else if (status == "PULSE") {
    Serial.print("--- Pulsing Pump 2s ---");
    pulse = true;
    digitalWrite(pumpPin, LOW);
    delay(2000);
    digitalWrite(pumpPin, HIGH);
  }
  publishPumpStatus(pulse);
}

void setup_pwm() {
  //ledcSetup(pwmChannel, pwmFreq, pwmResolution);
  //ledcAttachPin(pwmPin, pwmChannel);
  analogWriteResolution(pwmResolution);
  analogWriteFrequency(pwmFreq);
}

void set_pwm_intensity(const int intensity) {
  Serial.print("Pump Intensity:");
  Serial.println(intensity);
  uint32_t pwmPinValue;
  if (intensity != 0) {
    pwmPinValue = 2.56*intensity; //1.28 * intensity + 128;
  } else {
    pwmPinValue = 0;
  }
  Serial.print("PWM Pin Value:");
  Serial.println(pwmPinValue);

  analogWrite(pwmPin, pwmPinValue);
  publishPumpIntensity(intensity);
  //ledcWrite(pwmChannel, pwmPinValue);
}

void set_pump_id(const int pumpId) {
  Serial.print("Pump ID:");
  Serial.println(pumpId);

  if (pumpId == 1) {
    Serial.println("--- Setting Pump 1 Active ---");
    pumpPin = pump1Pin;
  } else if (pumpId == 2) {
    Serial.println("--- Setting Pump 2 Active ---");
    pumpPin = pump2Pin;
  }
  publishPumpId(pumpId);
  //ledcWrite(pwmChannel, pwmPinValue);
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("-------New message from Broker-----");
  Serial.println("MQTT Channel: ");
  Serial.println(topic);
  Serial.println("Message data:");
  Serial.write(payload, length);
  Serial.println("");
  String messageTemp;
  for (int i = 0; i < length; i++) {
    messageTemp += (char)payload[i];
  }
  if (strcmp(topic, mqttTopicReadAction) == 0) {
    Serial.println("--- Setting Pump ---");
    setPump(messageTemp);
  } else if (strcmp(topic, mqttTopicReadIntensity) == 0) {
    Serial.println("--- Setting Pump Intensity ---");
    set_pwm_intensity(messageTemp.toInt());
  } else if (strcmp(topic, mqttTopicReadPump) == 0) {
    set_pump_id(messageTemp.toInt());
  }
  Serial.println();
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
  pinMode(pump1Pin, OUTPUT);
  pinMode(pump2Pin, OUTPUT);
  // Set outputs to HIGH (TURN OFF PUMP)
  digitalWrite(pumpPin, HIGH);

  setup_spiffs();
  setup_wifi();
  setup_asyncWebServerRoutes();
  setup_pwm();
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setCallback(mqtt_callback);
  setup_mqtt();
  publishPumpStatus(false);
  publishPumpIntensity(0);
  publishPumpId(1);
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
