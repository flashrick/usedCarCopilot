import type { AIProviderId } from "@/lib/types";

export const recommendationProviders: Array<{
  id: AIProviderId;
  defaultModel: string;
  supportsApiKey: boolean;
  supportsBaseUrl: boolean;
  supportsTimeout: boolean;
}> = [
  {
    id: "deterministic",
    defaultModel: "deterministic_ranker_with_citations",
    supportsApiKey: false,
    supportsBaseUrl: false,
    supportsTimeout: false,
  },
  {
    id: "openai",
    defaultModel: "gpt-5-mini",
    supportsApiKey: true,
    supportsBaseUrl: true,
    supportsTimeout: true,
  },
  {
    id: "deepseek",
    defaultModel: "deepseek-chat",
    supportsApiKey: true,
    supportsBaseUrl: true,
    supportsTimeout: false,
  },
  {
    id: "qwen",
    defaultModel: "qwen-plus",
    supportsApiKey: true,
    supportsBaseUrl: true,
    supportsTimeout: false,
  },
  {
    id: "kimi",
    defaultModel: "kimi-k2.6",
    supportsApiKey: true,
    supportsBaseUrl: true,
    supportsTimeout: false,
  },
];

export function isProviderId(value: string): value is AIProviderId {
  return recommendationProviders.some((provider) => provider.id === value);
}

export function providerDefaultModel(providerId: AIProviderId): string {
  return recommendationProviders.find((provider) => provider.id === providerId)?.defaultModel ?? "gpt-5-mini";
}
