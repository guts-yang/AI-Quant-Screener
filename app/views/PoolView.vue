<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Eye, Search, Download, Star, Database, RefreshCw } from "lucide-vue-next";
import { useAppStore } from "../store";
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

const isDesktopView = computed(() => {
  if (typeof props.isDesktop === "boolean") return props.isDesktop;
  if (typeof window === "undefined") return true;
  return window.matchMedia("(min-width: 768px)").matches;
});

const {
  stocks,
  selectedStock,
  setSelectedStock,
  openMobileSheet,
  isRunning,
  universeOptions,
  selectedUniverse,
  universePreviewCount,
  setSelectedUniverse,
  loadUniverses,
  previewUniverse,
} = useAppStore();

const searchKeyword = ref("");
const marketFilter = ref<"all" | "SH" | "SZ">("all");
const boardFilter = ref("all");
const sortBy = ref("profit_desc");
const minProfitGrowth = ref(-10);
const favoritesOnly = ref(false);
const favorites = ref<string[]>([]);
const loadingUniverse = ref(false);

const storageKey = "aqs_favorite_stocks";

const boardOptions = ["all", "主板", "创业板", "科创板"];

const growthClass = (value: number) => (value >= 0 ? "text-[var(--color-up)]" : "text-[var(--color-down)]");
const formatPct = (value: number) => `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;

const totalStocksLabel = computed(() => `共 ${filteredStocks.value.length} 只`);
const watchCount = computed(() => favorites.value.length);
const selectedUniverseLabel = computed(() => universeOptions.value.find((item) => item.key === selectedUniverse.value)?.label ?? "当前股票池");

const filteredStocks = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();

  let result = stocks.value.filter((stock) => {
    const matchKeyword =
      !keyword ||
      stock.name.toLowerCase().includes(keyword) ||
      stock.code.toLowerCase().includes(keyword) ||
      stock.thsCode.toLowerCase().includes(keyword);

    const matchMarket = marketFilter.value === "all" || stock.market === marketFilter.value;
    const matchBoard = boardFilter.value === "all" || stock.marketType === boardFilter.value;
    const matchProfit = stock.profitGrowth >= minProfitGrowth.value;
    const matchFavorite = !favoritesOnly.value || favorites.value.includes(stock.thsCode);

    return matchKeyword && matchMarket && matchBoard && matchProfit && matchFavorite;
  });

  result = [...result].sort((a, b) => {
    switch (sortBy.value) {
      case "price_desc":
        return b.price - a.price;
      case "pe_asc":
        return a.pe - b.pe;
      case "change_desc":
        return b.change - a.change;
      case "roe_desc":
        return b.roe - a.roe;
      case "ff_score_desc":
        return b.ffScore - a.ffScore;
      case "alpha_desc":
        return b.alpha - a.alpha;
      case "profit_desc":
      default:
        return b.profitGrowth - a.profitGrowth;
    }
  });

  return result;
});

const summary = computed(() => {
  const data = filteredStocks.value;
  const avgPe = data.length ? data.reduce((sum, item) => sum + item.pe, 0) / data.length : 0;
  const avgScore = data.length ? data.reduce((sum, item) => sum + item.ffScore, 0) / data.length : 0;
  const avgGrowth = data.length ? data.reduce((sum, item) => sum + item.profitGrowth, 0) / data.length : 0;
  const positiveCount = data.filter((item) => item.change >= 0).length;
  return {
    avgPe,
    avgScore,
    avgGrowth,
    positiveCount,
    total: data.length,
  };
});

const isFavorite = (thsCode: string) => favorites.value.includes(thsCode);

const toggleFavorite = (thsCode: string) => {
  if (isFavorite(thsCode)) {
    favorites.value = favorites.value.filter((code) => code !== thsCode);
  } else {
    favorites.value = [...favorites.value, thsCode];
  }
};

const clearFilters = () => {
  searchKeyword.value = "";
  marketFilter.value = "all";
  boardFilter.value = "all";
  sortBy.value = "profit_desc";
  minProfitGrowth.value = -10;
  favoritesOnly.value = false;
};

const exportCsv = () => {
  const headers = ["thsCode", "code", "name", "market", "marketType", "ffScore", "alpha", "betaMkt", "betaSmb", "betaHml", "betaRmw", "betaCma", "price", "change", "pe", "revGrowth", "profitGrowth", "roe"];
  const rows = filteredStocks.value.map((stock) => [
    stock.thsCode,
    stock.code,
    stock.name,
    stock.market,
    stock.marketType,
    stock.ffScore.toFixed(2),
    stock.alpha.toFixed(4),
    stock.betaMkt.toFixed(3),
    stock.betaSmb.toFixed(3),
    stock.betaHml.toFixed(3),
    stock.betaRmw.toFixed(3),
    stock.betaCma.toFixed(3),
    stock.price.toFixed(2),
    stock.change.toFixed(2),
    stock.pe.toFixed(2),
    stock.revGrowth.toFixed(2),
    stock.profitGrowth.toFixed(2),
    stock.roe.toFixed(2),
  ]);

  const csv = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `stock-pool-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};

const refreshUniverse = async () => {
  loadingUniverse.value = true;
  try {
    await previewUniverse(selectedUniverse.value);
  } finally {
    loadingUniverse.value = false;
  }
};

const handleUniverseSelect = async (key: string) => {
  setSelectedUniverse(key);
  await refreshUniverse();
};

onMounted(async () => {
  const raw = localStorage.getItem(storageKey);
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as string[];
      favorites.value = parsed;
    } catch {
      favorites.value = [];
    }
  }
  try {
    await loadUniverses();
    await refreshUniverse();
  } catch {
    // 股票池预览失败时，保留已有筛选结果。
  }
});

watch(
  favorites,
  (nextValue) => {
    localStorage.setItem(storageKey, JSON.stringify(nextValue));
  },
  { deep: true },
);
</script>

<template>
  <div v-if="isDesktopView" class="w-full h-full flex flex-col gap-3 text-sm">
    <div class="glass-panel rounded-xl p-3 space-y-3">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <div class="text-sm font-semibold text-slate-800 inline-flex items-center gap-2">
            <Database class="w-4 h-4 text-blue-600" />
            股票池范围
          </div>
          <p class="text-xs text-slate-500 mt-1">{{ selectedUniverseLabel }}，预览 {{ universePreviewCount || stocks.length }} 只成分股</p>
        </div>
        <div class="flex items-center gap-2">
          <select
            :value="selectedUniverse"
            class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs outline-none focus:border-blue-400"
            :disabled="isRunning || loadingUniverse"
            @change="(event) => handleUniverseSelect((event.target as HTMLSelectElement).value)"
          >
            <option v-for="item in universeOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
          <button
            class="px-3 py-2 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 hover:border-blue-300 inline-flex items-center gap-1"
            :disabled="loadingUniverse"
            @click="refreshUniverse"
          >
            <RefreshCw class="w-4 h-4" :class="loadingUniverse ? 'animate-spin' : ''" />
            刷新
          </button>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <div class="flex-1 relative">
          <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索代码 / 名称 / THS 代码"
            class="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 bg-white text-sm outline-none focus:border-blue-400"
          />
        </div>
        <button
          class="px-3 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 transition-colors inline-flex items-center gap-1"
          @click="exportCsv"
        >
          <Download class="w-4 h-4" />
          导出 CSV
        </button>
      </div>

      <div class="grid grid-cols-6 gap-2">
        <label class="col-span-1">
          <span class="text-[11px] text-[var(--color-text-secondary)]">市场</span>
          <select v-model="marketFilter" class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs">
            <option value="all">全部</option>
            <option value="SH">沪市 SH</option>
            <option value="SZ">深市 SZ</option>
          </select>
        </label>

        <label class="col-span-1">
          <span class="text-[11px] text-[var(--color-text-secondary)]">板块</span>
          <select v-model="boardFilter" class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs">
            <option v-for="option in boardOptions" :key="option" :value="option">{{ option === "all" ? "全部" : option }}</option>
          </select>
        </label>

        <label class="col-span-1">
          <span class="text-[11px] text-[var(--color-text-secondary)]">排序</span>
          <select v-model="sortBy" class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs">
            <option value="profit_desc">净利增长率 ↓</option>
            <option value="ff_score_desc">五因子评分 ↓</option>
            <option value="alpha_desc">Alpha ↓</option>
            <option value="roe_desc">ROE ↓</option>
            <option value="change_desc">涨跌幅 ↓</option>
            <option value="pe_asc">PE ↑</option>
            <option value="price_desc">价格 ↓</option>
          </select>
        </label>

        <label class="col-span-2">
          <span class="text-[11px] text-[var(--color-text-secondary)]">净利增速下限: {{ minProfitGrowth.toFixed(1) }}%</span>
          <input v-model.number="minProfitGrowth" type="range" min="-20" max="60" step="1" class="mt-2 w-full" />
        </label>

        <div class="col-span-1 flex items-end justify-between gap-2">
          <button
            class="px-3 py-1.5 rounded-lg border text-xs"
            :class="favoritesOnly ? 'bg-amber-100 border-amber-300 text-amber-700' : 'bg-white border-slate-200 text-slate-600'"
            @click="favoritesOnly = !favoritesOnly"
          >
            自选 {{ favoritesOnly ? "开" : "关" }}
          </button>
          <button class="px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-600" @click="clearFilters">重置</button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-4 gap-3">
      <div class="glass-panel rounded-xl p-3">
        <div class="text-[11px] text-[var(--color-text-secondary)]">候选数量</div>
        <div class="mt-1 text-xl font-bold">{{ summary.total }}</div>
      </div>
      <div class="glass-panel rounded-xl p-3">
        <div class="text-[11px] text-[var(--color-text-secondary)]">平均五因子分</div>
        <div class="mt-1 text-xl font-bold">{{ summary.avgScore.toFixed(1) }}</div>
      </div>
      <div class="glass-panel rounded-xl p-3">
        <div class="text-[11px] text-[var(--color-text-secondary)]">平均净利增长</div>
        <div class="mt-1 text-xl font-bold" :class="growthClass(summary.avgGrowth)">{{ formatPct(summary.avgGrowth) }}</div>
      </div>
      <div class="glass-panel rounded-xl p-3">
        <div class="text-[11px] text-[var(--color-text-secondary)]">当日上涨家数</div>
        <div class="mt-1 text-xl font-bold">{{ summary.positiveCount }}</div>
      </div>
    </div>

    <div class="glass-panel rounded-xl overflow-hidden flex-1 min-h-0">
      <table v-if="filteredStocks.length > 0" class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-[var(--color-surface-border)] bg-slate-50 sticky top-0 z-10">
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-center">关注</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)]">代码</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)]">简称</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)]">板块</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">FF5</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">Alpha</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">最新价</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">涨跌幅</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">PE</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">营收同比</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">净利同比</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-right">ROE</th>
            <th class="px-3 py-3 font-medium text-[var(--color-text-secondary)] text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="stock in filteredStocks"
            :key="stock.thsCode"
            class="border-b border-[var(--color-surface-border)]/70 cursor-pointer transition-colors hover:bg-blue-50/40"
            :class="selectedStock?.thsCode === stock.thsCode ? 'bg-blue-50 border-blue-200' : ''"
            @click="setSelectedStock(stock)"
          >
            <td class="px-3 py-2 text-center">
              <button class="inline-flex" @click.stop="toggleFavorite(stock.thsCode)">
                <Star class="w-4 h-4" :class="isFavorite(stock.thsCode) ? 'text-amber-500 fill-amber-400' : 'text-slate-300'" />
              </button>
            </td>
            <td class="px-3 py-2 whitespace-nowrap">
              <MarketBadge :market="stock.market" />
              <span class="font-mono text-slate-700">{{ stock.code }}</span>
            </td>
            <td class="px-3 py-2 font-medium text-slate-800">{{ stock.name }}</td>
            <td class="px-3 py-2 text-slate-500">{{ stock.marketType }}</td>
            <td class="px-3 py-2 text-right font-mono font-semibold text-blue-700">{{ stock.ffScore.toFixed(1) }}</td>
            <td class="px-3 py-2 text-right font-mono" :class="growthClass(stock.alpha)">{{ stock.alpha.toFixed(3) }}</td>
            <td class="px-3 py-2 text-right font-mono font-semibold text-slate-800">{{ stock.price.toFixed(2) }}</td>
            <td class="px-3 py-2 text-right">
              <PriceChangeTag :value="stock.change" />
            </td>
            <td class="px-3 py-2 text-right font-mono text-slate-600">{{ stock.pe.toFixed(1) }}</td>
            <td class="px-3 py-2 text-right font-mono" :class="growthClass(stock.revGrowth)">{{ formatPct(stock.revGrowth) }}</td>
            <td class="px-3 py-2 text-right font-mono" :class="growthClass(stock.profitGrowth)">{{ formatPct(stock.profitGrowth) }}</td>
            <td class="px-3 py-2 text-right font-mono" :class="growthClass(stock.roe)">{{ formatPct(stock.roe) }}</td>
            <td class="px-3 py-2 text-center">
              <button
                class="p-1.5 rounded-md bg-blue-50 hover:bg-blue-100 hover:text-blue-700 text-blue-600 transition-colors cursor-pointer inline-flex items-center justify-center border border-blue-200"
                @click.stop="setSelectedStock(stock)"
              >
                <Eye class="w-4 h-4" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="h-full min-h-[260px] flex flex-col items-center justify-center text-[var(--color-text-secondary)] text-sm gap-2">
        <p>{{ isRunning ? "后端正在筛选，请稍候..." : "没有符合当前筛选条件的股票。" }}</p>
        <button class="px-3 py-1.5 rounded-md border border-slate-200 bg-white text-slate-600 text-xs" @click="clearFilters">清空筛选</button>
      </div>
    </div>
  </div>

  <div v-else class="p-4 space-y-4 bg-[var(--color-background)] min-h-full">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-lg font-bold">股票池</h2>
        <p class="text-xs text-slate-500 mt-1">{{ selectedUniverseLabel }}</p>
      </div>
      <span class="text-xs px-2 py-1 rounded bg-blue-50 border border-blue-200 text-blue-700">{{ totalStocksLabel }}</span>
    </div>

    <div class="glass-panel rounded-xl p-3 flex items-center gap-2">
      <select
        :value="selectedUniverse"
        class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
        :disabled="isRunning || loadingUniverse"
        @change="(event) => handleUniverseSelect((event.target as HTMLSelectElement).value)"
      >
        <option v-for="item in universeOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
      </select>
      <button class="p-2 rounded-lg border border-slate-200 bg-white text-blue-600" :disabled="loadingUniverse" @click="refreshUniverse">
        <RefreshCw class="w-4 h-4" :class="loadingUniverse ? 'animate-spin' : ''" />
      </button>
    </div>

    <div v-if="filteredStocks.length === 0" class="glass-panel rounded-xl p-6 text-sm text-[var(--color-text-secondary)] text-center">
      {{ isRunning ? "后端正在筛选，请稍候..." : "暂无结果，先去聊天区输入选股条件。" }}
    </div>

    <div
      v-for="stock in filteredStocks"
      :key="stock.thsCode"
      class="glass-panel rounded-xl p-4 transition-transform active:scale-[0.98]"
      :class="selectedStock?.thsCode === stock.thsCode ? 'border-blue-300 shadow-[0_0_15px_rgba(59,130,246,0.12)] bg-blue-50/40' : ''"
      @click="setSelectedStock(stock)"
    >
      <div class="flex justify-between items-start mb-4 border-b border-slate-200 pb-3">
        <div>
          <div class="flex items-center space-x-2 mb-1">
            <span class="font-bold text-lg tracking-wide">{{ stock.name }}</span>
            <MarketBadge :market="stock.market" />
            <button class="inline-flex" @click.stop="toggleFavorite(stock.thsCode)">
              <Star class="w-4 h-4" :class="isFavorite(stock.thsCode) ? 'text-amber-500 fill-amber-400' : 'text-slate-300'" />
            </button>
          </div>
          <span class="font-mono text-slate-500 text-xs tracking-wider">{{ stock.thsCode }}</span>
        </div>
        <div class="text-right">
          <div class="text-xs text-slate-500 mb-1">FF5 {{ stock.ffScore.toFixed(1) }}</div>
          <div class="text-2xl font-mono font-bold tracking-tight" :class="growthClass(stock.change)">
            {{ stock.price.toFixed(2) }}
          </div>
          <PriceChangeTag :value="stock.change" class-name="text-xs px-1.5 py-0 mt-1 block w-max ml-auto" />
        </div>
      </div>

      <div class="grid grid-cols-4 gap-2 mb-4">
        <div class="flex flex-col items-center justify-center bg-slate-50 rounded p-1.5 border border-slate-200">
          <span class="text-[10px] text-slate-500 uppercase tracking-tight mb-1">Alpha</span>
          <span class="text-xs font-mono font-semibold" :class="growthClass(stock.alpha)">{{ stock.alpha.toFixed(3) }}</span>
        </div>
        <div class="flex flex-col items-center justify-center bg-slate-50 rounded p-1.5 border border-slate-200">
          <span class="text-[10px] text-slate-500 uppercase tracking-tight mb-1">营收同比</span>
          <span class="text-xs font-mono font-semibold" :class="growthClass(stock.revGrowth)">
            {{ formatPct(stock.revGrowth) }}
          </span>
        </div>
        <div class="flex flex-col items-center justify-center bg-slate-50 rounded p-1.5 border border-slate-200">
          <span class="text-[10px] text-slate-500 uppercase tracking-tight mb-1">净利同比</span>
          <span class="text-xs font-mono font-semibold" :class="growthClass(stock.profitGrowth)">
            {{ formatPct(stock.profitGrowth) }}
          </span>
        </div>
        <div class="flex flex-col items-center justify-center bg-slate-50 rounded p-1.5 border border-slate-200">
          <span class="text-[10px] text-slate-500 uppercase tracking-tight mb-1">ROE</span>
          <span class="text-xs font-mono font-semibold text-slate-700">{{ formatPct(stock.roe) }}</span>
        </div>
      </div>

      <button
        class="w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 transition-colors flex items-center justify-center cursor-pointer"
        @click.stop="openMobileSheet(stock)"
      >
        <Eye class="w-4 h-4 mr-2" />
        查看 AI 研判
      </button>
    </div>

    <div class="text-xs text-[var(--color-text-secondary)]">自选股票：{{ watchCount }} 只</div>
  </div>
</template>
