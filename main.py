import time
import config
import datetime
import dateutil.parser

from modemUnit import ModemUnit


def updateGps(remote, imei, gps):
    assert isinstance(remote, ModemUnit)
    timestamp = 0
    if gps.utc != 0:
        iso_utc = str(gps.utc)[:8] + 'T' + str(gps.utc)[8:12]
        timestamp = dateutil.parser.isoparse(iso_utc).timestamp()
        remote.http_get("http://t.upnorthdevelopers.com:5055/?id=" + str(imei) + "&lat=" + str(gps.lat) + "&lon=" + str(gps.lon) + "&timestamp=" + str(timestamp)[:len(str(timestamp))-2] + "&altitude=" + str(gps.alt) + "&speed=" + str(gps.speed))


if __name__ == '__main__':

    # Start Modem Controller
    remote = ModemUnit(log=True)

    imei = remote.get_imei()
    remote.start_gps()
    gps = remote.get_gps()

    remote.data_open()
    remote.bearer_set_settings(apn='super')
    remote.bearer_open()

    while True:
        updateGps(remote, imei, gps)
        time.sleep(10)
