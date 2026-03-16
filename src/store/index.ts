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
      set({ cases: res.data || [] });
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
