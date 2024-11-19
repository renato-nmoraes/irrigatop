from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_basicauth import BasicAuth
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import threading

# Import configuration
try:
    import config_local as config
except ImportError:
    import config

# Flask app and database setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Basic authentication setup
app.config["BASIC_AUTH_USERNAME"] = config.BASIC_AUTH_USERNAME
app.config["BASIC_AUTH_PASSWORD"] = config.BASIC_AUTH_PASSWORD
basic_auth = BasicAuth(app)

# MQTT configuration
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

# Track the last health check time
last_health_check = None
HEALTH_CHECK_TIMEOUT = 30  # seconds


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100))

    def __repr__(self):
        return f"<Message {self.id}: {self.content}>"


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected successfully.")
        # Subscribe to topics
        client.subscribe(f"{config.MQTT_TOPIC}/status/action")
        client.subscribe(f"{config.MQTT_TOPIC}/health")
    else:
        print(f"MQTT connection failed with code {rc}")


def on_message(client, userdata, message):
    global last_health_check

    topic = message.topic
    payload = message.payload.decode()

    if topic.endswith("/health"):
        # Update health check timestamp
        last_health_check = datetime.now()
        print(f"Health check received at {last_health_check}")
    elif topic.endswith("/status/action"):
        print(f"Pump status received: {payload}")
        # Save status to database
        with app.app_context():
            db.session.add(Message(content=payload))
            db.session.commit()


def setup_mqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(config.MQTT_BROKER, int(config.MQTT_PORT))
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

    # Start MQTT loop in a separate thread
    threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()


# Routes
@app.route("/", methods=["GET", "POST"])
@basic_auth.required
def home():
    if request.method == "POST":
        action = request.form.get("action")
        if action:
            send_message(action, "action")
    return render_template("index.html")


@app.route("/status")
def get_pump_status():
    try:
        message = Message.query.order_by(Message.id.desc()).first()
        if message:
            return jsonify({"status": message.content})
        return jsonify({"status": "No status available"})
    except Exception as e:
        return jsonify({"status": "Error fetching status", "error": str(e)})


@app.route("/health")
def get_health_status():
    global last_health_check
    now = datetime.now()

    if last_health_check and (now - last_health_check).total_seconds() <= HEALTH_CHECK_TIMEOUT:
        return jsonify({"status": "online"})
    return jsonify({"status": "offline"})


@app.route("/intensity", methods=["POST"])
def set_intensity():
    try:
        intensity_value = int(request.form.get("slider", 0))
        send_message(intensity_value, "intensity")
        return jsonify({"message": "Intensity updated", "value": intensity_value})
    except Exception as e:
        return jsonify({"message": "Failed to update intensity", "error": str(e)})


@app.route("/pump", methods=["POST"])
def select_pump():
    try:
        pump_id = int(request.form.get("pump_id", 0))
        send_message(pump_id, "pump")
        return jsonify({"message": "Pump updated", "pump_id": pump_id})
    except Exception as e:
        return jsonify({"message": "Failed to update pump", "error": str(e)})


# Helper function to send MQTT messages
def send_message(payload, topic_suffix):
    full_topic = f"{config.MQTT_TOPIC}/{topic_suffix}"
    try:
        mqtt_client.publish(full_topic, payload)
        print(f"Message '{payload}' sent to topic '{full_topic}'")
    except Exception as e:
        print(f"Error publishing message to topic {full_topic}: {e}")


# App startup
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    setup_mqtt()
    app.run(debug=True)
