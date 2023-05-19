from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import paho.mqtt.publish as publish
from flask_basicauth import BasicAuth
import os
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
    # last_message = db.Column(db.String(100))

    def __repr__(self):
        return f'<Message {self.id}>'


def send_message_to_broker_and_store(message):
    mqtt_broker = config.MQTT_BROKER
    mqtt_topic = config.MQTT_TOPIC
    mqtt_port = config.MQTT_PORT
    mqtt_username = config.MQTT_USERNAME
    mqtt_password = config.MQTT_PASSWORD

    publish.single(mqtt_topic, payload=message, hostname=mqtt_broker, port=mqtt_port,
                   auth={'username': mqtt_username, 'password': mqtt_password})

    # Store the message in the database
    db.session.add(Message(content=message))
    db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@basic_auth.required
def home():
    if request.method == 'POST':
        action = request.form.get('action')
        if action:
            send_message_to_broker_and_store(action)
    messages = Message.query.order_by(Message.id.desc()).first()
    return render_template('index.html', messages=messages)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
