import subprocess
import threading
import time
import serial
import json
import uuid
import logging


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

        self.__power_check_time = 0
        self.__power_checking = False

        self.__modem_power = False
        self.__worker_working = False

        self.__cmd_queue = []
        self.__cmd_last = ""

        # Board Info
        self.__imei = ""
        self.__imei_lock = False

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
                logging.info("Modem Sent: " + cmd)
                # print("Sent: " + cmd)
            self.__cmd_last = cmd

            return True
        else:
            # print("Output locked")
            return False

    def __process_input(self):
        if self.__ser.in_waiting > 0:
            while self.__ser.in_waiting:
                newline = self.__ser.readline().decode('utf-8')
                if self.__log:
                    logging.info("Modem Received: " + newline)
                    # print("Received: " + newline)

                newline = newline.rstrip('\r').rstrip('\n').rstrip('\r')

                self.__power_checking = False
                self.__power_check_time = time.time()

                if "OK" in newline:
                    self.__modem_power = True
                    self.__write_lock = False
                elif "ERROR" in newline:
                    self.__write_lock = False
                elif "+CGNSPWR:" in newline:  # GNS Pwr Notification
                    pwr = newline.split(':')[1]
                    self.__gps_active = ('1' in pwr)
                    self.__write_lock = False
                    if self.__gps_active:
                        logging.info("Modem: GNSS Active")
                        # print("GNSS Active")
                    else:
                        logging.info("Modem: GNSS Not Active")
                        # print("GNSS Not Active")
                elif "+UGNSINF" in newline:  # GNS Data
                    # Parse Data and Update
                    try:
                        data = newline.split(':')[1].split(',')
                        self.__gps.utc = float(data[2])
                        self.__gps.lat = float(data[3])
                        self.__gps.lon = float(data[4])
                        self.__gps.alt = float(data[5])
                        self.__gps.speed = float(data[6])
                        self.__gps.course = float(data[7])
                    except ValueError:
                        pass
                elif newline.startswith("+HTTPACTION"):  # New HTTP Data
                    resdata = newline.split(',')
                    code = resdata[1]
                    self.__http_code = code
                    self.__http_size = int(resdata[2])
                    if code == "200" and self.__http_size > 0:
                        self.__exec_cmd("AT+HTTPREAD")
                    else:
                        self.__http_data[self.__http_request_last['uuid']] = {'code': self.__http_code}
                        self.__http_in_progress = False

                    self.__exec_cmd("AT+HTTPTERM")

                elif newline.startswith("+HTTPREAD"):
                    http_raw_data = self.__ser.read(self.__http_size).decode('utf-8')
                    try:
                        http_data = json.loads(http_raw_data)
                        self.__http_data[self.__http_request_last['uuid']] = http_data
                    except json.decoder.JSONDecodeError:  # If decode fails, return raw data
                        self.__http_data[self.__http_request_last['uuid']] = http_raw_data

                    self.__http_in_progress = False
                    if self.__log:
                        logging.info(
                            "Modem HTTP Request Data:" + str(self.__http_data[self.__http_request_last['uuid']]))
                        # print("HTTP Request Data:" + str(self.__http_data[self.__http_request_last['uuid']]))

                elif newline.startswith("+SAPBR"):  # Bearer Parameter Command
                    pass
                elif self.__cmd_last == "AT+CGSN" and not newline.startswith(
                        "AT") and not self.__imei_lock:  # IMEI Reply
                    logging.info("Modem Received IMEI: " + self.__imei)
                    # print("Received IMEI: " + self.__imei)
                    self.__imei = newline
                    self.__write_lock = False
                    self.__imei_lock = True

    def __start_worker(self):
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__worker_working = True
        self.__mthread.start()

    def __stop_worker(self):
        self.__worker_working = False
        self.__mthread.join(20)

    def __main_thread(self):
        # Startup

        self.__power_check_time = time.time()

        while self.__worker_working:

            if time.time() - self.__power_check_time > 20 and self.__write_lock:  # Timeout Check - Restart and Rerun
                self.power_toggle()
                time.sleep(10)
                self.__write_lock = False
                self.__modem_write(self.__cmd_last)

            self.__process_input()
            if not self.__write_lock:
                if not self.__http_in_progress:  # Perform next HTTP request
                    if len(self.__http_request_queue) > 0:
                        self.__perform_next_http()

                if len(self.__cmd_queue) > 0:
                    self.__modem_write(self.__cmd_queue.pop(0))
            time.sleep(0.1)

    # HTTP Functions
    def __perform_next_http(self):
        if not self.__http_in_progress:
            self.__http_in_progress = True
            next_request = self.__http_request_queue.pop(0)
            self.__http_request_last = next_request
            self.__exec_cmd("AT+HTTPTERM")
            self.__exec_cmd("AT+HTTPINIT")
            self.__exec_cmd('AT+HTTPPARA="URL","' + next_request['url'] + '"')
            self.__exec_cmd('AT+HTTPPARA="CID",1')
            self.__exec_cmd('AT+HTTPACTION=' + str(next_request['action']))
            return True
        return False

    def __http_request(self, url, action):
        new_uuid = uuid.uuid4()
        self.__http_request_queue.append({'url': url, 'action': action, 'uuid': new_uuid})
        self.__http_data[new_uuid] = None
        while True:
            if self.__http_data[new_uuid] is not None:
                return self.__http_data[new_uuid]
            time.sleep(0.1)

    def http_get(self, url):
        return self.__http_request(url, 0)

    def get_http_last(self):
        if len(self.__http_data) > 0:
            return self.__http_code, self.__http_data[0]
        return self.__http_code, {}

    def get_http_response(self, i):
        return self.__http_data[i]

    # Bearer Configuration

    def __bearer_set_val(self, cid, param, value):
        self.__exec_cmd('AT+SAPBR=3,' + str(cid) + ',"' + param + '","' + value + '"')

    def __bearer_update(self):
        if self.__bearer_apn != "":
            self.__bearer_set_val(1, "APN", self.__bearer_apn)  # Set APN
        if self.__bearer_username != "":
            self.__bearer_set_val(1, "USER", self.__bearer_username)  # Set Username
        if self.__bearer_password != "":
            self.__bearer_set_val(1, "PWD", self.__bearer_password)  # Password

    def bearer_set_settings(self, apn="", username="", password=""):
        self.__bearer_apn = apn
        self.__bearer_username = username
        self.__bearer_password = password
        self.__bearer_update()

    def data_open(self):
        self.__exec_cmd("AT+CMEE=1")
        self.__exec_cmd("AT+CGATT=1")
        self.__exec_cmd("AT+CGACT=1,1")
        self.__exec_cmd("AT+CGPADDR=1")
        self.__bearer_update()

    def bearer_open(self):
        self.__exec_cmd("AT+SAPBR=1,1")

    def bearer_close(self):
        self.__exec_cmd("AT+SAPBR=0,1")

    # GPS and Location Functions
    def start_gps(self):
        self.__exec_cmd("AT+CGNSPWR=1")  # Start GNS Modem
        self.__exec_cmd("AT+CGNSURC=10")  # Start GNS Reporting

    def stop_gps(self):
        self.__exec_cmd("AT+CGNSURC=0")
        self.__exec_cmd("AT+CGNSPWR=0")

    def get_gps(self):
        return self.__gps

    def power_toggle(self):
        # logging.info("Power Cycling Modem")
        print("Power Cycling Modem")
        self.__power_check_time = time.time()
        subprocess.Popen(['sudo', 'raspi-gpio', 'set', '4', 'op', 'dh'])
        time.sleep(2)
        subprocess.Popen(['sudo', 'raspi-gpio', 'set', '4', 'op', 'dl'])

    def start_sys_network(self):
        logging.info("Attempting to connect to network...")
        # print("Attempting to connect to network...")
        self.pon_p = subprocess.Popen(['sudo', 'pon'])

        while True:
            time.sleep(5)

            # Check if ppp0 exists
            print("Checking...")
            adapter_check = subprocess.check_output(['ip', 'addr', 'show'])
            if "ppp0" in adapter_check.decode('utf-8'):  # If ppp0 exists, create route and end
                logging.info("Creating route")
                # print("Creating route")
                subprocess.Popen(['sudo', 'route', 'add', '-net', '0.0.0.0', 'ppp0'])
                return

    def stop_sys_network(self):
        if self.pon_p is not None:
            subprocess.Popen(['sudo', 'poff'])
            self.pon_p = None

    def get_imei(self):  # Blocking get IMEI
        self.__imei = ""
        self.__imei_lock = False
        self.__exec_cmd("AT+CGSN")
        while True:
            if self.__imei != "":
                return self.__imei
            time.sleep(0.1)
