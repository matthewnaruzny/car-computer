from modemUnit import ModemUnit
from networkCommunication import NetworkCommunication
from safetyCheck import SafetyCheck

import logging
import time

if __name__ == '__main__':
    # Start Controllers
    logging.basicConfig(filename="main.log", level=logging.INFO)
    logging.info("--Starting Program--")
    remote = ModemUnit(log=True)

    imei = remote.get_imei()

    remote.start_gps()
    gps = remote.get_gps()

    remote.data_open()
    remote.bearer_set_settings(apn='super')
    remote.bearer_open()

    networkCommunication = NetworkCommunication(imei, remote)
    safetyCheck = SafetyCheck(networkCommunication)

    while True:
        time.sleep(0.5)
