use serialport::{SerialPort, SerialPortInfo, SerialPortType};
use std::io::{self, Write, Read};
use std::thread::sleep;
use std::time::Duration;
use std::process::Command;
use std::collections::HashMap;

fn find_pico_port() -> Result<String, Box<dyn std::error::Error>> {
    let ports = serialport::available_ports()?;
    for port in ports {
        if let SerialPortType::UsbPort(info) = port.port_type {
            if let Some(product) = info.product {
                if product.contains("Pico") || product.contains("RP2") || product.contains("MicroPython") {
                    return Ok(port.port_name);
                }
            }
        }
        if port.port_name.contains("usbmodem") {
            return Ok(port.port_name);
        }
    }
    Err("Device not found. Please connect the device and try again.".into())
}

fn reset_pico(port: &mut dyn SerialPort) {
    port.write_data_terminal_ready(false).unwrap();
    port.write_request_to_send(true).unwrap();
    sleep(Duration::from_millis(100));
    port.write_request_to_send(false).unwrap();
    port.write_data_terminal_ready(true).unwrap();
    sleep(Duration::from_millis(100));
    port.write_data_terminal_ready(false).unwrap();
    sleep(Duration::from_secs(2));
}

fn try_enter_raw_repl(port: &mut dyn SerialPort, retries: u8, delay: Duration) -> Result<(), Box<dyn std::error::Error>> {
    for _ in 0..retries {
        reset_pico(port);
        port.write_all(b"\x03")?; // Ctrl-C
        sleep(Duration::from_millis(100));
        port.write_all(b"\x01")?; // Ctrl-A for raw REPL
        sleep(Duration::from_millis(500));

        let mut buf = vec![0u8; 128];
        let n = port.read(&mut buf).unwrap_or(0);
        let response = String::from_utf8_lossy(&buf[..n]);

        if response.contains("raw REPL") {
            return Ok(());
        }

        sleep(delay);
    }
    Err("Failed to enter raw REPL after retries.".into())
}

fn exit_raw_repl(port: &mut dyn SerialPort) {
    let _ = port.write_all(b"\x02"); // Ctrl-B
    sleep(Duration::from_millis(100));
}

fn upload_file(
    port: &mut dyn SerialPort,
    file_contents: &str,
    remote_path: &str
) -> Result<(), Box<dyn std::error::Error>> {
    let python_code = format!(
        "print('')\njjk = open('{}', 'wb')\njjk.write({:?})\njjk.close()\n",
        remote_path, file_contents
    );
    // println!("{}",python_code);
    try_enter_raw_repl(port, 10, Duration::from_secs(1))?;

    port.write_all(b"\x05A")?; // Ctrl-E (paste mode)
    sleep(Duration::from_millis(100));

    for line in python_code.lines() {
        port.write_all(line.as_bytes())?;
        port.write_all(b"\r")?;
        sleep(Duration::from_millis(10));
        port.write_all(b"\x04")?; // Ctrl-D to execute
    }

    sleep(Duration::from_millis(500));

    let mut buf = vec![0u8; 1024];
    let n = port.read(&mut buf).unwrap_or(0);
    let output = String::from_utf8_lossy(&buf[..n]);

    if output.contains("\x04>OK\x04\x04>OK\x04\x04>OK\x04\x04>") {
        println!("[*] File uploaded successfully");
    } else {
        println!("[!] Upload error:\n{}", output);
    }

    exit_raw_repl(port);
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Welcome to the Blinds Manager Device Setup!");
    print!("Enter the device location: ");
    io::stdout().flush().unwrap();
    let mut location = String::new();
    io::stdin().read_line(&mut location)?;
    let location = location.trim();

    print!("Enter the WiFi SSID: ");
    io::stdout().flush().unwrap();
    let mut wlan = String::new();
    io::stdin().read_line(&mut wlan)?;
    let wlan = wlan.trim();

    print!("Enter the WiFi password: ");
    io::stdout().flush().unwrap();
    let mut pwd = String::new();
    io::stdin().read_line(&mut pwd)?;
    let pwd = pwd.trim();

    // Use ping to get the IP of the server
    let output = Command::new("ping")
        .args(&["-c", "1", "camerapi"])
        .output()?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let server_ip = if stdout.contains("camerapi") {
        stdout
            .split_whitespace()
            .nth(2)
            .unwrap_or("not found")
            .trim_matches(&['(', ')', ':'][..])
            .to_string()
    } else {
        "not found".to_string()
    };

    if server_ip == "not found" {
        println!("[!] Error: Could not find the server IP.");
        return Ok(());
    } else {
        println!("[*] Server IP: {}", server_ip);
    }

    println!("[*] Formatting info...");
    let client_data = format!(
        "{{\"ssid\": \"{}\", \"pwd\": \"{}\", \"server_ip\": \"{}\", \"location\": \"{}\"}}",
        wlan, pwd, server_ip, location
    );

    let port_path = find_pico_port()?;
    println!("[*] Found device at port: {}", port_path);
    let mut port = serialport::new(port_path, 115200)
        .timeout(Duration::from_secs(2))
        .open()?;

    upload_file(&mut *port, &client_data, "client_data.json")?;

    Ok(())
}
