import type { RecommendRequest } from "@/lib/types";
import { formattedInteger, parseIntegerInput } from "@/lib/form";

export type FindFilters = {
  budget: string;
  brand: string;
  bodyType: string;
  fuel: string;
};

export const defaultFindFilters: FindFilters = {
  budget: "",
  brand: "",
  bodyType: "",
  fuel: "",
};

export const findSelectOptions = {
  bodyType: ["", "hatchback", "sedan", "suv"],
  brand: ["", "Toyota", "Honda", "Mazda"],
  fuel: ["", "petrol", "hybrid"],
};

function normalizeNumberForUrl(value: string): string {
  const parsed = parseIntegerInput(value);
  return parsed === undefined ? "" : String(parsed);
}

export function normalizeFindFilters(filters: FindFilters): FindFilters {
  return {
    budget: normalizeNumberForUrl(filters.budget),
    brand: filters.brand.trim(),
    bodyType: filters.bodyType.trim().toLowerCase(),
    fuel: filters.fuel.trim().toLowerCase(),
  };
}

type SearchParamsLike = {
  get(name: string): string | null;
};

export function readFindFilters(searchParams: SearchParamsLike): FindFilters {
  return {
    budget: searchParams.get("budget") ?? "",
    brand: searchParams.get("brand") ?? "",
    bodyType: searchParams.get("bodyType") ?? "",
    fuel: searchParams.get("fuel") ?? "",
  };
}

export function toFindSearchParams(filters: FindFilters): URLSearchParams {
  const normalized = normalizeFindFilters(filters);
  const params = new URLSearchParams();

  if (normalized.budget) params.set("budget", normalized.budget);
  if (normalized.brand) params.set("brand", normalized.brand);
  if (normalized.bodyType) params.set("bodyType", normalized.bodyType);
  if (normalized.fuel) params.set("fuel", normalized.fuel);

  return params;
}

export function buildPrompt(query: string, filters: FindFilters): string {
  const parsedBudget = parseIntegerInput(filters.budget);

  const additions = [
    parsedBudget !== undefined ? `Budget up to $${formattedInteger(parsedBudget)}.` : null,
    filters.bodyType ? `Body type: ${filters.bodyType}.` : null,
    filters.brand ? `Preferred brand: ${filters.brand}.` : null,
    filters.fuel ? `Fuel preference: ${filters.fuel}.` : null,
  ].filter(Boolean);

  return [query.trim(), ...additions].join(" ").trim();
}

export function toRecommendRequest(query: string, filters: FindFilters, selectedProfileIds: string[]): RecommendRequest {
  return {
    query: buildPrompt(query, filters),
    selected_profile_ids: selectedProfileIds,
  };
}

export function hasAnyFilter(filters: FindFilters): boolean {
  return Boolean(filters.budget || filters.brand || filters.bodyType || filters.fuel);
}
