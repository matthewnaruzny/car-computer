import subprocess


def get_networks():
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
            channel = result[i+1].split(":")[1]
            networks.append({"macAddress": bssid, "channel": int(channel)})
    return networks


