from modemUnit import ModemUnit
import dateutil.parser
import time
import threading


class NetworkCommunication:
    def __init__(self, imei, mUnit):
        assert isinstance(mUnit, ModemUnit)
        self.imei = imei
        self.mUnit = mUnit
        self.__sos = False
        self.__gps = None

        # Start Worker Thread
        self.__mthread = threading.Thread(target=self.__main_thread, daemon=True)
        self.__mthread.start()

    def __main_thread(self):
        while True:
            self.__sendPing()
            time.sleep(20)

    def updateGPS(self, gps):
        self.__gps = gps

    def sos(self, sos=True):
        self.__sos = sos

    def __sendPing(self):
        # Generate Base
        newcall = "http://t.upnorthdevelopers.com:5055/id=" + str(self.imei)

        # GPS
        if self.__gps is not None and self.__gps.lat != 0:
            iso_utc = str(self.__gps.utc)[:8] + 'T' + str(self.__gps.utc)[8:12]
            timestamp = dateutil.parser.isoparse(iso_utc).timestamp()
            newcall += "&lat=" + str(self.__gps.lat) + "&lon=" + str(
                    self.__gps.lon) + "&timestamp=" + str(timestamp)[:len(str(timestamp)) - 2] + "&altitude=" + str(
                    self.__gps.alt) + "&speed=" + str(self.__gps.speed)
        else:
            newcall += "&timestamp=" + str(time.time()).split('.')[0]

        # Alarm
        if self.__sos:
            newcall += "&alarm=sos"

        self.mUnit.http_get(newcall)