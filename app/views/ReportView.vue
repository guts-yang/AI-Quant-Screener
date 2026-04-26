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
  if (!selectedStock.value) return { level: "待评估", style: "text-slate-600 bg-slate-100 border-slate-200" };
  let score = 0;
  if (selectedStock.value.pe > 35) score += 2;
  if (selectedStock.value.profitGrowth < 0) score += 3;
  if (selectedStock.value.revGrowth < 0) score += 2;
  if (selectedStock.value.change < -3) score += 1;
  if (selectedStock.value.idiosyncraticVol > 0.3) score += 2;
  if (selectedStock.value.ffScore < 50) score += 2;

  if (score >= 5) return { level: "高", style: "text-red-700 bg-red-50 border-red-200" };
  if (score >= 3) return { level: "中", style: "text-amber-700 bg-amber-50 border-amber-200" };
  return { level: "低", style: "text-emerald-700 bg-emerald-50 border-emerald-200" };
});

const keyFactors = computed(() => {
  if (!selectedStock.value) return [];
  return [
    {
      label: "五因子综合分",
      value: selectedStock.value.ffScore.toFixed(1),
      status: selectedStock.value.ffScore >= 70 ? "较强" : selectedStock.value.ffScore >= 55 ? "观察" : "偏弱",
    },
    {
      label: "Alpha 代理信号",
      value: selectedStock.value.alpha.toFixed(4),
      status: selectedStock.value.alpha > 0 ? "正向" : "负向",
    },
    {
      label: "价值因子 / HML",
      value: selectedStock.value.bookToMarket.toFixed(3),
      status: selectedStock.value.betaHml > 0 ? "价值倾向" : "成长倾向",
    },
    {
      label: "盈利质量 / RMW",
      value: `${(selectedStock.value.operatingProfitability * 100).toFixed(2)}%`,
      status: selectedStock.value.betaRmw > 0 ? "稳健" : "偏弱",
    },
    {
      label: "投资风格 / CMA",
      value: `${(selectedStock.value.assetGrowth * 100).toFixed(2)}%`,
      status: selectedStock.value.betaCma > 0 ? "稳健扩张" : "激进扩张",
    },
    {
      label: "特异波动",
      value: `${(selectedStock.value.idiosyncraticVol * 100).toFixed(2)}%`,
      status: selectedStock.value.idiosyncraticVol <= 0.25 ? "可控" : "偏高",
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
    <p class="text-base text-[var(--color-text-primary)] font-semibold">还没有选择股票</p>
    <p class="text-sm mt-2">请先在股票池中选择一个候选标的，再查看完整研报和风险建议。</p>
    <button class="mt-5 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500" @click="goPool">打开股票池</button>
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
            <span class="px-2 py-0.5 text-xs rounded-md border" :class="riskSummary.style">风险 {{ riskSummary.level }}</span>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 hover:border-blue-300 hover:text-blue-700"
            @click="copyMarkdown"
          >
            <Copy class="w-3.5 h-3.5" />
            {{ isCopied ? "已复制" : "复制研报" }}
          </button>
          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 hover:border-blue-300 hover:text-blue-700"
            @click="downloadMarkdown"
          >
            <Download class="w-3.5 h-3.5" />
            下载原文
          </button>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">池内排名</div>
          <div class="text-base font-semibold mt-0.5">#{{ selectedStock.ffRank || stockRank }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">五因子分</div>
          <div class="text-base font-semibold mt-0.5 text-blue-700">{{ selectedStock.ffScore.toFixed(1) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">Alpha</div>
          <div class="text-base font-semibold mt-0.5" :class="selectedStock.alpha >= 0 ? 'text-[var(--color-up)]' : 'text-[var(--color-down)]'">
            {{ selectedStock.alpha.toFixed(4) }}
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">数据质量</div>
          <div class="text-base font-semibold mt-0.5">{{ selectedStock.dataQuality.toFixed(0) }}%</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div class="text-[11px] text-slate-500">报告字数</div>
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
          研报
        </button>
        <button
          class="flex-1 rounded-lg px-3 py-2 text-sm"
          :class="activeTab === 'risk' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'risk'"
        >
          风险
        </button>
        <button
          class="flex-1 rounded-lg px-3 py-2 text-sm"
          :class="activeTab === 'factors' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'factors'"
        >
          因子
        </button>
      </div>
    </section>

    <section class="mt-3 flex-1 min-h-0 overflow-y-auto pr-1 custom-scrollbar">
      <div v-if="activeTab === 'report'" class="glass-panel rounded-xl p-4">
        <div class="flex items-center justify-between mb-3 text-xs text-[var(--color-text-secondary)]">
          <span class="inline-flex items-center gap-1"><Sparkles class="w-3.5 h-3.5 text-blue-600" /> AI 生成内容</span>
          <span v-if="reportUpdatedAt">更新于 {{ reportUpdatedAt.toLocaleString() }}</span>
        </div>
        <MarkdownReport :content="finalReport" />
      </div>

      <div v-else-if="activeTab === 'risk'" class="glass-panel rounded-xl p-4 space-y-3">
        <div class="flex items-center gap-2 text-[var(--color-text-primary)]">
          <ShieldAlert class="w-4 h-4 text-amber-600" />
          <h3 class="text-sm font-semibold">组合风险摘要</h3>
        </div>
        <p class="text-sm leading-7 text-[var(--color-text-secondary)]">
          {{ riskAssessment || "暂无风险评估。请先运行一次选股策略。" }}
        </p>
        <p v-if="factorSummary" class="text-xs leading-6 text-slate-500 rounded-lg border border-slate-200 bg-slate-50 p-3">
          {{ factorSummary }}
        </p>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 leading-6">
          <p>仓位建议：{{ riskSummary.level === "高" ? "总仓位建议控制在 40% 以内" : riskSummary.level === "中" ? "适合分批建仓，目标仓位 40%-65%" : "可在纪律约束下逐步提高到约 70%" }}</p>
          <p>止损纪律：单票亏损接近 8% 时建议复盘并考虑减仓。</p>
          <p>分散要求：尽量保留 5-8 只标的，避免单一行业过度集中。</p>
        </div>
      </div>

      <div v-else class="glass-panel rounded-xl p-4">
        <h3 class="text-sm font-semibold mb-3">因子拆解</h3>
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
      AI 内容仅供研究参考，不构成投资建议。
    </div>
  </div>
</template>
