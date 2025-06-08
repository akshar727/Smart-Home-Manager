import json
from client_network_manager import BlindsClientNetworkManager
import uos

if not "calibration.json" in  uos.listdir():
    calibrations = {
        "closed_to_open": 10,
        "open_to_closed": 10,
        "state": "open"
    }
    with open("calibration.json", "w") as f:
        json.dump(calibrations, f)
else:   
    with open("calibration.json", "r") as f:
        calibrations = json.load(f)
        print("Calibrations: ", calibrations)

fname = "client_data.json"
setup = True
def isfile(path):
    # check if there is a file at path
    try:
        with open(path) as f:
            return True
    except:
        return False

client_data = {}
if isfile(fname):
    setup = False
    with open(fname) as f:
        client_data = json.load(f)
    self_id = client_data.get("id", None)
    print(self_id)
    server_ip = client_data["server_ip"]

print("Setup: ",setup)
if not setup:
    network_manager = BlindsClientNetworkManager(client_data["location"], calibrations.get("state") if calibrations.get("state") is not None else "close", server_ip, client_data["ssid"], client_data["pwd"], calibrations["closed_to_open"], calibrations["open_to_closed"],self_id)