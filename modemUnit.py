import subprocess
import threading
import time
from pyVoIP.VoIP import VoIPPhone, InvalidStateError

import config
from config import sip_config


class RemoteCommunication:

    def __init__(self):
        self.t_watch = None
        self.phone = None
        self.pon_p = None

    def power_cycle(self):
        subprocess.Popen(['sudo', 'raspi-gpio', 'set', '4', 'op', 'dh'])
        time.sleep(2)
        subprocess.Popen(['sudo', 'raspi-gpio', 'set', '4', 'op', 'dl'])

    def start_network(self):
        print("Attempting to connect to network...")
        self.pon_p = subprocess.Popen(['sudo', 'pon'])

        while True:
            time.sleep(5)

            # Check if ppp0 exists
            print("Checking...")
            adapter_check = subprocess.check_output(['ip', 'addr', 'show'])
            if "ppp0" in adapter_check.decode('utf-8'):  # If ppp0 exists, create route and end
                print("Creating route")
                subprocess.Popen(['sudo', 'route', 'add', '-net', '0.0.0.0', 'ppp0'])
                return

    def stop_network(self):
        if self.pon_p is not None:
            subprocess.Popen(['sudo', 'poff'])
            self.pon_p = None

    def sip_connect(self):
        self.phone = VoIPPhone(sip_config['sip_host'], sip_config['sip_port'],
                               sip_config['sip_username'], sip_config['sip_password'])

    def start_call(self, number):
        pass

    def receive_call(self, call):
        try:
            call.answer()
        except InvalidStateError:
            print("Error Answering Call")
