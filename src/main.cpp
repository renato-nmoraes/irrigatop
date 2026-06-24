/*
References:
  https://randomnerdtutorials.com/esp32-web-server-spiffs-spi-flash-file-system/
*/
#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <PubSubClient.h>
#include <SPIFFS.h>
#include <WiFi.h>
#include <esp_task_wdt.h>

/*
  Network and MQTT Configuration
*/
const char* ssid = "acougue";
const char* password = "BomDi@159";
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
const char* mqttTopicPublishHealth = "irrigation/health";

/*
  GPIO Configuration
*/
const int pump1Pin = 27;
const int pump2Pin = 33;
const int pwmPin = 16;
const int boardLedPin = 2;

int pumpPin = pump1Pin; // Active pump
bool pumpState = false; // Tracks pump state (OFF = false, ON = true)

/*
  PWM Configuration
*/
const int pwmFreq = 1000;
const int pwmResolution = 8;

/*
  Static IP Configuration
*/
IPAddress local_IP(192, 168, 15, 69);
IPAddress gateway(192, 168, 15, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);
IPAddress secondaryDNS(8, 8, 4, 4);

/*
  WiFi and MQTT Configuration
*/
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
AsyncWebServer server(80);

/*
  System Variables
*/
// Stores LED state
bool ledState = false;
// Variable to store the HTTP request
String requestFromClient;

unsigned long lastMQTTReconnectAttempt = 0;
const unsigned long mqttReconnectInterval = 5000;

unsigned long lastWiFiReconnectAttempt = 0;
const unsigned long wifiReconnectInterval = 10000;
const unsigned long wifiConnectTimeout = 20000; // Stop blocking after 20s and retry in loop()

unsigned long lastLEDUpdate = 0;
const unsigned long ledBlinkInterval = 1000;

unsigned long lastHealthCheck = 0;
const unsigned long healthCheckInterval = 10000; // Send health check every 10 seconds

// Hardware watchdog: reboot the board if loop() stalls for this long. Must
// comfortably exceed the 2s blocking delay in the PULSE path.
const uint32_t wdtTimeoutSeconds = 30;

// Self-recovery: if MQTT stays unreachable this long, reboot to clear any wedged
// network/stack state that a plain reconnect can't fix.
unsigned long lastMqttConnected = 0;
const unsigned long mqttMaxDisconnectedMs = 15UL * 60UL * 1000UL; // 15 minutes

// Setup connection to MQTT
void setup_mqtt() {
  if (mqttClient.connected()) return;
  if (WiFi.status() != WL_CONNECTED) return; // No point trying without a network

  if (millis() - lastMQTTReconnectAttempt > mqttReconnectInterval) {
    lastMQTTReconnectAttempt = millis();
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-IrrigaTOP" + String(random(0xffff), HEX);
    // Attempt to connect
    if (mqttClient.connect(clientId.c_str(), mqttUser, mqttPassword)) {
      Serial.println("Connected to MQTT broker.");
      mqttClient.subscribe(mqttTopicReadAction);
      mqttClient.subscribe(mqttTopicReadIntensity);
      mqttClient.subscribe(mqttTopicReadPump);
    } else {
      Serial.print("MQTT connection failed, rc=");
      Serial.print(mqttClient.state());
    }
  }
}

// Replaces the %STATE% placeholder in the served HTML with the current pump state
String processor(const String& var) {
  if (var == "STATE") {
    return pumpState ? "ON" : "OFF";
  }
  return String();
}

// Publish pump status via MQTT
void publishCurrentPumpStatus(bool publishStatus) {
  // Publish the current pump status read from the pin when publishStatus is true, otherwise report a PULSE
  const char* pumpStatus = publishStatus ? (digitalRead(pumpPin) ? "OFF" : "ON") : "PULSE";
  mqttClient.publish(mqttTopicPublishAction, pumpStatus);
}

// Publish pump intensity via MQTT
void publishPumpIntensity(int intensity) {
  char intensityStr[4];
  itoa(intensity, intensityStr, 10);
  mqttClient.publish(mqttTopicPublishIntensity, intensityStr);
}

// Publish active pump ID via MQTT
void publishPumpId(int id) {
  char idStr[2];
  itoa(id, idStr, 10);
  mqttClient.publish(mqttTopicPublishPump, idStr);
}

void setPump(String status) {
  bool pulse = false;
  Serial.println();
  Serial.print("Pump Status:");
  Serial.println(status);
  if (status == "ON") {
    Serial.print("--- Turning Pump ON ---");
    digitalWrite(pumpPin, LOW);
    pumpState = true;
  } else if (status == "OFF") {
    Serial.print("--- Turning Pump OFF ---");
    digitalWrite(pumpPin, HIGH);
    pumpState = false;
  } else if (status == "PULSE") {
    Serial.print("--- Pulsing Pump 2s ---");
    pulse = true;
    digitalWrite(pumpPin, LOW);
    delay(2000);
    digitalWrite(pumpPin, HIGH);
    pumpState = false;
  }
  // Publish PULSE otherwise will publish the current status of the Pump from the Pin
  publishCurrentPumpStatus(!pulse);
}

void setup_pwm() {
  analogWriteResolution(pwmResolution);
  analogWriteFrequency(pwmFreq);
}

void set_pwm_intensity(const int intensity) {
  Serial.print("Pump Intensity:");
  Serial.println(intensity);
  uint32_t pwmPinValue = (intensity * 256) / 100; // Scale from 0-100% to 0-255

  Serial.print("PWM Pin Value:");
  Serial.println(pwmPinValue);

  analogWrite(pwmPin, pwmPinValue);
  publishPumpIntensity(intensity);
}

void set_pump_id(const int pumpId) {
  if (pumpId == 1) {
    Serial.println("--- Setting Pump 1 Active ---");
    pumpPin = pump1Pin;
  } else if (pumpId == 2) {
    Serial.println("--- Setting Pump 2 Active ---");
    pumpPin = pump2Pin;
  }
  publishPumpId(pumpId);
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp = String((char*)payload).substring(0, length);
  Serial.printf("\nMQTT Topic: %s, Message: %s\n", topic, messageTemp.c_str());

  if (strcmp(topic, mqttTopicReadAction) == 0) {
    Serial.printf("Set Pump Action: %s\n", messageTemp.c_str());
    setPump(messageTemp);
  } else if (strcmp(topic, mqttTopicReadIntensity) == 0) {
    Serial.printf("Set Pump Intensity: %s\n", messageTemp.c_str());
    set_pwm_intensity(messageTemp.toInt());
  } else if (strcmp(topic, mqttTopicReadPump) == 0) {
    set_pump_id(messageTemp.toInt());
  }
  Serial.printf("\n");
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

  // Route to turn the pump ON
  server.on("/on", HTTP_GET, [](AsyncWebServerRequest* request) {
    setPump("ON");
    request->send(SPIFFS, "/index.html", String(), false, processor);
  });

  // Route to turn the pump OFF
  server.on("/off", HTTP_GET, [](AsyncWebServerRequest* request) {
    setPump("OFF");
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
    Serial.println("Failed to configure static IP");
  }

  // Connect to Wi-Fi network with SSID and password
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  // Wait for a connection, but give up after wifiConnectTimeout so the device
  // still boots when the network is momentarily unavailable. loop() keeps retrying.
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < wifiConnectTimeout) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected. IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection timed out, will keep retrying in the background.");
  }
}

// Arm the hardware Task Watchdog Timer. If loop() ever stops feeding it (a hang
// or deadlock), the ESP32 reboots itself — essential for an unattended device.
// The init API changed between arduino-esp32 2.x and 3.x, so guard on the version.
void setup_watchdog() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  esp_task_wdt_config_t wdtConfig = {
    .timeout_ms = wdtTimeoutSeconds * 1000,
    .idle_core_mask = 0,    // Don't watch the idle tasks, only loopTask
    .trigger_panic = true,  // Panic (and reboot) on timeout
  };
  esp_task_wdt_init(&wdtConfig);
#else
  esp_task_wdt_init(wdtTimeoutSeconds, true);
#endif
  esp_task_wdt_add(NULL); // Subscribe the Arduino loop task
  Serial.printf("Task watchdog armed (%us timeout)\n", wdtTimeoutSeconds);
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
  digitalWrite(pump1Pin, HIGH);
  digitalWrite(pump2Pin, HIGH);

  setup_spiffs();
  setup_wifi();
  setup_asyncWebServerRoutes();
  setup_pwm();
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setCallback(mqtt_callback);

  publishCurrentPumpStatus(false);
  publishPumpIntensity(0);
  publishPumpId(1);

  lastMqttConnected = millis(); // Start the MQTT-stuck timer from boot
  setup_watchdog();             // Arm last, so blocking setup steps can't trip it
}

void loop() {
  // Feed the hardware watchdog; if loop() stalls past the timeout, the board reboots.
  esp_task_wdt_reset();

  // Reboot if MQTT has been unreachable too long, to clear any wedged state.
  if (mqttClient.connected()) {
    lastMqttConnected = millis();
  } else if (millis() - lastMqttConnected > mqttMaxDisconnectedMs) {
    Serial.println("MQTT unreachable too long; restarting to recover...");
    Serial.flush();
    ESP.restart();
  }

  // Non-blocking WiFi reconnect so a dropped network self-heals while unattended
  if (WiFi.status() != WL_CONNECTED &&
      millis() - lastWiFiReconnectAttempt > wifiReconnectInterval) {
    lastWiFiReconnectAttempt = millis();
    Serial.println("WiFi disconnected, attempting to reconnect...");
    WiFi.reconnect();
  }

  // Non-blocking MQTT handling
  setup_mqtt();
  mqttClient.loop();

  // Non-blocking LED blinking
  if (millis() - lastLEDUpdate > ledBlinkInterval) {
    lastLEDUpdate = millis();
    ledState = !ledState;
    digitalWrite(boardLedPin, ledState ? HIGH : LOW);
  }

  // Non-blocking health check publishing
  if (mqttClient.connected() && millis() - lastHealthCheck > healthCheckInterval) {
    lastHealthCheck = millis();
    mqttClient.publish(mqttTopicPublishHealth, "alive");
    Serial.println("Health check sent");
  }
}
