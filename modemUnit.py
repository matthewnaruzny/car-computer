import subprocess
import threading
import time


class RemoteCommunication:

    def __init__(self):
        self.pon_p = None

    def start_network(self):
        print("Attempting to connect to network...")
        self.pon_p = subprocess.Popen(['sudo', 'pon'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            time.sleep(5)
            stdout, stderr = self.pon_p.communicate()
            output = stdout.decode('utf-8')
            if "failed" in output:
                print("Failed... retrying")
                self.pon_p = subprocess.Popen(['sudo', 'pon'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

    def send(self, payload):
        pass

    def start_call(self):
        pass

    def receive_call(self):
        pass
