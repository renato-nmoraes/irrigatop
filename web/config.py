import os

MQTT_BROKER = os.environ.get("MQTT_BROKER", "CHANGE_ME")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "CHANGE_ME")
MQTT_PORT = os.environ.get("MQTT_TOPIC", "CHANGE_ME")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "CHANGE_ME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "CHANGE_ME")

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///messages.db")

BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME", "CHANGE_ME")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD", "CHANGE_ME")