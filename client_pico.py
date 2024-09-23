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


MODE_CBC = 2
BLOCK_SIZE = 16
 
# key size must be 16 or 32
key = b"q\x06\xfd\xc1\x01'\x8a<\x1bV\xf0\xf4\xda\x0e\xf05q\x17Ws\x16\x18\xbfqL\x10\x9c\xe0\xed\x11F\xa1"
iv = b'gf4]\xd8\xf27Tg\xa7\xf5\xfdb,\xf6\xc3'
# server_ip = "192.168.86.195"


def aes_decrypt(ct_bytes):
    print(ct_bytes)
    cipher = aes(key,MODE_CBC,iv)
    decrypted = cipher.decrypt(ct_bytes)
    return decrypted.strip()



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
print("Setup: ",setup)
if setup:
    # ap_app= Microdot()
    
    # if you do not see the network you may have to power cycle
    # unplug your pico w for 10 seconds and plug it in again
    
    # def ap_mode(ssid, password):
    #     """
    #         Description: This is a function to activate AP mode
    
    #         Parameters:
    
    #         ssid[str]: The name of your internet connection
    #         password[str]: Password for your internet connection
    
    #         Returns: Nada
    #     """
    #     # Just making our internet connection
    #     ap = network.WLAN(network.AP_IF)
    #     ap.config(essid=ssid, password=password,hidden=True)
    #     ap.active(True)
    #     ap.ifconfig(("192.168.4.1","255.255.255.0","192.168.4.1","8.8.8.8"))
    #     while ap.active() == False:
    #         pass
    #     print('AP Mode Is Active, You can Now Connect')
    #     print('IP Address To Connect to:: ' + ap.ifconfig()[0])
    
    _SERVER_UUID = bluetooth.UUID(0x2A6E)
    _GENERIC = bluetooth.UUID(0x180A)
    _SERVER_CHARACTERISTICS_UUID = bluetooth.UUID(0xBCA3)

    connected = False
    alive = False
    info = {}

    async def find_server():
        async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
            async for result in scanner:
                if result.name() == "Pico W Blinds":
                    print("Found Server")
                    for item in result.services():
                        print(item)
                    if _GENERIC in result.services():
                        print("Found Server WIFI Transfer Service")
                        return result.device
        return None
    def save_credential(cred):
        # print("Recieved Credential: ",cred)
        if  cred[:2] == b"w;" or cred[:2] == b"p;":
            dec = cred[:2].decode() + aes_decrypt(cred[2:]).decode()
        else:
            dec = cred.decode()
        print("Recieved Credential: ", dec)
        if dec.startswith("w;"):
            info["ssid"] = dec.split(";")[1]
        elif dec.startswith("p;"):
            info["pwd"] = dec.split(";")[1]
        elif dec.startswith("l;"):
            info["location"] = dec.split(";")[1]
        elif dec.startswith("i;"):
            info["server_ip"] = dec.split(";")[1]
        elif dec.startswith("t;"):
            info["type"] = dec.split(";")[1]
            print("Recieved all data necessary.")
            with open(fname,"w") as f:
                json.dump(info,f)

    async def peripheral_task():
        global connected, alive
        
        connected = False
        device = await find_server()
        if not device:
            print("Server not found")
            return
        try:
            print("Connecting to", device)
            connection = await device.connect()
            
        except asyncio.TimeoutError:
            print("Timeout during connection")
            return
        
        async with connection:
            print("Connected to Server")
            connected = True
            alive = True
            try:
                connection = await device.connect()
            except asyncio.TimeoutError:
                print("Connection failed")
                return
            
            async with connection:
                print("Connected")
                alive = True
                connected = True



                while True and alive: 
                    try:
                        wifi_service = await connection.service(_SERVER_UUID)
                        print(wifi_service)
                        wifi_characteristic = await wifi_service.characteristic(_SERVER_CHARACTERISTICS_UUID)  
                        print(wifi_characteristic)
                        # if wifi_service == None:
                        #     print("Server disconnected")
                        #     alive = False
                        #     break
                    except asyncio.TimeoutError:
                        print("Connection timeout when getting service/caracteristic")
                        alive = False
                        return
                    
                    if wifi_characteristic == None:
                        print("Server disconnected")
                        alive = False
                        break
                    buff = b""
                    buff_type =b""
                    while True:
                        # try:
                            # cred = await wifi_characteristic.read()
                            # await wifi_characteristic.subscribe(notify=T rue)
                            cred = await wifi_characteristic.notified()
                            if cred[:2] == b"w;" or cred[:2] == b"p;":
                                print("Start of transmission. Transmission type is " + cred[:2].decode())
                                buff += cred
                                buff_type = cred[:2]
                            elif cred == b";e":
                                print(b"End of transmission: " + buff)
                                save_credential(buff)
                                buff = b""
                                buff_type = b""
                            else:
                                buff += cred
                                print(b"Transmission part: " + cred)
                            # print("Live cred: ",cred)
                            
                        # except Exception as e:
                        #     print("Something went wrong "+str(e))
                        #     connected = False
                        #     alive = False
                        #     break
            await connection.disconnect()
            connected = False
            print("Disconnected")
            alive = False
    asyncio.run(peripheral_task())
else:


    def send_identification():
        k = {
            # "type": client_data["type"],
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


    print("Sending identification..")
    send_identification()
    print("Done!")

    app = Microdot()


    def change_state(status):




        pass # TODO: this is where we actually move the motors

    @app.route("/status",methods=["POST"])
    async def status_change(request):
        data = request.json
        status = data["status"]
        change_state(status)
        #{"new_status": "open" | "close"}

    app.run(host=ip, port=80)





