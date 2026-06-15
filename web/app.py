import logging
import threading
import time
from datetime import datetime

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_basicauth import BasicAuth
import paho.mqtt.client as mqtt

# Import configuration
try:
    import config_local as config
except ImportError:
    import config

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
MAIN_TEMPLATE = "index.html"
HEALTH_CHECK_TIMEOUT = 30  # seconds

# Global variables
mqtt_connected = False
last_health_check = None

# Flask app setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["BASIC_AUTH_USERNAME"] = config.BASIC_AUTH_USERNAME
app.config["BASIC_AUTH_PASSWORD"] = config.BASIC_AUTH_PASSWORD

# Extensions initialization
db = SQLAlchemy(app)
migrate = Migrate(app, db)
basic_auth = BasicAuth(app)

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100))

    def __repr__(self):
        return f"<Message {self.id}: {self.content}>"


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
            status_topic = f"{config.MQTT_TOPIC}/status/action"
            health_topic = f"{config.MQTT_TOPIC}/health"

            client.subscribe(status_topic)
            client.subscribe(health_topic)
            logger.info(f"Subscribed to topics: {status_topic}, {health_topic}")

            global mqtt_connected
            mqtt_connected = True
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
        last_health_check = datetime.now()
        logger.info(f"Health check received at {last_health_check}")
    elif topic.endswith("/status/action"):
        logger.info(f"Pump status received: {payload}")
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
        retry_count = 0
        max_retries = 3
        broker_address = f"{config.MQTT_BROKER}:{config.MQTT_PORT}"
        logger.info(f"Attempting to connect to MQTT broker at {broker_address}")

        while retry_count < max_retries:
            try:
                mqtt_client.connect(config.MQTT_BROKER, int(config.MQTT_PORT))
                logger.info("MQTT connection successful")
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"MQTT connection attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2)

        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
        mqtt_thread.start()
        logger.info("MQTT loop thread started")

    except Exception as e:
        logger.error(f"Unexpected error in MQTT setup: {str(e)}")
        raise


def send_message(payload, topic_suffix):
    if not mqtt_connected:
        error_msg = "Cannot send message: MQTT client not connected"
        logger.error(error_msg)
        raise Exception(error_msg)

    full_topic = f"{config.MQTT_TOPIC}/{topic_suffix}"
    try:
        result = mqtt_client.publish(full_topic, str(payload))
        if result.rc != 0:
            error_msg = f"Failed to publish message: return code {result.rc}"
            logger.error(error_msg)
            raise Exception(error_msg)

        result.wait_for_publish()
        logger.info(f"Message '{payload}' published to '{full_topic}'")

    except Exception as e:
        error_msg = f"Error publishing message to {full_topic}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# Routes
@app.route("/", methods=["GET", "POST"])
@basic_auth.required
def home():
    if request.method == "POST":
        action = request.form.get("action")
        if action:
            try:
                send_message(action, "action")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": True, "message": "Action sent successfully"})
                return redirect(url_for("home"))
            except Exception as e:
                logger.error(f"Failed to send action: {str(e)}")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify(
                        {
                            "success": False,
                            "message": "Failed to send command to pump. Please try again later.",
                        }
                    ), 500
                return redirect(url_for("home"))

    return render_template(MAIN_TEMPLATE)


@app.route("/status")
def get_pump_status():
    try:
        message = Message.query.order_by(Message.id.desc()).first()
        return jsonify(
            {
                "success": True,
                "status": message.content if message else "No status available",
            }
        )
    except Exception as e:
        logger.error(f"Error fetching pump status: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Unable to fetch pump status. Please try again later.",
                    "status": "error",
                }
            ),
            500,
        )


@app.route("/health")
def get_health_status():
    if last_health_check and (
        datetime.now() - last_health_check
    ).total_seconds() <= HEALTH_CHECK_TIMEOUT:
        return jsonify({"status": "online"})
    return jsonify({"status": "offline"})


@app.route("/intensity", methods=["POST"])
def set_intensity():
    try:
        intensity_value = int(request.form.get("slider", 0))
        send_message(intensity_value, "intensity")
        return jsonify(
            {
                "success": True,
                "message": "Intensity updated successfully",
                "value": intensity_value,
            }
        )
    except ValueError:
        logger.error("Invalid intensity value provided")
        return (
            jsonify({"success": False, "message": "Please provide a valid intensity value"}),
            400,
        )
    except Exception as e:
        logger.error(f"Failed to update intensity: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to update intensity. Please try again later.",
                }
            ),
            500,
        )


@app.route("/pump", methods=["POST"])
def select_pump():
    try:
        pump_id = int(request.form.get("pump_id", 0))
        send_message(pump_id, "pump")
        return jsonify(
            {"success": True, "message": "Pump selected successfully", "pump_id": pump_id}
        )
    except ValueError:
        logger.error("Invalid pump ID provided")
        return (
            jsonify({"success": False, "message": "Please provide a valid pump ID"}),
            400,
        )
    except Exception as e:
        logger.error(f"Failed to select pump: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Failed to select pump. Please try again later."}
            ),
            500,
        )


def init_app(app):
    logger.info("Initializing application...")
    with app.app_context():
        db.create_all()
        setup_mqtt()
        time.sleep(2)  # Wait for MQTT connection

        if not mqtt_connected:
            logger.warning("⚠️ Starting Flask app without MQTT connection!")
        else:
            logger.info("MQTT connection established successfully")


# Initialize the app
init_app(app)

if __name__ == "__main__":
    logger.info("Starting Flask development server...")
    app.run(debug=True)
