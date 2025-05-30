
import asyncio
import os
import json
from microdot.cors import CORS
from microdot.microdot import Microdot, send_file, Response
from microdot.sse import with_sse
import urequests as requests
import machine
import aioble
import bluetooth
import sys
import network
from utime import sleep
import utime as time
import _thread
from machine import Pin
import os
import micropython
import cryptolib

from machine import WDT
def uid():
    return "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(*machine.unique_id())


wdt = ...


# logfile = open('log.txt', 'a',0)
# # clear the log file
# # duplicate stdout and stderr to the log file
# os.dupterm(logfile) # type: ignore

    
MODE_CBC = 2
BLOCK_SIZE = 16

# key size must be 16 or 32
key = b"q\x06\xfd\xc1\x01'\x8a<\x1bV\xf0\xf4\xda\x0e\xf05q\x17Ws\x16\x18\xbfqL\x10\x9c\xe0\xed\x11F\xa1"
iv = b'gf4]\xd8\xf27Tg\xa7\xf5\xfdb,\xf6\xc3'


def aes_encrypt(plaintext,_id):
    pad = BLOCK_SIZE - len(plaintext) % BLOCK_SIZE
    plaintext = plaintext + " "*pad
    
    # Generate iv with HW random generator 
    # iv = uos.urandom(BLOCK_SIZE)
    cipher = cryptolib.aes(key,MODE_CBC,iv)
    
    ct_bytes = cipher.encrypt(plaintext)
    # join the id and the ciphertext
    ct_bytes = _id.encode() + ct_bytes
    return ct_bytes

def split_into_chunk_20(inp):
    return [inp[i:i+20] for i in range(0,len(inp),20)]



print("\n")
print("Starting up server")

class NetworkError(Exception):
    pass

app = Microdot()
CORS(app, allowed_origins='*', allow_credentials=True)
available_devices = []

def connect(ssid,password,exit_on_not_found):
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if exit_on_not_found == True:
        found_network = False
        _networks = wlan.scan()
        for _network in _networks:
            print(_network)
            if _network[0] == ssid:
                found_network = True
                break

        if not found_network:
            print("Network not found")
            raise NetworkError("Network not found")
        
    wlan.connect(ssid, password)
    tries = 15
    while wlan.isconnected() == False and tries >0:
        print('Waiting for connection...')
        tries -= 1
        sleep(1)
    if tries == 0:
        print("Failed to connect")
        raise NetworkError("Failed to connect")
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip


def isfile(path):
    # check if there is a file at path
    try:
        with open(path) as f:
            return True
    except:
        return False
    
def machine_reset():
    sleep(1)
    print("Resetting")
    machine.reset()

fname = "wifi.json"
test_fname = "wifi_test.json"
devices_name = "devices.json"
setup = 1
if isfile(fname):
    setup = 0

if isfile(test_fname):
    try:
        with open(test_fname) as f:
            cred = json.load(f)
            ip = connect(cred["ssid"],cred["password"],exit_on_not_found=False)
            # rename the wifi_test.json file to wifi.json
            if ip:
                os.rename(test_fname,fname)
                setup = 0
    except NetworkError:
        os.remove(test_fname)
        setup = 2


# load a file named devices.json
next_id = 0

if isfile(devices_name):
    with open(devices_name) as f:
        data = json.load(f)
        available_devices = data["devices"]
        next_id = data["next_id"]


if setup == 1:
    ap_app= Microdot()
    
    # if you do not see the network you may have to power cycle
    # unplug your pico w for 10 seconds and plug it in again
    
    def ap_mode(ssid, password):
        """
            Description: This is a function to activate AP mode
    
            Parameters:
    
            ssid[str]: The name of your internet connection
            password[str]: Password for your internet connection
    
            Returns: Nada
        """
        # Just making our internet connection
        ap = network.WLAN(network.AP_IF)
        ap.config(essid=ssid, password=password)
        ap.active(True)
        ap.ifconfig(("192.168.4.1","255.255.255.0","192.168.4.1","8.8.8.8"))
        while ap.active() == False:
            pass
        print('AP Mode Is Active, You can Now Connect')
        print('IP Address To Connect to:: ' + ap.ifconfig()[0])
    
    
    
    ap_mode('Rpi Pico W',
            '123456789')
    
    @ap_app.get("/")
    async def startup_portal(request):
        with open("startup.html","r") as f:
            base = f.read()
            wlan = network.WLAN(network.STA_IF)
            networks = wlan.scan()
            networks = [networks[i][0].decode() for i in range(len(networks)) if networks[i][0].decode().strip() != ""]
            # remove duplicate networks
            networks = list(set(networks))
            # remove networks that are just \x00
            networks = [net for net in networks if net.replace("\x00","") != ""]
            print(networks)
            
            opts = []
            for net in networks:
                opts.append(f"<option name='{net}'>{net}</option>")
            opts = "\n".join(opts)
            base = base.replace("{{options}}",opts)
            return base, {'Content-Type':'text/html'}
        
    @ap_app.post("/check")
    async def try_to_connect(request):
        cred = request.json
        ssid = cred["ssid"]
        pwd = cred["password"]
        with open(test_fname,"w") as f:
            json.dump({"ssid":ssid,"password":pwd},f)
        request.app.shutdown()
        return {"success":True}
    
    ap_app.run(port=80)
    _thread.start_new_thread(machine_reset,())
    while True:
        pass
elif setup == 0:
    led = machine.Pin("LED", machine.Pin.OUT)
    led.off()
    ip = ""

    with open(fname) as f:
        cred = json.load(f)
        ssid = cred["ssid"]
        password = cred["password"]


    MANUFACTURER_DATA = micropython.const(0x02A29)
    MODEL_NUMBER = micropython.const(0x02A24)
    SERIAL_NUMBER = micropython.const(0x02A25)
    FIRMWARE_REVISION = micropython.const(0x02A26)
    BLE_VERSION = micropython.const(0x02A28)


    _GENERIC = bluetooth.UUID(0x180A)

    _WIFI_UUID = bluetooth.UUID(0x2A6E)

    _SSID_UUID = bluetooth.UUID(0xBCA3)

    _BLE_APPEARANCE_GENERIC_UNKNOWN = micropython.const(0)

    ADV_INTERVAL_MS = micropython.const(250_000)

    device_info = aioble.Service(_GENERIC)
    connection = None

    aioble.Characteristic(device_info, bluetooth.UUID(MANUFACTURER_DATA),read=True,initial="Pico W Server")
    aioble.Characteristic(device_info, bluetooth.UUID(MODEL_NUMBER),read=True,initial="1.0")
    aioble.Characteristic(device_info, bluetooth.UUID(SERIAL_NUMBER),read=True,initial=uid())
    aioble.Characteristic(device_info, bluetooth.UUID(FIRMWARE_REVISION),read=True,initial=sys.version)
    aioble.Characteristic(device_info, bluetooth.UUID(BLE_VERSION),read=True,initial="1.0")

    wifi_service = aioble.Service(_WIFI_UUID)


    wifi_ssd_characteristic = aioble.Characteristic(wifi_service, _SSID_UUID, notify=True, read=True)
    print("Starting BLE")
    aioble.register_services(device_info, wifi_service)

    async def ble_advertise():    
        global connected, connection
        while True:
            connected = False
            async with await aioble.advertise(ADV_INTERVAL_MS, name="Pico W Server",appearance=_BLE_APPEARANCE_GENERIC_UNKNOWN,services=[_GENERIC]) as connection:
                print("Connection from ", connection.device)
                connected = True
                await connection.disconnected()
                connected = False
                print("Disconnected")

    connected = False

    print(available_devices)


    print('Connecting to Network...')
    try:
        led.on()
        ip = connect(ssid,password,False)
    except KeyboardInterrupt:
        machine.reset()


    led.off()

    @app.before_request
    async def log_request(request):
        print(f"Request from {request.client_addr[0]} to {request.url} with method {request.method}")

    @app.route('/')
    async def index(request):
        return send_file("index.html")
    


    
        

    @app.route('/index.css')
    async def index_css(request):
        return send_file("index.css")

    @app.route("/api/net/id",methods=["POST"])
    async def register(request):
        global next_id
        data = request.json
        # wdt.feed()
        # check if the device is already registered if so then just act like it was successful
        for device in available_devices:
            if device["ip"] == request.client_addr[0]:
                print(f"The existing device at {device['location']} and ip {device['ip']} has reregistered...")
                return {"success":True, "id":device["id"]}
        device = {"ip":request.client_addr[0],"location":data["location"],"type":data["type"],"id":next_id,"status":data["state"]}
        available_devices.append(device)
        next_id += 1
        with open(devices_name,"w") as f:
            json.dump({"next_id":next_id, "devices":available_devices},f)
        print(f"Found a NEW device at {data['location']} with ip {device['ip']}. Assigning ID of {device['id']}")
        print(available_devices)
        return {"success":True,"id":device["id"]}
    # user to server pico to client pico
    @app.route("/api/operation/<int:id>/<string:status>",methods=["GET"])
    async def run_pico(request, id,status):
        # wdt.feed()
        target_device = None
        for device in available_devices:
            if device["id"] ==  id:
                target_device = device
                break
        if target_device == None:
            return {"success":False, "err": "Device not found or not registered"}
        if target_device["status"] == "offline":
            return {"success":False, "err": "Device is offline"}
        req_data = {"status":status,"id":target_device["id"]}
        target_device["status"] = "transit_open" if status == "open" else "transit_close"
        print(target_device["ip"])
        print(f"Sending {status} to {target_device['location']} with id {target_device['id']}")
        print(req_data)
        print(type(target_device["ip"]))
        print("sending")
        r = requests.post(f"http://{target_device['ip']}/status", json=req_data)
        print("sent")
        print(r.status_code)
        status = r.json()
        return status

    # meant from client pico to server
    @app.route("/api/net/finish",methods=["POST"])
    async def finish_status_change(request):
        data = json.loads(request.body)
        _id = data["id"]
        target_device = None
        for device in available_devices:
            print(device)
            if device["id"] ==  _id:
                target_device = device
                break
        if target_device == None:
            return {"success":False, "err": "Device not found or not registered"}
        target_device["status"] = data["final_status"]
        return {"success":True}
        
    lock = False
    def get_elapsed_time():
        return time.ticks_ms() // 1000  # Convert milliseconds to seconds
    def format_uptime(seconds):
        days = seconds // (24 * 3600)
        seconds %= (24 * 3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    @app.route("/api/server-info")
    async def server_info(request):
        uptime = format_uptime(get_elapsed_time())
        # format uptime as XX days, XX hours, XX minutes, XX seconds before returning

        return {"ip":ip,"time":get_elapsed_time()}
    @app.route("/api/network")
    async def check_for_devices(request):
        if connected and not lock:
            led.on()
            return [True]
        else:
            led.off()
            return [False]

    @app.route("/api/credential-apply",methods=["POST"])
    async def apply_credentials(request):
        global lock
        if not connected:
            return {"success":False,"err":"Device not found"}
        data = json.loads(request.body.decode())
        print(data)
        loc = data["location"]
        print("Characteristic: "+ str(wifi_ssd_characteristic))
        await asyncio.sleep(1)

        async def send(data,_id,encrypt=True):
            # start from 16 because the iv will also be on the client pico
            pdata = aes_encrypt(data,_id) if encrypt else _id.encode()+data
            chunks = split_into_chunk_20(pdata)
            print(pdata)
            print(chunks)
            for chunk in chunks:
                wifi_ssd_characteristic.write(chunk)
                wifi_ssd_characteristic.notify(connection,chunk)
                await asyncio.sleep(0.05)
            wifi_ssd_characteristic.write(";e")
            wifi_ssd_characteristic.notify(connection,";e")
        lock = True
        await send(ssid,"w;")
        await asyncio.sleep(0.3)
        await send(password,"p;")
        await asyncio.sleep(0.3)
        await send(loc.encode(),"l;",False)
        await asyncio.sleep(0.3)
        await send(ip.encode(),"i;",False)
        # disconnect from the device
        lock = False
        return {"success":True}
    

        

    @app.route("/terminate")
    async def terminate(request):
        request.app.shutdown()
        return "Shutdown initiated…"

    @app.errorhandler(404)
    async def not_found(request):
        return {'error': 'Resource not found'}, 404
    
    async def ping_clients():
        # truncate the logfile on start
        while True:
            # wdt.feed()
            # if the logfile is more than 200 lines, remove the first couple lines till it goes back to 200
            
            # check if the device is reachable
            
            for device in available_devices:
                try:
                    r = requests.post(f"http://{device['ip']}/net/ping",timeout=8)
                    print(r.status_code)
                    print(f"Device reachable, IP is {device['ip']} and location is {device['location']}")
                    if device.get("old_status") != None:
                        device["status"] = device["old_status"]
                        device["old_status"] = None
                except Exception as e:
                    print(f"Device not reachable, IP is {device['ip']} and location is {device['location']}.")
                    # try two more times to ping and if both fail then mark as offline
                    fail_times = 0
                    try:
                        r = requests.post(f"http://{device['ip']}/net/ping",timeout=8)
                        print(r.status_code)
                        print(f"Device reachable after 2nd try, IP is {device['ip']} and location is {device['location']}")
                        continue
                    except Exception as e:
                        fail_times += 1
                        print("2nd ping failed, trying once more")

                    try:
                        r = requests.post(f"http://{device['ip']}/net/ping",timeout=8)
                        print(r.status_code)
                        print(f"Device reachable after 3rd try, IP is {device['ip']} and location is {device['location']}")
                        continue
                    except Exception as e:
                        fail_times += 1
                        print("3rd ping failed, marking as offline")

                    if fail_times == 2:
                        if device["status"] != "offline":
                            device["old_status"] = device["status"]
                            device["status"] = "offline"

            await asyncio.sleep(120)

        
    @app.route("/devices")
    @with_sse
    async def devices_sse(request,sse):
        # test the sse
        print("Begin setting old")
        old = available_devices
        print("End setting old")
        await sse.send(available_devices)
        while True:
            # wdt.feed()
            # print(f"Old instance: {old} new instance: {available_devices}")
            if available_devices != old:
                print(f"Old instance: {old} new instance: {available_devices}")
                await sse.send(available_devices)
                old = available_devices
            await asyncio.sleep(1)
    print("running")
    async def main():
        # global wdt
        # wdt = WDT(timeout=8000)
        server = asyncio.create_task(app.start_server(port=80,debug=True,host="0.0.0.0"))
        
        advertising = asyncio.create_task(ble_advertise())
        
        # client_pings = asyncio.create_task(ping_clients())
        
        await server
        await advertising
        # await client_pings
        # wdt.feed()
    asyncio.run(main())

