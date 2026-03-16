import { ClinicalCase, User } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Helper to get auth token
export const getAuthToken = () => {
  // We'll read the token right from the auth store or local storage later
  // For now, let's just make the request raw or grab it if available
  const authStateStr = localStorage.getItem("cancer-copilot-auth");
  if (authStateStr) {
    try {
      const authState = JSON.parse(authStateStr);
      // Depending on how login was implemented, the token might be here
      // Let's assume there's an access_token for now if we add one later
      return authState?.state?.user?.token || ""; 
    } catch {
      return "";
    }
  }
  return "";
};

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
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || errorData?.error || `API error: ${response.status}`);
  }

  return response.json();
};

export const api = {
  // Auth
  login: (credentials: any) => fetchWithAuth("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  }),
  
  // Cases
  getCases: () => fetchWithAuth("/cases"),
  getCase: (id: string) => fetchWithAuth(`/cases/${id}`),
  createCase: (data: any) => fetchWithAuth("/cases", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  updateCase: (id: string, data: any) => fetchWithAuth(`/cases/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  }),

  // Clinical Data
  saveClinicalData: (caseId: string, data: any) => fetchWithAuth(`/cases/${caseId}/clinical`, {
    method: "POST",
    body: JSON.stringify(data),
  }),

  // Analysis
  runAnalysis: (caseId: string) => fetchWithAuth(`/cases/${caseId}/analyse`, {
    method: "POST",
  }),
  
  simulateAnalysis: (caseId: string, overrides: any) => fetchWithAuth(`/cases/${caseId}/analyse/simulate`, {
    method: "POST",
    body: JSON.stringify({ overrides }),
  }),
};
