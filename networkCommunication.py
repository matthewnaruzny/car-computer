from modemUnit import ModemUnit
import dateutil.parser
import time
import threading
import logging


class NetworkCommunication:
    def __init__(self, imei, mUnit):
        assert isinstance(mUnit, ModemUnit)
        self.imei = imei
        self.mUnit = mUnit
        self.__sos = False
        self.__sos_old = False
        self.__gps = None

        self.__last_ping_time = 0

        # Start Worker Thread
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__mthread.start()

    def __main_thread(self):
        while True:
            time_lapsed = time.time() - self.__last_ping_time

            if self.__gps is not None and self.__gps.speed > 1 and time_lapsed >= 20:
                self.__sendPing()
                self.__last_ping_time = time.time()
            elif time_lapsed >= 60:
                self.__sendPing()
                self.__last_ping_time = time.time()

            time.sleep(0.1)

    def updateGPS(self, gps):
        self.__gps = gps

    def sos(self, sos=True):
        self.__sos = sos
        if self.__sos is not self.__sos_old:
            self.__sendPing()
        self.__sos_old = self.__sos

    def __sendPing(self):
        # Generate Base
        newcall = "http://t.upnorthdevelopers.com:5055/?id=" + str(self.imei)

        # GPS
        self.__gps = self.mUnit.get_gps()  # Update GPS Values from modem
        if self.__gps is not None and self.__gps.lat != 0:
            knot_speed = self.__gps.speed * 0.539957  # Convert from km/h to Knot
            iso_utc = str(self.__gps.utc)[:8] + 'T' + str(self.__gps.utc)[8:12]
            timestamp = dateutil.parser.isoparse(iso_utc).timestamp()
            newcall += "&lat=" + str(self.__gps.lat) + "&lon=" + str(
                self.__gps.lon) + "&timestamp=" + str(timestamp)[:len(str(timestamp)) - 2] + "&altitude=" + str(
                self.__gps.alt) + "&speed=" + str(knot_speed) + "&heading=" + str(self.__gps.course)
        else:
            newcall += "&timestamp=" + str(time.time()).split('.')[0]

        # Alarm
        if self.__sos:
            newcall += "&alarm=sos"

        logging.info("Sending Ping: " + newcall)
        self.mUnit.http_get(newcall)
