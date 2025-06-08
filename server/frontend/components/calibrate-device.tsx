import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CalibrateDevice(props: any) {
  const [calibrating, setCalibrating] = React.useState(null);
  const [startTime, setStartTime] = React.useState(null);

  function startCalibration(id, operation) {
    const data = props.devices.blind.find((device) => device.uuid === id);
    setCalibrating({ id, operation, ip: data.ip });
    fetch(`http://${data.ip}/api/calibrate/toggle/${operation}`)
      .then((res) => {
        if (res.ok) {
          if (!startTime) {
            setStartTime(Date.now());
          }
          fetch(`/api/lock/${id}`, {
            method: "POST",
          }).then((response) => {
            if (response.ok) {
              console.log(`Device ${id} is now locked for calibration.`);
            }
          });
        } else {
          alert("Failed to toggle motor. Please try again.");
        }
      })
      .catch(() => {
        alert("An error occurred while toggling the motor. Please try again.");
      });
  }

  function stopCalibration() {
    if (startTime) {
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
    }
    if (calibrating) {
      console.log(`Start time: ${startTime}`);
      console.log(`End time: ${Date.now()}`);
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
      fetch(`http://${calibrating.ip}/api/calibrate/set`, {
        method: "POST",
        body: JSON.stringify({
          duration: elapsedTime,
          operation: calibrating.operation,
        }),
        headers: { "Content-Type": "application/json" },
      })
        .then((res) => {
          if (res.ok) {
            alert(`Calibration finished. Set to: ${elapsedTime} seconds.`);
            fetch(`/api/unlock/${calibrating.id}`, {
              method: "POST",
              body: JSON.stringify({
                force_status: calibrating.operation,
              }),
              headers: { "Content-Type": "application/json" },
            }).then((response) => {
              if (response.ok) {
                console.log(`Device ${calibrating.id} is now unlocked.`);
              }
            });
          } else {
            alert("Failed to finish calibration. Please try again.");
          }
        })
        .finally(() => {
          setCalibrating(null);
          setStartTime(null);
        });
    }
  }

  return (
    <>
      {Object.keys(props.devices).length === 0 && (
        <p className="text-lg mt-4 mb-4 ml-4">
          No devices available for calibration.
        </p>
      )}
      {Object.keys(props.devices).length > 0 && (
        <div className="flex flex-wrap gap-4 ml-3 mt-3">
          {props.devices.blind.map((device) => (
            <Card key={device.location}>
              <CardHeader>
                <CardTitle className="text-xl">{device.location}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div className="flex flex-col w-full gap-2">
                  <Button
                    className="op-btn"
                    onClick={() => startCalibration(device.uuid, "open")}
                    disabled={
                      calibrating !== null ||
                      device.status === "offline" ||
                      device.status === "lock"
                    }
                  >
                    Calibrate Opening
                  </Button>
                  <Button
                    className="op-btn"
                    onClick={() => startCalibration(device.uuid, "close")}
                    disabled={
                      calibrating !== null ||
                      device.status === "offline" ||
                      device.status === "lock"
                    }
                  >
                    Calibrate Closing
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      {calibrating && (
        <div>
          <h2>
            Calibrating
            {calibrating.operation === "open" ? " Opening" : " Closing"}
            ...
          </h2>
          <p>
            Press the stop button when you are satisfied with the status of your
            blinds for{" "}
            {calibrating.operation === "open" ? " Opening" : " Closing"}.
          </p>
          <Button className="op-btn" onClick={stopCalibration}>
            Stop
          </Button>
        </div>
      )}
    </>
  );
}
