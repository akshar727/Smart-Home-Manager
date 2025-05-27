import serial
import time
import serial.tools.list_ports


def find_pico_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
             if (
                     "Pico" in port.description or
                     "RP2" in port.description or 
                     "MicroPython" in port.description or
                     "usbmodem" in port.device
             ):
                     return port.device
    raise Exception("Device not found. Please connect the device and try again.")

def reset_pico(ser):
    # Toggle DTR/RTS to perform a reset
    ser.dtr = False
    ser.rts = True
    time.sleep(0.1)
    ser.rts = False
    ser.dtr = True
    time.sleep(0.1)
    ser.dtr = False
    time.sleep(2)  # Allow time for device to reboot

def try_enter_raw_repl(ser, retries=10, delay=1.0):
    """
    Attempt to enter raw REPL, retrying if main.py is blocking.
    """
    for attempt in range(retries):
        try:
            # print(f"[*] Attempt {attempt + 1} to enter raw REPL...")
            reset_pico(ser)
            ser.write(b'\x03')  # Ctrl-C to interrupt any running program
            time.sleep(0.1)
            ser.write(b'\x01')  # Ctrl-A to request raw REPL
            time.sleep(0.5)

            response = ser.read_all()
            if b'raw REPL' in response:
                # print("[+] Entered raw REPL!")
                return True
            else:
                # print("[!] raw REPL not ready, retrying...")
                time.sleep(delay)
        except Exception as e:
            print(e)
            time.sleep(delay)
        
    raise Exception("[-] Failed to enter raw REPL after multiple attempts.")

def exit_raw_repl(ser):
    ser.write(b'\x02')  # Ctrl-B to exit raw REPL
    time.sleep(0.1)


def upload_file(ser, file_content, remote_path):

    # Remove EOF markers and encode the write script
    python_code = f"""
f = open("{remote_path}", "wb")
f.write("{file_content!r}")
f.close()
"""
    # print(python_code)
    # Enter raw REPL mode
    try_enter_raw_repl(ser)

    # Send code
    ser.write(b'\x05A')  # ctrl-E to enter paste mode
    time.sleep(0.1)
    # print("[*] Uploading code in paste mode...")

    for line in python_code.splitlines():
        ser.write(line.encode('utf-8') + b'\r')
        time.sleep(0.01)
        ser.write(b'\x04')  # ctrl-D to execute

    time.sleep(0.5)
    output = ser.read_all()
    if output.endswith(b'\x04>OK\x04\x04>OK\x04\x04>OK\x04\x04>'):
        print("[*] File uploaded successfully")
    else:
        print("[!] Error uploading file:", output.decode('utf-8'))

    # Exit raw REPL
    exit_raw_repl(ser)

def main():
    print("Welcome to the Blinds Manager Device Setup!")
    print("Enter the device location: ",end='')
    location = input().strip()
    print("Enter the Wi-Fi SSID: ", end='')
    wlan = input().strip()
    print("Enter the Wi-Fi Password: ", end='')
    pwd = input().strip()

    import os
    response = os.popen(f'ping -c 1 camerapi').read()
    server_ip = response.split()[2].strip('()').replace("):","") if 'camerapi' in response else 'not found'
    if server_ip == 'not found':
        print("[!] Error: Could not find the server IP. Make sure the server device is reachable.")
        return
    else:
        print(f"[*] Server IP: {server_ip}")
    print(f"[*] Device Location: {location}")
    print("[*] Formatting information...")
    client_data = {
        "ssid": wlan,
        "pwd": pwd,
        "server_ip": server_ip,
        "location": location
    }
    print("[*] Uploading to device...")


    serial_port = find_pico_port()
    baudrate = 115200
    remote_file_path = 'client_data.json'

    try:
        with serial.Serial(serial_port, baudrate, timeout=1) as ser:
            time.sleep(2)  # wait for Pico to initialize
            upload_file(ser, client_data, remote_file_path)
            print(f"[*] File uploaded to device")
            # print("[*] Temporary file removed.")
    except Exception as e:
        print("[!] Error:", e)

if __name__ == "__main__":
    main()
