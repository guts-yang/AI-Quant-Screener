<script setup lang="ts">
import { computed } from "vue";
import { useAppStore } from "../store";
import MarkdownReport from "../components/MarkdownReport.vue";
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

const { selectedStock, finalReport, riskAssessment } = useAppStore();

const changeClass = computed(() => {
  if (!selectedStock.value) return "text-[var(--color-text-primary)]";
  return selectedStock.value.change >= 0 ? "text-[var(--color-up)]" : "text-[var(--color-down)]";
});
</script>

<template>
  <div
    v-if="!selectedStock"
    class="flex flex-col items-center justify-center h-full text-[var(--color-text-secondary)] space-y-4"
  >
    <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
      <span class="text-2xl opacity-50">📊</span>
    </div>
    <p>在左侧列表中选择一只股票以查看详细研报</p>
  </div>

  <div v-else class="w-full h-full text-[var(--color-text-primary)] relative" :class="!props.isDesktop ? 'pt-2' : ''">
    <div class="flex items-start justify-between mb-6 pb-4 border-b border-[var(--color-surface-border)] sticky top-0 bg-[var(--color-background)] z-10">
      <div>
        <div class="flex items-center space-x-2 mb-1">
          <h2 class="text-xl font-bold tracking-wider">{{ selectedStock.name }}</h2>
          <MarketBadge :market="selectedStock.market" />
          <span class="text-sm text-gray-400 font-mono tracking-widest">{{ selectedStock.thsCode }}</span>
        </div>
        <div class="flex items-baseline space-x-3">
          <span class="text-3xl font-mono font-bold tracking-tight" :class="changeClass">
            {{ selectedStock.price.toFixed(2) }}
          </span>
          <PriceChangeTag :value="selectedStock.change" class-name="text-sm px-2 py-0.5" />
        </div>
      </div>

      <div class="px-3 py-1 bg-yellow-500/10 border border-yellow-500/30 text-yellow-500 rounded-full text-xs font-bold uppercase tracking-wider shadow-[0_0_15px_rgba(234,179,8,0.2)]">
        核心标的
      </div>
    </div>

    <MarkdownReport :content="finalReport" />

    <div
      v-if="riskAssessment"
      class="mt-6 p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-xs text-yellow-200 leading-relaxed"
    >
      <strong class="text-yellow-400">风险摘要：</strong>{{ riskAssessment }}
    </div>

    <div class="mt-8 pt-4 border-t border-[var(--color-surface-border)] text-xs text-[var(--color-text-secondary)] text-center opacity-60">
      <p>本研报由 AI Quant Screener 自动生成，仅供参考，不构成投资建议。</p>
      <p>市场有风险，投资需谨慎。</p>
    </div>
  </div>
</template>
