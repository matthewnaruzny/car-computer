import subprocess
import threading
import time


class RemoteCommunication:

    def __init__(self):
        self.pon_p = None

    def start_network(self):
        self.pon_p = subprocess.Popen(['sudo', 'pon'])
        time.sleep(5)

        # Check if ppp0 is created
        while True:
            r = subprocess.Popen(['ip', 'addr', 'show'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = r.communicate()
            assert isinstance(stdout, bytes)
            if "ppp0" in stdout.decode("utf-8"):
                # Create network route
                subprocess.call(['sudo', 'route', 'add', '-net', '0.0.0.0', 'ppp0'])
                break
            else:
                time.sleep(5)

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
