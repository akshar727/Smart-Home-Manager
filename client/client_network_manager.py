from microdot.cors import CORS
from microdot.microdot import Microdot
import urequests as requests
import network
from time import sleep
import uasyncio as asyncio
import json
import os
import machine

# logfile = open('log.txt', 'a',0)
# # clear the log file
# # duplicate stdout and stderr to the log file
# os.dupterm(logfile) # type: ignore



class ClientNetworkManager:
    def __init__(self, _type, location, state, server_ip, wlan_ssid, wlan_pwd) -> None:
        self.type = _type
        self.location = location
        self.state = state
        self.server_ip = server_ip
        self.ssid = wlan_ssid
        self.pwd = wlan_pwd
        led = machine.Pin("LED", machine.Pin.OUT)
        led.on()
        self.client_ip = self.connect_to_wifi()
        led.off()
        self.send_identification()
        self.app = Microdot()
        # async def log(request):
        #     # stream the log.txt file in parts using a generator and a def function
        #     # logfile.flush()
        #     def generate():
        #         with open('log.txt') as f:
        #             while True:
        #                 line = f.readline()
        #                 if not line:
        #                     break
        #                 yield line
        #     return generate(), {'Content-Type': 'text/css'}

        # async def clear_log(request):
        #     logfile.flush()
        #     logfile.seek(0)
        #     logfile.truncate(0)
        #     logfile.flush()
        #     return "Log cleared"
        
        async def ping_recieve(request):
            return {"success": True}

        # self.app.route('/log.txt')(log)
        self.app.route("/net/ping", methods=["POST"])(ping_recieve)

        # self.app.route("/clearlog")(clear_log)

        CORS(self.app, allowed_origins=[f'http://{server_ip}'], allow_credentials=True)
        self.log("Created Microdot Application")

    def register_methods(self):
        pass
        


    def connect_to_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.pwd)
        while wlan.isconnected() == False:
            self.log('Waiting for connection...')
            sleep(1)
        ip = wlan.ifconfig()[0]
        self.log(f'Connected on {ip}')
        return ip

    def log(self, *args):
        print("ClientNetworkManager: ",*args)
    
    def send_identification(self):
        k = {
            "type": self.type,
            "location": self.location,
            "state": self.state,
        }
        try:
            r = requests.post(f"http://{self.server_ip}/api/net/id", json=k,timeout=8)
            self.log(r.json())
            self.id = r.json().get('id')
            self.log("ID sent")
        except Exception as e:
            self.log("Failed to send ID:" + str(e))

    async def ping_server(self):
        server_ping_has_failed = False
        while True:
            try:
                r = requests.post(f"http://{self.server_ip}/net/ping",timeout=8)
                self.log("Pinged server successfully at ip of", self.client_ip)
                if server_ping_has_failed:
                    self.send_identification()
                    self.log("Trying to send to reregister again")
                    server_ping_has_failed = False
            except Exception as e:
                self.log("Failed to ping server trying twice more:" + str(e))
                server_ping_has_failed = True
                try:
                    r = requests.post(f"http://{self.server_ip}/net/ping")
                    self.log("Pinged server successfully at ip of", self.client_ip)
                    server_ping_has_failed = False
                    await asyncio.sleep(20)
                    continue
                except Exception as e:
                    self.log("Failed to ping server again:" + str(e))
                    server_ping_has_failed = True

                try:
                    r = requests.post(f"http://{self.server_ip}/net/ping")
                    self.log("Pinged server successfully at ip of", self.client_ip)
                    server_ping_has_failed = False
                    await asyncio.sleep(20)
                    continue
                except Exception as e:
                    self.log("Failed to ping server again:" + str(e))
                    server_ping_has_failed = True
            await asyncio.sleep(20)

    


class BlindsClientNetworkManager(ClientNetworkManager):
    def __init__(self,location, state, server_ip, wlan_ssid, wlan_pwd, open_calibration: int, close_calibration: int) -> None:
        super().__init__('blind',location, state, server_ip, wlan_ssid, wlan_pwd)
        self.calibrations: dict[str, int] = {
            "closed_to_open": open_calibration,
            "open_to_closed": close_calibration
        }
        self.forward_pin = machine.Pin(27,machine.Pin.OUT)
        self.backward_pin = machine.Pin(28, machine.Pin.OUT)
        self.register_methods()

        async def main():
            server = asyncio.create_task(self.app.start_server(host=self.client_ip, port=80))
            # ping = asyncio.create_task(self.ping_server())

            await server
            # await ping
        asyncio.run(main())
    
    def register_methods(self):
        async def change_state(status):
            self.log("Moving motors")
            self.forward_pin.off()
            self.backward_pin.off()
            if status == "open":
                self.backward_pin.off()
                self.forward_pin.on()
                await asyncio.sleep(self.calibrations["closed_to_open"])
                self.state = "open"
                self.forward_pin.off()
            elif status == "close":
                self.forward_pin.off()
                self.backward_pin.on()
                await asyncio.sleep(self.calibrations["open_to_closed"])
                self.backward_pin.off()
                self.state = "close"
            r = requests.post(f"http://{self.server_ip}/api/net/finish", json={"final_status": status, "id": self.id})
            response = r.json()
            self.log(response)
            self.log("Finished moving motors")
        async def set_calibration(request):
            data = json.loads(request.body)
            operation = data["operation"]
            self.forward_pin.off()
            self.backward_pin.off()
            if operation == "open":
                self.calibrations["closed_to_open"] = data["duration"]
                self.state = "open"
            elif operation == "close":
                self.calibrations["open_to_closed"] = data["duration"]
                self.state = "close"
            with open("calibration.json", "w") as f:
                json.dump(self.calibrations, f)
            return {"success": True,"open_to_closed": self.calibrations["open_to_closed"], "closed_to_open": self.calibrations["closed_to_open"]}
        
        
        async def toggle_calibration(request, method):
            if method == "open":
                self.backward_pin.off()
                self.forward_pin.on()
            elif method == "close":
                self.forward_pin.off()
                self.backward_pin.on()
            
            return {"success": True}

        async def status_change(request):
            data = json.loads(request.body)
            status = data["status"]
            my_id = data["id"]
            asyncio.create_task(change_state(status))
            #{"new_status": "open" | "close"}
            return {"success": True}
        
        self.app.route("/status",methods=["POST"])(status_change)
        self.app.route("/api/calibrate/toggle/<string:method>", methods=["GET"])(toggle_calibration)
        self.app.route("/api/calibrate/set", methods=["POST"])(set_calibration)
        self.log("Methods Registered")

class CameraClientNetworkManager(ClientNetworkManager):
    def __init__(self,location, server_ip, wlan_ssid, wlan_pwd) -> None:
        super().__init__('camera',location, None, server_ip, wlan_ssid, wlan_pwd)
        self.register_methods()

        self.app.run(host=self.client_ip, port=80)
    
    def register_methods(self):
        pass
