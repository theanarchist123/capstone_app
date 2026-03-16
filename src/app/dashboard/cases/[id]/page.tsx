"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useCasesStore } from "@/store";
import { mockCases } from "@/lib/mock-data";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { getSubtypeColor, getSubtypeBg, animateCounter, cn } from "@/lib/utils";
import { ShieldAlert, Info, GitCommit, GitPullRequest, Search, CheckCircle2, ChevronRight, Activity, Save, History, SlidersHorizontal, Scale } from "lucide-react";

// --- Sub-components for Results Page ---

const RingProgress = ({ value, color, size = 60, stroke = 6 }: { value: number, color: string, size?: number, stroke?: number }) => {
    const radius = (size - stroke) / 2;
    const circumference = radius * 2 * Math.PI;
    const [offset, setOffset] = useState(circumference);
    const [displayVal, setDisplayVal] = useState(0);

    useEffect(() => {
        animateCounter(0, value, 1000, setDisplayVal);
        setOffset(circumference - (value / 100) * circumference);
    }, [value, circumference]);

    return (
        <div className="relative flex items-center justify-center font-mono" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90" width={size} height={size}>
                <circle className="text-slate-800" strokeWidth={stroke} stroke="currentColor" fill="transparent" r={radius} cx={size/2} cy={size/2} />
                <circle 
                  className="progress-ring-circle" 
                  stroke={color} strokeWidth={stroke} strokeDasharray={circumference} strokeDashoffset={offset} 
                  strokeLinecap="round" fill="transparent" r={radius} cx={size/2} cy={size/2} 
                />
            </svg>
            <span className="absolute text-sm font-bold opacity-90" style={{ color }}>{displayVal}%</span>
        </div>
    );
};

const ConstellationMap = ({ subtype, biomarkers }: { subtype: string, biomarkers: any }) => {
    const marks = [
        { id: "ER", val: biomarkers.er, cat: "Receptor" }, { id: "PR", val: biomarkers.pr, cat: "Receptor" },
        { id: "HER2", val: biomarkers.her2, cat: "Receptor" }, { id: "Ki-67", val: biomarkers.ki67 ? (biomarkers.ki67 > 20 ? "Positive" : "Negative") : "Unknown", cat: "Proliferation" },
        { id: "BRCA1", val: biomarkers.brca1, cat: "Mutation" }, { id: "BRCA2", val: biomarkers.brca2, cat: "Mutation" },
        { id: "TP53", val: biomarkers.tp53, cat: "Mutation" }, { id: "PIK3CA", val: biomarkers.pik3ca, cat: "Mutation" },
        { id: "PD-L1", val: biomarkers.pdl1, cat: "Receptor" }, { id: "TILs", val: biomarkers.tils ? (biomarkers.tils > 30 ? "Positive": "Negative") : "Unknown", cat: "Proliferation" },
        { id: "TOP2A", val: biomarkers.top2a, cat: "Proliferation"}, { id: "BCL2", val: biomarkers.bcl2, cat: "Mutation"}
    ];

    const radius = 120;
    const center = 150;
    const color = getSubtypeColor(subtype);

    return (
        <div className="flex justify-center items-center p-8 bg-slate-900 border border-slate-800 rounded-2xl relative overflow-hidden">
             <div className="absolute inset-0 bg-gradient-radial from-slate-800/20 to-transparent opacity-50" />
             <svg width="300" height="300" className="relative z-10 overflow-visible">
                 {/* Connections to center */}
                 {marks.map((m, i) => {
                     const angle = (i * (Math.PI * 2)) / marks.length;
                     const x = center + radius * Math.cos(angle);
                     const y = center + radius * Math.sin(angle);
                     return <line key={`l-${i}`} x1={center} y1={center} x2={x} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="1" strokeDasharray="2,2"/>
                 })}
                 
                 {/* Center Node */}
                 <circle cx={center} cy={center} r="35" fill="rgba(8,13,26,0.8)" stroke={color} strokeWidth="2" className="glow-teal-sm" />
                 <text x={center} y={center} textAnchor="middle" dominantBaseline="middle" fill={color} fontSize="10" fontWeight="bold">{subtype.split(" ")[0]}</text>

                 {/* Orbit Nodes */}
                 {marks.map((m, i) => {
                     const angle = (i * (Math.PI * 2)) / marks.length;
                     const x = center + radius * Math.cos(angle);
                     const y = center + radius * Math.sin(angle);
                     const isPos = m.val === "Positive";
                     const isNeg = m.val === "Negative";
                     const isUnk = !isPos && !isNeg;
                     
                     return (
                         <TooltipProvider key={m.id}>
                           <Tooltip>
                             <TooltipTrigger asChild>
                               <g className="cursor-pointer group">
                                   <circle 
                                      cx={x} cy={y} r="14" 
                                      fill={isPos ? color : "rgba(15,52,96,0.5)"} 
                                      stroke={isNeg ? "rgba(255,255,255,0.5)" : isPos ? color : "rgba(255,255,255,0.1)"} 
                                      strokeWidth="1.5"
                                      className="transition-all duration-300 group-hover:scale-125 origin-center"
                                   />
                                   <text x={x} y={y} textAnchor="middle" dominantBaseline="middle" fill={isPos ? "#080D1A" : "#a1a1aa"} fontSize="8" fontWeight="bold">{m.id.substring(0,3)}</text>
                               </g>
                             </TooltipTrigger>
                             <TooltipContent className="bg-slate-900 border-slate-700">
                                 <p className="font-bold text-white mb-1">{m.id} : <span className={isPos ? "text-emerald-400" : isNeg ? "text-rose-400" : "text-slate-500"}>{m.val}</span></p>
                                 <p className="text-xs text-slate-400 text-center">{m.cat}</p>
                             </TooltipContent>
                           </Tooltip>
                         </TooltipProvider>
                     )
                 })}
             </svg>
        </div>
    );
};

// --- Page Main Component ---

export default function CaseResultsPage() {
    const params = useParams();
    const cId = Array.isArray(params.id) ? params.id[0] : params.id;
    const { cases, updateCase } = useCasesStore(s => ({
        cases: s.cases.length ? s.cases : mockCases,
        updateCase: s.updateCase
    }));
    const caseData = cases.find(c => c.id === cId) || cases[0];

    const [simulating, setSimulating] = useState(false);
    const [simEr, setSimEr] = useState("Positive");
    const [simKi67, setSimKi67] = useState([14]);
    const [simMenopause, setSimMenopause] = useState(false);
    
    // Subtype Unfold Animation variables
    const color = getSubtypeColor(caseData.subtype);

    if (!caseData) return <div className="p-20 text-center">Loading...</div>;

    const runSimulation = async () => {
        setSimulating(true);
        try {
            // Build the override payload mapping simple frontend states to backend properties
            const overrides = {
                er_status: simEr,
                ki67_percent: simKi67[0],
                menopausal_status: simMenopause ? "post" : "pre"
            };

            // Trigger the simulation engine on Backend
            const res = await api.simulateAnalysis(caseData.id, overrides);
            
            if (res.success && res.data) {
                const backendData = res.data;
                // Map the Python backend structure to the TS frontend structure
                const mappedRecommendations = (backendData.recommendations || []).map((r: any, idx: number) => ({
                    id: `rec-${idx}`,
                    isTopRecommendation: r.rank === 1,
                    name: r.protocol_name || "Treatment Protocol",
                    description: r.clinical_notes || "",
                    guidelineSource: r.guideline_source || "AI Generated",
                    confidenceScore: Math.round((r.confidence_score || 0) * 100),
                    duration: r.duration_months ? `${r.duration_months} Months` : "Unknown",
                    ruleTrace: (r.rule_trace || []).map((tr: any, trIdx: number) => ({
                        id: `tr-${idx}-${trIdx}`,
                        label: tr.biomarker || tr.label || "Feature",
                        value: tr.value,
                        conclusion: tr.implication || tr.conclusion || "Matched"
                    }))
                }));

                const mappedAlerts = (backendData.alerts || []).map((a: any, idx: number) => ({
                    id: `alert-${idx}`,
                    triggerSource: a.contraindication_type || a.source || "System Alert",
                    affectedTreatment: a.affected_drug || "Protocol",
                    description: a.reason || a.description || "Safety alert triggered.",
                    recommendedAction: a.action || a.recommendation || "Review required."
                }));

                // Update real Zustand store + Sync Backend
                updateCase(caseData.id, { 
                    subtype: backendData.molecular_subtype || caseData.subtype,
                    recommendations: mappedRecommendations,
                    safetyAlerts: mappedAlerts,
                });
            }
        } catch (e) {
            console.error("Analysis failed:", e);
            // Fallback UI or toast could go here
        } finally {
            setSimulating(false);
        }
    }

    return (
        <div className="flex h-[calc(100vh-5rem)] w-full overflow-hidden">
            {/* Left Main Scrollable Content */}
            <div className="flex-1 overflow-y-auto w-full p-6 md:p-8 space-y-8 pb-32">
                
                {/* Section: Subtype Reveal */}
                <motion.div 
                   initial={{ filter: "blur(20px)", opacity: 0, scale: 0.95 }}
                   animate={{ filter: "blur(0px)", opacity: 1, scale: 1 }}
                   transition={{ duration: 1, ease: "easeOut" }}
                   className="relative flex flex-col items-center justify-center py-20 bg-slate-900/40 border border-white/5 rounded-3xl overflow-hidden"
                >
                    <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] select-none pointer-events-none overflow-hidden">
                        <span className="text-[120px] font-black tracking-tighter text-white whitespace-nowrap">{caseData.subtype.toUpperCase()}</span>
                    </div>
                    
                    <motion.div initial={{ y: 20 }} animate={{ y: 0 }} transition={{ delay: 0.5 }}>
                        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-[0.2em] mb-4 text-center">AI Molecular Classification completed</h2>
                        <h1 
                           className="text-5xl md:text-7xl font-black text-center"
                           style={{ color, textShadow: `0 0 40px ${color}80` }}
                        >
                            {caseData.subtype}
                        </h1>
                        <div className="flex items-center justify-center gap-4 mt-8">
                            <Badge className="bg-white/5 border-white/10 text-slate-300 px-4 py-1">Stage {caseData.tumour.stage}</Badge>
                            <Badge className="bg-white/5 border-white/10 text-slate-300 px-4 py-1">Grade {caseData.tumour.grade}</Badge>
                        </div>
                    </motion.div>
                </motion.div>

                {/* Grid: Constellation & Notes */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-1 flex flex-col gap-6">
                        <ConstellationMap subtype={caseData.subtype} biomarkers={caseData.biomarkers} />
                    </div>
                    <div className="lg:col-span-2 flex flex-col h-full bg-[#fef9e7] dark:bg-[#1a1f2e] border border-white/10 rounded-2xl relative notepad shadow-inner p-6">
                         <div className="absolute top-4 right-4 flex items-center text-xs font-mono text-emerald-600 dark:text-emerald-400 opacity-70">
                             <Save className="w-3 h-3 mr-1" /> Saved
                         </div>
                         <h3 className="text-sm font-bold text-slate-800 dark:text-slate-300 mb-4 font-sans flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-amber-500" /> Clinical Notes</h3>
                         <textarea 
                            className="bg-transparent border-none outline-none resize-none flex-1 text-slate-700 dark:text-slate-300 font-mono text-sm leading-7"
                            defaultValue={caseData.doctorNotes}
                            placeholder="Add your clinical observations here..."
                         />
                    </div>
                </div>

                {/* Section: Safety Alerts (Shake Animation) */}
                <AnimatePresence>
                    {caseData.safetyAlerts && caseData.safetyAlerts.length > 0 && (
                        <motion.div 
                           initial={{ x: 20, opacity: 0 }}
                           animate={{ x: [0, -10, 10, -10, 10, 0], opacity: 1 }}
                           transition={{ duration: 0.6, delay: 1 }}
                           className="bg-rose-500/10 border-l-4 border-rose-500 rounded-r-2xl p-6"
                        >
                            <h3 className="flex items-center gap-2 text-rose-500 font-bold mb-4"><ShieldAlert className="w-5 h-5"/> Crucial Safety Alerts</h3>
                            <div className="space-y-3">
                                {caseData.safetyAlerts.map(alert => (
                                    <div key={alert.id} className="bg-black/20 p-4 rounded-xl text-sm border border-rose-500/10">
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="font-bold text-rose-400">{alert.triggerSource}</span>
                                            <Badge variant="danger">Affected: {alert.affectedTreatment}</Badge>
                                        </div>
                                        <p className="text-slate-300 mb-3">{alert.description}</p>
                                        <p className="font-medium text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-4 h-4"/> Recommendation: {alert.recommendedAction}</p>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Section: Treatment Recommendations */}
                <div>
                   <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4 mt-12">
                       <h2 className="text-2xl font-bold flex items-center gap-3">
                           <Activity className="w-6 h-6 text-[#0891B2]" /> Suggested Treatment Paths
                       </h2>
                       <Badge variant="outline" className="text-slate-400 border-white/10"><Scale className="w-4 h-4 mr-2"/> Evidence Level A</Badge>
                   </div>
                   
                   <AnimatePresence mode="popLayout">
                       {simulating ? (
                           <motion.div initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="py-20 flex justify-center">
                               <div className="w-10 h-10 border-4 border-[#0891B2] border-t-transparent rounded-full animate-spin" />
                           </motion.div>
                       ) : (
                           caseData.recommendations?.map((rec, i) => (
                               <motion.div 
                                   initial={{ y: 20, opacity: 0 }}
                                   whileInView={{ y: 0, opacity: 1 }}
                                   viewport={{ once: true }}
                                   transition={{ delay: i * 0.15 }}
                                   key={rec.id}
                                   className={cn(
                                       "relative bg-slate-900 border rounded-2xl p-6 mb-6 group transition-all duration-300 overflow-hidden",
                                       rec.isTopRecommendation ? "border-[#0891B2]/50 shadow-[0_10px_30px_-10px_rgba(8,145,178,0.2)]" : "border-slate-800 hover:border-slate-700"
                                   )}
                               >
                                   {/* Top Badge */}
                                   {rec.isTopRecommendation && (
                                       <div className="absolute top-0 right-0 bg-[#0891B2] text-white text-xs font-bold px-4 py-1 rounded-bl-xl shadow-lg flex items-center gap-1">
                                           <CheckCircle2 className="w-3 h-3"/> Best Match
                                       </div>
                                   )}
                                   {/* Left accent bar */}
                                   {rec.isTopRecommendation && <div className="absolute top-0 bottom-0 left-0 w-1 bg-[#0891B2]" />}

                                   <div className="flex flex-col md:flex-row gap-6 mb-8">
                                       <div className="md:w-[70%]">
                                           <h3 className={cn("text-xl font-bold mb-2", rec.isTopRecommendation ? "text-white" : "text-slate-200")}>{rec.name}</h3>
                                           <p className="text-slate-400 text-sm leading-relaxed mb-4">{rec.description}</p>
                                           <div className="flex flex-wrap items-center gap-2 mb-2">
                                              <Badge className="bg-slate-800 text-slate-300 border-white/5">{rec.guidelineSource} Guidelines</Badge>
                                              <span className="text-xs text-slate-500">• Duration: {rec.duration}</span>
                                           </div>
                                       </div>
                                       <div className="md:w-[30%] flex items-center justify-end md:justify-center border-l-0 md:border-l border-white/5">
                                           <div className="text-center">
                                               <RingProgress value={rec.confidenceScore} color={rec.isTopRecommendation ? "#0891B2" : "#94a3b8"} size={70} stroke={5} />
                                               <span className="text-xs text-slate-500 font-medium tracking-wide mt-2 block uppercase">Confidence Index</span>
                                           </div>
                                       </div>
                                   </div>

                                   {/* Rule Trace Flow */}
                                   <div className="bg-black/30 rounded-xl p-4 overflow-x-auto scrollbar-hide border border-white/5">
                                       <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                           <GitPullRequest className="w-4 h-4" /> AI Rule Trace Execution
                                       </h4>
                                       <div className="flex items-center min-w-max">
                                           {rec.ruleTrace.map((node, i, arr) => (
                                              <motion.div 
                                                 initial={{ opacity: 0, scale: 0.9 }}
                                                 whileInView={{ opacity: 1, scale: 1 }}
                                                 viewport={{ once: true }}
                                                 transition={{ delay: 0.5 + (i * 0.1) }}
                                                 key={node.id} 
                                                 className="flex items-center"
                                              >
                                                  <TooltipProvider>
                                                      <Tooltip>
                                                          <TooltipTrigger asChild>
                                                              <div className="rule-node cursor-pointer hover:bg-accent/20 transition-colors">
                                                                  <span className="text-xs opacity-70 font-mono">[{node.label}: {node.value}]</span>
                                                                  <span className="text-sm">{node.conclusion}</span>
                                                              </div>
                                                          </TooltipTrigger>
                                                          <TooltipContent className="bg-slate-900 border-slate-700">Matched Rule ID: {node.id.toUpperCase()}</TooltipContent>
                                                      </Tooltip>
                                                  </TooltipProvider>
                                                  {i < arr.length - 1 && <ChevronRight className="w-4 h-4 text-slate-600 mx-2 flex-shrink-0" />}
                                              </motion.div>
                                           ))}
                                       </div>
                                   </div>

                                   <div className="mt-6 flex justify-end">
                                       <Button variant={rec.isTopRecommendation ? "teal" : "outline"} className={rec.isTopRecommendation ? "" : "border-slate-700 text-slate-300 hover:text-white"}>
                                           Select This Protocol
                                       </Button>
                                   </div>
                               </motion.div>
                           ))
                       )}
                   </AnimatePresence>
                </div>
            </div>

            {/* Right Sticky Panel: What-If Simulator & History */}
            <div className="w-[350px] shrink-0 border-l border-white/5 bg-slate-950/80 backdrop-blur-3xl overflow-y-auto">
                <Tabs defaultValue="simulator" className="w-full">
                    <TabsList className="w-full bg-slate-900 rounded-none h-12 border-b border-white/5 p-0 justify-start px-2">
                         <TabsTrigger value="simulator" className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-[#0891B2] data-[state=active]:text-white">Simulator</TabsTrigger>
                         <TabsTrigger value="history" className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-[#0891B2] data-[state=active]:text-white">History Logs</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="simulator" className="p-6 m-0 space-y-6">
                        <div className="flex items-center gap-2 text-amber-500 mb-2">
                             <SlidersHorizontal className="w-5 h-5"/>
                             <h3 className="font-bold">What-If Scenarios</h3>
                        </div>
                        <p className="text-xs text-slate-400 leading-relaxed mb-6">Modify biomarker parameters to simulate how AI guidelines would branch recommendations.</p>
                        
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm bg-slate-900 border border-slate-800 p-3 rounded-xl">
                                <span className="text-slate-300 font-medium">Force ER</span>
                                <div className="flex bg-slate-950 p-1 rounded-lg">
                                    <button onClick={() => setSimEr("Positive")} className={cn("px-3 py-1 rounded-md text-xs font-bold transition-colors", simEr === "Positive" ? "bg-emerald-500/20 text-emerald-500" : "text-slate-500 hover:text-slate-300")}>+</button>
                                    <button onClick={() => setSimEr("Negative")} className={cn("px-3 py-1 rounded-md text-xs font-bold transition-colors", simEr === "Negative" ? "bg-rose-500/20 text-rose-500" : "text-slate-500 hover:text-slate-300")}>-</button>
                                </div>
                            </div>
                            
                            <div className="space-y-2 bg-slate-900 border border-slate-800 p-4 rounded-xl">
                                <span className="text-xs font-medium text-slate-400">Ki-67 Proliferation Override ({simKi67[0]}%)</span>
                                <Slider value={simKi67} onValueChange={setSimKi67} max={100} step={1} className="mt-4" />
                            </div>

                            <div className="flex items-center justify-between text-sm bg-slate-900 border border-slate-800 p-3 rounded-xl">
                                <span className="text-slate-300 font-medium">Simulate Menopause</span>
                                <Switch checked={simMenopause} onCheckedChange={setSimMenopause} />
                            </div>
                        </div>

                        <Button onClick={runSimulation} className="w-full mt-4 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700">
                             <Play className="w-4 h-4 mr-2" /> Run AI Simulation
                        </Button>

                        {simulating && (
                            <div className="text-xs text-emerald-400 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl mt-4 animate-pulse">
                                Simulating pathways...
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="history" className="p-6 m-0">
                         <div className="flex items-center gap-2 text-slate-300 mb-6">
                             <GitCommit className="w-5 h-5"/>
                             <h3 className="font-bold">Protocol History</h3>
                        </div>
                        <div className="space-y-0 relative before:absolute before:inset-0 before:ml-[15px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-800 before:to-transparent">
                            {caseData.versions?.map((v, i) => (
                                <div key={v.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active mb-8">
                                    <div className="flex items-center justify-center w-8 h-8 rounded-full border border-slate-700 bg-slate-900 group-[.is-active]:bg-[#0891B2] text-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow absolute left-0 md:left-1/2 z-10 transition-colors">
                                       <span className="text-[10px] font-bold">v{v.version}</span>
                                    </div>
                                    <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2rem)] p-4 rounded-xl border border-white/5 bg-slate-900/50 hover:bg-slate-800 ml-12 md:ml-0 transition-colors">
                                        <div className="flex items-center justify-between space-x-2 mb-1">
                                            <div className="font-bold text-slate-200 text-sm">{v.doctorName}</div>
                                            <time className="font-mono text-xs text-slate-500">{new Date(v.createdAt).toLocaleDateString()}</time>
                                        </div>
                                        <div className="text-slate-400 text-xs">
                                            {v.changeSummary}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
}

// Ensure Play icon is defined if not imported from lucide-react above
const Play = ({ className }: { className: string }) => <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>;
