import { ClinicalCase, User } from "@/types";

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const fallbackApiBaseUrl =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8001/api"
    : "https://capstone-app-hqi3.vercel.app/api";

const API_BASE_URL =
  configuredApiBaseUrl && configuredApiBaseUrl !== "/api"
    ? (configuredApiBaseUrl.endsWith("/api") ? configuredApiBaseUrl : `${configuredApiBaseUrl.replace(/\/$/, "")}/api`)
    : fallbackApiBaseUrl;
const API_BASE_URLS = [API_BASE_URL];

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
const requestJson = async (
  endpoint: string,
  options: RequestInit = {},
  withAuth = false
) => {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  for (const baseUrl of API_BASE_URLS) {
    let response: Response;
    try {
      response = await fetch(`${baseUrl}${endpoint}`, {
        ...options,
        headers,
      });
    } catch (error) {
      continue;
    }

    if (!response.ok) {
      if (withAuth && response.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("cancer-copilot-auth");
        window.location.href = "/login";
      }
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || errorData?.error || `API error ${response.status}`
      );
    }

    return response.json();
  }

  throw new Error(
    `Cannot reach the API at ${API_BASE_URL}${endpoint}. Make sure the backend proxy or server is reachable.`
  );
};

// ─── Fetch wrapper ────────────────────────────────────────────────────────────
const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) =>
  requestJson(endpoint, options, true);

// ─── Public (no-auth) fetch ───────────────────────────────────────────────────
// Used for endpoints that intentionally don't require authentication
const fetchPublic = async (endpoint: string, options: RequestInit = {}) =>
  requestJson(endpoint, options, false);

const fetchPublicOrAuth = async (
  endpoint: string,
  options: RequestInit = {},
  withAuth = false
) => (withAuth ? fetchWithAuth(endpoint, options) : fetchPublic(endpoint, options));

// ─── API surface ──────────────────────────────────────────────────────────────
export const api = {
  // Health
  health: () => fetchPublic("/health"),

  // Auth
  register: (data: any) => fetchPublic("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  login: (credentials: any) => fetchPublic("/auth/login", {
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
  }, withAuth = false) =>
    fetchPublicOrAuth("/analyse/instant", {
      method: "POST",
      body: JSON.stringify(payload),
    }, withAuth),
};
