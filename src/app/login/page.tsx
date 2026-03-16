"use client"

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, ArrowRight, ArrowLeft } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store";
import { mockUser } from "@/lib/mock-data";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
        const res = await api.login({ email, password });
        if (res.success && res.data?.access_token) {
            // Save the real token attached to the mockUser interface format for the store
            const token = res.data.access_token;
            login({ ...mockUser, token } as any);
            router.push("/dashboard");
        }
    } catch (err: any) {
        console.error("Login failed:", err);
        setError(err.message || "Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Left split - Image & Overlay */}
      <div className="hidden lg:flex flex-col relative w-[55%] overflow-hidden bg-[#080D1A]">
        {/* Unsplash Image Base */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-40 mix-blend-luminosity"
          style={{ backgroundImage: `url('https://images.unsplash.com/photo-1579684385127-1ef15d508118?q=80&w=2680&auto=format&fit=crop')` }}
        />
        {/* Dark overlay gradients */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#080D1A] via-transparent to-[#080D1A]/80" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#080D1A] to-transparent/10" />
        
        {/* Floating Hexagons */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
           {[...Array(6)].map((_, i) => (
             <motion.div
               key={i}
               className="absolute w-32 h-32 border border-[#0891B2]/20 hexagon flex items-center justify-center opacity-30"
               animate={{
                 y: [Math.random() * 100, Math.random() * -100, Math.random() * 100],
                 rotate: [0, 180, 360],
               }}
               transition={{
                 duration: 15 + Math.random() * 10,
                 repeat: Infinity,
                 ease: "linear",
               }}
               style={{
                 left: `${Math.random() * 80}%`,
                 top: `${Math.random() * 80}%`,
               }}
             />
           ))}
        </div>

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
              "Precision oncology isn't just about data. It's about turning complex data into singular, actionable clarity."
            </h2>
            <div className="flex items-center gap-4">
               <div className="h-px bg-[#0891B2] w-12" />
               <p className="text-[#0891B2] font-semibold tracking-wider uppercase text-sm">OnCopilot Vision</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right split - Form */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center px-8 sm:px-16 xl:px-32 bg-background relative z-20">
         <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
         >
             <div className="mb-10 text-center lg:text-left">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Welcome back</h1>
                <p className="text-muted-foreground">Sign in to your clinical account</p>
             </div>

             <form onSubmit={handleLogin} className="space-y-6">
                 <Input 
                   type="email" 
                   label="Email Address"
                   value={email}
                   onChange={e => setEmail(e.target.value)}
                   required
                   placeholder="seed.doctor@oncopilot.dev"
                 />
                 
                 <Input 
                   type="password" 
                   label="Password"
                   value={password}
                   onChange={e => setPassword(e.target.value)}
                   required
                 />

                 {error && (
                     <div className="text-rose-500 text-sm font-semibold">{error}</div>
                 )}

                 <div className="flex items-center justify-between text-sm">
                    <label className="flex items-center gap-2 cursor-pointer text-muted-foreground">
                        <input type="checkbox" className="rounded border-border text-primary focus:ring-primary accent-primary" />
                        Remember me
                    </label>
                    <Link href="#" className="text-[#0891B2] font-medium hover:underline">Forgot password?</Link>
                 </div>

                 <Button type="submit" className="w-full group h-12 text-base" variant="shimmer">
                    Sign in <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                 </Button>

                 <div className="text-center mt-6 text-sm">
                    <span className="text-muted-foreground">Don't have an account? </span>
                    <Link href="/signup" className="text-[#0891B2] font-semibold hover:underline">Request access</Link>
                 </div>
             </form>
         </motion.div>
      </div>
    </div>
  );
}
