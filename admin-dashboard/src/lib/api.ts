import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./tokenStorage";
import type {
  AuthResponse,
  Complaint,
  ComplaintStatus,
  MatchingWeights,
  NurseAdmin,
  NurseDocument,
  Payment,
  PaymentStatus,
  PlatformSettings,
  PlatformStats,
  Specialty,
  ServiceItem,
  UserAdmin,
  UserRole,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiRequestError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export class SessionExpiredError extends Error {}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

interface FetchOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  query?: Record<string, string | number | boolean | undefined>;
}

async function apiFetch<T>(path: string, options: FetchOptions = {}, isRetry = false): Promise<T> {
  const { method = "GET", body, auth = true, query } = options;

  let url = `${API_BASE}${path}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) params.set(key, String(value));
    }
    const qs = params.toString();
    if (qs) url += `?${qs}`;
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && !isRetry) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return apiFetch<T>(path, options, true);
    }
    clearTokens();
    throw new SessionExpiredError("Your session has expired. Please sign in again.");
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = data?.error?.message ?? "Something went wrong. Please try again.";
    const code = data?.error?.code ?? "UNKNOWN_ERROR";
    throw new ApiRequestError(res.status, code, message);
  }

  return data as T;
}

export const login = (email: string, password: string) =>
  apiFetch<AuthResponse>("/auth/login", { method: "POST", body: { email, password }, auth: false });

export const listUsers = (role?: UserRole) =>
  apiFetch<UserAdmin[]>("/admin/users", { query: { role, limit: 100 } });

export const deactivateUser = (userId: string, reason?: string) =>
  apiFetch<UserAdmin>(`/admin/users/${userId}/deactivate`, { method: "POST", body: { reason } });

export const activateUser = (userId: string) =>
  apiFetch<UserAdmin>(`/admin/users/${userId}/activate`, { method: "POST" });

export const listNursesAdmin = (params: { is_approved?: boolean; pending_verification?: boolean }) =>
  apiFetch<NurseAdmin[]>("/admin/nurses", { query: { ...params, limit: 100 } });

export const getNurse = (nurseId: string) => apiFetch<NurseAdmin>(`/nurses/${nurseId}`);

export const getNurseDocuments = (nurseId: string) =>
  apiFetch<NurseDocument[]>(`/admin/nurses/${nurseId}/documents`);

export const approveDocument = (nurseId: string, documentId: string) =>
  apiFetch<NurseDocument>(`/admin/nurses/${nurseId}/documents/${documentId}/approve`, { method: "POST" });

export const rejectDocument = (nurseId: string, documentId: string, reason: string) =>
  apiFetch<NurseDocument>(`/admin/nurses/${nurseId}/documents/${documentId}/reject`, {
    method: "POST",
    body: { reason },
  });

export const approveNurse = (nurseId: string) =>
  apiFetch(`/admin/nurses/${nurseId}/approve`, { method: "POST" });

export const suspendNurse = (nurseId: string, reason?: string) =>
  apiFetch(`/admin/nurses/${nurseId}/suspend`, { method: "POST", body: { reason } });

export const reactivateNurse = (nurseId: string) =>
  apiFetch(`/admin/nurses/${nurseId}/reactivate`, { method: "POST" });

export const listServicesPublic = () => apiFetch<ServiceItem[]>("/services", { auth: false });
export const listSpecialtiesPublic = () => apiFetch<Specialty[]>("/specialties", { auth: false });

// Admin variants include inactive items too (needed to reactivate them) —
// the public endpoints only ever return active ones, by design.
export const listServicesAdmin = () => apiFetch<ServiceItem[]>("/admin/services");
export const listSpecialtiesAdmin = () => apiFetch<Specialty[]>("/admin/specialties");

export const createService = (data: { name_en: string; name_ar: string; is_active: boolean }) =>
  apiFetch<ServiceItem>("/admin/services", { method: "POST", body: data });

export const updateService = (
  id: string,
  data: { name_en: string; name_ar: string; is_active: boolean }
) => apiFetch<ServiceItem>(`/admin/services/${id}`, { method: "PATCH", body: data });

export const createSpecialty = (data: { name_en: string; name_ar: string; is_active: boolean }) =>
  apiFetch<Specialty>("/admin/specialties", { method: "POST", body: data });

export const updateSpecialty = (
  id: string,
  data: { name_en: string; name_ar: string; is_active: boolean }
) => apiFetch<Specialty>(`/admin/specialties/${id}`, { method: "PATCH", body: data });

export const getMatchingWeights = () => apiFetch<MatchingWeights>("/admin/matching-weights");
export const updateMatchingWeights = (weights: MatchingWeights) =>
  apiFetch<MatchingWeights>("/admin/matching-weights", { method: "PATCH", body: weights });

export const getPlatformSettings = () => apiFetch<PlatformSettings>("/admin/settings");
export const updatePlatformSettings = (commission_percentage: number) =>
  apiFetch<PlatformSettings>("/admin/settings", { method: "PATCH", body: { commission_percentage } });

export const getStats = () => apiFetch<PlatformStats>("/admin/stats");

export const listPayments = (status?: PaymentStatus) =>
  apiFetch<Payment[]>("/admin/payments", { query: { status, limit: 100 } });

export const markPaymentPaid = (paymentId: string, payment_method: string, transaction_id?: string) =>
  apiFetch<Payment>(`/admin/payments/${paymentId}/mark-paid`, {
    method: "POST",
    body: { payment_method, transaction_id },
  });

export const listComplaintsAdmin = (status?: ComplaintStatus) =>
  apiFetch<Complaint[]>("/admin/complaints", { query: { status, limit: 100 } });

export const updateComplaintAdmin = (id: string, status: ComplaintStatus, admin_response?: string) =>
  apiFetch<Complaint>(`/admin/complaints/${id}`, { method: "PATCH", body: { status, admin_response } });
