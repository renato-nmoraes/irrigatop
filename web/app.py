from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import paho.mqtt.publish as publish
import paho.mqtt.client as mqqt_client
import paho.mqtt.subscribe as subscribe
import threading
from flask_basicauth import BasicAuth

try:
    import config_local as config
except ImportError:
    import config

app = Flask(__name__)

# DATABASE DATA
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# AUTH
app.config["BASIC_AUTH_USERNAME"] = config.BASIC_AUTH_USERNAME
app.config["BASIC_AUTH_PASSWORD"] = config.BASIC_AUTH_PASSWORD
basic_auth = BasicAuth(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100))

    def __repr__(self):
        return f"<Message {self.id}>"


def setup_mqtt_reader():
    client = mqqt_client.Client()
    client.username_pw_set(
        username=config.MQTT_USERNAME, password=config.MQTT_PASSWORD
    )
    try:
        client.connect(
            host=config.MQTT_BROKER,
            port=int(config.MQTT_PORT),
        )
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

    client.on_connect = on_connect
    topic_name = f"{config.MQTT_TOPIC}/status/action"
    print(f"Subscribing to topic: {topic_name}")
    client.subscribe(topic_name)
    client.on_message = on_message
    client.loop_start()
    # mqtt_thread = threading.Thread(target=client.loop_forever)
    # mqtt_thread.start()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def on_message(client, userdata, message):
    pump_status = message.payload.decode()
    print(f"Received pump status: {pump_status}")

    with app.app_context():
        # Update the message in the database
        # message = Message.query.filter_by(content="action").first()
        # if message:
            # message.content = pump_status
        db.session.add(Message(content=pump_status))
        db.session.commit()
        
        with app.test_client() as client:  # Use test client to simulate internal request
            response = client.get("/status")
            print(response.data)


def send_message_to_broker_and_store(message, topic=None):
    mqtt_broker = config.MQTT_BROKER
    mqtt_topic = config.MQTT_TOPIC
    mqtt_port = int(config.MQTT_PORT)
    mqtt_username = config.MQTT_USERNAME
    mqtt_password = config.MQTT_PASSWORD

    if topic is None:
        raise Exception("Missing topic")

    publish.single(
        f"{mqtt_topic}/{topic}",
        payload=message,
        hostname=mqtt_broker,
        port=mqtt_port,
        auth={"username": mqtt_username, "password": mqtt_password},
    )

    # # Store the message in the database
    # if topic == "action":
    #     db.session.add(Message(content=message))
    #     db.session.commit()


@app.route("/", methods=["GET", "POST"])
@basic_auth.required
def home():
    if request.method == "POST":
        action = request.form.get("action")
        if action:
            send_message_to_broker_and_store(message=action, topic="action")

    return render_template("index.html")  # , message=message)


@app.route("/status")
def get_pump_status():
    try:
        message = Message.query.order_by(Message.id.desc()).first()
        if message:
            return jsonify({"status": message.content})
        else:
            return jsonify({"status": "No status available"})
    except:
        return jsonify({"status": "Error fetching status"})


@app.route("/intensity", methods=["POST"])
def process():
    intensity_value = int(request.form.get("slider"))
    send_message_to_broker_and_store(message=intensity_value, topic="intensity")

    # Do something with the slider value
    # For example, print it to the console
    print(f"Slider value: {intensity_value}")
    return jsonify({"message": "Slider value received"})


@app.route("/pump", methods=["POST"])
def handle_pump_selection():
    pump_id = request.form["pump_id"]
    send_message_to_broker_and_store(message=pump_id, topic="pump")
    # Process the pump ID here (e.g., store it in a database, send it to a controller, etc.)
    print(f"Pump ID: {pump_id}")
    return jsonify({"pump_id": pump_id})  # Return the processed

with app.app_context():
    print("Inside application context")  # This will print
    db.create_all()
    setup_mqtt_reader()
    
if __name__ == "__main__":
    with app.app_context():
        print("Inside application context")  # This will print
        db.create_all()
        setup_mqtt_reader()
    print("Outside application context")  # This will also print
    app.run(debug=True)
