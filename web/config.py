import os

MQTT_BROKER = os.environ.get("MQTT_BROKER", "CHANGE_ME")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "CHANGE_ME")
MQTT_PORT = os.environ.get("MQTT_TOPIC", "CHANGE_ME")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "CHANGE_ME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "CHANGE_ME")

sqlite_file = os.environ.get("DATABASE_PATH", "messages.db")
sqlite_path = os.path.join(os.getcwd(), "/data", sqlite_file)
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{sqlite_path}")

BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME", "CHANGE_ME")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD", "CHANGE_ME")