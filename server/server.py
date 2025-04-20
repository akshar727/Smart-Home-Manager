import asyncio
import os
import json
from flask import Flask, request, jsonify, send_from_directory, Response #type: ignore
from flask_cors import CORS #type: ignore
# from bleak import BleakScanner, BleakClient
import threading
import time
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # type: ignore
from cryptography.hazmat.backends import default_backend #type: ignore

# Flask app setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# AES encryption setup
MODE_CBC = modes.CBC
BLOCK_SIZE = 16

# Key and IV for AES encryption
key = b"q\x06\xfd\xc1\x01'\x8a<\x1bV\xf0\xf4\xda\x0e\xf05q\x17Ws\x16\x18\xbfqL\x10\x9c\xe0\xed\x11F\xa1"
iv = b'gf4]\xd8\xf27Tg\xa7\xf5\xfdb,\xf6\xc3'


# def aes_encrypt(plaintext, _id):
#     pad = BLOCK_SIZE - len(plaintext) % BLOCK_SIZE
#     plaintext = plaintext + " " * pad

#     cipher = Cipher(algorithms.AES(key), MODE_CBC(iv), backend=default_backend())
#     encryptor = cipher.encryptor()
#     ct_bytes = encryptor.update(plaintext.encode()) + encryptor.finalize()

#     # Join the ID and the ciphertext
#     ct_bytes = _id.encode() + ct_bytes
#     return ct_bytes


# def split_into_chunk_20(inp):
#     return [inp[i:i + 20] for i in range(0, len(inp), 20)]


print("\n")
print("Starting up server")

available_devices = []
next_id = 0

# Load devices from file
devices_name = "devices.json"
if os.path.isfile(devices_name): #type: ignore
    with open(devices_name) as f:
        data = json.load(f)
        available_devices = data["devices"]
        next_id = data["next_id"]


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/index.css')
def index_css():
    return send_from_directory('.', 'index.css')


@app.route("/api/net/id", methods=["POST"])
def register():
    global next_id
    data = request.json

    # Check if the device is already registered
    for device in available_devices:
        if device["ip"] == request.remote_addr:
            
            print(f"The existing device at {device['location']} and IP {device['ip']} has re-registered...")
            return jsonify({"success": True, "id": device["id"]})

    device = {
        "ip": request.remote_addr,
        "location": data["location"],
        "type": data["type"],
        "id": next_id,
        "status": data["state"]
    }
    available_devices.append(device)
    next_id += 1

    with open(devices_name, "w") as f:
        json.dump({"next_id": next_id, "devices": available_devices}, f)

    print(f"Found a NEW device at {data['location']} with IP {device['ip']}. Assigning ID of {device['id']}")
    print(available_devices)
    
    return jsonify({"success": True, "id": device["id"]})


@app.route("/api/operation/<int:id>/<string:status>", methods=["GET"])
def run_pico(id, status):
    target_device = None
    for device in available_devices:
        if device["id"] == id:
            target_device = device
            break

    if target_device is None:
        return jsonify({"success": False, "err": "Device not found or not registered"})

    if target_device["status"] == "offline":
        return jsonify({"success": False, "err": "Device is offline"})

    req_data = {"status": status, "id": target_device["id"]}
    target_device["status"] = "transit_open" if status == "open" else "transit_close"

    try:
        r = requests.post(f"http://{target_device['ip']}/status", json=req_data)
        status = r.json()
        
        return jsonify(status)
    except Exception as e:
        print(f"Error sending request to device: {e}")
        return jsonify({"success": False, "err": "Failed to communicate with device"})


@app.route("/api/net/finish", methods=["POST"])
def finish_status_change():
    data = request.json
    _id = data["id"]
    target_device = None
    for device in available_devices:
        if device["id"] == _id:
            target_device = device
            break

    if target_device is None:
        return jsonify({"success": False, "err": "Device not found or not registered"})

    target_device["status"] = data["final_status"]
    
    return jsonify({"success": True})


@app.route("/api/server-info")
def server_info():
    uptime = format_uptime(get_elapsed_time())
    return jsonify({"uptime": uptime})


@app.route("/api/network")
def check_for_devices():
    return jsonify([True])


# @app.route("/api/credential-apply", methods=["POST"])
# async def apply_credentials():
#     data = request.json
#     loc = data["location"]

#     async def send(data, _id, encrypt=True):
#         pdata = aes_encrypt(data, _id) if encrypt else _id.encode() + data
#         chunks = split_into_chunk_20(pdata)
#         for chunk in chunks:
#             # Simulate BLE characteristic write
#             print(f"Sending chunk: {chunk}")
#             await asyncio.sleep(0.05)

#     await send("SSID", "w;")
#     await asyncio.sleep(0.3)
#     await send("PASSWORD", "p;")
#     await asyncio.sleep(0.3)
#     await send(loc.encode(), "l;", False)
#     await asyncio.sleep(0.3)
#     await send("IP_ADDRESS".encode(), "i;", False)

#     return jsonify({"success": True})


# @app.route("/terminate")
# def terminate():
#     func = request.environ.get('werkzeug.server.shutdown')
#     if func is None:
#         raise RuntimeError('Not running with the Werkzeug Server')
#     func()
#     return "Shutdown initiated…"


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404


def get_elapsed_time():
    return int(time.time())  # Seconds since epoch



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
                r = requests.post(f"http://{device['ip']}/net/ping", timeout=8)
                print(f"Device reachable, IP is {device['ip']} and location is {device['location']}")
                if device.get("old_status") is not None:
                    device["status"] = device["old_status"]
                    device["old_status"] = None
            except Exception as e:
                print(f"Device not reachable, IP is {device['ip']} and location is {device['location']}.")
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


if __name__ == "__main__":
    # Start the ping_clients coroutine in a separate thread
    def start_ping_clients():
        asyncio.run(ping_clients())

    threading.Thread(target=start_ping_clients, daemon=True).start()

    # Run the Flask server
    app.run(host="0.0.0.0", port=80)