from flask import Flask, render_template, request
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


def send_message_to_broker_and_store(message, topic=None):
    mqtt_broker = config.MQTT_BROKER
    mqtt_topic = config.MQTT_TOPIC_PUBLISH
    mqtt_port = int(config.MQTT_PORT)
    mqtt_username = config.MQTT_USERNAME
    mqtt_password = config.MQTT_PASSWORD

    publish.single(f"{mqtt_topic}/{topic}" if topic is not None else mqtt_topic, payload=message, hostname=mqtt_broker,
                   port=mqtt_port, auth={'username': mqtt_username, 'password': mqtt_password})

    # Store the message in the database
    if topic == "action":
        db.session.add(Message(content=message))
        db.session.commit()


def subscribe_mqtt(topic=None):
    subscribe_result = subscribe.simple(
        topics=[
            f"{config.MQTT_TOPIC_STATUS}/{topic}"
            if topic is not None
            else f"{config.MQTT_TOPIC_STATUS}/action"
        ],
        hostname=config.MQTT_BROKER,
        port=int(config.MQTT_PORT),
        auth={"username": config.MQTT_USERNAME, "password": config.MQTT_PASSWORD},
        keepalive=5
    )

    if topic == "action":
        db.session.add(Message(content=subscribe_result.payload.decode()))
        db.session.commit()
    
    return subscribe_result.payload.decode()


@app.route('/', methods=['GET', 'POST'])
@basic_auth.required
def home():
    if request.method == 'POST':
        action = request.form.get('action')
        if action:
            send_message_to_broker_and_store(message=action, topic="action")
    # try:
    #     message = Message.query.order_by(Message.id.desc()).first()
    #     if message:
    #         message = message.content
    #     else:
    #         message = "No message available"
    # except:
    #     message = "No message available"

    return render_template('index.html', message=subscribe_mqtt("action"))


@app.route('/intensity', methods=['POST'])
def process():
    intensity_value = int(request.form.get('slider'))
    send_message_to_broker_and_store(message=intensity_value, topic="intensity")

    # Do something with the slider value
    # For example, print it to the console
    print(f"Slider value: {intensity_value}")
    return 'Slider value captured!'


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
