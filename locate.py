import subprocess
import googlemaps

from config import locate_config


class Locate:
    def __init__(self):
        self.gclient = googlemaps.Client(key=locate_config['googlemaps_apikey'])

    def geolocate(self):
        networks = self.__get_networks()
        r = self.gclient.geolocate(wifi_access_points=networks)
        return r

    def __get_networks(self):
        networks = []
        result = subprocess.check_output(["sudo", "iwlist", "wlan0", "scan"])
        result = result.decode('ascii')
        result = result.split('\n')
        for i in range(len(result)):
            line = result[i]
            if "Cell" in line:
                bssid_s = line.split(":")
                bssid = bssid_s[1][1:]
                for s in bssid_s[2:]:
                    bssid = bssid + ":" + s
                channel = result[i + 1].split(":")[1]
                networks.append({"macAddress": bssid, "channel": int(channel)})
        return networks
