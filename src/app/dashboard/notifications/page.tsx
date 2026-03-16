"use client"

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, ShieldAlert, Activity, FileEdit, Users, Check, MessageSquare } from "lucide-react";
import { useNotificationsStore } from "@/store";
import { mockNotifications } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatRelativeTime, cn } from "@/lib/utils";

export default function NotificationsPage() {
    const notifications = useNotificationsStore(s => s.notifications.length ? s.notifications : mockNotifications);
    const markRead = useNotificationsStore(s => s.markRead);
    const markAllRead = useNotificationsStore(s => s.markAllRead);
    
    const [filter, setFilter] = useState("All");

    const filtered = notifications.filter(n => {
        if (filter === "Unread") return !n.isRead;
        if (filter === "Alerts") return n.type === "alert";
        if (filter === "Messages") return n.type === "second_opinion"; // Treating second opinion as messages for demo
        return true;
    });

    const getTypeStyles = (type: string) => {
        switch (type) {
            case "alert": return { brd: "border-rose-500", bg: "bg-rose-500/10", icn: <ShieldAlert className="w-4 h-4 text-rose-500"/>, tbg: "bg-rose-500/5" };
            case "analysis": return { brd: "border-[#0891B2]", bg: "bg-[#0891B2]/10", icn: <Activity className="w-4 h-4 text-[#0891B2]"/>, tbg: "bg-[#0891B2]/5" };
            case "case_update": return { brd: "border-[#0F3460]", bg: "bg-[#0F3460]/20", icn: <FileEdit className="w-4 h-4 text-[#0F3460] dark:text-blue-400"/>, tbg: "bg-[#0F3460]/10" };
            case "second_opinion": return { brd: "border-amber-500", bg: "bg-amber-500/10", icn: <Users className="w-4 h-4 text-amber-500"/>, tbg: "bg-amber-500/5" };
            default: return { brd: "border-slate-500", bg: "bg-slate-500/10", icn: <Bell className="w-4 h-4 text-slate-500"/>, tbg: "bg-slate-500/5" };
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-8 h-full">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                <div>
                     <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                         <Bell className="w-8 h-8 text-[#0891B2]" /> Activity Feed
                     </h1>
                </div>
                <Button variant="outline" size="sm" onClick={markAllRead} className="text-slate-400 border-white/10 hover:text-white hover:bg-white/5">
                    <Check className="w-4 h-4 mr-2" /> Mark all as read
                </Button>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-4 scrollbar-hide mb-4 border-b border-white/5">
                {["All", "Unread", "Alerts", "Messages"].map(f => (
                   <button
                       key={f}
                       onClick={() => setFilter(f)}
                       className={cn(
                           "px-4 py-2 font-medium text-sm transition-colors border-b-2",
                           filter === f ? "border-[#0891B2] text-white" : "border-transparent text-slate-500 hover:text-slate-300"
                       )}
                   >
                       {f}
                   </button>
                ))}
            </div>

            <div className="space-y-4 pb-20">
                <AnimatePresence>
                    {filtered.map(n => {
                        const styles = getTypeStyles(n.type);
                        return (
                            <motion.div
                               initial={{ opacity: 0, y: 10 }}
                               animate={{ opacity: 1, y: 0 }}
                               exit={{ opacity: 0, scale: 0.95 }}
                               key={n.id}
                               onClick={() => !n.isRead && markRead(n.id)}
                               className={cn(
                                   "flex gap-4 p-4 rounded-xl border relative overflow-hidden transition-colors cursor-pointer group",
                                   n.isRead ? "border-white/5 bg-slate-900 shadow-sm hover:border-white/10" : `border-white/10 ${styles.tbg} shadow-md`
                               )}
                            >
                               {/* Left color bar */}
                               <div className={cn("absolute left-0 top-0 bottom-0 w-[3px]", styles.brd, !n.isRead && "shadow-[0_0_10px_currentColor]")} />
                               
                               <div className={cn("mt-1 w-8 h-8 rounded-full flex shrink-0 items-center justify-center", styles.bg)}>
                                   {styles.icn}
                               </div>

                               <div className="flex-1 min-w-0">
                                   <div className="flex justify-between items-start mb-1 gap-2">
                                       <h4 className={cn("font-bold text-sm truncate", n.isRead ? "text-slate-300" : "text-white")}>{n.title}</h4>
                                       <span className="text-xs text-slate-500 whitespace-nowrap">{formatRelativeTime(n.createdAt)}</span>
                                   </div>
                                   <p className={cn("text-sm", n.isRead ? "text-slate-500" : "text-slate-300 font-medium")}>{n.message}</p>
                                   
                                   {n.caseId && (
                                       <div className="mt-3">
                                           <Badge variant="outline" className="text-xs border-white/5 bg-black/20 text-slate-400 font-mono group-hover:border-white/20 transition-colors">Ref: {n.caseId.toUpperCase()}</Badge>
                                       </div>
                                   )}
                               </div>
                               
                               {!n.isRead && (
                                   <div className="w-2 h-2 rounded-full bg-[#0891B2] mt-2 shrink-0 animate-pulse shadow-[0_0_8px_rgba(8,145,178,0.8)]" />
                               )}
                            </motion.div>
                        )
                    })}
                </AnimatePresence>

                {filtered.length === 0 && (
                     <div className="py-20 text-center text-slate-500">
                         <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-20" />
                         <p>No activity to display here.</p>
                     </div>
                )}
            </div>
        </div>
    );
}
