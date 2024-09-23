import socket 
import time
import json
server_ip = '0.0.0.0'  # Listen on all interfaces
server_port = 12345

device_list = []

try:
    with open("devices.json", "r") as f:
        device_list = json.load(f)
except:
    print("No saved devices found.")
active_pings = []

if device_list:
    print("Saved devices:\n")
    for device in device_list:
        print("Location:", device["location"], "\nIP:", device["ip"])
        # send a message to each device
        print("Sending ping to this device...\n")
        try:
            s = socket.socket()
            s.connect((device["ip"], server_port))
            s.send(json.dumps({"action":"hello"}).encode())
            s.close()
            active_pings.append(device["ip"])
        except Exception as e:
            print("Failed to send message to", device["location"], "at", device["ip"], ":", str(e))


s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((server_ip, server_port))
s.listen(1)
print("Listening on port", server_port)
while True:
    conn, addr = s.accept()
    print("-"*20+"\n"+"Connection from", addr)
    data = conn.recv(1024).decode()
    if data:
        print("Received data: ", data)
        parsed = json.loads(data)
        if parsed["type"] == "ID":
            print("New Pico found at", parsed["location"], "with IP", parsed["ip"], ". Saving device list...")
            for device in device_list:
                if device["location"] == parsed["location"]:
                    print("Device already in list, no changes made.")
                    break
            else:
                device_list.append(parsed)
            with open("devices.json", "w") as f:
                json.dump(device_list, f)
        elif parsed["type"] == "pong":
            print("Got pong from", addr[0])
            active_pings.remove(addr[0])
            print("Active pings:", active_pings)
    print("-"*20)
    conn.close()

