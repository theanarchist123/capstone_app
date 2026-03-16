"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
    ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend,
    AreaChart, Area, XAxis, YAxis, CartesianGrid,
    BarChart, Bar, ScatterChart, Scatter, ZAxis, Treemap
} from "recharts";
import { mockAnalytics } from "@/lib/mock-data";

export default function AnalyticsPage() {
   // Format data for Recharts
   const subtypeData = Object.entries(mockAnalytics.subtypeDistribution).map(([name, value]) => ({ name, value }));
   const SUBTYPE_COLORS = ["#059669", "#0891B2", "#D97706", "#E11D48", "#64748b"];

   const stageData = Object.entries(mockAnalytics.casesByStage).map(([name, value]) => ({ name: `Stage ${name}`, value }));
   
   const biomarkerData = Object.entries(mockAnalytics.biomarkerPositivity).map(([name, value], i) => ({ 
       name, value, 
       x: i % 5, y: Math.floor(i / 5), z: value 
   }));

   const treemapData = [
       { name: "Treatments", children: Object.entries(mockAnalytics.treatmentFrequency).map(([name, size]) => ({ name, size })) }
   ];

   return (
      <div className="p-8 pb-32 max-w-[1600px] mx-auto space-y-8 bg-[#060810] min-h-full">
         <div className="flex items-center justify-between mb-8">
            <div>
               <h1 className="text-4xl font-bold tracking-tight text-white mb-2 font-mono uppercase">Clinical Command Center</h1>
               <p className="text-[#0891B2] font-semibold tracking-wider text-sm uppercase">Real-time Oncology Population Analytics</p>
            </div>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-[400px]">
            
            {/* 1. Subtype Distribution Donut */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="col-span-1 bg-slate-900 border border-white/10 rounded-2xl p-6 glass-dark relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-[#0891B2]/5 to-transparent pointer-events-none" />
                <h3 className="text-white font-bold mb-4 font-mono">1. Subtype Distribution</h3>
                <div className="h-[300px] w-full relative z-10">
                    <ResponsiveContainer>
                        <PieChart>
                            <Pie data={subtypeData} cx="50%" cy="50%" innerRadius={70} outerRadius={110} paddingAngle={5} dataKey="value" stroke="rgba(255,255,255,0.1)">
                                {subtypeData.map((entry, index) => <Cell key={`cell-${index}`} fill={SUBTYPE_COLORS[index % SUBTYPE_COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#fff" }} itemStyle={{ color: "#fff" }} />
                            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "20px" }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </motion.div>

            {/* 4. Monthly Volume Area Chart */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="col-span-1 xl:col-span-2 bg-slate-900 border border-white/10 rounded-2xl p-6 glass-dark relative overflow-hidden group">
                <h3 className="text-white font-bold mb-4 font-mono">2. Case Volume Trending</h3>
                <div className="h-[300px] w-full">
                    <ResponsiveContainer>
                        <AreaChart data={mockAnalytics.monthlyVolume}>
                            <defs>
                                <linearGradient id="colorCases" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#0891B2" stopOpacity={0.8}/>
                                    <stop offset="95%" stopColor="#0891B2" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="month" stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} />
                            <YAxis stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} />
                            <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", color: "#fff" }} />
                            <Area type="monotone" dataKey="cases" stroke="#0891B2" strokeWidth={3} fillOpacity={1} fill="url(#colorCases)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </motion.div>

            {/* 2. Cases by Stage Bar Chart */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="col-span-1 bg-slate-900 border border-white/10 rounded-2xl p-6 glass-dark">
                <h3 className="text-white font-bold mb-4 font-mono">3. Tumour Staging</h3>
                <div className="h-[300px] w-full">
                    <ResponsiveContainer>
                        <BarChart data={stageData} layout="vertical" margin={{ left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                            <XAxis type="number" stroke="#64748b" />
                            <YAxis dataKey="name" type="category" stroke="#cbd5e1" fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b" }} />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {stageData.map((e, index) => <Cell key={`cell-${index}`} fill={`url(#barGradient-${index})`} />)}
                            </Bar>
                            <defs>
                                {stageData.map((_, i) => (
                                   <linearGradient key={`barGradient-${i}`} id={`barGradient-${i}`} x1="0" y1="0" x2="1" y2="0">
                                       <stop offset="0%" stopColor="#0F3460" />
                                       <stop offset="100%" stopColor="#0891B2" />
                                   </linearGradient>
                                ))}
                            </defs>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </motion.div>

            {/* 3. Biomarker Positivity Bubble Chart */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="col-span-1 bg-slate-900 border border-white/10 rounded-2xl p-6 glass-dark flex flex-col items-center">
                 <h3 className="text-white font-bold mb-4 font-mono self-start border-l-4 border-amber-500 pl-3">4. Biomarker Positivity Density</h3>
                 <div className="h-[300px] w-full flex items-center justify-center relative">
                     {/* Custom styled bubble chart representation */}
                     {biomarkerData.map((bm, i) => (
                         <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.5 + (i * 0.05) }}
                            key={bm.name}
                            className="absolute rounded-full border border-rose-500/50 flex flex-col items-center justify-center bg-rose-500/10 hover:bg-rose-500/30 transition-colors shadow-[0_0_15px_rgba(225,29,72,0.2)]"
                            style={{
                                width: Math.max(40, bm.value * 1.5),
                                height: Math.max(40, bm.value * 1.5),
                                left: `${10 + (bm.x * 20)}%`,
                                top: `${10 + (bm.y * 35)}%`,
                            }}
                         >
                            <span className="text-[10px] font-bold text-white text-center leading-tight px-1">{bm.name}</span>
                            <span className="text-xs font-mono text-rose-400">{bm.value}%</span>
                         </motion.div>
                     ))}
                 </div>
            </motion.div>

            {/* 6. Alert Frequency */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="col-span-1 bg-slate-900 border border-white/10 rounded-2xl p-6 glass-dark">
                <h3 className="text-white font-bold mb-4 font-mono text-rose-500">5. Safety Alert Velocity</h3>
                <div className="h-[300px] w-full">
                    <ResponsiveContainer>
                        <BarChart data={mockAnalytics.alertFrequency}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="type" stroke="#64748b" tick={{fill: '#64748b', fontSize: 10}} angle={-45} textAnchor="end" height={60} />
                            <YAxis stroke="#64748b" />
                            <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: "#0f172a", borderColor: "#e11d48", color: "#e11d48" }} />
                            <Bar dataKey="count" fill="#e11d48" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </motion.div>
         </div>
      </div>
   );
}
