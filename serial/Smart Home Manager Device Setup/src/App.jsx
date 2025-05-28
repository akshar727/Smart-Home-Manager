import { useEffect, useState } from "react";
import reactLogo from "./assets/react.svg";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

function App() {
  const [statusMsg, setstatusMsg] = useState("");
  const [wlan, setWlan] = useState("");
  const [pwd, setPwd] = useState("");
  const [location, setLocation] = useState("");

  async function upload_data() {
    // Learn more about Tauri commands at https://v1.tauri.app/v1/guides/features/command
    setstatusMsg(await invoke("upload", { wlan,pwd,location }));
  }

  useEffect(() => {
    // This effect runs once when the component mounts
    // You can use it to perform any setup or initial data fetching
    // const wlans = invoke("get_wifi_list_command").then((result) => {
    //   console.log("get_wifi_list_command result:", result);
    //   return result;
    // });
    console.log("App component mounted");
  }, []);

  return (
    <main className="container">
      <h1>Smart Home Manager Device Setup</h1>

      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          upload_data();
        }}
      >
        <label htmlFor="wlan-input">WiFi Network:</label>
        <input
          id="wlan-input"
          type="text"
          placeholder="Enter WiFi network name..."
          required

          onChange={(e) => setWlan(e.currentTarget.value)}
        />
        <br />
        <label htmlFor="pwd-input">Password:</label>
        <input
          id="pwd-input"
          type="password"
          placeholder="Enter WiFi password..."
          required
          onChange={(e) => setPwd(e.currentTarget.value)}
        />
        <br />
        <label htmlFor="data-input">Device Location:</label>
        <input
          id="data-input"
          placeholder="Office, Living Room, etc."
          type="text"
          required
          onChange={(e) => setLocation(e.currentTarget.value)}
        />
        <br />
        <button type="submit">Upload Information</button>
      </form>
      <p>{statusMsg}</p>
    </main>
  );
}

export default App;
