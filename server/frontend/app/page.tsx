"use client";

import { AppSidebar } from "@/components/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import React from "react";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { organizeData } from "@/components/utils";
import DeviceWidgets from "@/components/device-widgets";
import ServerInfo from "@/components/server-info";
import CalibrateDevice from "@/components/calibrate-device";
import Head from "next/head";
// Metadata cannot be set dynamically on the client side in Next.js 13+ app directory.
// You can only use the `metadata` export on the server side (in server components or layout.tsx).
// If you want to set the document title on the client side, use a useEffect:

export default function Page() {
  const [page, setPage] = React.useState(0);
  const [deviceToRemove, setDeviceToRemove] = React.useState("");
  const [devices, setDevices] = React.useState([]);
  React.useEffect(() => {
    const evtSource = new EventSource("/devices");
    evtSource.onmessage = (event) => {
      const updatedData = JSON.parse(event.data.replace(/'/g, '"'));
      setDevices((prevDevices) => {
        const organized = organizeData(updatedData);
        return {
          ...prevDevices,
          ...organized,
        };
      });
    };

    return () => {
      // Cleanup the event source when the component unmounts
      evtSource.close();
      console.log("EventSource closed");
    };
  }, []);
  return (
    <>
    <Head>
      <title>Smart Home Manager</title>
    </Head>
      <SidebarProvider>
        <AppSidebar pageSetter={setPage} page={page} />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center justify-between gap-2 border-b px-4">
            <div className="flex items-center gap-2">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mr-2 h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="#">Smart Home Manager</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbPage>
                      {page === 0 && "Your Devices"}
                      {page === 1 && "Server Information"}
                      {page === 2 && "Calibrate A Device"}
                    </BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
            <Dialog>
              <DialogTrigger asChild>
                <Button style={{ marginRight: "10px" }}>Remove a Device</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Remove a Device</DialogTitle>
                  <DialogDescription>
                    Select a device to remove it from the system.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex items-center space-x-2">
                  <div className="grid flex-1 gap-2 w-full">
                    <Select onValueChange={setDeviceToRemove} defaultValue={""}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select a device to remove" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.keys(devices).length > 0 &&
                          devices.blind.map((device) => (
                            <SelectItem key={device.uuid} value={device.uuid}>
                              {device.location}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter className="sm:justify-start">
                  <DialogClose asChild>
                    <Button
                      onClick={() => {
                        setDeviceToRemove("");
                      }}
                      type="button"
                      variant="secondary"
                    >
                      Close
                    </Button>
                  </DialogClose>
                  <Button
                    type="button"
                    variant="destructive"
                    disabled={!deviceToRemove}
                    onClick={() => {
                      if (deviceToRemove) {
                        fetch(`/api/remove/${deviceToRemove}`, {
                          method: "DELETE",
                          headers: {
                            "Content-Type": "application/json",
                          },
                        })
                          .then((res) => {
                            if (res.ok) {
                              alert("Device removed successfully.");
                              setDeviceToRemove("");
                            } else {
                              alert(
                                "Failed to remove device. Please try again."
                              );
                            }
                          })
                          .catch((error) => {
                            console.error("Error removing device:", error);
                            alert(
                              "An error occurred while removing the device."
                            );
                          });
                      }
                    }}
                  >
                    Remove
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </header>
          {page === 0 && <DeviceWidgets devices={devices} />}
          {page === 1 && <ServerInfo />}
          {page === 2 && <CalibrateDevice devices={devices} />}
        </SidebarInset>
      </SidebarProvider>
    </>
  );
}
