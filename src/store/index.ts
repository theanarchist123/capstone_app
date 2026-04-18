import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, ClinicalCase, Notification } from "@/types";
import { api } from "@/lib/api";

// ─── Auth Store ──────────────────────────────────────────────────────────────

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: (user) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, isAuthenticated: false }),
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: "cancer-copilot-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// ─── Cases Store ─────────────────────────────────────────────────────────────

interface CasesState {
  cases: ClinicalCase[];
  currentCase: ClinicalCase | null;
  isLoading: boolean;
  setCases: (cases: ClinicalCase[]) => void;
  setCurrentCase: (c: ClinicalCase | null) => void;
  addCase: (c: ClinicalCase) => void;
  updateCase: (id: string, updates: Partial<ClinicalCase>) => Promise<void> | void;
  setLoading: (loading: boolean) => void;
  fetchCases: () => Promise<void>;
}

export const useCasesStore = create<CasesState>()((set) => ({
  cases: [],
  currentCase: null,
  isLoading: false,
  setCases: (cases) => set({ cases }),
  setCurrentCase: (currentCase) => set({ currentCase }),
  
  // Async thunk alternatives
  fetchCases: async () => {
    set({ isLoading: true });
    try {
      const res = await api.getCases();
      const mappedCases = (res.data || []).map((c: any) => {
        // Find latest non-simulation result
        const latestResult = (c.results || []).sort((a: any, b: any) => b.version - a.version)[0];
        
        return {
          ...c,
          id: c.id,
          patientName: c.patient_name || c.patientName || "Unknown Patient",
          patientAge: c.patient_age || c.patientAge || 0,
          patientSex: c.patient_sex || c.patientSex || "Female",
          status: (c.status || "Pending Review").replace(/_/g, " ").replace(/\b\w/g, (char: string) => char.toUpperCase()),
          subtype: latestResult?.molecular_subtype || c.subtype || "Unknown",
          createdAt: c.created_at || c.createdAt || new Date().toISOString(),
          updatedAt: c.updated_at || c.updatedAt || new Date().toISOString(),
          doctorId: c.doctor_id || c.doctorId,
          tumour: c.tumour || { 
            stage: c.clinical_data?.stage || "Unknown", 
            grade: c.clinical_data?.grade || 2 
          },
          biomarkers: c.biomarkers || {
            er: c.clinical_data?.er_status || "Unknown",
            pr: c.clinical_data?.pr_status || "Unknown",
            her2: c.clinical_data?.her2_status || "Unknown",
            ki67: c.clinical_data?.ki67_percent,
            pdl1: c.clinical_data?.pdl1_status || "Unknown",
            brca1: c.clinical_data?.brca1_status || "Unknown",
            brca2: c.clinical_data?.brca2_status || "Unknown",
            pik3ca: c.clinical_data?.pik3ca_status || "Unknown",
            cyclinD1: c.clinical_data?.cyclin_d1 || "Unknown",
            tp53: c.clinical_data?.tp53_status || "Unknown",
            top2a: c.clinical_data?.top2a || "Unknown",
            bcl2: c.clinical_data?.bcl2 || "Unknown",
            tils: c.clinical_data?.tils_percent,
            oncotypeDX: c.clinical_data?.oncotype_dx_score,
            mammaPrint: c.clinical_data?.mammaprint || "Unknown",
            pam50: c.clinical_data?.pam50 || "Unknown",
          },
          healthProfile: c.healthProfile || {
            lvef: c.clinical_data?.lvef_percent,
            menopausalStatus: c.clinical_data?.menopausal_status || "Unknown",
            performanceScore: c.clinical_data?.ecog_score,
            comorbidities: c.clinical_data?.comorbidities ? Object.keys(c.clinical_data.comorbidities) : [],
            medications: c.clinical_data?.medications ? [c.clinical_data.medications] : [],
            allergies: c.clinical_data?.allergies ? [c.clinical_data.allergies] : [],
          },
          recommendations: latestResult?.recommendations ? latestResult.recommendations.map((r: any, idx: number) => ({
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
          })) : undefined,
          safetyAlerts: latestResult?.alerts ? latestResult.alerts.map((a: any, idx: number) => ({
              id: `alert-${idx}`,
              triggerSource: a.contraindication_type || a.source || "System Alert",
              affectedTreatment: a.affected_drug || "Protocol",
              description: a.reason || a.description || "Safety alert triggered.",
              recommendedAction: a.action || a.recommendation || "Review required."
          })) : undefined,
          versions: (c.results || []).map((v: any) => ({
              id: `v${v.version}`,
              version: v.version,
              createdAt: v.created_at || c.created_at,
              doctorName: "AI Pipeline",
              changeSummary: `Molecular classification: ${v.molecular_subtype} (Conf: ${Math.round((v.subtype_confidence || 0) * 100)}%)`,
              snapshot: {}
          }))
        };
      });
      set({ cases: mappedCases });
    } catch (e) {
      console.error("Failed to fetch cases:", e);
    } finally {
      set({ isLoading: false });
    }
  },
  
  addCase: async (c) => {
    // For local immediate update
    set((s) => ({ cases: [c, ...s.cases] }));
    try {
      // Background sync
      await api.createCase(c);
    } catch(e) {
      console.error("Failed to save case:", e);
    }
  },
  
  updateCase: async (id, updates) => {
    set((s) => ({
      cases: s.cases.map((c) => (c.id === id ? { ...c, ...updates } : c)),
      currentCase: s.currentCase?.id === id ? { ...s.currentCase, ...updates } : s.currentCase,
    }));
    try {
      await api.updateCase(id, updates);
    } catch(e) {
      console.error("Failed to update case:", e);
    }
  },
  setLoading: (isLoading) => set({ isLoading }),
}));

// ─── Notifications Store ─────────────────────────────────────────────────────

interface NotificationsState {
  notifications: Notification[];
  unreadCount: number;
  setNotifications: (n: Notification[]) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
}

export const useNotificationsStore = create<NotificationsState>()((set) => ({
  notifications: [],
  unreadCount: 0,
  setNotifications: (notifications) =>
    set({ notifications, unreadCount: notifications.filter((n) => !n.isRead).length }),
  markRead: (id) =>
    set((s) => {
      const updated = s.notifications.map((n) => (n.id === id ? { ...n, isRead: true } : n));
      return { notifications: updated, unreadCount: updated.filter((n) => !n.isRead).length };
    }),
  markAllRead: () =>
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, isRead: true })),
      unreadCount: 0,
    })),
}));

// ─── UI Store ────────────────────────────────────────────────────────────────

interface UIState {
  sidebarCollapsed: boolean;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      sidebarOpen: true,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
    }),
    { name: "cancer-copilot-ui" }
  )
);

// ─── Instant Analysis Result Store ───────────────────────────────────────────
// Holds the result of the onboarding form submission so the results page
// can display it without hitting the DB.

export interface AnalysisResult {
  molecular_subtype: string;
  subtype_confidence: number;
  recommendations: Array<Record<string, any>>;
  alerts: Array<Record<string, any>>;
  rule_trace: Array<Record<string, any>>;
  ai_reasoning: {
    subtype_rationale?: string;
    treatment_rationale?: string;
    key_biomarkers?: string[];
    clinical_considerations?: string;
    prognosis_summary?: string;
    confidence_explanation?: string;
  };
  patient_name?: string;
  patient_age?: number;
  analyzed_at: string;
}

interface AnalysisResultState {
  result: AnalysisResult | null;
  setResult: (r: AnalysisResult) => void;
  clearResult: () => void;
}

export const useAnalysisResultStore = create<AnalysisResultState>()(
  persist(
    (set) => ({
      result: null,
      setResult: (result) => set({ result }),
      clearResult: () => set({ result: null }),
    }),
    { name: "cancer-copilot-analysis-result" }
  )
);
