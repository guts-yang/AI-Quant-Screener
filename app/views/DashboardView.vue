<script setup lang="ts">
import ChatView from "./ChatView.vue";
import PoolView from "./PoolView.vue";
import ReportView from "./ReportView.vue";
</script>

<template>
  <div class="flex w-full h-full bg-[var(--color-background)]">
    <div class="w-[400px] border-r border-[var(--color-surface-border)] h-full bg-[var(--color-surface)] relative z-10">
      <ChatView />
    </div>

    <div class="flex-1 flex flex-col h-full bg-[var(--color-background)] overflow-hidden">
      <div class="h-[55%] border-b border-[var(--color-surface-border)] overflow-hidden relative group p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold tracking-wide flex items-center">
            <span class="w-1.5 h-6 bg-blue-600 rounded-sm mr-2.5"></span>
            AI 量化初筛股票池
          </h2>
          <span class="text-xs px-2 py-1 rounded bg-blue-50 border border-blue-200 text-blue-700 font-mono">
            实时联动后端
          </span>
        </div>

        <div class="h-[calc(100%-2rem)] overflow-y-auto pr-2 custom-scrollbar">
          <PoolView :is-desktop="true" />
        </div>
      </div>

      <div class="h-[45%] overflow-hidden relative bg-[var(--color-background)] p-8 pt-6">
        <div class="flex items-center space-x-3 mb-6 border-b border-[var(--color-surface-border)] pb-3">
          <div class="w-8 h-8 rounded-lg bg-amber-100 border border-amber-200 flex items-center justify-center">
            <span class="text-amber-700 font-bold text-lg">CIO</span>
          </div>
          <div>
            <h3 class="font-semibold text-[var(--color-text-primary)]">深度研报分析</h3>
            <p class="text-xs text-[var(--color-text-secondary)]">Agent-generated insights &amp; risk control</p>
          </div>
        </div>

        <div class="h-full overflow-y-auto pb-10 custom-scrollbar pr-4">
          <ReportView :is-desktop="true" />
        </div>
      </div>
    </div>
  </div>
</template>
