from networkCommunication import NetworkCommunication
import RPi.GPIO as GPIO
import threading
import time


class SafetyCheck:

    def __init__(self, networker):
        assert isinstance(networker, NetworkCommunication)
        self.networker = networker
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.__start_thread()

    def __start_thread(self):
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__mthread.start()

    def __main_thread(self):
        state = GPIO.input(21)
        print("State: " + str(state))
        if state == 21:
            self.networker.sendSOS()
        time.sleep(0.1)
