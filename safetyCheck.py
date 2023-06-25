from networkCommunication import NetworkCommunication
from gpiozero import Buzzer

import RPi.GPIO as GPIO
import threading
import time
import logging


class SafetyCheck:

    def __init__(self, networker):
        assert isinstance(networker, NetworkCommunication)
        self.networker = networker
        GPIO.setmode(GPIO.BCM)

        self.__safetyPin = 16
        buzzerPin = 12

        GPIO.setup(self.__safetyPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.buzzer = Buzzer(buzzerPin)

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
            state = GPIO.input(self.__safetyPin)

            if state == 0:  # SOS Raised
                if self.__sos_active:
                    self.networker.sos(sos=True)
                elif self.__sos_pending:
                    if time.time() - self.__sos_pending_time > 5:
                        self.__sos_active = True
                        self.buzzer.on()
                else:
                    logging.warning("SOS Starting Pending")
                    self.__sos_pending = True
                    self.__sos_pending_time = time.time()
                    self.buzzer.beep()
            else:
                self.buzzer.off()
                self.__sos_active = False
                self.__sos_pending = False
                self.networker.sos(sos=False)

            # self.networker.sos(sos=(state != 1))
            time.sleep(0.1)
