<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Copy, Download, FileText, ShieldAlert, Sparkles } from "lucide-vue-next";
import { useAppStore } from "../store";
import MarkdownReport from "../components/MarkdownReport.vue";
import MarketBadge from "../components/MarketBadge.vue";
import PriceChangeTag from "../components/PriceChangeTag.vue";

const props = withDefaults(
  defineProps<{
    isDesktop?: boolean;
  }>(),
  {
    isDesktop: undefined,
  },
);

type TabKey = "report" | "risk" | "factors";

const router = useRouter();
const { selectedStock, finalReport, riskAssessment, factorSummary, stocks } = useAppStore();
const isDesktopView = computed(() => {
  if (typeof props.isDesktop === "boolean") return props.isDesktop;
  if (typeof window === "undefined") return true;
  return window.matchMedia("(min-width: 768px)").matches;
});

const activeTab = ref<TabKey>("report");
const isCopied = ref(false);
const reportUpdatedAt = ref<Date | null>(null);

watch(
  finalReport,
  (nextReport) => {
    if (nextReport?.trim()) {
      reportUpdatedAt.value = new Date();
    }
  },
  { immediate: true },
);

const changeClass = computed(() => {
  if (!selectedStock.value) return "text-[var(--color-text-primary)]";
  return selectedStock.value.change >= 0 ? "text-[var(--color-up)]" : "text-[var(--color-down)]";
});

const stockRank = computed(() => {
  if (!selectedStock.value) return "-";
  const index = stocks.value.findIndex((item) => item.thsCode === selectedStock.value?.thsCode);
  return index >= 0 ? `#${index + 1}` : "-";
});

const reportWordCount = computed(() => {
  const text = finalReport.value || "";
  return text.replace(/\s+/g, "").length;
});

const riskSummary = computed(() => {
  if (!selectedStock.value) return { level: "Pending", style: "text-slate-600 bg-slate-100 border-slate-200" };
  let score = 0;
  if (selectedStock.value.pe > 35) score += 2;
  if (selectedStock.value.profitGrowth < 0) score += 3;
  if (selectedStock.value.revGrowth < 0) score += 2;
  if (selectedStock.value.change < -3) score += 1;
  if (selectedStock.value.idiosyncraticVol > 0.3) score += 2;
  if (selectedStock.value.ffScore < 50) score += 2;

  if (score >= 5) return { level: "High", style: "text-red-700 bg-red-50 border-red-200" };
  if (score >= 3) return { level: "Medium", style: "text-amber-700 bg-amber-50 border-amber-200" };
  return { level: "Low", style: "text-emerald-700 bg-emerald-50 border-emerald-200" };
});

const keyFactors = computed(() => {
  if (!selectedStock.value) return [];
  return [
    {
      label: "FF5 Composite Score",
      value: selectedStock.value.ffScore.toFixed(1),
      status: selectedStock.value.ffScore >= 70 ? "Strong" : selectedStock.value.ffScore >= 55 ? "Watch" : "Weak",
    },
    {
      label: "Alpha Proxy",
      value: selectedStock.value.alpha.toFixed(4),
      status: selectedStock.value.alpha > 0 ? "Positive" : "Negative",
    },
    {
      label: "Value / HML",
      value: selectedStock.value.bookToMarket.toFixed(3),
      status: selectedStock.value.betaHml > 0 ? "Value Tilt" : "Growth Tilt",
    },
    {
      label: "Profitability / RMW",
      value: `${(selectedStock.value.operatingProfitability * 100).toFixed(2)}%`,
      status: selectedStock.value.betaRmw > 0 ? "Robust" : "Weak",
    },
    {
      label: "Investment / CMA",
      value: `${(selectedStock.value.assetGrowth * 100).toFixed(2)}%`,
      status: selectedStock.value.betaCma > 0 ? "Conservative" : "Aggressive",
    },
    {
      label: "Idiosyncratic Vol",
      value: `${(selectedStock.value.idiosyncraticVol * 100).toFixed(2)}%`,
      status: selectedStock.value.idiosyncraticVol <= 0.25 ? "Controlled" : "Elevated",
    },
  ];
});

const factorExposures = computed(() => {
  if (!selectedStock.value) return [];
  return [
    { label: "MKT", value: selectedStock.value.betaMkt },
    { label: "SMB", value: selectedStock.value.betaSmb },
    { label: "HML", value: selectedStock.value.betaHml },
    { label: "RMW", value: selectedStock.value.betaRmw },
    { label: "CMA", value: selectedStock.value.betaCma },
  ];
});

const copyMarkdown = async () => {
  if (!finalReport.value?.trim()) return;
  await navigator.clipboard.writeText(finalReport.value);
  isCopied.value = true;
  setTimeout(() => {
    isCopied.value = false;
  }, 1500);
};

const downloadMarkdown = () => {
  const content = finalReport.value?.trim();
  if (!content) return;

  const filename = `${selectedStock.value?.code ?? "report"}-${Date.now()}.md`;
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

const goPool = () => {
  router.push("/pool");
};
</script>

<template>
  <div
    v-if="!selectedStock"
    class="h-full min-h-[260px] glass-panel rounded-xl p-8 flex flex-col items-center justify-center text-center text-[var(--color-text-secondary)]"
  >
    <div class="w-14 h-14 rounded-full bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center mb-4">
      <FileText class="w-6 h-6" />
    </div>
    <p class="text-base text-[var(--color-text-primary)] font-semibold">No stock selected</p>
    <p class="text-sm mt-2">Pick one candidate in Stock Pool to view the full AI report and risk suggestions.</p>
    <button class="mt-5 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500" @click="goPool">Open Stock Pool</button>
  </div>

  <div v-else class="w-full h-full flex flex-col text-[var(--color-text-primary)]" :class="!isDesktopView ? 'pt-2' : ''">
    <section class="glass-panel rounded-xl p-4">
      <div class="flex items-start justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <h2 class="text-xl font-bold tracking-wide">{{ selectedStock.name }}</h2>
            <MarketBadge :market="selectedStock.market" />
            <span class="text-xs text-slate-500 font-mono">{{ selectedStock.thsCode }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-3xl font-mono font-bold tracking-tight" :class="changeClass">{{ selectedStock.price.toFixed(2) }}</span>
            <PriceChangeTag :value="selectedStock.change" class-name="text-sm px-2 py-0.5" />
            <span class="px-2 py-0.5 text-xs rounded-md border" :class="riskSummary.style">Risk {{ riskSummary.level }}</span>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 hover:border-blue-300 hover:text-blue-700"
            @click="copyMarkdown"
          >
            <Copy class="w-3.5 h-3.5" />
            {{ isCopied ? "Copied" : "Copy Report" }}
          </button>
          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 hover:border-blue-300 hover:text-blue-700"
            @click="downloadMarkdown"
          >
            <Download class="w-3.5 h-3.5" />
            Download MD
          </button>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">Pool Rank</div>
          <div class="text-base font-semibold mt-0.5">#{{ selectedStock.ffRank || stockRank }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">FF5 Score</div>
          <div class="text-base font-semibold mt-0.5 text-blue-700">{{ selectedStock.ffScore.toFixed(1) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">Alpha</div>
          <div class="text-base font-semibold mt-0.5" :class="selectedStock.alpha >= 0 ? 'text-[var(--color-up)]' : 'text-[var(--color-down)]'">
            {{ selectedStock.alpha.toFixed(4) }}
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">Data Quality</div>
          <div class="text-base font-semibold mt-0.5">{{ selectedStock.dataQuality.toFixed(0) }}%</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">Report Size</div>
          <div class="text-base font-semibold mt-0.5">{{ reportWordCount }}</div>
        </div>
      </div>
    </section>

    <section class="mt-3 rounded-xl border border-slate-200 bg-white p-1">
      <div class="flex items-center gap-1">
        <button
          class="flex-1 rounded-lg px-3 py-2 text-sm"
          :class="activeTab === 'report' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'report'"
        >
          Report
        </button>
        <button
          class="flex-1 rounded-lg px-3 py-2 text-sm"
          :class="activeTab === 'risk' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'risk'"
        >
          Risk
        </button>
        <button
          class="flex-1 rounded-lg px-3 py-2 text-sm"
          :class="activeTab === 'factors' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'factors'"
        >
          Factors
        </button>
      </div>
    </section>

    <section class="mt-3 flex-1 min-h-0 overflow-y-auto pr-1 custom-scrollbar">
      <div v-if="activeTab === 'report'" class="glass-panel rounded-xl p-4">
        <div class="flex items-center justify-between mb-3 text-xs text-[var(--color-text-secondary)]">
          <span class="inline-flex items-center gap-1"><Sparkles class="w-3.5 h-3.5 text-blue-600" /> AI generated content</span>
          <span v-if="reportUpdatedAt">Updated {{ reportUpdatedAt.toLocaleString() }}</span>
        </div>
        <MarkdownReport :content="finalReport" />
      </div>

      <div v-else-if="activeTab === 'risk'" class="glass-panel rounded-xl p-4 space-y-3">
        <div class="flex items-center gap-2 text-[var(--color-text-primary)]">
          <ShieldAlert class="w-4 h-4 text-amber-600" />
          <h3 class="text-sm font-semibold">Portfolio Risk Summary</h3>
        </div>
        <p class="text-sm leading-7 text-[var(--color-text-secondary)]">
          {{ riskAssessment || "No risk assessment yet. Please run a screener query first." }}
        </p>
        <p v-if="factorSummary" class="text-xs leading-6 text-slate-500 rounded-lg border border-slate-200 bg-slate-50 p-3">
          {{ factorSummary }}
        </p>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 leading-6">
          <p>Position suggestion: {{ riskSummary.level === "High" ? "Target total exposure <= 40%" : riskSummary.level === "Medium" ? "Scale in gradually, target 40%-65%" : "Can increase exposure to around 70% with discipline" }}</p>
          <p>Stop loss discipline: consider reducing when single-name loss approaches 8%.</p>
          <p>Diversification: keep 5-8 names and avoid single-sector concentration.</p>
        </div>
      </div>

      <div v-else class="glass-panel rounded-xl p-4">
        <h3 class="text-sm font-semibold mb-3">Factor Breakdown</h3>
        <div class="grid grid-cols-5 gap-2 mb-3">
          <div v-for="item in factorExposures" :key="item.label" class="rounded-lg border border-slate-200 bg-white p-2 text-center">
            <div class="text-[10px] text-slate-500">{{ item.label }}</div>
            <div class="mt-1 text-xs font-mono font-semibold" :class="item.value >= 0 ? 'text-blue-700' : 'text-slate-600'">{{ item.value.toFixed(3) }}</div>
          </div>
        </div>
        <div class="space-y-2">
          <div v-for="factor in keyFactors" :key="factor.label" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5">
            <div class="flex items-center justify-between">
              <span class="text-xs text-slate-500">{{ factor.label }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full border border-slate-200 bg-white text-slate-600">{{ factor.status }}</span>
            </div>
            <p class="mt-1 text-sm font-semibold">{{ factor.value }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="mt-3 text-xs text-[var(--color-text-secondary)] text-center">
      AI generated content for research only, not financial advice.
    </div>
  </div>
</template>
