import time
import config

from modemUnit import ModemUnit

if __name__ == '__main__':

    # Start Modem Controller
    remote = ModemUnit(log=False)
    imei = remote.get_imei()
    remote.bearer_set_settings(apn='super')
    remote.data_open()
    remote.bearer_open()
    data1 = remote.http_get("http://httpbin.org/get")
    print("Data: " + str(data1))
    data2 = remote.http_get("http://route.upnorthdevelopers.com/health")
    print("Data: " + str(data2))

    while True:
        time.sleep(0.1)

