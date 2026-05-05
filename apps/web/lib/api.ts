import type {
  AdminReportsResponse,
  AdminSettingsResponse,
  AdminSettingsUpdate,
  RecommendRequest,
  RecommendResponse,
  RetrieveRequest,
  RetrieveResponse,
} from "@/lib/types";

const API_BASE_URL = "/api";

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
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchRecommend(payload: RecommendRequest): Promise<RecommendResponse> {
  return apiRequest<RecommendResponse>("/recommend", {
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
