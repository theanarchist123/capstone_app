import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(date));
}

export function formatRelativeTime(date: Date | string): string {
  const now = new Date();
  const d = new Date(date);
  const diff = now.getTime() - d.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return formatDate(date);
}

export function getSubtypeColor(subtype: string): string {
  const map: Record<string, string> = {
    "Luminal A": "#059669",
    "Luminal B": "#0891B2",
    "HER2-Enriched": "#D97706",
    "TNBC": "#E11D48",
    "Triple Negative": "#E11D48",
  };
  return map[subtype] || "#6B7280";
}

export function getSubtypeBg(subtype: string): string {
  const map: Record<string, string> = {
    "Luminal A": "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    "Luminal B": "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
    "HER2-Enriched": "bg-amber-500/15 text-amber-400 border-amber-500/30",
    "TNBC": "bg-rose-500/15 text-rose-400 border-rose-500/30",
    "Triple Negative": "bg-rose-500/15 text-rose-400 border-rose-500/30",
  };
  return map[subtype] || "bg-gray-500/15 text-gray-400 border-gray-500/30";
}

export function animateCounter(
  start: number,
  end: number,
  duration: number,
  callback: (value: number) => void
): void {
  const startTime = performance.now();
  const update = (currentTime: number) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    callback(Math.round(start + (end - start) * eased));
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}
