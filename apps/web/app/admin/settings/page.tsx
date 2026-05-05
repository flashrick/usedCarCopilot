"use client";

import { useEffect, useState, useTransition } from "react";
import { AlertTriangle, CheckCircle2, KeyRound, RefreshCw, ServerCog } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { recommendationProviders, providerDefaultModel } from "@/lib/admin-settings";
import { fetchAdminSettings, saveAdminSettings } from "@/lib/api";
import type { AdminSettingsResponse, AdminSettingsUpdate, AIProviderId } from "@/lib/types";

type ExternalProviderId = keyof AdminSettingsResponse["providers"];

type FormState = AdminSettingsUpdate & {
  envFilePath: string;
  configured: AdminSettingsResponse["providers"];
};

function buildInitialFormState(): FormState {
  return {
    envFilePath: "",
    recommendationProvider: "deterministic",
    recommendationModel: providerDefaultModel("deterministic"),
    configured: {
      openai: { apiKeyConfigured: false, baseUrl: "https://api.openai.com/v1", timeoutSeconds: "30" },
      deepseek: { apiKeyConfigured: false, baseUrl: "https://api.deepseek.com" },
      qwen: { apiKeyConfigured: false, baseUrl: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1" },
      kimi: { apiKeyConfigured: false, baseUrl: "https://api.moonshot.ai/v1" },
    },
    providers: {
      openai: { apiKey: "", baseUrl: "https://api.openai.com/v1", timeoutSeconds: "30" },
      deepseek: { apiKey: "", baseUrl: "https://api.deepseek.com" },
      qwen: { apiKey: "", baseUrl: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1" },
      kimi: { apiKey: "", baseUrl: "https://api.moonshot.ai/v1" },
    },
  };
}

function toFormState(settings: AdminSettingsResponse): FormState {
  return {
    envFilePath: settings.envFilePath,
    recommendationProvider: settings.recommendationProvider,
    recommendationModel: settings.recommendationModel,
    configured: settings.providers,
    providers: {
      openai: { apiKey: "", baseUrl: settings.providers.openai.baseUrl, timeoutSeconds: settings.providers.openai.timeoutSeconds },
      deepseek: { apiKey: "", baseUrl: settings.providers.deepseek.baseUrl },
      qwen: { apiKey: "", baseUrl: settings.providers.qwen.baseUrl },
      kimi: { apiKey: "", baseUrl: settings.providers.kimi.baseUrl },
    },
  };
}

function SettingField({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-ink">{label}</span>
      {children}
      {hint ? <span className="text-xs text-muted">{hint}</span> : null}
    </label>
  );
}

function ProviderBadge({ configured, configuredLabel, missingLabel }: { configured: boolean; configuredLabel: string; missingLabel: string }) {
  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
        configured ? "bg-[#edf7ef] text-[#1f6b38]" : "bg-[#fff4e8] text-[#8a5a1d]"
      }`}
    >
      {configured ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
      {configured ? configuredLabel : missingLabel}
    </div>
  );
}

function isExternalProviderId(providerId: AIProviderId): providerId is ExternalProviderId {
  return providerId !== "deterministic";
}

export default function SettingsPage() {
  const { copy } = useLocale();
  const [form, setForm] = useState<FormState>(buildInitialFormState);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isBooting, setIsBooting] = useState(true);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      setLoadError(null);
      try {
        const data = await fetchAdminSettings();
        if (active) {
          setForm(toFormState(data));
        }
      } catch (caughtError) {
        if (active) {
          setLoadError(caughtError instanceof Error ? caughtError.message : copy.settings.loadFailed);
        }
      } finally {
        if (active) {
          setIsBooting(false);
        }
      }
    }

    loadSettings();

    return () => {
      active = false;
    };
  }, [copy.settings.loadFailed]);

  const selectedProvider = recommendationProviders.find((provider) => provider.id === form.recommendationProvider) ?? recommendationProviders[0];
  const selectedProviderMeta = copy.settings.providerMeta[selectedProvider.id];
  const selectedExternalProviderId = isExternalProviderId(selectedProvider.id) ? selectedProvider.id : null;

  function updateProviderField<K extends keyof FormState["providers"]>(
    providerId: K,
    field: keyof FormState["providers"][K],
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      providers: {
        ...current.providers,
        [providerId]: {
          ...current.providers[providerId],
          [field]: value,
        },
      },
    }));
  }

  function changeRecommendationProvider(providerId: AIProviderId) {
    setForm((current) => {
      const shouldResetModel = current.recommendationModel === providerDefaultModel(current.recommendationProvider) || !current.recommendationModel.trim();
      return {
        ...current,
        recommendationProvider: providerId,
        recommendationModel: shouldResetModel ? providerDefaultModel(providerId) : current.recommendationModel,
      };
    });
  }

  function handleSave() {
    setSaveError(null);
    setSaveSuccess(null);

    startTransition(async () => {
      try {
        const payload: AdminSettingsUpdate = {
          recommendationProvider: form.recommendationProvider,
          recommendationModel: form.recommendationModel.trim() || providerDefaultModel(form.recommendationProvider),
          providers: form.providers,
        };

        const saved = await saveAdminSettings(payload);
        setForm(toFormState(saved));
        setSaveSuccess(copy.settings.saveSuccess);
      } catch (caughtError) {
        setSaveError(caughtError instanceof Error ? caughtError.message : copy.settings.saveFailed);
      }
    });
  }

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4 xl:grid-cols-[1.02fr_1.18fr]">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.settings.providerEyebrow}</div>
              <h2 className="mt-1 text-2xl font-semibold">{copy.settings.providerTitle}</h2>
              <p className="mt-2 max-w-2xl text-sm text-muted">{copy.settings.providerDescription}</p>
            </div>
            <div className="hidden rounded-md bg-shell p-3 text-muted md:block">
              <ServerCog className="h-5 w-5" />
            </div>
          </div>

          <div className="mt-5 grid gap-4">
            <SettingField label={copy.settings.providerFieldLabel} hint={copy.settings.providerFieldHint}>
              <select
                value={form.recommendationProvider}
                onChange={(event) => changeRecommendationProvider(event.target.value as AIProviderId)}
                className="h-11 rounded-md border border-line bg-shell px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
                disabled={isBooting}
              >
                {recommendationProviders.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {copy.settings.providerMeta[provider.id].label}
                  </option>
                ))}
              </select>
            </SettingField>

            <SettingField label={copy.settings.modelFieldLabel} hint={copy.settings.modelFieldHint}>
              <input
                value={form.recommendationModel}
                onChange={(event) => setForm((current) => ({ ...current, recommendationModel: event.target.value }))}
                className="h-11 rounded-md border border-line bg-shell px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
                placeholder={selectedProvider.defaultModel}
                disabled={isBooting}
              />
            </SettingField>

            <div className="rounded-md bg-shell p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium">{selectedProviderMeta.label}</div>
                  <div className="mt-1 font-mono text-xs text-muted">{selectedProvider.defaultModel}</div>
                </div>
                <ProviderBadge
                  configured={selectedExternalProviderId ? form.configured[selectedExternalProviderId].apiKeyConfigured : true}
                  configuredLabel={copy.settings.secretConfigured}
                  missingLabel={copy.settings.secretMissing}
                />
              </div>
              <p className="mt-3 text-sm text-muted">{selectedProviderMeta.note}</p>
            </div>

            <div className="grid gap-3">
              {recommendationProviders.map((provider) => {
                const meta = copy.settings.providerMeta[provider.id];
                const configured = isExternalProviderId(provider.id) ? form.configured[provider.id].apiKeyConfigured : true;
                return (
                  <article
                    key={provider.id}
                    className={`rounded-md border p-4 transition ${
                      form.recommendationProvider === provider.id ? "border-steel/40 bg-[#f8fbfd]" : "border-line/70 bg-shell"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">{meta.label}</div>
                        <div className="mt-1 font-mono text-xs text-muted">{provider.defaultModel}</div>
                      </div>
                      <ProviderBadge configured={configured} configuredLabel={copy.settings.secretConfigured} missingLabel={copy.settings.secretMissing} />
                    </div>
                    <p className="mt-3 text-sm text-muted">{meta.note}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.settings.configurationEyebrow}</div>
              <h2 className="mt-1 text-2xl font-semibold">{copy.settings.configurationTitle}</h2>
              <p className="mt-2 max-w-2xl text-sm text-muted">{copy.settings.configurationDescription}</p>
            </div>
            <div className="hidden rounded-md bg-shell p-3 text-muted md:block">
              <KeyRound className="h-5 w-5" />
            </div>
          </div>

          {loadError ? (
            <div className="mt-4 flex items-center gap-3 rounded-md border border-riskHigh/70 bg-[#fff1f1] px-4 py-3 text-sm text-rose-900">
              <AlertTriangle className="h-4 w-4" />
              {loadError}
            </div>
          ) : null}

          {saveError ? (
            <div className="mt-4 flex items-center gap-3 rounded-md border border-riskHigh/70 bg-[#fff1f1] px-4 py-3 text-sm text-rose-900">
              <AlertTriangle className="h-4 w-4" />
              {saveError}
            </div>
          ) : null}

          {saveSuccess ? (
            <div className="mt-4 flex items-center gap-3 rounded-md border border-[#b8e0c2] bg-[#eff9f1] px-4 py-3 text-sm text-[#1f6b38]">
              <CheckCircle2 className="h-4 w-4" />
              {saveSuccess}
            </div>
          ) : null}

          <div className="mt-5 grid gap-4">
            {selectedProvider.supportsApiKey ? (
              <SettingField label={copy.settings.apiKeyLabel} hint={copy.settings.apiKeyHint}>
                <input
                  type="password"
                  value={selectedExternalProviderId ? form.providers[selectedExternalProviderId].apiKey ?? "" : ""}
                  onChange={(event) => selectedExternalProviderId && updateProviderField(selectedExternalProviderId, "apiKey", event.target.value)}
                  className="h-11 rounded-md border border-line bg-shell px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
                  placeholder={copy.settings.apiKeyPlaceholder}
                  disabled={isBooting}
                />
              </SettingField>
            ) : (
              <div className="rounded-md border border-dashed border-line/80 bg-shell p-4 text-sm text-muted">{copy.settings.noSecretRequired}</div>
            )}

            {selectedProvider.supportsBaseUrl ? (
              <SettingField label={copy.settings.baseUrlLabel}>
                <input
                  value={selectedExternalProviderId ? form.providers[selectedExternalProviderId].baseUrl : ""}
                  onChange={(event) => selectedExternalProviderId && updateProviderField(selectedExternalProviderId, "baseUrl", event.target.value)}
                  className="h-11 rounded-md border border-line bg-shell px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
                  disabled={isBooting}
                />
              </SettingField>
            ) : null}

            {selectedProvider.supportsTimeout ? (
              <SettingField label={copy.settings.timeoutLabel} hint={copy.settings.timeoutHint}>
                <input
                  value={form.providers.openai.timeoutSeconds ?? ""}
                  onChange={(event) => updateProviderField("openai", "timeoutSeconds", event.target.value)}
                  className="h-11 rounded-md border border-line bg-shell px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
                  inputMode="decimal"
                  disabled={isBooting}
                />
              </SettingField>
            ) : null}

            <div className="rounded-md bg-shell p-4 text-sm text-muted">
              <div className="font-medium text-ink">{copy.settings.envFileLabel}</div>
              <div className="mt-2 font-mono text-xs">{form.envFilePath || copy.settings.loadingPath}</div>
            </div>

            <div className="rounded-md bg-shell p-4 text-sm text-muted">
              <div className="font-medium text-ink">{copy.settings.restartTitle}</div>
              <div className="mt-2 space-y-2">
                {copy.settings.restartNotes.map((note) => (
                  <div key={note}>{note}</div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleSave}
                disabled={isBooting || isPending}
                className="inline-flex h-11 items-center gap-2 rounded-md bg-gradient-to-b from-steel to-steelDeep px-4 text-sm font-medium text-white shadow-panel transition hover:brightness-105 disabled:opacity-70"
              >
                {isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : null}
                {isPending ? copy.settings.savingButton : copy.settings.saveButton}
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
