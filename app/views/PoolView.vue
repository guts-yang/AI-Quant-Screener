<script setup lang="ts">
import { computed } from "vue";
import { Eye } from "lucide-vue-next";
import { useAppStore } from "../store";
import MarketBadge from "../components/MarketBadge.vue";
import PriceChangeTag from "../components/PriceChangeTag.vue";

const props = withDefaults(
  defineProps<{
    isDesktop?: boolean;
  }>(),
  {
    isDesktop: false,
  },
);

const { stocks, selectedStock, setSelectedStock, openMobileSheet, isRunning } = useAppStore();

const totalStocksLabel = computed(() => `共 ${stocks.value.length} 只`);

const growthClass = (value: number) => (value >= 0 ? "text-[var(--color-up)]" : "text-[var(--color-down)]");
const formatPct = (value: number) => `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
</script>

<template>
  <div
    v-if="props.isDesktop"
    class="w-full bg-[var(--color-surface)] border-y border-[var(--color-surface-border)] shadow-xl overflow-hidden glass-panel rounded-xl text-sm"
  >
    <table v-if="stocks.length > 0" class="w-full text-left border-collapse">
      <thead>
        <tr class="border-b border-[var(--color-surface-border)] bg-[var(--color-background)]/50">
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)]">代码</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)]">简称</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)] text-right">最新价</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)] text-right">涨跌幅</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)] text-right">PE(TTM)</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)] text-right">营收同比</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)] text-right">净利同比</th>
          <th class="px-4 py-3 font-medium text-[var(--color-text-secondary)] text-center">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="stock in stocks"
          :key="stock.thsCode"
          class="border-b border-[var(--color-surface-border)]/50 cursor-pointer transition-colors hover:bg-white/5"
          :class="selectedStock?.thsCode === stock.thsCode ? 'bg-blue-900/20 border-blue-500/20 shadow-[inset_4px_0_0_rgba(59,130,246,1)]' : ''"
          @click="setSelectedStock(stock)"
        >
          <td class="px-4 py-3 whitespace-nowrap">
            <MarketBadge :market="stock.market" />
            <span class="font-mono text-gray-300">{{ stock.code }}</span>
          </td>
          <td class="px-4 py-3 font-medium">{{ stock.name }}</td>
          <td class="px-4 py-3 text-right font-mono font-semibold">{{ stock.price.toFixed(2) }}</td>
          <td class="px-4 py-3 text-right">
            <PriceChangeTag :value="stock.change" />
          </td>
          <td class="px-4 py-3 text-right font-mono text-gray-400">{{ stock.pe.toFixed(1) }}</td>
          <td class="px-4 py-3 text-right font-mono" :class="growthClass(stock.revGrowth)">
            {{ formatPct(stock.revGrowth) }}
          </td>
          <td class="px-4 py-3 text-right font-mono" :class="growthClass(stock.profitGrowth)">
            {{ formatPct(stock.profitGrowth) }}
          </td>
          <td class="px-4 py-3 text-center">
            <button
              class="p-1 rounded bg-white/5 hover:bg-blue-500/20 hover:text-blue-400 text-gray-500 transition-colors cursor-pointer inline-flex items-center justify-center"
              @click.stop="setSelectedStock(stock)"
            >
              <Eye class="w-4 h-4" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="h-full min-h-[240px] flex items-center justify-center text-[var(--color-text-secondary)] text-sm">
      {{ isRunning ? "后端正在筛选，请稍候..." : "暂无股票池结果，请先在左侧发起选股指令。" }}
    </div>
  </div>

  <div v-else class="p-4 space-y-4 bg-[var(--color-background)] min-h-full">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold">今日股票池</h2>
      <span class="text-xs px-2 py-1 rounded bg-white/5 border border-white/10 text-gray-400">{{ totalStocksLabel }}</span>
    </div>

    <div v-if="stocks.length === 0" class="glass-panel rounded-xl p-6 text-sm text-[var(--color-text-secondary)] text-center">
      {{ isRunning ? "后端正在筛选，请稍候..." : "暂无结果，先去聊天区输入选股条件。" }}
    </div>

    <div
      v-for="stock in stocks"
      :key="stock.thsCode"
      class="glass-panel rounded-xl p-4 transition-transform active:scale-[0.98]"
      :class="selectedStock?.thsCode === stock.thsCode ? 'border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)] bg-blue-900/10' : ''"
      @click="setSelectedStock(stock)"
    >
      <div class="flex justify-between items-start mb-4 border-b border-white/5 pb-3">
        <div>
          <div class="flex items-center space-x-2 mb-1">
            <span class="font-bold text-lg tracking-wide">{{ stock.name }}</span>
            <MarketBadge :market="stock.market" />
          </div>
          <span class="font-mono text-gray-500 text-xs tracking-wider">{{ stock.thsCode }}</span>
        </div>
        <div class="text-right">
          <div class="text-2xl font-mono font-bold tracking-tight" :class="growthClass(stock.change)">
            {{ stock.price.toFixed(2) }}
          </div>
          <PriceChangeTag :value="stock.change" class-name="text-xs px-1.5 py-0 mt-1 block w-max ml-auto" />
        </div>
      </div>

      <div class="grid grid-cols-4 gap-2 mb-4">
        <div class="flex flex-col items-center justify-center bg-black/20 rounded p-1.5 border border-white/5">
          <span class="text-[10px] text-gray-500 uppercase tracking-tight mb-1">PE(TTM)</span>
          <span class="text-xs font-mono font-semibold text-gray-300">{{ stock.pe.toFixed(1) }}</span>
        </div>
        <div class="flex flex-col items-center justify-center bg-black/20 rounded p-1.5 border border-white/5">
          <span class="text-[10px] text-gray-500 uppercase tracking-tight mb-1">营收同比</span>
          <span class="text-xs font-mono font-semibold" :class="growthClass(stock.revGrowth)">
            {{ formatPct(stock.revGrowth) }}
          </span>
        </div>
        <div class="flex flex-col items-center justify-center bg-black/20 rounded p-1.5 border border-white/5">
          <span class="text-[10px] text-gray-500 uppercase tracking-tight mb-1">净利同比</span>
          <span class="text-xs font-mono font-semibold" :class="growthClass(stock.profitGrowth)">
            {{ formatPct(stock.profitGrowth) }}
          </span>
        </div>
        <div class="flex flex-col items-center justify-center bg-black/20 rounded p-1.5 border border-white/5">
          <span class="text-[10px] text-gray-500 uppercase tracking-tight mb-1">ROE</span>
          <span class="text-xs font-mono font-semibold text-gray-300">{{ formatPct(stock.roe) }}</span>
        </div>
      </div>

      <button
        class="w-full py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm font-medium hover:bg-blue-500/20 hover:text-blue-400 transition-colors flex items-center justify-center cursor-pointer"
        @click.stop="openMobileSheet(stock)"
      >
        <Eye class="w-4 h-4 mr-2" />
        查看 AI 研判
      </button>
    </div>
  </div>
</template>
