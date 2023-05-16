import time
import config
import datetime
import dateutil.parser

from modemUnit import ModemUnit


def updateGps(remote, imei, gps):
    assert isinstance(remote, ModemUnit)
    iso_utc = str(gps.utc)[:8] + 'T' + str(gps.utc)[8:]
    timestamp = dateutil.parser.isoparse(gps.utc).timestamp()
    result = remote.http_get("http://t.upnorthdevelopers.com:5055/?id=" + str(imei) + "&lat=" + str(gps.lat) + "&lon=" + str(gps.lon) + "&timestamp=" + timestamp + "&altitude=" + str(gps.alt) + "&speed=" + str(gps.speed))
    if "code" in result and result["code"] == 601:
        remote.bearer_close()
        remote.bearer_open()


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
