import type { RecommendRequest, RecommendResponse, RetrieveRequest, RetrieveResponse } from "@/lib/types";

const API_BASE_URL = "/api";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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

export async function fetchListings(limit = 24) {
  return apiRequest(`/listings?limit=${limit}`);
}
