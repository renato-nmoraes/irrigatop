from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
from flask_basicauth import BasicAuth

try:
    import config_local as config
except ImportError:
    import config

app = Flask(__name__)

# DATABASE DATA
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# AUTH
app.config['BASIC_AUTH_USERNAME'] = config.BASIC_AUTH_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = config.BASIC_AUTH_PASSWORD
basic_auth = BasicAuth(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100))

    def __repr__(self):
        return f'<Message {self.id}>'


def send_message_to_broker_and_store(message, topic=None, pump_id=None):
    mqtt_broker = config.MQTT_BROKER
    mqtt_topic = config.MQTT_TOPIC
    mqtt_port = int(config.MQTT_PORT)
    mqtt_username = config.MQTT_USERNAME
    mqtt_password = config.MQTT_PASSWORD

    if topic is None:
        raise Exception("Missing topic")

    publish.single(f"{mqtt_topic}/{pump_id}/{topic}", payload=message, hostname=mqtt_broker,
                   port=mqtt_port, auth={'username': mqtt_username, 'password': mqtt_password})

    # Store the message in the database
    if topic == "action":
        db.session.add(Message(content=message))
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@basic_auth.required
def home():
    if request.method == 'POST':
        action = request.form.get('action')
        pump_id = int(request.form.get('pump_id'))  # Get the selected pump ID
        if action:
            send_message_to_broker_and_store(message=action, topic="action", pump_id=pump_id)
    try:
        message = Message.query.order_by(Message.id.desc()).first()
        if message:
            message = message.content
        else:
            message = "No message available"
    except:
        message = "No message available"

    return render_template('index.html', message=message)


@app.route('/intensity', methods=['POST'])
def process():
    intensity_value = int(request.form.get('slider'))
    # send_message_to_broker_and_store(message=intensity_value, topic="intensity")

    # Do something with the slider value
    # For example, print it to the console
    print(f"Slider value: {intensity_value}")
    return jsonify({'message': 'Slider value received'})

@app.route('/pump', methods=['POST'])
def handle_pump_selection():
    pump_id = request.form['pump_id']
    # Process the pump ID here (e.g., store it in a database, send it to a controller, etc.)
    print(f"Pump ID: {pump_id}")
    return jsonify({'pump_id': pump_id})  # Return the processed

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
