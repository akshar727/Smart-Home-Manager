import asyncio
import os
import json
import sys
from flask import Flask, request, jsonify, send_from_directory, Response #type: ignore
from flask_cors import CORS #type: ignore
# from bleak import BleakScanner, BleakClient
import threading
import time
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # type: ignore
from cryptography.hazmat.backends import default_backend #type: ignore
import queue
from uuid import uuid4
# from flask_talisman import Talisman

# Flask app setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Talisman(app, content_security_policy=None)  # Disable CSP for simplicity


print("\n")
print("Starting up server")

available_devices = []

# Load devices from file
devices_name = "devices.json"
if os.path.isfile(devices_name): #type: ignore
    with open(devices_name) as f:
        data = json.load(f)
        available_devices = data["devices"]

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/_next/<path:filename>')
def next_static(filename):
    return send_from_directory(os.path.join('.', '_next'), filename)




@app.route("/api/net/id", methods=["POST"])
def register():
    data = request.json

    # Check if the device is already registered
    for device in available_devices:
        if device["ip"] == request.remote_addr:
            
            print(f"The existing device at {device['location']} and IP {device['ip']} has re-registered...")
            if device["status"] == "offline":
                device["status"] = device["old_status"]
                device["old_status"] = "none"
            if device["status"] == "transit_open" or device["status"] == "transit_close":
                # somehow a bug, but just set it to its finished state
                device["status"] = "open" if data["status"] == "transit_open" else "close"
            return jsonify({"success": True, "uuid": device["uuid"]})
        elif device["uuid"] == data["uuid"]:
            print(f"The existing device with ID {device['uuid']} has re-registered under a new IP...")
            if device["status"] == "offline":
                device["status"] = device["old_status"]
                device["old_status"] = "none"
            device["ip"] = request.remote_addr
            return jsonify({"success": True, "uuid": device["uuid"]})

    device = {
        "ip": request.remote_addr,
        "location": data["location"],
        "type": data["type"],
        "uuid": uuid4().hex,
        "status": data["state"]
    }
    available_devices.append(device)

    with open(devices_name, "w") as f:
        json.dump({"devices": available_devices}, f)

    print(f"Found a NEW device at {data['location']} with IP {device['ip']}. Assigning ID of {device['uuid']}")
    print(available_devices) 
    return jsonify({"success": True, "uuid": device["uuid"]})


@app.route("/api/operation/<string:id>/<string:status>", methods=["GET"])
def run_pico(id, status):
    target_device = None
    for device in available_devices:
        if device["uuid"] == id:
            target_device = device
            break

    if target_device is None:
        return jsonify({"success": False, "err": "Device not found or not registered"})

    if target_device["status"] == "offline":
        return jsonify({"success": False, "err": "Device is offline"})

    req_data = {"status": status, "id": target_device["uuid"]}
    target_device["status"] = "transit_open" if status == "open" else "transit_close"

    try:
        r = requests.post(f"http://{target_device['ip']}/status", json=req_data)
        status = r.json()
        
        return jsonify(status)
    except Exception as e:
        print(f"Error sending request to device: {e}")
        return jsonify({"success": False, "err": "Failed to communicate with device"})
    
@app.route("/api/remove/<string:id>", methods=["DELETE"])
def remove_device(id):
    global available_devices
    target_device = None
    for device in available_devices:
        if device["uuid"] == id:
            target_device = device
            break

    if target_device is None:
        return jsonify({"success": False, "err": "Device not found or not registered"})

    print(f"Removing device {target_device['uuid']} at {target_device['location']} with IP {target_device['ip']}")
    def request_task(url, json, headers):
        requests.post(url, json=data, headers=headers)


    def fire_and_forget(url, json, headers):
        threading.Thread(target=request_task, args=(url, json, headers)).start()
    fire_and_forget(
        url=f"http://{target_device['ip']}/remove",
        json={"uuid": target_device["uuid"]},
        headers={}
    )
    available_devices.remove(target_device)
    print(target_device)
    print(available_devices)
    with open(devices_name, "w") as f:
        json.dump({"devices": available_devices}, f)

    return jsonify({"success": True})


@app.route("/api/net/finish", methods=["POST"])
def finish_status_change():
    data = request.json
    print(data)
    _id = data["uuid"]
    target_device = None
    for device in available_devices:
        if device["uuid"] == _id:
            target_device = device
            break

    if target_device is None:
        return jsonify({"success": False, "err": "Device not found or not registered"})

    print(f"Finishing status change for device {target_device['uuid']} at {target_device['location']} with IP {target_device['ip']}")
    target_device["status"] = data["final_status"]
    target_device["last_state_change"] = int(time.time())
    with open(devices_name, "w") as f:
        json.dump({"devices": available_devices}, f)
    
    return jsonify({"success": True})


@app.route("/api/server-info")
def server_info():
    return jsonify({"uptime": get_elapsed_time()})


@app.route("/api/network")
def check_for_devices():
    return jsonify([True])


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

start_time = int(time.time())

def get_elapsed_time():
    return int(time.time()) - start_time  # Seconds since epoch



def format_uptime(seconds):
    days = seconds // (24 * 3600)
    seconds %= (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


async def ping_clients():
    while True:
        for device in available_devices:
            try:
                r = requests.post(f"http://{device['ip']}/net/ping", json={"uuid": device['uuid']}, timeout=8)
                print(f"Device reachable, IP is {device['ip']} and location is {device['location']}")
                if device.get("old_status") is not None and device.get("old_status") != "none":
                    device["status"] = device["old_status"]
                    device["old_status"] = "none"
            except Exception as e:
                print(f"Device not reachable, IP is {device['ip']} and location is {device['location']}.")
                if device.get("old_status") == "none" or device.get("old_status") is None:
                    device["old_status"] = device["status"]
                    device["status"] = "offline"
                
        await asyncio.sleep(120)

@app.route('/devices')
def stream():
    def event_stream():
        yield "data: {}\n\n".format(available_devices)
        while True:
            # old_devices = available_devices.copy()
            time.sleep(1)
            # if old_devices != available_devices:
            #     # Check if the devices list has changed
            #     print("Devices list has changed")
            #     # Send the updated devices list to the client
            yield f"data: {available_devices}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")




log_queue = queue.Queue()

class LoggedStdout:
    def __init__(self, original):
        self.original = original

    def write(self, message):
        self.original.write(message)
        self.original.flush()
        if message.strip():  # avoid empty lines
            log_queue.put(message.strip())

    def flush(self):
        self.original.flush()

# Redirect stdout
sys.stdout = LoggedStdout(sys.stdout)
sys.stderr = LoggedStdout(sys.stderr) 


# Custom print function that adds to the queue
@app.route('/logs')
def stream_logs():
    def event_stream():
        yield "data: {}\n\n".format("Connected to logs")
        while True:
            msg = log_queue.get()
            yield f"data: {msg}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/log")
def get_logs():
    return send_from_directory('.', 'log.html')

    

if __name__ == "__main__":
    # Start the ping_clients coroutine in a separate thread
    def start_ping_clients():
        asyncio.run(ping_clients())

    threading.Thread(target=start_ping_clients, daemon=True).start()

    # Run the Flask server
    app.debug = False
    app.run(host="0.0.0.0", port=80)  # Use SSL context if you have cert.pem and key.pem