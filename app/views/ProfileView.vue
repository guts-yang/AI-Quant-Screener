<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Bell, Database, RefreshCw, Save, Server, Shield, User } from "lucide-vue-next";

type RiskLevel = "conservative" | "balanced" | "aggressive";
type RebalanceCycle = "daily" | "weekly" | "monthly";

interface DataSourceStatus {
  name: string;
  enabled: boolean;
  configured: boolean;
  base_url: string;
  timeout_seconds: number;
}

interface UserSettings {
  riskLevel: RiskLevel;
  maxDrawdown: number;
  stopLoss: number;
  maxPosition: number;
  rebalanceCycle: RebalanceCycle;
  prioritizeSse: boolean;
  autoFallback: boolean;
  desktopNotice: boolean;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8006";
const storageKey = "aqs_user_settings";

const defaults: UserSettings = {
  riskLevel: "balanced",
  maxDrawdown: 12,
  stopLoss: 8,
  maxPosition: 20,
  rebalanceCycle: "weekly",
  prioritizeSse: true,
  autoFallback: true,
  desktopNotice: false,
};

const settings = ref<UserSettings>({ ...defaults });
const savedAt = ref<Date | null>(null);
const saveMessage = ref("");
const healthStatus = ref<"unknown" | "ok" | "error">("unknown");
const healthText = ref("Not checked");
const checkingHealth = ref(false);
const dataSources = ref<DataSourceStatus[]>([]);
const loadingSources = ref(false);

const profileStats = computed(() => {
  const riskScore =
    settings.value.riskLevel === "aggressive"
      ? 80
      : settings.value.riskLevel === "balanced"
        ? 60
        : 35;

  return {
    riskScore,
    executionMode: settings.value.prioritizeSse ? "SSE First" : "HTTP Direct",
    fallbackMode: settings.value.autoFallback ? "Fallback On" : "Fallback Off",
  };
});

const loadSettings = () => {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw) as Partial<UserSettings>;
    settings.value = { ...defaults, ...parsed };
  } catch {
    settings.value = { ...defaults };
  }
};

const saveSettings = () => {
  localStorage.setItem(storageKey, JSON.stringify(settings.value));
  savedAt.value = new Date();
  saveMessage.value = "Saved locally";
  setTimeout(() => {
    saveMessage.value = "";
  }, 1800);
};

const resetSettings = () => {
  settings.value = { ...defaults };
  localStorage.setItem(storageKey, JSON.stringify(settings.value));
  saveMessage.value = "Defaults restored";
  setTimeout(() => {
    saveMessage.value = "";
  }, 1800);
};

const checkHealth = async () => {
  checkingHealth.value = true;
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    healthStatus.value = "ok";
    healthText.value = "Backend reachable";
  } catch {
    healthStatus.value = "error";
    healthText.value = "Backend unavailable";
  } finally {
    checkingHealth.value = false;
  }
};

const loadDataSources = async () => {
  loadingSources.value = true;
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/config/data-sources`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const payload = (await res.json()) as { sources?: DataSourceStatus[] };
    dataSources.value = Array.isArray(payload.sources) ? payload.sources : [];
  } catch {
    dataSources.value = [];
  } finally {
    loadingSources.value = false;
  }
};

onMounted(async () => {
  loadSettings();
  await Promise.all([checkHealth(), loadDataSources()]);
});
</script>

<template>
  <div class="p-4 md:p-5 space-y-4 bg-[var(--color-background)] min-h-full">
    <section class="glass-panel rounded-xl p-4">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-blue-100 border border-blue-200 flex items-center justify-center">
            <User class="w-6 h-6 text-blue-700" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-[var(--color-text-primary)]">Profile & Strategy</h2>
            <p class="text-xs text-[var(--color-text-secondary)]">Local settings + backend runtime checks</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            class="px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:text-blue-700 inline-flex items-center gap-1.5"
            :disabled="checkingHealth"
            @click="checkHealth"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="checkingHealth ? 'animate-spin' : ''" />
            Health Check
          </button>
          <button
            class="px-3 py-2 text-xs rounded-lg border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 inline-flex items-center gap-1.5"
            @click="loadDataSources"
          >
            <Database class="w-3.5 h-3.5" />
            Refresh Sources
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-2 mt-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] text-slate-500">Risk Score</div>
          <p class="mt-1 text-base font-semibold">{{ profileStats.riskScore }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] text-slate-500">Execution</div>
          <p class="mt-1 text-base font-semibold">{{ profileStats.executionMode }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] text-slate-500">Fallback</div>
          <p class="mt-1 text-base font-semibold">{{ profileStats.fallbackMode }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] text-slate-500">Backend</div>
          <p
            class="mt-1 text-base font-semibold"
            :class="healthStatus === 'ok' ? 'text-emerald-700' : healthStatus === 'error' ? 'text-red-700' : 'text-slate-600'"
          >
            {{ healthText }}
          </p>
        </div>
      </div>
    </section>

    <section class="glass-panel rounded-xl p-4">
      <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-3 inline-flex items-center gap-2">
        <Shield class="w-4 h-4 text-amber-600" />
        Risk Controls
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label class="rounded-lg border border-slate-200 bg-white p-3">
          <span class="text-xs text-slate-500">Risk Style</span>
          <select v-model="settings.riskLevel" class="mt-1 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm bg-white">
            <option value="conservative">Conservative</option>
            <option value="balanced">Balanced</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </label>

        <label class="rounded-lg border border-slate-200 bg-white p-3">
          <span class="text-xs text-slate-500">Rebalance Cycle</span>
          <select v-model="settings.rebalanceCycle" class="mt-1 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm bg-white">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </label>
      </div>

      <div class="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
        <label class="rounded-lg border border-slate-200 bg-white p-3">
          <div class="text-xs text-slate-500">Max Drawdown {{ settings.maxDrawdown }}%</div>
          <input v-model.number="settings.maxDrawdown" type="range" min="5" max="30" step="1" class="mt-2 w-full" />
        </label>
        <label class="rounded-lg border border-slate-200 bg-white p-3">
          <div class="text-xs text-slate-500">Stop Loss {{ settings.stopLoss }}%</div>
          <input v-model.number="settings.stopLoss" type="range" min="3" max="15" step="1" class="mt-2 w-full" />
        </label>
        <label class="rounded-lg border border-slate-200 bg-white p-3">
          <div class="text-xs text-slate-500">Max Single Position {{ settings.maxPosition }}%</div>
          <input v-model.number="settings.maxPosition" type="range" min="5" max="40" step="1" class="mt-2 w-full" />
        </label>
      </div>
    </section>

    <section class="glass-panel rounded-xl p-4">
      <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-3 inline-flex items-center gap-2">
        <Bell class="w-4 h-4 text-blue-600" />
        Runtime Preferences
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <label class="rounded-lg border border-slate-200 bg-white p-3 flex items-center justify-between">
          <span class="text-sm text-slate-700">Prefer SSE</span>
          <input v-model="settings.prioritizeSse" type="checkbox" class="h-4 w-4 accent-blue-600" />
        </label>
        <label class="rounded-lg border border-slate-200 bg-white p-3 flex items-center justify-between">
          <span class="text-sm text-slate-700">Auto fallback to /run</span>
          <input v-model="settings.autoFallback" type="checkbox" class="h-4 w-4 accent-blue-600" />
        </label>
        <label class="rounded-lg border border-slate-200 bg-white p-3 flex items-center justify-between">
          <span class="text-sm text-slate-700">Desktop notify</span>
          <input v-model="settings.desktopNotice" type="checkbox" class="h-4 w-4 accent-blue-600" />
        </label>
      </div>
    </section>

    <section class="glass-panel rounded-xl p-4">
      <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-3 inline-flex items-center gap-2">
        <Server class="w-4 h-4 text-indigo-600" />
        Data Source Status
      </h3>

      <div v-if="loadingSources" class="text-sm text-slate-500">Loading source status...</div>
      <div v-else-if="dataSources.length === 0" class="text-sm text-slate-500">No data source info from backend.</div>
      <div v-else class="space-y-2">
        <div v-for="source in dataSources" :key="source.name" class="rounded-lg border border-slate-200 bg-white p-3">
          <div class="flex items-center justify-between gap-2">
            <div>
              <p class="text-sm font-semibold text-slate-800 uppercase">{{ source.name }}</p>
              <p class="text-xs text-slate-500 mt-1 font-mono break-all">{{ source.base_url }}</p>
            </div>
            <div class="text-right text-xs">
              <p>
                Enabled:
                <span :class="source.enabled ? 'text-emerald-700' : 'text-slate-500'">{{ source.enabled ? "Yes" : "No" }}</span>
              </p>
              <p>
                Configured:
                <span :class="source.configured ? 'text-emerald-700' : 'text-amber-700'">{{ source.configured ? "Yes" : "No" }}</span>
              </p>
              <p class="text-slate-500">Timeout: {{ source.timeout_seconds }}s</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="flex items-center justify-between gap-2 flex-wrap">
      <div class="text-xs text-slate-500">
        <span v-if="savedAt">Last saved: {{ savedAt.toLocaleString() }}</span>
        <span v-else>Settings not saved yet</span>
        <span v-if="saveMessage" class="ml-2 text-blue-700">{{ saveMessage }}</span>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm text-slate-700 hover:border-slate-300" @click="resetSettings">
          Reset
        </button>
        <button class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500 inline-flex items-center gap-1.5" @click="saveSettings">
          <Save class="w-4 h-4" />
          Save Settings
        </button>
      </div>
    </section>
  </div>
</template>
