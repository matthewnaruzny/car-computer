import subprocess
import threading
import time
import serial
import json


class GPSData:
    def __init__(self):
        self.utc = 0
        self.lat = 0
        self.lon = 0
        self.alt = 0
        self.speed = 0


class ModemUnit:

    def __init__(self, port='COM3', baudrate=115200, log=False):
        self.__mthread = None
        self.__ser = serial.Serial(port, baudrate=baudrate)
        self.pon_p = None

        self.__log = log

        self.__modem_power = False
        self.__worker_working = False

        self.__cmd_queue = []
        self.__cmd_last = ""

        # Serial Vals
        self.__data_lock = False
        self.__write_lock = False

        # GPS Vals
        self.__gps_active = False
        self.__gps = GPSData()

        # HTTP Vals
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
                newline = self.__ser.readline().decode('utf-8').rstrip('\r\n')
                if self.__log:
                    print("Received: " + newline)

                if "OK" in newline:
                    self.__modem_power = True
                    self.__write_lock = False
                elif "ERROR" in newline:
                    self.__write_lock = False
                elif "+CGNSPWR:" in newline: # GNS Pwr Notification
                    pwr = newline.split(':')[1]
                    self.__gps_active = ('1' in pwr)
                    self.__write_lock = False
                    if self.__gps_active:
                        print("GNSS Active")
                    else:
                        print("GNSS Not Active")
                elif "+UGNSINF" in newline:  # GNS Data
                    # Parse Data and Update
                    try:
                        data = newline.split(':')[1].split(',')
                        self.__gps.utc = float(data[2])
                        self.__gps.lat = float(data[3])
                        self.__gps.lon = float(data[4])
                        self.__gps.alt = float(data[5])
                        self.__gps.speed = float(data[6])
                    except ValueError:
                        pass
                    self.__write_lock = False
                elif newline.startswith("+HTTPACTION"):  # New HTTP Data
                    resdata = newline.split(',')
                    code = resdata[1]
                    self.__http_code = code
                    self.__http_size = int(resdata[2])
                    if code == "200":
                        self.__exec_cmd("AT+HTTPREAD")
                elif newline.startswith("+HTTPREAD"):
                    http_data = self.__ser.read(self.__http_size).decode('utf-8')
                    self.__http_data = json.loads(http_data)
                    print("Data\n" + str(self.__http_data))



    def __start_worker(self):
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__worker_working = True
        self.__mthread.start()

    def __stop_worker(self):
        self.__worker_working = True
        self.__mthread.join(20)

    def __main_thread(self):
        # Startup

        self.__exec_cmd("ATE1V1")

        while self.__worker_working:
            self.__process_input()
            if not self.__write_lock:
                if len(self.__cmd_queue) > 0:
                    self.__modem_write(self.__cmd_queue.pop(0))
            time.sleep(0.1)

    def http_get(self, url):
        self.__exec_cmd("AT+HTTPTERM")
        self.__exec_cmd("AT+HTTPINIT")
        self.__exec_cmd('AT+HTTPPARA="URL","'+url+'"')
        self.__exec_cmd('AT+HTTPPARA="CID",1')
        self.__exec_cmd('AT+HTTPACTION=0')

    def get_http_data(self):
        return self.__http_code, self.__http_data

    def data_open(self):
        self.__exec_cmd("AT+CMEE=1")
        self.__exec_cmd("AT+CGATT=1")
        self.__exec_cmd("AT+CGACT=1,1")
        self.__exec_cmd("AT+CGPADDR=1")
        self.__exec_cmd('AT+SAPBR=3,1,"APN","super"')

    def network_open(self):
        self.__exec_cmd("AT+SAPBR=1,1")

    def network_close(self):
        self.__exec_cmd("AT+SAPBR=0,1")



    def start_gps(self):
        self.__exec_cmd("AT+CGNSPWR=1")  # Start GNS Modem
        self.__exec_cmd("AT+CGNSURC=2")  # Start GNS Reporting

    def stop_gps(self):
        self.__exec_cmd("AT+CGNSURC=0")
        self.__exec_cmd("AT+CGNSPWR=0")

    def get_gps(self):
        return self.__gps

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
