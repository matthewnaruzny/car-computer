import subprocess

import paho.mqtt.client as mqtt
from config import mqtt_config
from modemUnit import RemoteCommunication
import json


class MQTTController:

    def __init__(self, remote=None):
        assert isinstance(remote, RemoteCommunication)
        self.remote = remote
        self.default_topic = mqtt_config['topic']

        self.client_status = {'state': 'up'}

        # Client(client_id="", clean_session=True, userdata=None, protocol=MQTTv311, transport="tcp")
        self.client = mqtt.Client(client_id=mqtt_config['client'])
        self.connect(mqtt_config['url'], mqtt_config['port'])
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.loop_start()

    def on_message(self, client, userdata, msg):
        print("New Msg: " + msg.payload.decode('utf-8'))

        try:
            cmd = json.loads(msg.payload.decode('utf-8'))
            # Process Commands
            if cmd['unit'] == 'shell':
                try:
                    r = subprocess.check_output(cmd['cmd'].split())
                    self.publish(msg.topic, r, qos=2)
                except subprocess.CalledProcessError:
                    self.publish(msg.topic, "Error Executing", qos=2)

            if cmd['unit'] == 'ping':
                self.publish(msg.topic, "Pong", qos=2)

            if cmd['unit'] == 'modem':
                if cmd['cmd'] == 'power':
                    self.remote.power_cycle()
                    self.publish(msg.topic, 'Modem Power Cycle', qos=2)

                if cmd['cmd'] == 'up':
                    print('Modem Up')
                    self.publish(msg.topic, 'Modem Up', qos=2)
                    self.remote.start_network()
                if cmd['cmd'] == 'down':
                    print('Modem Down')
                    self.publish(msg.topic, 'Modem Down', qos=2)
                    self.remote.stop_network()

        except json.decoder.JSONDecodeError:
            pass

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result " + str(rc))
        self.client.subscribe(self.default_topic)

    def connect(self, url, port):
        print("Connecting...")
        self.client.tls_set(ca_certs=mqtt_config['root_cert'])
        self.client.username_pw_set(mqtt_config['username'], mqtt_config['password'])
        self.client.connect(url, port, 60)

    def update_state(self):
        self.client.publish(self.default_topic+'/state', json.dumps(self.client_status), qos=2, retain=True)

    def publish(self, topic, payload=None, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)
