import os
import json
import sys
from client_network_manager import CameraClientNetworkManager
from time import sleep
from microdot.cors import CORS
import urequests as requests # type: ignore
from microdot import Microdot # type: ignore
from client.client_setup import ClientSetupManager

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

    server_ip = client_data["server_ip"]


print("Setup: ",setup)
if setup:
    setup_manager = ClientSetupManager(fname)
    setup_manager.start_setup()
else:
    network_manager = CameraClientNetworkManager(client_data["location"], server_ip, client_data["ssid"], client_data["pwd"])