import logging
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_basicauth import BasicAuth
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import threading
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    import config_local as config
except ImportError:
    import config

# Global variables
mqtt_connected = False
last_health_check = None
HEALTH_CHECK_TIMEOUT = 30  # seconds

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


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100))

    def __repr__(self):
        return f"<Message {self.id}: {self.content}>"


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    connection_codes = {
        0: "Connected successfully",
        1: "Incorrect protocol version",
        2: "Invalid client identifier",
        3: "Server unavailable",
        4: "Bad username or password",
        5: "Not authorized",
    }

    if rc == 0:
        logger.info("MQTT connected successfully")
        try:
            # Subscribe to topics
            status_topic = f"{config.MQTT_TOPIC}/status/action"
            health_topic = f"{config.MQTT_TOPIC}/health"

            logger.debug(f"Subscribing to topic: {status_topic}")
            client.subscribe(status_topic)
            logger.debug(f"Subscribing to topic: {health_topic}")
            client.subscribe(health_topic)

            # Add a flag to indicate successful connection
            global mqtt_connected
            mqtt_connected = True
            logger.info("MQTT topic subscriptions completed")
        except Exception as e:
            logger.error(f"Error during topic subscription: {str(e)}")
    else:
        error_message = connection_codes.get(rc, f"Unknown error code: {rc}")
        logger.error(f"MQTT connection failed - {error_message}")


def on_message(client, userdata, message):
    global last_health_check

    topic = message.topic
    payload = message.payload.decode()

    if topic.endswith("/health"):
        # Update health check timestamp
        last_health_check = datetime.now()
        logger.info(f"Health check received at {last_health_check}")
    elif topic.endswith("/status/action"):
        logger.info(f"Pump status received: {payload}")
        # Save status to database using app context
        with app.app_context():
            try:
                db.session.add(Message(content=payload))
                db.session.commit()
                logger.debug("Successfully saved message to database")
            except Exception as e:
                logger.error(f"Failed to save message to database: {e}")
                db.session.rollback()


def setup_mqtt():
    logger.info("Starting MQTT setup...")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        # Add connection retry logic
        retry_count = 0
        max_retries = 3
        logger.info(
            f"Attempting to connect to MQTT broker at {config.MQTT_BROKER}:{config.MQTT_PORT}"
        )

        while retry_count < max_retries:
            try:
                logger.debug(f"Connection attempt {retry_count + 1} of {max_retries}")
                mqtt_client.connect(config.MQTT_BROKER, int(config.MQTT_PORT))
                logger.info("Initial MQTT connection successful")
                break
            except Exception as e:
                logger.error(
                    f"MQTT connection attempt {retry_count + 1} failed: {str(e)}"
                )
                retry_count += 1
                if retry_count < max_retries:
                    logger.info("Waiting 2 seconds before retry...")
                    time.sleep(2)
                else:
                    logger.error("All MQTT connection attempts failed")

        # Start MQTT loop in a separate thread
        logger.debug("Starting MQTT loop thread")
        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
        mqtt_thread.start()
        logger.info("MQTT loop thread started")

    except Exception as e:
        logger.error(f"Unexpected error in MQTT setup: {str(e)}")
        raise


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
        logger.error("Error fetching pump status")
        return jsonify({"status": "Error fetching status", "error": str(e)})


@app.route("/health")
def get_health_status():
    global last_health_check
    now = datetime.now()

    if (
        last_health_check
        and (now - last_health_check).total_seconds() <= HEALTH_CHECK_TIMEOUT
    ):
        return jsonify({"status": "online"})
    return jsonify({"status": "offline"})


@app.route("/intensity", methods=["POST"])
def set_intensity():
    try:
        intensity_value = int(request.form.get("slider", 0))
        send_message(intensity_value, "intensity")
        return jsonify({"message": "Intensity updated", "value": intensity_value})
    except Exception as e:
        logger.error("Failed to update intensity")
        return jsonify({"message": "Failed to update intensity", "error": str(e)})


@app.route("/pump", methods=["POST"])
def select_pump():
    try:
        pump_id = int(request.form.get("pump_id", 0))
        send_message(pump_id, "pump")
        return jsonify({"message": "Pump updated", "pump_id": pump_id})
    except Exception as e:
        logger.error("Failed to update pump")
        return jsonify({"message": "Failed to update pump", "error": str(e)})


def send_message(payload, topic_suffix):
    logger.debug(
        f"Attempting to send message. Payload: {payload}, Topic suffix: {topic_suffix}"
    )

    if not mqtt_connected:
        error_msg = "Cannot send message: MQTT client not connected"
        logger.error(error_msg)
        raise Exception(error_msg)

    full_topic = f"{config.MQTT_TOPIC}/{topic_suffix}"
    try:
        logger.debug(f"Publishing to topic {full_topic}")
        result = mqtt_client.publish(full_topic, str(payload))

        if result.rc == 0:
            logger.info(
                f"Successfully published message '{payload}' to topic '{full_topic}'"
            )
        else:
            error_msg = f"Failed to publish message: return code {result.rc}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Wait for message to be sent
        result.wait_for_publish()
        logger.debug("Message delivery confirmed")

    except Exception as e:
        error_msg = f"Error publishing message to topic {full_topic}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def init_app(app):
    logger.info("Initializing application...")

    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()

        logger.info("Setting up MQTT connection...")
        setup_mqtt()

        # Wait a moment for MQTT to connect
        time.sleep(2)

        if not mqtt_connected:
            logger.warning("⚠️ Starting Flask app without MQTT connection!")
        else:
            logger.info("MQTT connection established successfully")


# Initialize the app
init_app(app)

# Keep the __main__ block for local development
if __name__ == "__main__":
    logger.info("Starting Flask development server...")
    app.run(debug=True)
