import paho.mqtt.client as mqtt
from config import mqtt_config


class MQTTController:

    def __init__(self):
        # Client(client_id="", clean_session=True, userdata=None, protocol=MQTTv311, transport="tcp")
        self.client = mqtt.Client(client_id=mqtt_config['client'])
        self.connect(mqtt_config['url'], mqtt_config['port'])
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.loop_start()

    def on_message(self, client, userdata, msg):
        print("New Msg: " + msg.payload.decode('utf-8'))

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result " + str(rc))
        self.client.subscribe(mqtt_config['topic'])

    def connect(self, url, port):
        print("Connecting...")
        self.client.tls_set(ca_certs=mqtt_config['root_cert'])
        self.client.username_pw_set(mqtt_config['username'], mqtt_config['password'])
        self.client.connect(url, port, 60)

    def publish(self, topic, payload=None, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)
