"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, LayoutDashboard, Folders, PlusCircle, PieChart,
  Bell, Settings, LogOut, ChevronLeft, Menu
} from "lucide-react";
import { useUIStore, useNotificationsStore } from "@/store";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/cases", label: "My Cases", icon: Folders },
  { href: "/dashboard/cases/new", label: "New Case", icon: PlusCircle },
  { href: "/dashboard/analytics", label: "Analytics", icon: PieChart },
  { href: "/dashboard/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const unreadCount = useNotificationsStore((s) => s.unreadCount);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarCollapsed ? "5rem" : "16rem" }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className={cn(
          "relative z-20 flex flex-col bg-slate-950 border-r border-slate-800",
          "transition-colors duration-300 backdrop-blur-3xl shrink-0"
        )}
      >
        <div className={cn("flex items-center h-20 px-6", sidebarCollapsed ? "justify-center px-0" : "justify-between")}>
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0891B2] to-[#0F3460] flex shrink-0 items-center justify-center group-hover:bg-[#0891B2] transition-colors shadow-[0_0_15px_rgba(8,145,178,0.3)]">
              <Activity className="w-6 h-6 text-white" />
            </div>
            {!sidebarCollapsed && (
              <motion.span 
                 initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                 className="font-bold text-xl tracking-tight text-white whitespace-nowrap overflow-hidden"
              >
                 On<span className="text-[#0891B2]">Copilot</span>
              </motion.span>
            )}
          </Link>
        </div>

        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-24 w-6 h-6 bg-slate-800 rounded-full border border-slate-700 text-slate-400 flex items-center justify-center hover:text-white transition-colors hover:bg-[#0891B2] hover:border-[#0891B2]"
        >
          <ChevronLeft className={cn("w-4 h-4 transition-transform duration-300", sidebarCollapsed && "rotate-180")} />
        </button>

        <div className="flex-1 py-6 flex flex-col gap-2 px-3 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/") && item.href !== "/dashboard";
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className="group relative">
                <div
                  className={cn(
                    "flex items-center h-12 rounded-xl transition-all duration-200 group-hover:bg-slate-900",
                    isActive ? "bg-slate-900 nav-item-active" : "text-slate-400 hover:text-slate-200",
                    sidebarCollapsed ? "justify-center" : "px-4"
                  )}
                >
                  <Icon className={cn("shrink-0 w-5 h-5", isActive ? "text-[#0891B2]" : "")} />
                  
                  {!sidebarCollapsed && (
                     <span className={cn("ml-3 font-medium whitespace-nowrap", isActive ? "text-white" : "")}>
                       {item.label}
                     </span>
                  )}

                  {/* Notification Badge */}
                  {item.href === "/dashboard/notifications" && unreadCount > 0 && (
                    <div className={cn(
                      "bg-rose-500 rounded-full flex items-center justify-center text-white font-bold text-xs ring-2 ring-slate-950",
                      sidebarCollapsed ? "absolute top-2 right-2 w-4 h-4 text-[10px]" : "ml-auto px-2 py-0.5"
                    )}>
                      {unreadCount}
                    </div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-slate-800">
           <Link href="/login" className={cn(
               "flex items-center gap-3 h-12 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 transition-all",
               sidebarCollapsed ? "justify-center" : "px-4"
           )}>
              <LogOut className="w-5 h-5" />
              {!sidebarCollapsed && <span className="font-medium whitespace-nowrap">Logout</span>}
           </Link>
        </div>
      </motion.aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 bg-slate-50/50 dark:bg-[#060810] relative z-10 flex flex-col h-full overflow-hidden">
         {/* Mobile Header */}
         <div className="md:hidden flex items-center justify-between h-16 px-6 glass-dark border-b border-white/5 shrink-0 z-20">
            <div className="flex items-center gap-2">
               <Activity className="w-6 h-6 text-[#0891B2]" />
               <span className="font-bold text-xl text-white">On<span className="text-[#0891B2]">Copilot</span></span>
            </div>
            <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
               <Menu className="w-5 h-5 text-white" />
            </Button>
         </div>

         {/* Page Content Scrollable Area */}
         <div className="flex-1 overflow-y-auto">
           {children}
         </div>
      </main>
    </div>
  );
}
