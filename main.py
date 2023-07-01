from modemUnit import ModemUnit
from networkCommunication import NetworkCommunication
from safetyCheck import SafetyCheck

import logging
import time
import argparse
import os

if __name__ == '__main__':
    # Start Controllers

    parser = argparse.ArgumentParser(prog='Car Computer')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-a', '--analyze', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        if not os.path.exists('log'):
            os.mkdir('log')

        # Find next log file increment
        i = 0
        while os.path.exists("log/" + str(i) + ".log"):
            i += 1

        logging.basicConfig(filename=("log/" + str(i) + ".log"), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info("--Starting Program--")
    remote = ModemUnit(log=True)

    imei = remote.get_imei()

    remote.start_gps()
    gps = remote.get_gps()

    remote.network_init()

    networkCommunication = NetworkCommunication(imei, remote, analyze=args.analyze)
    safetyCheck = SafetyCheck(networkCommunication)

    while True:
        time.sleep(0.5)
