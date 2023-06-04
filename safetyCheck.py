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

        self.__sos_active = False
        self.__sos_pending = False
        self.__sos_pending_time = 0

        self.__start_thread()

    def __start_thread(self):
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__mthread.start()

    def __main_thread(self):
        while True:
            # SOS Check
            state = GPIO.input(21)

            if state == 0:  # SOS Raised
                if self.__sos_active:
                    print("Current SOS")
                    self.networker.sos(sos=True)
                elif self.__sos_pending:
                    if time.time() - self.__sos_pending_time > 5:
                        self.__sos_active = True
                else:
                    print("SOS Starting Pending")
                    self.__sos_pending = True
                    self.__sos_pending_time = time.time()
            else:
                self.__sos_pending = False
                self.networker.sos(sos=False)

            # self.networker.sos(sos=(state != 1))
            time.sleep(0.1)
