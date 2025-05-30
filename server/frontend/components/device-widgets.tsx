import React from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { Badge, TrendingUpIcon } from "lucide-react";

export default function DeviceWidgets(props: any) {
  //Implementing the setInterval method

  //Clearing the interval

  function fetchOperation(id: string, operation: string) {
    fetch(`/api/operation/${id}/${operation}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success === true) {
          console.log(`Operation ${operation} on device ${id} was successful.`);
        } else {
          console.log(
            "An error occurred while performing the operation. Please try again."
          );
        }
      });
  }
  console.log("Rendering these devices", props.devices);
  return (
    <React.Fragment>
      {Object.keys(props.devices).length === 0 && (
        <p className="text-lg mt-4 mb-4 ml-4">
          No devices yet. Check the instructions on how to add one!
        </p>
      )}
      {Object.keys(props.devices).length > 0 && (
        <React.Fragment>
          <h3 className="text-3xl mt-4 font-medium mb-4 ml-4">Blinds</h3>
          <div className="*:data-[slot=card]:shadow-xs xl:grid-cols-2 5xl:grid-cols-4 grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card lg:px-6">
            {props.devices.blind.map((device: any) => (
              <Card key={device.location} className="@container/card">
                <CardHeader className="relative">
                  <CardDescription>{device.location}</CardDescription>
                  <CardTitle className="@[250px]/card:text-3xl text-2xl font-semibold tabular-nums">
                    {device.status === "offline"
                      ? "Offline"
                      : device.status === "open"
                      ? "Opened"
                      : device.status === "close"
                      ? "Closed"
                      : device.status === "transit_open"
                      ? "Opening..."
                      : "Closing..."}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-8">
                  <div className="flex-col items-start gap-1 text-sm">
                    <div className="text-muted-foreground">
                        {device.status === "open" || device.status === "close" ? (
                        (() => {
                          const now = Date.now();
                          const lastChange = device.last_state_change * 1000; // convert seconds to ms
                          const diffMs = now - lastChange;
                          const diffH = Math.floor(diffMs / (1000 * 60 * 60));
                          const diffM = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                          const label = device.status === "open" ? "Opened" : "Closed";
                          if (isNaN(diffM) || isNaN(diffH)) {
                            return "";
                          }
                          if (diffM === 0) {
                            return <span>{`${label} just now`}</span>;
                          }
                          if (diffH === 0) {
                            return <span>{`${label} for ${diffM}m`}</span>;
                          }
                          return <span>{`${label} for ${diffH}h, ${diffM}m`}</span>;
                        })()
                        ) : (
                        <span>&nbsp;</span>
                        )}
                    </div>
                  </div>
                  <div className="flex flex-col w-full gap-2">
                    <Button
                      disabled={
                        device.status === "open" ||
                        device.status === "transit_open" ||
                        device.status === "transit_close" ||
                        device.status === "offline"
                      }
                      onClick={() => fetchOperation(device.uuid, "open")}
                    >
                      <i className="fa-solid fa-blinds-open text-white"></i>
                      Open
                    </Button>
                    <Button
                      disabled={
                        device.status === "close" ||
                        device.status === "transit_open" ||
                        device.status === "transit_close" ||
                        device.status === "offline"
                      }
                      onClick={() => fetchOperation(device.uuid, "close")}
                    >
                      <i className="fa-solid fa-blinds text-white"></i>
                      Close
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <Separator className="mt-4 mb-4" />
          {/* <h3 className="category-title">Cameras</h3>
            <div className="devices">
              {devices.camera !== undefined && (
                <>
                  {devices.camera.map((device) => (
                    <div key={device.location} className="device">
                      <h3>{device.location}</h3>
                      <Button>
                        <i className="fa-solid fa-video"></i>
                        View Stream
                      </Button>
                    </div>
                  ))}
                </>
              )}
            </div> */}
        </React.Fragment>
      )}
    </React.Fragment>
  );
}
