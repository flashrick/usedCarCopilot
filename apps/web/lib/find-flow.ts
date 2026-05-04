import type { RecommendRequest } from "@/lib/types";
import { formattedInteger, parseIntegerInput } from "@/lib/form";

export type FindFilters = {
  budget: string;
  location: string;
  brand: string;
  bodyType: string;
  fuel: string;
  mileage: string;
};

export const defaultFindFilters: FindFilters = {
  budget: "",
  location: "",
  brand: "",
  bodyType: "",
  fuel: "",
  mileage: "",
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
    location: filters.location.trim(),
    brand: filters.brand.trim(),
    bodyType: filters.bodyType.trim().toLowerCase(),
    fuel: filters.fuel.trim().toLowerCase(),
    mileage: normalizeNumberForUrl(filters.mileage),
  };
}

type SearchParamsLike = {
  get(name: string): string | null;
};

export function readFindFilters(searchParams: SearchParamsLike): FindFilters {
  return {
    budget: searchParams.get("budget") ?? "",
    location: searchParams.get("location") ?? "",
    brand: searchParams.get("brand") ?? "",
    bodyType: searchParams.get("bodyType") ?? "",
    fuel: searchParams.get("fuel") ?? "",
    mileage: searchParams.get("mileage") ?? "",
  };
}

export function toFindSearchParams(filters: FindFilters): URLSearchParams {
  const normalized = normalizeFindFilters(filters);
  const params = new URLSearchParams();

  if (normalized.budget) params.set("budget", normalized.budget);
  if (normalized.location) params.set("location", normalized.location);
  if (normalized.brand) params.set("brand", normalized.brand);
  if (normalized.bodyType) params.set("bodyType", normalized.bodyType);
  if (normalized.fuel) params.set("fuel", normalized.fuel);
  if (normalized.mileage) params.set("mileage", normalized.mileage);

  return params;
}

export function buildPrompt(query: string, filters: FindFilters): string {
  const parsedBudget = parseIntegerInput(filters.budget);
  const parsedMileage = parseIntegerInput(filters.mileage);

  const additions = [
    parsedBudget !== undefined ? `Budget up to $${formattedInteger(parsedBudget)}.` : null,
    filters.location ? `Location: ${filters.location}.` : null,
    filters.bodyType ? `Body type: ${filters.bodyType}.` : null,
    filters.brand ? `Preferred brand: ${filters.brand}.` : null,
    filters.fuel ? `Fuel preference: ${filters.fuel}.` : null,
    parsedMileage !== undefined ? `Mileage preference: under ${formattedInteger(parsedMileage)} km.` : null,
  ].filter(Boolean);

  return [query.trim(), ...additions].join(" ").trim();
}

export function toRecommendRequest(query: string, filters: FindFilters, limit: number): RecommendRequest {
  return {
    query: buildPrompt(query, filters),
    max_price: parseIntegerInput(filters.budget),
    max_mileage: parseIntegerInput(filters.mileage),
    brand: filters.brand || undefined,
    body_type: filters.bodyType || undefined,
    fuel_type: filters.fuel || undefined,
    location: filters.location || undefined,
    limit,
  };
}

export function hasAnyFilter(filters: FindFilters): boolean {
  return Boolean(
    filters.budget || filters.location || filters.brand || filters.bodyType || filters.fuel || filters.mileage,
  );
}
