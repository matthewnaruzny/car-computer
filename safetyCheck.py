from networkCommunication import NetworkCommunication
import RPi.GPIO as GPIO
import threading
import time


class SafetyCheck:

    def __init__(self, networker):
        assert isinstance(networker, NetworkCommunication)
        self.networker = networker
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.__old_state = 1
        self.__start_thread()

    def __start_thread(self):
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__mthread.start()

    def __main_thread(self):
        while True:
            state = GPIO.input(21)
            if state == 0 and state != self.__old_state:
                self.networker.sendSOS()
            self.__old_state = state
            time.sleep(0.1)
