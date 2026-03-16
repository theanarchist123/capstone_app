"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ChevronRight, Activity, ShieldCheck, ShieldAlert,
  FlaskConical, History, Users, FileText, Stethoscope,
  Lock, CheckCircle2, ArrowRight, Database
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Unsplash Images ─────────────────────────────────────────────────────────
const HERO_BG = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?q=80&w=2670&auto=format&fit=crop";
const SPLIT_IMG = "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=2670&auto=format&fit=crop";

// ─── Data ────────────────────────────────────────────────────────────────────
const features = [
  { icon: FlaskConical, color: "#0891B2", title: "16-Biomarker Analysis", desc: "Maps ER, PR, HER2, Ki-67, BRCA1/2, and 10+ markers to molecular subtypes against international standards." },
  { icon: ShieldCheck, color: "#10b981", title: "Explainable Recommendations", desc: "Every suggestion traces to an explicit NCCN / ESMO / St. Gallen rule. No black boxes — ever." },
  { icon: ShieldAlert, color: "#f43f5e", title: "Real-Time Safety Alerts", desc: "LVEF thresholds, BRCA flags, contraindications, and drug interaction warnings evaluated before surfacing any protocol." },
  { icon: Activity, color: "#f59e0b", title: "What-If Simulator", desc: "Adjust biomarkers live to explore how staging or receptor changes shift the recommended treatment plan." },
  { icon: History, color: "#a78bfa", title: "Version History", desc: "Every iteration locked, timestamped. Compare evaluations and generate audit-ready clinical documentation." },
  { icon: Users, color: "#60a5fa", title: "MDT Collaboration", desc: "Flag for second opinion, add peer commentary, and build a transparent decision chain across teams." },
];

const steps = [
  { n: "01", title: "Upload Reports", body: "PDF pathology, IHC, FISH & genomic panel reports parsed by AI." },
  { n: "02", title: "Physician Verifies", body: "Extracted biomarkers displayed for human confirmation before analysis proceeds." },
  { n: "03", title: "Rules Engine Fires", body: "120+ clinical rules evaluate the profile against four major guideline frameworks." },
  { n: "04", title: "Safe Plan Delivered", body: "Ranked, explainable protocols with rule chains and safety status — ready in minutes." },
];

const trustItems = [
  { icon: Lock, label: "End-to-end encrypted patient data" },
  { icon: FileText, label: "Full audit trail for every case decision" },
  { icon: Stethoscope, label: "Physician-in-the-loop at every step" },
  { icon: ShieldCheck, label: "Aligned with NCCN, ESMO, ABC, St. Gallen" },
];

const ruleRows = [
  { rule: "ER Positive", col: "emerald" },
  { rule: "HER2 Negative", col: "emerald" },
  { rule: "Ki-67 < 20%", col: "emerald" },
  { rule: "LVEF > 55%", col: "blue" },
  { rule: "BRCA1/2 Negative", col: "blue" },
];

// ─── Tiny helpers ─────────────────────────────────────────────────────────────
const Tag = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-flex items-center gap-1.5 bg-[#0891B2]/15 text-[#67d7f0] border border-[#0891B2]/25 rounded-full text-[11px] font-semibold px-2.5 py-0.5 tracking-wide">
    {children}
  </span>
);

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <div className="min-h-screen bg-[#07091C] text-slate-100 overflow-x-hidden font-sans">

      {/* ─── Navbar ──────────────────────────────────────────────────────── */}
      <header className={cn(
        "fixed top-0 left-0 right-0 z-50 h-16 transition-all duration-300",
        scrolled ? "bg-[#07091C]/95 backdrop-blur-lg border-b border-white/5 shadow-lg" : "bg-transparent"
      )}>
        <div className="max-w-6xl mx-auto px-6 h-full flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#0891B2] flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-base tracking-tight text-white">
              On<span className="text-[#0891B2]">Copilot</span>
            </span>
          </div>

          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how" className="hover:text-white transition-colors">How it works</a>
            <a href="#trust" className="hover:text-white transition-colors">Trust</a>
          </nav>

          {/* CTA buttons */}
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
              Sign in
            </Link>
            <Link href="/signup">
              <button className="h-9 px-4 rounded-lg bg-[#0891B2] hover:bg-[#0680a0] text-white text-sm font-semibold transition-colors shadow-lg shadow-[#0891B2]/20">
                Request Access
              </button>
            </Link>
          </div>
        </div>
      </header>

      {/* ─── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative min-h-[100svh] flex flex-col items-center justify-center text-center overflow-hidden">
        {/* Full-bleed background */}
        <div className="absolute inset-0">
          <img
            src={HERO_BG}
            alt="Oncologist reviewing patient data"
            className="w-full h-full object-cover object-center"
          />
          {/* Layered overlays for depth */}
          <div className="absolute inset-0 bg-[#07091C]/65" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#07091C]/40 via-transparent to-[#07091C]" />
        </div>

        {/* Content — padded top significantly to clear navbar and prevent overlap */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 pt-32 pb-20 mt-16 text-center">
          {/* Eyebrow */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 bg-[#0891B2]/15 border border-[#0891B2]/30 text-[#67d7f0] text-[11px] font-bold tracking-widest uppercase px-3 py-1.5 rounded-full mb-7"
          >
            <span className="w-1.5 h-1.5 bg-[#0891B2] rounded-full animate-pulse" />
            Clinical Decision Intelligence · Oncology
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08] mb-5"
          >
            Treatment Intelligence
            <br />
            <span className="text-[#0891B2]">for Breast Cancer</span>
            <br />
            Oncology.
          </motion.h1>

          {/* Sub-headline */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base md:text-lg text-slate-300 max-w-2xl mx-auto mb-9 leading-relaxed"
          >
            <span className="block mb-2">Evaluate 16+ biomarkers against four global guidelines.</span>
            <span>Get ranked, explainable, safety-checked treatment plans — in minutes, not hours.</span>
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3"
          >
            <Link href="/signup">
              <button className="group flex items-center gap-2 h-12 px-8 rounded-full bg-[#0891B2] hover:bg-[#0680a0] text-white font-bold text-sm shadow-xl shadow-[#0891B2]/30 transition-all">
                Start Free Trial
                <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </Link>
            <Link href="/login">
              <button className="flex items-center h-12 px-8 rounded-full border border-white/20 bg-white/5 hover:bg-white/10 text-white font-semibold text-sm backdrop-blur-sm transition-all">
                View Demo
              </button>
            </Link>
          </motion.div>
        </div>

        {/* Stats strip — anchored at bottom of hero */}
        <motion.div
          className="relative z-10 w-full max-w-4xl mx-auto px-6 pb-20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
            {[
              { v: "16+", l: "Biomarkers" },
              { v: "120+", l: "Clinical Rules" },
              { v: "4", l: "Global Guidelines" },
              { v: "5", l: "Molecular Subtypes" },
            ].map((s) => (
              <div key={s.l} className="bg-white/[0.04] py-5 px-4 text-center">
                <p className="text-2xl font-bold text-white mb-0.5">{s.v}</p>
                <p className="text-[11px] text-slate-400 uppercase tracking-wider">{s.l}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ─── Logos ───────────────────────────────────────────────────────── */}
      <section className="py-10 border-y border-white/5 bg-[#07091C]">
        <div className="max-w-5xl mx-auto px-6">
          <p className="text-center text-[11px] uppercase tracking-widest text-slate-500 font-semibold mb-6">
            Trusted by oncology teams at
          </p>
          <div className="flex flex-wrap justify-center items-center gap-x-10 gap-y-3">
            {["AIIMS Delhi", "Apollo Hospitals", "Tata Memorial Centre", "Max Healthcare", "Manipal Hospitals"].map((n) => (
              <span key={n} className="text-slate-500 text-sm font-medium hover:text-slate-300 transition-colors">{n}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features ─────────────────────────────────────────────────────── */}
      <section id="features" className="py-20 bg-[#07091C]">
        <div className="max-w-6xl mx-auto px-6">
          {/* Section header */}
          <div className="text-center mb-12">
            <p className="text-[11px] uppercase tracking-widest text-[#0891B2] font-bold mb-3">Capabilities</p>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">Built for real clinical decisions.</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm">
              Every feature designed alongside oncologists to support actual clinical workflows.
            </p>
          </div>

          {/* 3-col grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ delay: i * 0.07 }}
                className="group bg-[#0c0f24] border border-white/[0.07] rounded-xl p-5 hover:border-[#0891B2]/30 hover:bg-[#0d1028] transition-all duration-200"
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center mb-4"
                  style={{ backgroundColor: `${f.color}18` }}
                >
                  <f.icon className="w-4.5 h-4.5" style={{ color: f.color }} />
                </div>
                <h3 className="text-white font-semibold text-sm mb-2">{f.title}</h3>
                <p className="text-slate-400 text-xs leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─────────────────────────────────────────────────── */}
      <section id="how" className="py-20 bg-[#060818] border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-[11px] uppercase tracking-widest text-[#0891B2] font-bold mb-3">How it works</p>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
              From report to recommendation in 5 minutes.
            </h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm">
              Our clinician-in-the-loop pipeline extracts, verifies, evaluates, and surfaces — fast.
            </p>
          </div>

          {/* Horizontal steps */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {steps.map((s, i) => (
              <motion.div
                key={s.n}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-[#0c0f24] border border-white/[0.07] rounded-xl p-5 relative"
              >
                {/* Connector line for desktop */}
                {i < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-8 -right-2 w-4 h-px bg-white/10 z-10" />
                )}
                <span className="text-[#0891B2] font-mono font-bold text-xs mb-3 block">{s.n}</span>
                <h4 className="text-white font-semibold text-sm mb-2">{s.title}</h4>
                <p className="text-slate-400 text-xs leading-relaxed">{s.body}</p>
              </motion.div>
            ))}
          </div>

          {/* Large image + overlay result card */}
          <motion.div
            className="mt-10 relative rounded-2xl overflow-hidden group"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <img
              src={SPLIT_IMG}
              alt="Clinical lab"
              className="w-full h-64 md:h-80 object-cover object-top brightness-50 group-hover:brightness-60 transition-all duration-700"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#07091C]/90 via-[#07091C]/60 to-transparent" />

            {/* Floating result card */}
            <div className="absolute left-6 top-1/2 -translate-y-1/2 bg-[#0c0f24]/95 border border-white/10 rounded-xl p-4 max-w-xs backdrop-blur-md">
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <p className="text-white font-semibold text-xs">Analysis Complete · 94%</p>
                  <p className="text-slate-400 text-[11px]">Luminal A · Stage II · ER+ / HER2−</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <Tag>Endocrine Therapy</Tag>
                <Tag>Anti-HER2 Spared</Tag>
                <Tag>Low Risk</Tag>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── Trust ─────────────────────────────────────────────────────────── */}
      <section id="trust" className="py-24 bg-[#07091C] border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
            {/* Left */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <p className="text-[11px] uppercase tracking-widest text-[#0891B2] font-bold mb-4">Trust & Compliance</p>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
                Designed for clinical environments.
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-7">
                OnCopilot augments, never overrides, physician judgment. All recommendations
                are traceable, logged, and audit-ready.
              </p>
              <div className="space-y-3">
                {trustItems.map((item) => (
                  <div key={item.label} className="flex items-center gap-3 text-sm text-slate-300">
                    <div className="w-7 h-7 rounded-lg bg-[#0891B2]/15 flex items-center justify-center shrink-0">
                      <item.icon className="w-3.5 h-3.5 text-[#0891B2]" />
                    </div>
                    {item.label}
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Right — rule card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-[#0c0f24] border border-white/[0.08] rounded-xl p-6"
            >
              <div className="flex items-center gap-3 mb-5 pb-4 border-b border-white/5">
                <div className="w-9 h-9 rounded-lg bg-[#0891B2]/15 flex items-center justify-center">
                  <Database className="w-4 h-4 text-[#0891B2]" />
                </div>
                <div>
                  <p className="text-white font-semibold text-sm">Clinical Rule Engine</p>
                  <p className="text-slate-400 text-xs">Rule 41 fired — ER+ / HER2−</p>
                </div>
              </div>
              <div className="space-y-2 mb-5">
                {ruleRows.map((r) => (
                  <div key={r.rule} className="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
                    <span className="text-slate-300 text-xs">{r.rule}</span>
                    <span className={cn(
                      "text-[10px] font-semibold px-2 py-0.5 rounded-full",
                      r.col === "emerald" ? "bg-emerald-500/15 text-emerald-400" : "bg-blue-500/15 text-blue-400"
                    )}>
                      {r.col === "emerald" ? "matched" : "safe"}
                    </span>
                  </div>
                ))}
              </div>
              <div className="bg-[#0891B2]/10 border border-[#0891B2]/20 rounded-lg px-4 py-3">
                <p className="font-bold text-white text-xs mb-1">Recommendation</p>
                <p className="text-slate-300 text-xs leading-relaxed">
                  Endocrine therapy (5–10 yrs). Consider CDK4/6 inhibitor — St. Gallen 2023.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────────────────────────── */}
      <section className="py-28 bg-gradient-to-b from-[#07091C] to-[#060818]">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-4 leading-tight">
            The clinical copilot that
            <br />
            <span className="text-[#0891B2]">never sleeps.</span>
          </h2>
          <p className="text-slate-400 text-sm mb-8 leading-relaxed">
            Join oncologists already using OnCopilot to cut analysis time, reduce errors,
            and build confidence in every treatment decision.
          </p>
          <Link href="/signup">
            <button className="group inline-flex items-center gap-2 h-12 px-8 rounded-full bg-[#0891B2] hover:bg-[#0680a0] text-white font-bold shadow-2xl shadow-[#0891B2]/25 text-sm transition-all">
              Request Early Access
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </Link>
          <p className="text-[11px] text-slate-500 mt-3">No payment required · HIPAA-aligned</p>
        </div>
      </section>

      {/* ─── Footer ───────────────────────────────────────────────────────── */}
      <footer className="bg-[#040611] border-t border-white/5 py-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-start gap-8">
          <div className="max-w-xs">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-md bg-[#0891B2] flex items-center justify-center">
                <Activity className="w-3 h-3 text-white" />
              </div>
              <span className="font-bold text-sm text-white">OnCopilot</span>
            </div>
            <p className="text-slate-500 text-xs leading-relaxed">
              Clinical decision support for breast cancer oncology. Assists, never replaces, physician judgment.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-8 text-xs">
            <div>
              <p className="text-white font-semibold mb-3">Platform</p>
              <ul className="space-y-1.5 text-slate-500">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#how" className="hover:text-white transition-colors">How it works</a></li>
                <li><a href="#trust" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
            <div>
              <p className="text-white font-semibold mb-3">Company</p>
              <ul className="space-y-1.5 text-slate-500">
                <li><Link href="#" className="hover:text-white transition-colors">About</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">Contact</Link></li>
                <li><Link href="#" className="hover:text-white transition-colors">Privacy</Link></li>
              </ul>
            </div>
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-6 mt-8 pt-6 border-t border-white/5 text-[10px] text-slate-600">
          © 2026 OnCopilot. DISCLAIMER: Decision support tool only. Treatment decisions remain the treating physician&apos;s sole responsibility.
        </div>
      </footer>

    </div>
  );
}
