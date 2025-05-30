import React from "react";

export default function ServerInfo() {
  const [serverInfo, setServerInfo] = React.useState({ time: 0 });
  const intervalRef = React.useRef(null);

  function formatTime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${days}d ${hours}h ${minutes}m ${secs}s`;
  }

  React.useEffect(() => {
    // Fetch the initial server uptime
    fetch("/api/server-info")
      .then((res) => res.json())
      .then((data) => {
        setServerInfo(data);
        // Start the interval to increment uptime
        intervalRef.current = setInterval(() => {
          setServerInfo((prev) => ({
            ...prev,
            uptime: prev.uptime + 1,
          }));
        }, 1000);
      });

    // Cleanup interval when the component is unmounted
    return () => clearInterval(intervalRef.current);
  }, []);

  return (
    <div className="p-4">
      <h1 className="font-medium text-3xl">Server Uptime</h1>
      <p>Server has been up for {formatTime(serverInfo.uptime)}</p>
    </div>
  );
}
  