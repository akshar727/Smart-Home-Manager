import os
import json
import network
import aioble
import bluetooth
import machine
import asyncio
from time import sleep
import requests
from microdot import Microdot # type: ignore
from cryptolib import aes
from client_setup import ClientSetupManager


MODE_CBC = 2
BLOCK_SIZE = 16

status = ""

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


_type = ""
# should be preset by developer
id_file = "IDENTITY"
with open(id_file, "r") as f:
    _type = f.read()

print("Setup: ",setup)
if setup:
    setup_manager = ClientSetupManager(fname)
    setup_manager.start_setup()
else:


    def send_identification():
        k = {
            "type": _type,
            "location": client_data["location"],
        }
        try:
            r = requests.post(f"http://{server_ip}/api/net/id", json=k)
            print(r.json())
            print("ID sent")
        except Exception as e:
            print("Failed to send ID:" + str(e))



    def connect():
        #Connect to WLAN
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(client_data["ssid"], client_data["pwd"])
        while wlan.isconnected() == False:
            print('Waiting for connection...')
            sleep(1)
        ip = wlan.ifconfig()[0]
        print(f'Connected on {ip}')
        return ip



    print("Connecting to Wifi")
    led = machine.Pin("LED", machine.Pin.OUT)
    led.toggle()
    try:
        ip = connect()
    except KeyboardInterrupt:
        machine.reset()
        pass
    led.toggle()
    forward_pin = machine.Pin(27, machine.Pin.OUT)
    backward_pin = machine.Pin(28, machine.Pin.OUT)

    print("Sending identification..")
    send_identification()
    print("Done!")

    app = Microdot()
    calibrations = {
        "closed_to_open": 10,
        "open_to_closed": 10
    }
    my_id = 0

    async def change_state(status):
        if status == "open":
            forward_pin.on()
            backward_pin.off()
            await asyncio.sleep(calibrations["closed_to_open"])
            forward_pin.off()
        elif status == "close":
            forward_pin.off()
            backward_pin.on()
            await asyncio.sleep(calibrations["open_to_closed"])
            backward_pin.off()
        # TODO: this is where we actually move the motors

        r = requests.post(f"http://{server_ip}/api/net/state", json={"status": status, "id": my_id})

    @app.route("/status",methods=["POST"])
    async def status_change(request):
        data = request.json
        status = data["status"]
        my_id = data["id"]
        await change_state(status)
        #{"new_status": "open" | "close"}
        return {"success": True}

    app.run(host=ip, port=80)
