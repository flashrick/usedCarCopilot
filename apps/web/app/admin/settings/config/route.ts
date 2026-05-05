import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import { isProviderId, providerDefaultModel } from "@/lib/admin-settings";
import type { AdminSettingsResponse, AdminSettingsUpdate, AIProviderId } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ProviderKey = keyof AdminSettingsResponse["providers"];

type EnvMap = Map<string, string>;

const defaultSettings = {
  recommendationProvider: "deterministic" as AIProviderId,
  recommendationModel: "deterministic_ranker_with_citations",
  providers: {
    openai: {
      apiKeyConfigured: false,
      baseUrl: "https://api.openai.com/v1",
      timeoutSeconds: "30",
    },
    deepseek: {
      apiKeyConfigured: false,
      baseUrl: "https://api.deepseek.com",
    },
    qwen: {
      apiKeyConfigured: false,
      baseUrl: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    },
    kimi: {
      apiKeyConfigured: false,
      baseUrl: "https://api.moonshot.ai/v1",
    },
  },
};

const providerEnvKeys: Record<ProviderKey, { apiKey: string; baseUrl: string; timeoutSeconds?: string }> = {
  openai: {
    apiKey: "OPENAI_API_KEY",
    baseUrl: "OPENAI_BASE_URL",
    timeoutSeconds: "OPENAI_TIMEOUT_SECONDS",
  },
  deepseek: {
    apiKey: "DEEPSEEK_API_KEY",
    baseUrl: "DEEPSEEK_BASE_URL",
  },
  qwen: {
    apiKey: "QWEN_API_KEY",
    baseUrl: "QWEN_BASE_URL",
  },
  kimi: {
    apiKey: "KIMI_API_KEY",
    baseUrl: "KIMI_BASE_URL",
  },
};

async function fileExists(filePath: string) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function resolveEnvFilePath() {
  let currentDir = process.cwd();

  for (let depth = 0; depth < 5; depth += 1) {
    const candidate = path.join(currentDir, ".env");
    if (await fileExists(candidate)) {
      return candidate;
    }

    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      break;
    }
    currentDir = parentDir;
  }

  return path.resolve(process.cwd(), ".env");
}

async function readEnvFile(envFilePath: string) {
  try {
    return await fs.readFile(envFilePath, "utf-8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return "";
    }
    throw error;
  }
}

function parseEnvFile(content: string): EnvMap {
  const values = new Map<string, string>();

  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    const value = trimmed.slice(separatorIndex + 1).trim().replace(/^['"]|['"]$/g, "");
    if (key) {
      values.set(key, value);
    }
  }

  return values;
}

function buildSettings(envFilePath: string, values: EnvMap): AdminSettingsResponse {
  const providerValue = values.get("RECOMMENDATION_PROVIDER") ?? defaultSettings.recommendationProvider;
  const recommendationProvider = isProviderId(providerValue) ? providerValue : defaultSettings.recommendationProvider;

  return {
    envFilePath,
    recommendationProvider,
    recommendationModel:
      values.get("RECOMMENDATION_MODEL") ?? providerDefaultModel(recommendationProvider) ?? defaultSettings.recommendationModel,
    providers: {
      openai: {
        apiKeyConfigured: Boolean(values.get("OPENAI_API_KEY")),
        baseUrl: values.get("OPENAI_BASE_URL") ?? defaultSettings.providers.openai.baseUrl,
        timeoutSeconds: values.get("OPENAI_TIMEOUT_SECONDS") ?? defaultSettings.providers.openai.timeoutSeconds,
      },
      deepseek: {
        apiKeyConfigured: Boolean(values.get("DEEPSEEK_API_KEY") || values.get("AI_API_KEY")),
        baseUrl: values.get("DEEPSEEK_BASE_URL") ?? defaultSettings.providers.deepseek.baseUrl,
      },
      qwen: {
        apiKeyConfigured: Boolean(values.get("QWEN_API_KEY") || values.get("DASHSCOPE_API_KEY") || values.get("AI_API_KEY")),
        baseUrl: values.get("QWEN_BASE_URL") ?? defaultSettings.providers.qwen.baseUrl,
      },
      kimi: {
        apiKeyConfigured: Boolean(values.get("KIMI_API_KEY") || values.get("MOONSHOT_API_KEY") || values.get("AI_API_KEY")),
        baseUrl: values.get("KIMI_BASE_URL") ?? defaultSettings.providers.kimi.baseUrl,
      },
    },
  };
}

function normalizeTimeoutSeconds(rawValue: string | undefined) {
  const value = rawValue?.trim();
  if (!value) {
    return defaultSettings.providers.openai.timeoutSeconds;
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error("OPENAI timeout must be a positive number.");
  }

  return String(parsed);
}

function normalizePayload(body: unknown): AdminSettingsUpdate {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid settings payload.");
  }

  const payload = body as Partial<AdminSettingsUpdate>;
  if (!payload.recommendationProvider || !isProviderId(payload.recommendationProvider)) {
    throw new Error("Unsupported recommendation provider.");
  }

  if (!payload.providers?.openai || !payload.providers.deepseek || !payload.providers.qwen || !payload.providers.kimi) {
    throw new Error("Provider settings are incomplete.");
  }

  return {
    recommendationProvider: payload.recommendationProvider,
    recommendationModel: payload.recommendationModel?.trim() || providerDefaultModel(payload.recommendationProvider),
    providers: {
      openai: {
        apiKey: payload.providers.openai.apiKey?.trim(),
        baseUrl: payload.providers.openai.baseUrl?.trim() || defaultSettings.providers.openai.baseUrl,
        timeoutSeconds: normalizeTimeoutSeconds(payload.providers.openai.timeoutSeconds),
      },
      deepseek: {
        apiKey: payload.providers.deepseek.apiKey?.trim(),
        baseUrl: payload.providers.deepseek.baseUrl?.trim() || defaultSettings.providers.deepseek.baseUrl,
      },
      qwen: {
        apiKey: payload.providers.qwen.apiKey?.trim(),
        baseUrl: payload.providers.qwen.baseUrl?.trim() || defaultSettings.providers.qwen.baseUrl,
      },
      kimi: {
        apiKey: payload.providers.kimi.apiKey?.trim(),
        baseUrl: payload.providers.kimi.baseUrl?.trim() || defaultSettings.providers.kimi.baseUrl,
      },
    },
  };
}

function upsertEnvLine(lines: string[], key: string, value: string) {
  const entry = `${key}=${value}`;
  const lineIndex = lines.findIndex((line) => line.startsWith(`${key}=`));

  if (lineIndex >= 0) {
    lines[lineIndex] = entry;
    return;
  }

  lines.push(entry);
}

async function writeSettings(envFilePath: string, payload: AdminSettingsUpdate) {
  const currentContent = await readEnvFile(envFilePath);
  const lines = currentContent ? currentContent.split(/\r?\n/) : [];

  upsertEnvLine(lines, "RECOMMENDATION_PROVIDER", payload.recommendationProvider);
  upsertEnvLine(lines, "RECOMMENDATION_MODEL", payload.recommendationModel);

  (Object.entries(providerEnvKeys) as Array<[ProviderKey, (typeof providerEnvKeys)[ProviderKey]]>).forEach(([providerKey, envKeys]) => {
    const provider = payload.providers[providerKey];
    if (provider.apiKey) {
      upsertEnvLine(lines, envKeys.apiKey, provider.apiKey);
    }
    upsertEnvLine(lines, envKeys.baseUrl, provider.baseUrl);
    if (envKeys.timeoutSeconds && provider.timeoutSeconds) {
      upsertEnvLine(lines, envKeys.timeoutSeconds, provider.timeoutSeconds);
    }
  });

  const normalizedContent = `${lines.filter((line, index, allLines) => index < allLines.length - 1 || line !== "").join("\n")}\n`;
  await fs.writeFile(envFilePath, normalizedContent, "utf-8");
}

export async function GET() {
  const envFilePath = await resolveEnvFilePath();
  const content = await readEnvFile(envFilePath);
  const values = parseEnvFile(content);

  return NextResponse.json(buildSettings(envFilePath, values));
}

export async function POST(request: Request) {
  try {
    const payload = normalizePayload(await request.json());
    const envFilePath = await resolveEnvFilePath();
    await writeSettings(envFilePath, payload);
    const content = await readEnvFile(envFilePath);
    const values = parseEnvFile(content);

    return NextResponse.json(buildSettings(envFilePath, values));
  } catch (error) {
    return new NextResponse(error instanceof Error ? error.message : "Failed to save settings.", {
      status: 400,
    });
  }
}
