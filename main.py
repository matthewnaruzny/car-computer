import time
import config

from modemUnit import ModemUnit
from mqtt_connector import MQTTController

if __name__ == '__main__':

    # Start Modem Controller
    remote = ModemUnit(log=True)
    remote.start_gps()

    # Starts Comms
    mqtt = MQTTController(remote)
    gpsData = remote.get_gps()
    while True:
        mqtt.update_state()
        mqtt.publish(config.mqtt_config['topic'] + '/time', time.time())
        time.sleep(60)

