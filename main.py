from modemUnit import ModemUnit
from networkCommunication import NetworkCommunication
from safetyCheck import SafetyCheck

import logging
import time
import argparse

if __name__ == '__main__':
    # Start Controllers

    parser = argparse.ArgumentParser(prog='Car Computer')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(filename="main.log", level=logging.INFO)

    logging.info("--Starting Program--")
    remote = ModemUnit(log=True)

    imei = remote.get_imei()

    remote.start_gps()
    gps = remote.get_gps()

    remote.network_init()

    networkCommunication = NetworkCommunication(imei, remote)
    safetyCheck = SafetyCheck(networkCommunication)

    while True:
        time.sleep(0.5)
