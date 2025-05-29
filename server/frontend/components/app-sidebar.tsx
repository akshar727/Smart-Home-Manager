"use client";
import * as React from "react";

import { SearchForm } from "@/components/search-form";
import { VersionSwitcher } from "@/components/version-switcher";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";

// This is sample data.
const data = {
  navMain: [
    {
      title: "Dashboard",
      pageSet: 0,
    },
    {
      title: "Server Information",
      pageSet: 1,
    },
    {
      title: "Calibrate A Device",
      pageSet: 2,
    },
  ],
};

export function AppSidebar(props: any) {
  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Smart Home Manager</h1>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {data.navMain.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a
                      onClick={() => {
                        if (typeof props.pageSetter === "function") {
                          props.pageSetter(item.pageSet);
                        }
                      }}
                    >
                      {item.title}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
