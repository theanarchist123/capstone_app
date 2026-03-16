"use client"

import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, ArrowRight, ArrowLeft, Stethoscope, UserRound } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [role, setRole] = useState<"doctor" | "patient" | null>(null);

  const handleNext = () => {
    if (role) setStep(2);
  };

  const handleBack = () => {
    setStep(1);
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Left split - Image & Overlay */}
      <div className="hidden lg:flex flex-col relative w-[55%] overflow-hidden bg-[#080D1A]">
        {/* Unsplash Image Base */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-40 mix-blend-luminosity"
          style={{ backgroundImage: `url('https://images.unsplash.com/photo-1581093588401-fbb62a02f120?q=80&w=2680&auto=format&fit=crop')` }}
        />
        {/* Dark overlay gradients */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#080D1A] via-transparent to-[#080D1A]/80" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#080D1A] to-transparent/10" />
        
        {/* Content */}
        <div className="relative z-10 p-12 flex flex-col h-full justify-between">
          <Link href="/" className="flex items-center gap-2 w-fit group">
            <div className="w-10 h-10 rounded-xl bg-[#0F3460] flex items-center justify-center group-hover:bg-[#0891B2] transition-colors shadow-lg">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-2xl tracking-tight text-white">On<span className="text-[#0891B2]">Copilot</span></span>
          </Link>

          <div className="max-w-xl">
            <h2 className="text-4xl font-bold text-white mb-6 leading-tight select-none">
              "Join the network of oncologists elevating the standard of precision care globally."
            </h2>
            <div className="flex items-center gap-4">
               <div className="h-px bg-[#0891B2] w-12" />
               <p className="text-[#0891B2] font-semibold tracking-wider uppercase text-sm">Empowering Clinicians</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right split - Form */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center px-8 sm:px-16 xl:px-32 bg-background relative z-20 overflow-hidden">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.4 }}
              className="w-full max-w-md mx-auto"
            >
              <div className="mb-10 text-center lg:text-left">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Create an account</h1>
                <p className="text-muted-foreground">Select your profile type to configure your workspace.</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-8">
                {/* Doctor Card */}
                <motion.div
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setRole("doctor")}
                  className={`relative p-6 rounded-2xl border-2 cursor-pointer transition-colors ${role === "doctor" ? "border-[#0891B2] bg-[#0891B2]/5" : "border-border hover:border-muted hover:bg-muted/50"}`}
                >
                  {role === "doctor" && <div className="absolute top-3 right-3 w-3 h-3 rounded-full bg-[#0891B2]" />}
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-colors ${role === "doctor" ? "bg-[#0891B2]" : "bg-muted"}`}>
                    <Stethoscope className={`w-6 h-6 ${role === "doctor" ? "text-white" : "text-muted-foreground"}`} />
                  </div>
                  <h3 className="text-lg font-bold mb-1">Doctor</h3>
                  <p className="text-xs text-muted-foreground">Manage cases, view recommendations</p>
                </motion.div>

                {/* Patient Card */}
                <motion.div
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setRole("patient")}
                  className={`relative p-6 rounded-2xl border-2 cursor-pointer transition-colors ${role === "patient" ? "border-[#0891B2] bg-[#0891B2]/5" : "border-border hover:border-muted hover:bg-muted/50"}`}
                >
                  {role === "patient" && <div className="absolute top-3 right-3 w-3 h-3 rounded-full bg-[#0891B2]" />}
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-colors ${role === "patient" ? "bg-[#0891B2]" : "bg-muted"}`}>
                    <UserRound className={`w-6 h-6 ${role === "patient" ? "text-white" : "text-muted-foreground"}`} />
                  </div>
                  <h3 className="text-lg font-bold mb-1">Patient</h3>
                  <p className="text-xs text-muted-foreground">View reports and second opinions</p>
                </motion.div>
              </div>

              <Button 
                onClick={handleNext} 
                disabled={!role} 
                className="w-full group h-12 text-base" 
                variant="shimmer"
              >
                Continue Setup <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform inline" />
              </Button>

              <div className="text-center mt-6 text-sm">
                <span className="text-muted-foreground">Already have an account? </span>
                <Link href="/login" className="text-[#0891B2] font-semibold hover:underline">Sign in</Link>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.4 }}
              className="w-full max-w-md mx-auto"
            >
              <button onClick={handleBack} className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-8 transition-colors">
                <ArrowLeft className="w-4 h-4" /> Back to role selection
              </button>

              <div className="mb-8 text-center lg:text-left">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Complete Profile</h1>
                <p className="text-muted-foreground">Let's set up your {role} credentials.</p>
              </div>

              <form className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <Input type="text" label="First Name" required />
                  <Input type="text" label="Last Name" required />
                </div>
                
                <Input type="email" label="Email Address" required />
                
                {role === "doctor" && (
                   <Input type="text" label="Hospital / Affiliation" required />
                )}

                <Input type="password" label="Create Password" required />

                <div className="flex items-center text-sm mb-6">
                  <label className="flex items-start gap-3 cursor-pointer text-muted-foreground leading-snug">
                    <input type="checkbox" required className="mt-1 rounded border-border text-primary focus:ring-primary accent-[#0891B2]" />
                    <span>I agree to the <Link href="#" className="text-[#0891B2] hover:underline">Terms of Service</Link> and <Link href="#" className="text-[#0891B2] hover:underline">Privacy Policy</Link></span>
                  </label>
                </div>

                <Link href="/dashboard" className="block w-full">
                  <Button type="button" className="w-full h-12 text-base" variant="teal">
                    Create Account
                  </Button>
                </Link>
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
