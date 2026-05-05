import type { Market } from "@/lib/types";

export const pendingRecommendationStorageKey = "used-car-copilot-pending-recommendation";

export type PendingRecommendation = {
  query: string;
  market: Market;
  selectedProfileIds: string[];
};

export function savePendingRecommendation(payload: PendingRecommendation) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(pendingRecommendationStorageKey, JSON.stringify(payload));
}

export function readPendingRecommendation(): PendingRecommendation | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawValue = window.sessionStorage.getItem(pendingRecommendationStorageKey);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as PendingRecommendation;
    if (!parsed.query || (parsed.market !== "US" && parsed.market !== "CN") || !Array.isArray(parsed.selectedProfileIds)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function clearPendingRecommendation() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(pendingRecommendationStorageKey);
}

export function buildResumeRecommendationPath(query: string, market: Market): string {
  return `/find/query?market=${encodeURIComponent(market)}&query=${encodeURIComponent(query)}&resumeRecommendation=1`;
}
