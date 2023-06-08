from modemUnit import ModemUnit
from networkCommunication import NetworkCommunication
from safetyCheck import SafetyCheck

import logging
import time
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Car Computer')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    logging.info("--Starting Test--")

    # Start Modem and Network
    logging.info("TEST: Starting Modem")
    remote = ModemUnit(log=True)
    remote.data_open()
    remote.bearer_set_settings(apn='super')
    remote.bearer_open()

    logging.info("Testing GET Requests")
    g1 = remote.http_get("https://httpstat.us/200")
    logging.info("G1: " + g1)
