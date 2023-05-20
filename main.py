import time

from modemUnit import ModemUnit
from networkCommunication import NetworkCommunication
from safetyCheck import SafetyCheck

if __name__ == '__main__':
    # Start Controllers
    remote = ModemUnit(log=True)

    imei = remote.get_imei()

    remote.start_gps()
    gps = remote.get_gps()

    remote.data_open()
    remote.bearer_set_settings(apn='super')
    remote.bearer_open()

    networkCommunication = NetworkCommunication(imei, remote)
    safetyCheck = SafetyCheck(networkCommunication)
