import subprocess
import threading
import time
import serial


class ModemUnit:

    def __init__(self, port='COM3', baudrate=115200):
        self.__mthread = None
        self.__ser = serial.Serial(port, baudrate=baudrate)
        self.pon_p = None

        self.__modem_power = False
        self.__worker_working = False

        # Serial Vals
        self.__write_lock = False

        # GPS Vals
        self.__gps_active = False
        self.__gps_utc = 0
        self.__gps_lat = 0
        self.__gps_lon = 0
        self.__gps_alt = 0
        self.__gps_speed = 0

    def start_gps(self):
        if not self.__write_lock:
            self.__modem_write("AT+CGNSPWR=1\n")  # Start GNS Modem
            self.__modem_write("AT+CGNSURC=2\n")  # Start GNS Reporting

    def __modem_write(self, cmd):
        if not self.__write_lock:
            self.__ser.write(cmd)
            self.__write_lock = True

            return True
        else:
            return False

    def __process_input(self):
        if self.__ser.in_waiting > 0:
            while self.__ser.in_waiting:
                newline = self.__ser.readline().decode('utf-8').rstrip('\r\n')
                if "OK" in newline:
                    self.__modem_power = True
                    self.__write_lock = False
                elif "+CGNSINF" in newline:  # GNS Data
                    # Parse Data and Update
                    data = newline.split(':')[1].split(',')
                    self.__gps_active = True
                    self.__gps_utc = data[3]
                    self.__gps_lat = float(data[3])
                    self.__gps_lon = float(data[4])
                    self.__gps_alt = float(data[5])
                    self.__gps_speed = float(data[6])

                    self.__write_lock = False

    def __start_worker(self):
        self.__mthread = threading.Thread(target=self.__main_thread(), daemon=True)
        self.__worker_working = True
        self.__mthread.start()

    def __stop_worker(self):
        self.__worker_working = True
        self.__mthread.join(20)

    def __main_thread(self):
        while self.__worker_working:
            self.__process_input()
            time.sleep(0.1)

    def power_toggle(self):
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
