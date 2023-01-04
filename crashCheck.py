import threading
import time


class CrashCheck:
    def __init__(self):
        self.t = None

    def start_monitor(self):
        self.t = threading.Thread(target=self.monit)
        self.t.start()

    def monit(self):
        self.crash_check()
        time.sleep(0.25)

    def crash_check(self):
        pass
