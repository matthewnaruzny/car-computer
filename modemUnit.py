import subprocess
import threading
import time
import serial
import json
import uuid


class GPSData:
    def __init__(self):
        self.utc = 0
        self.lat = 0
        self.lon = 0
        self.alt = 0
        self.speed = 0


class ModemUnit:

    def __init__(self, port='/dev/ttyS0', baudrate=115200, log=False):
        self.__mthread = None
        self.__ser = serial.Serial(port, baudrate=baudrate)
        self.pon_p = None

        self.__log = log

        self.__modem_power = False
        self.__worker_working = False

        self.__cmd_queue = []
        self.__cmd_last = ""

        # Board Info
        self.__imei = ""

        # Serial Vals
        self.__data_lock = False
        self.__write_lock = False

        # GPS Vals
        self.__gps_active = False
        self.__gps = GPSData()

        # Bearer Settings
        self.__bearer_apn = ""
        self.__bearer_username = ""
        self.__bearer_password = ""
        self.__bearer_ip = ""

        # HTTP Vals
        self.__http_in_progress = False
        self.__http_request_queue = []
        self.__http_request_last = {}
        self.__http_code = 0
        self.__http_data = {}

        self.__start_worker()

    def __exec_cmd(self, cmd):
        self.__cmd_queue.append(cmd)

    def __modem_write(self, cmd):
        if not self.__write_lock:
            self.__ser.write((cmd + '\n').encode('utf-8'))
            self.__write_lock = True
            if self.__log:
                print("Sent: " + cmd)
            self.__cmd_last = cmd

            return True
        else:
            print("Output locked")
            return False

    def __process_input(self):
        if self.__ser.in_waiting > 0:
            while self.__ser.in_waiting:
                newline = self.__ser.readline().decode('utf-8')
                if self.__log:
                    print("Received: " + newline)

                newline = newline.rstrip('\r').rstrip('\n').rstrip('\r')

                if "OK" in newline:
                    self.__modem_power = True
                    self.__write_lock = False
                elif "ERROR" in newline:
                    self.__write_lock = False

    def __start_worker(self):
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__worker_working = True
        self.__mthread.start()

    def __stop_worker(self):
        self.__worker_working = True
        self.__mthread.join(20)

    def __main_thread(self):
        # Startup

        # Check Modem Power - Send AT, if delay too long toggle power
        while not self.__modem_power:
            self.__exec_cmd("AT")
            check_time = time.time()
            while self.__write_lock:
                if time.time() - check_time > 10:
                    self.power_toggle()
                    time.sleep(10)
                time.sleep(0.1)

        self.__exec_cmd("ATE1V1")

        while self.__worker_working:
            self.__process_input()
            if not self.__write_lock:
                if len(self.__cmd_queue) > 0:
                    self.__modem_write(self.__cmd_queue.pop(0))
            time.sleep(0.1)

    # HTTP Methods

    # GPS Methods

    def power_toggle(self):
        subprocess.Popen(['sudo', 'raspi-gpio', 'set', '4', 'op', 'dh'])
        time.sleep(2)
        subprocess.Popen(['sudo', 'raspi-gpio', 'set', '4', 'op', 'dl'])
        time.sleep(2)

    def start_sys_network(self):
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

    def stop_sys_network(self):
        if self.pon_p is not None:
            subprocess.Popen(['sudo', 'poff'])
            self.pon_p = None

    def get_imei(self):  # Blocking get IMEI
        self.__imei = ""
        self.__exec_cmd("AT+CGSN")
        while True:
            if self.__imei != "":
                return self.__imei
            time.sleep(0.1)
