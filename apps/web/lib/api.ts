import type {
  AdminReportsResponse,
  AdminSettingsResponse,
  AdminSettingsUpdate,
  AuthSessionResponse,
  AuthUser,
  HistoryDetail,
  HistoryListItem,
  LoginRequest,
  RecommendRequest,
  RecommendResponse,
  RegisterRequest,
  RetrieveRequest,
  RetrieveResponse,
} from "@/lib/types";

const API_BASE_URL = "/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function resolveBrowserUrl(path: string) {
  if (typeof window === "undefined") {
    return path;
  }

  return new URL(path, window.location.origin).toString();
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(resolveBrowserUrl(`${API_BASE_URL}${path}`), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
    credentials: "include",
  });

  if (!response.ok) {
    const text = await response.text();
    let message = text || `Request failed: ${response.status}`;

    try {
      const payload = JSON.parse(text) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Fall through to raw text.
    }

    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export async function fetchRecommend(payload: RecommendRequest): Promise<RecommendResponse> {
  return apiRequest<RecommendResponse>("/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchSavedRecommendation(payload: RecommendRequest): Promise<RecommendResponse> {
  return apiRequest<RecommendResponse>("/me/recommendations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchRetrieve(payload: RetrieveRequest): Promise<RetrieveResponse> {
  return apiRequest<RetrieveResponse>("/retrieve", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchVehicleProfiles(limit = 24) {
  return apiRequest(`/vehicle-profiles?limit=${limit}`);
}

export async function fetchAdminReports(): Promise<AdminReportsResponse> {
  return apiRequest<AdminReportsResponse>("/admin/reports");
}

export async function registerUser(payload: RegisterRequest): Promise<AuthSessionResponse> {
  return apiRequest<AuthSessionResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginRequest): Promise<AuthSessionResponse> {
  return apiRequest<AuthSessionResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logoutUser(): Promise<void> {
  await apiRequest<{ ok: boolean }>("/auth/logout", {
    method: "POST",
  });
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}

export async function fetchHistoryList(): Promise<HistoryListItem[]> {
  return apiRequest<HistoryListItem[]>("/me/history");
}

export async function fetchHistoryDetail(historyId: number | string): Promise<HistoryDetail> {
  return apiRequest<HistoryDetail>(`/me/history/${historyId}`);
}

export async function fetchAdminSettings(): Promise<AdminSettingsResponse> {
  const response = await fetch(resolveBrowserUrl("/admin/settings/config"), {
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return (await response.json()) as AdminSettingsResponse;
}

export async function saveAdminSettings(payload: AdminSettingsUpdate): Promise<AdminSettingsResponse> {
  const response = await fetch(resolveBrowserUrl("/admin/settings/config"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return (await response.json()) as AdminSettingsResponse;
}
