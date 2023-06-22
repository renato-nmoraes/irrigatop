import os

MQTT_BROKER = os.environ.get("MQTT_BROKER", "CHANGE_ME")
MQTT_TOPIC_PUBLISH = os.environ.get("MQTT_TOPIC_PUBLISH", "CHANGE_ME")
MQTT_TOPIC_STATUS = os.environ.get("MQTT_TOPIC_STATUS", "CHANGE_ME")
MQTT_PORT = os.environ.get("MQTT_PORT", "CHANGE_ME")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "CHANGE_ME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "CHANGE_ME")

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///messages.db")

BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME", "CHANGE_ME")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD", "CHANGE_ME")