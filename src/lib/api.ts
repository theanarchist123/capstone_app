import { ClinicalCase, User } from "@/types";

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const API_BASE_URL =
  configuredApiBaseUrl &&
  !configuredApiBaseUrl.includes("localhost:8000") &&
  !configuredApiBaseUrl.includes("127.0.0.1:8000")
    ? configuredApiBaseUrl
    : "http://localhost:8001/api";

// ─── Auth token reader ────────────────────────────────────────────────────────
// Reads from Zustand-persisted localStorage. Tries both 'token' and
// 'access_token' field names to handle any login implementation variation.
export const getAuthToken = (): string => {
  if (typeof window === "undefined") return "";
  const raw = localStorage.getItem("cancer-copilot-auth");
  if (!raw) return "";
  try {
    const state = JSON.parse(raw)?.state?.user;
    // Login page stores: { ...mockUser, token: access_token }
    const tok = state?.token || state?.access_token || "";
    if (tok) return tok;
  } catch {
    // ignore parse errors
  }
  return "";
};

// ─── Fetch wrapper ────────────────────────────────────────────────────────────
const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("cancer-copilot-auth");
        window.location.href = "/login";
      }
    }
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || errorData?.error || `API error ${response.status}`
    );
  }

  return response.json();
};

// ─── Public (no-auth) fetch ───────────────────────────────────────────────────
// Used for endpoints that intentionally don't require authentication
const fetchPublic = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken(); // still attach if available, but doesn't fail if absent
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || errorData?.error || `API error ${response.status}`
    );
  }

  return response.json();
};

// ─── API surface ──────────────────────────────────────────────────────────────
export const api = {
  // Health
  health: () => fetchPublic("/health"),

  // Auth
  register: (data: any) => fetchWithAuth("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  login: (credentials: any) => fetchWithAuth("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  }),

  // Cases
  getCases: () => fetchWithAuth("/cases/"),
  getCase: (id: string) => fetchWithAuth(`/cases/${id}`),
  createCase: (data: any) => fetchWithAuth("/cases/", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  updateCase: (id: string, data: any) => fetchWithAuth(`/cases/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  }),

  // Clinical Data
  saveClinicalData: (caseId: string, data: any) =>
    fetchWithAuth(`/cases/${caseId}/clinical`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Analysis
  runAnalysis: (caseId: string) =>
    fetchWithAuth(`/cases/${caseId}/analyse`, { method: "POST" }),

  simulateAnalysis: (caseId: string, overrides: any) =>
    fetchWithAuth(`/cases/${caseId}/analyse/simulate`, {
      method: "POST",
      body: JSON.stringify({ overrides }),
    }),

  // ─── Instant Analysis (stateless — public endpoint, no auth required) ──────
  // Auth is optional on the backend so this never 401s even after token expiry.
  instantAnalysis: (payload: {
    patient_name?: string;
    patient_age?: number;
    save_case?: boolean;
    clinical_data: Record<string, any>;
  }) =>
    fetchPublic("/analyse/instant", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
