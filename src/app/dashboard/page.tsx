"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Search, Filter, MoreHorizontal, ArrowUpRight, TrendingUp, Users, Activity, CheckCircle, Bell, Folders } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

import { useCasesStore } from "@/store";
import { mockCases } from "@/lib/mock-data";
import { getSubtypeBg, animateCounter, formatRelativeTime } from "@/lib/utils";
import type { ClinicalCase } from "@/types";

// ─── Stat Card Component ────────────────────────────────────────────────────
const StatCard = ({ title, value, trend, icon: Icon, delay }: { title: string, value: number, trend: string, icon: any, delay: number }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    animateCounter(0, value, 2000, setDisplayValue);
  }, [value]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="p-6 rounded-2xl border border-white/5 bg-slate-900/50 glass-dark flex flex-col justify-between"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
           <p className="text-sm font-medium text-slate-400 mb-1">{title}</p>
           <h3 className="text-3xl font-bold text-white">{displayValue.toLocaleString()}</h3>
        </div>
        <div className="w-10 h-10 rounded-xl bg-[#0891B2]/10 flex items-center justify-center">
            <Icon className="w-5 h-5 text-[#0891B2]" />
        </div>
      </div>
      <div className="flex items-center gap-2 mt-auto pt-4 border-t border-slate-800/50">
         <div className="flex items-center text-emerald-400 text-xs font-medium">
            <TrendingUp className="w-3 h-3 mr-1" /> {trend}
         </div>
         <span className="text-xs text-slate-500">vs last week</span>
      </div>
    </motion.div>
  );
};

// ─── Main Dashboard Page ────────────────────────────────────────────────────
export default function DashboardPage() {
  const { cases, fetchCases, isLoading } = useCasesStore();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const filteredCases = cases.filter(c => {
     if (filter !== "All" && c.status !== filter && c.subtype !== filter) return false;
     if (search && !c.patientName.toLowerCase().includes(search.toLowerCase())) return false;
     return true;
  });

  return (
    <div className="min-h-full p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
         <div>
            <h1 className="text-4xl font-bold tracking-tight text-white mb-2">Overview</h1>
            <p className="text-slate-400">Welcome back, Dr. Sharma. You have 3 pending reviews.</p>
         </div>
         <Link href="/dashboard/cases/new">
            <Button variant="teal" className="h-11 shadow-[0_0_20px_rgba(8,145,178,0.3)]">
               <Plus className="w-5 h-5 mr-2" /> New Case Consultation
            </Button>
         </Link>
      </div>

      {/* Living Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
         <StatCard title="Active Cases" value={142} trend="+12%" icon={Activity} delay={0.1} />
         <StatCard title="Total Patients" value={860} trend="+5%" icon={Users} delay={0.2} />
         <StatCard title="Analysis Complete" value={105} trend="+22%" icon={CheckCircle} delay={0.3} />
         <StatCard title="Pending Review" value={18} trend="-2%" icon={Bell} delay={0.4} />
      </div>

      {/* Case List Controls */}
      <div className="pt-4 flex flex-col sm:flex-row justify-between gap-4 items-center">
         <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <Input 
              placeholder="Search patients..." 
              className="pl-9 bg-slate-900 border-white/10 text-white placeholder:text-slate-500 rounded-xl"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
         </div>
         <div className="flex gap-2 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0 scrollbar-hide">
            {["All", "Under Analysis", "Pending Review", "HER2-Enriched", "TNBC"].map(f => (
               <Badge
                 key={f} 
                 variant={filter === f ? "teal" : "outline"}
                 className={`cursor-pointer shrink-0 rounded-lg px-3 py-1.5 transition-colors ${filter !== f ? 'border-white/10 text-slate-400 hover:text-white hover:border-[#0891B2]/50 hover:bg-[#0891B2]/10' : ''}`}
                 onClick={() => setFilter(f)}
               >
                 {f}
               </Badge>
            ))}
         </div>
      </div>

      {/* Custom Case List - Card Rows */}
      <div className="space-y-3 pb-20">
         <AnimatePresence>
            {filteredCases.map((c, i) => (
               <motion.div
                 key={c.id}
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, scale: 0.95 }}
                 transition={{ duration: 0.2, delay: i * 0.05 }}
                 className="relative group bg-slate-900 border border-white/5 rounded-2xl overflow-hidden hover:border-white/10 card-hover"
               >
                  {/* Left Color Bar */}
                  <div className={`absolute top-0 bottom-0 left-0 w-2 ${getSubtypeBg(c.subtype).split(' ')[1]}`} style={{ backgroundColor: getSubtypeBg(c.subtype).split(' ').find(cls => cls.startsWith('text-'))?.replace('text-', '') }} />
                  
                  <Link href={`/dashboard/cases/${c.id}`} className="flex flex-col sm:flex-row items-center gap-4 p-5 pl-8 w-full block">
                     {/* Patient Info */}
                     <div className="flex items-center gap-4 min-w-[250px] w-full sm:w-auto">
                        <div className="w-12 h-12 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center font-bold text-white shadow-sm">
                           {c.patientName.split(" ").map(n => n[0]).join("")}
                        </div>
                        <div>
                           <h4 className="font-bold text-lg text-white group-hover:text-[#0891B2] transition-colors">{c.patientName}</h4>
                           <p className="text-sm text-slate-400">{c.patientAge}y • {c.patientSex} • ID: {c.id.toUpperCase()}</p>
                        </div>
                     </div>

                     {/* Subtype & Stage */}
                     <div className="flex-1 min-w-[200px] w-full sm:w-auto flex flex-col justify-center gap-1.5">
                        <div className="flex items-center gap-2">
                           <Badge className={getSubtypeBg(c.subtype)}>{c.subtype}</Badge>
                           <span className="text-sm font-medium text-slate-300">Stage {c.tumour.stage}</span>
                        </div>
                        <p className="text-xs text-slate-500 truncate max-w-xs">{c.doctorNotes || 'No notes provided yet.'}</p>
                     </div>

                     {/* Status Badges */}
                     <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto mt-4 sm:mt-0">
                         {c.status === "Under Analysis" ? (
                            <div className="flex items-center gap-2 bg-[#0F3460]/40 text-[#0891B2] px-3 py-1.5 rounded-full border border-[#0F3460]">
                               <div className="w-2 h-2 rounded-full bg-[#0891B2] status-analyzing" />
                               <span className="text-sm font-medium">Under Analysis</span>
                            </div>
                         ) : c.status === "Pending Review" ? (
                            <div className="flex items-center gap-2 bg-amber-500/10 text-amber-500 px-3 py-1.5 rounded-full border border-amber-500/20">
                               <div className="w-2 h-2 rounded-full bg-amber-500 status-pending" />
                               <span className="text-sm font-medium">Pending Review</span>
                            </div>
                         ) : (
                            <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 px-3 py-1.5 rounded-full border border-emerald-500/20">
                               <div className="w-2 h-2 rounded-full bg-emerald-500 status-ongoing" />
                               <span className="text-sm font-medium">{c.status}</span>
                            </div>
                         )}
                         
                         <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500 hidden md:block whitespace-nowrap">{formatRelativeTime(c.updatedAt)}</span>
                            <div className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-white/10 text-slate-400 hover:text-white transition-colors" onClick={(e) => e.preventDefault()}>
                                <ArrowUpRight className="w-5 h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                            </div>
                         </div>
                     </div>
                  </Link>
               </motion.div>
            ))}
         </AnimatePresence>
         {filteredCases.length === 0 && (
            <div className="py-20 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-3xl bg-slate-900/20">
               {isLoading ? (
                  <>
                     <div className="w-12 h-12 border-4 border-[#0891B2] border-t-transparent rounded-full animate-spin mb-4" />
                     <h3 className="text-xl font-medium text-slate-300 mb-2">Loading your clinical cases...</h3>
                  </>
               ) : (
                  <>
                     <Folders className="w-12 h-12 text-slate-600 mb-4 opacity-50" />
                     <h3 className="text-xl font-medium text-slate-300 mb-2">No cases found</h3>
                     <p className="text-slate-500 mb-6">Create a new case consultation to begin clinical analysis.</p>
                     <Link href="/dashboard/cases/new">
                        <Button variant="outline" className="border-slate-700 bg-slate-800 text-slate-300">Start New Case</Button>
                     </Link>
                  </>
               )}
            </div>
         )}
      </div>
    </div>
  );
}
