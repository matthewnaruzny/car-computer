from modemUnit import ModemUnit


class NetworkCommunication:
    def __init__(self, imei, mUnit):
        assert isinstance(mUnit, ModemUnit)
        self.imei = imei
        self.mUnit = mUnit

    def sendSOS(self):
        print("Trigger SOS")
        self.mUnit.http_get("http://t.upnorthdevelopers.com:5055/?id=" + str(self.imei) + "&alarm=sos")
