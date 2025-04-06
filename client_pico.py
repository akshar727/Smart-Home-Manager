import os
import json
import sys
import network
import aioble
import bluetooth
import machine
import asyncio
from time import sleep
from microdot.cors import CORS
import urequests as requests # type: ignore
from microdot import Microdot # type: ignore
from cryptolib import aes
from client_setup import ClientSetupManager


MODE_CBC = 2
BLOCK_SIZE = 16

status = ""
logfile = open('log.txt', 'a',0)
os.dupterm(logfile) # type: ignore

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
    CORS(app, allowed_origins=[f'http://{server_ip}'], allow_credentials=True)
    calibrations = {
        "closed_to_open": 10,
        "open_to_closed": 10
    }
    my_id = 0

    async def change_state(status):
        if status == "open":
            backward_pin.off()
            if forward_pin.value() == 0:
                forward_pin.on()
            else:
                forward_pin.off()
            # forward_pin.on()
            # backward_pin.off()
            # await asyncio.sleep(calibrations["closed_to_open"])
            # forward_pin.off()
        elif status == "close":
            forward_pin.off()
            # set as a toggle so if the pin is already on, it will turn off and vice versa
            if backward_pin.value() == 0:
                backward_pin.on()
            else:
                backward_pin.off()
            # backward_pin.on()
            # await asyncio.sleep(calibrations["open_to_closed"])
            # backward_pin.off()
        # TODO: this is where we actually move the motors
        print("Moving motors")
        print(server_ip)
        await asyncio.sleep(1)
        r = requests.post(f"http://{server_ip}/api/net/finish", json={"final_status": status, "id": my_id})
        response = r.json()
        print("Finished moving motors")

    @app.route("/status",methods=["POST"])
    async def status_change(request):
        print(request.body)
        data = json.loads(request.body)
        status = data["status"]
        my_id = data["id"]
        asyncio.create_task(change_state(status))
        print("done")
        #{"new_status": "open" | "close"}
        return {"success": True}

    @app.route('/log.txt')
    async def log(request):
        # stream the log.txt file in parts using a generator and a def function
        logfile.flush()
        def generate():
            with open('log.txt') as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    yield line
        return generate(), {'Content-Type': 'text/css'}
    
    @app.route("/clearlog")
    async def clear_log(request):
        logfile.flush()
        logfile.seek(0)
        logfile.truncate(0)
        logfile.flush()
        return "Log cleared"

    app.run(host=ip, port=80)
