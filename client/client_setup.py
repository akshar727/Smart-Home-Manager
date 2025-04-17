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


def aes_decrypt(ct_bytes):
    cipher = aes(key,MODE_CBC,iv)
    decrypted = cipher.decrypt(ct_bytes)
    return decrypted.strip()



class ClientSetupManager():
    def __init__(self,fname):
        self._SERVER_UUID = bluetooth.UUID(0x2A6E)
        self._GENERIC = bluetooth.UUID(0x180A)
        self._SERVER_CHARACTERISTICS_UUID = bluetooth.UUID(0xBCA3)

        self.connected = False
        self.alive = False
        self.info = {}
        self.fname = fname

    async def find_server(self):
        async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
            async for result in scanner:
                if result.name() == "Pico W Server":
                    print("Found Server")
                    for item in result.services():
                        print(item)
                    if self._GENERIC in result.services():
                        print("Found Server WIFI Transfer Service")
                        return result.device
        return None
    def save_credential(self,cred):
        if  cred[:2] == b"w;" or cred[:2] == b"p;":
            dec = cred[:2].decode() + aes_decrypt(cred[2:]).decode()
        else:
            dec = cred.decode()
        print("Recieved Credential: ", dec)
        if dec.startswith("w;"):
            self.info["ssid"] = dec.split(";")[1]
        elif dec.startswith("p;"):
            self.info["pwd"] = dec.split(";")[1]
        elif dec.startswith("l;"):
            self.info["location"] = dec.split(";")[1]
        elif dec.startswith("i;"):
            self.info["server_ip"] = dec.split(";")[1]
            print("Recieved all data necessary.")
            with open(self.fname,"w") as f:
                json.dump(self.info,f)

    async def peripheral_task(self):
        global connected, alive
        
        connected = False
        device = await self.find_server()
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
                led = machine.Pin("LED", machine.Pin.OUT)
                led.on()
                alive = True
                connected = True



                while True and alive: 
                    try:
                        wifi_service = await connection.service(self._SERVER_UUID)
                        print(wifi_service)
                        wifi_characteristic = await wifi_service.characteristic(self._SERVER_CHARACTERISTICS_UUID)  
                        print(wifi_characteristic)
                    except asyncio.TimeoutError:
                        print("Connection timeout when getting service/caracteristic")
                        alive = False
                        return
                    
                    if wifi_characteristic == None:
                        print("Server disconnected")
                        alive = False
                        break
                    buff = b""
                    buff_type = b""
                    while True:
                        try:
                            cred = await wifi_characteristic.notified()
                            available_cred_starts = [
                                b"w;",
                                b"p;",
                                b"l;",
                                b"i;",
                            ]
                            if cred[:2] in available_cred_starts:
                                print("Start of transmission. Transmission type is " + cred[:2].decode())
                                buff += cred
                                buff_type = cred[:2]
                            elif cred == b";e":
                                print(b"End of transmission: " + buff)
                                self.save_credential(buff)
                                buff = b""
                                buff_type = b""
                            else:
                                buff += cred
                                print(b"Transmission part: " + cred)
                            
                        except Exception as e:
                            print("Something went wrong "+str(e))
                            connected = False
                            alive = False
                            break
            await connection.disconnect()
            connected = False
            print("Disconnected")
            led.off()
            alive = False
    def start_setup(self):
        asyncio.run(self.peripheral_task())