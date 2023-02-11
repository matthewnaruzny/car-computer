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
                subprocess.call(['sudo', 'route', 'add', '-net', '0.0.0.0', 'ppp0'])
                return

    def stop_network(self):
        if self.pon_p is not None:
            subprocess.call(['sudo', 'poff'])
            self.pon_p = None

    def start_tunnel(self):
        print("Starting Tunnel")
        subprocess.call(config.tunnel_config['start_cmd'].split())
        self.t_watch = threading.Thread(target=self.watch_tunnel)
        self.t_watch.start()

    def watch_tunnel(self):
        ssh_check = subprocess.check_output(['sudo', 'lsof', '-i', '-n'])
        if config.tunnel_config['check_ip'] not in ssh_check:
            print("Restarting Tunnel")
            self.start_tunnel()
        time.sleep(10)

    def send(self, payload):
        pass

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
