<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Sparkles, User, BrainCircuit, Activity, Send, Database } from "lucide-vue-next";
import AgentStatusPill from "../components/AgentStatusPill.vue";
import { useAppStore } from "../store";

const {
  chatHistory,
  addChatMessage,
  agentStatuses,
  isRunning,
  runScreener,
  stopScreener,
  streamMessage,
  cioThinking,
  universeOptions,
  selectedUniverse,
  setSelectedUniverse,
  loadUniverses,
  previewUniverse,
} = useAppStore();

const input = ref("");
const scrollRef = ref<HTMLDivElement | null>(null);

const hasLoadingAgent = computed(() => Object.values(agentStatuses.value).some((status) => status === "loading"));
const selectedUniverseText = computed(() => universeOptions.value.find((item) => item.key === selectedUniverse.value)?.label ?? "当前股票池");

watch(
  [chatHistory, agentStatuses],
  async () => {
    await nextTick();
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
    }
  },
  { deep: true },
);

const handleSend = async () => {
  const text = input.value.trim();
  if (!text || isRunning.value) return;

  addChatMessage({ sender: "user", text });
  input.value = "";

  try {
    await runScreener(text);
  } catch (error) {
    const message = error instanceof Error ? error.message : "未知错误";
    addChatMessage({
      sender: "ai",
      text: `本次执行失败：${message}`,
    });
  }
};

const handleUniverseChange = async () => {
  try {
    await previewUniverse(selectedUniverse.value);
  } catch {
    // 预览失败不影响用户发起筛选，后端运行时仍会尝试拉取。
  }
};

onMounted(async () => {
  try {
    await loadUniverses();
    await previewUniverse(selectedUniverse.value);
  } catch {
    // 保留本地默认选项。
  }
});

onBeforeUnmount(() => {
  stopScreener();
});
</script>

<template>
  <div class="flex flex-col h-full bg-[var(--color-surface)] relative z-10 w-full overflow-hidden md:rounded-xl md:border md:border-[var(--color-surface-border)]">
    <div class="h-14 border-b border-[var(--color-surface-border)] flex items-center justify-between px-4 sticky top-0 bg-[var(--color-surface)] z-20">
      <div class="flex items-center space-x-2">
        <BrainCircuit class="w-5 h-5 text-blue-600" />
        <span class="font-bold text-sm tracking-wide bg-gradient-to-r from-blue-700 to-indigo-500 bg-clip-text text-transparent">智能选股助手</span>
      </div>
      <div class="flex items-center space-x-1 text-[10px] text-emerald-700 bg-emerald-100 px-2 py-1 rounded-full border border-emerald-200">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
        <span>后端已连接</span>
      </div>
    </div>

    <div class="px-4 py-3 border-b border-[var(--color-surface-border)] bg-[var(--color-background)]">
      <div class="flex items-center justify-between gap-3 mb-3">
        <div>
          <div class="text-xs text-[var(--color-text-secondary)] font-medium mb-1">智能体工作流</div>
          <div class="text-[11px] text-slate-500">当前范围：{{ selectedUniverseText }}</div>
        </div>
        <label class="inline-flex items-center gap-1.5 text-xs text-slate-600">
          <Database class="w-3.5 h-3.5 text-blue-600" />
          <select
            :value="selectedUniverse"
            class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-blue-400"
            :disabled="isRunning"
            @change="(event) => { setSelectedUniverse((event.target as HTMLSelectElement).value); handleUniverseChange(); }"
          >
            <option v-for="item in universeOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
        </label>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <AgentStatusPill name="数据" :status="agentStatuses.data" />
        <AgentStatusPill name="因子" :status="agentStatuses.factor" />
        <AgentStatusPill name="筛选" :status="agentStatuses.quant" />
        <AgentStatusPill name="风控" :status="agentStatuses.risk" />
        <AgentStatusPill name="研报" :status="agentStatuses.cio" class="col-span-2" />
      </div>
      <p v-if="streamMessage" class="mt-2 text-xs text-[var(--color-text-secondary)]">{{ streamMessage }}</p>
      <div
        v-if="cioThinking"
        class="mt-2 rounded-md border border-blue-200 bg-blue-50 p-2 text-[11px] leading-5 text-blue-800"
      >
        <div class="font-semibold text-blue-700 mb-1">研报生成进度</div>
        <pre class="whitespace-pre-wrap break-words font-sans">{{ cioThinking }}</pre>
      </div>
    </div>

    <div ref="scrollRef" class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth custom-scrollbar bg-[var(--color-background)]">
      <div
        v-for="msg in chatHistory"
        :key="msg.id"
        class="flex max-w-[85%] mb-4"
        :class="msg.sender === 'user' ? 'ml-auto' : 'mr-auto'"
      >
        <div
          v-if="msg.sender === 'ai'"
          class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2 border border-blue-200 shrink-0"
        >
          <Sparkles class="w-4 h-4 text-blue-600" />
        </div>

        <div
          class="p-3 rounded-2xl text-[13px] leading-relaxed relative border"
          :class="
            msg.sender === 'user'
              ? 'bg-blue-600 text-white border-blue-600 rounded-tr-sm'
              : 'bg-white text-[var(--color-text-primary)] border-[var(--color-surface-border)] rounded-tl-sm'
          "
        >
          {{ msg.text }}
          <div
            v-if="msg.isAction"
            class="mt-3 pt-3 border-t border-blue-100 flex items-center space-x-2 text-xs text-blue-700"
          >
            <Activity class="w-4 h-4" />
            <span>查看最新股票池与研报</span>
          </div>
        </div>

        <div
          v-if="msg.sender === 'user'"
          class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center ml-2 border border-slate-200 shrink-0"
        >
          <User class="w-4 h-4 text-slate-600" />
        </div>
      </div>

      <div v-if="hasLoadingAgent || isRunning" class="flex items-center space-x-2 text-[var(--color-text-secondary)] text-sm ml-10">
        <div class="flex space-x-1">
          <div class="w-1.5 h-1.5 bg-blue-500/60 rounded-full animate-bounce" style="animation-delay: 0ms" />
          <div class="w-1.5 h-1.5 bg-blue-500/60 rounded-full animate-bounce" style="animation-delay: 150ms" />
          <div class="w-1.5 h-1.5 bg-blue-500/60 rounded-full animate-bounce" style="animation-delay: 300ms" />
        </div>
        <span class="text-xs">正在分析，请稍候...</span>
      </div>
    </div>

    <div class="p-4 bg-[var(--color-surface)] border-t border-[var(--color-surface-border)]">
      <div class="relative flex items-center glass-panel rounded-xl overflow-hidden shadow-inner-white">
        <div class="pl-3 pr-2 text-slate-400 font-mono text-sm shrink-0 flex items-center">/</div>
        <input
          v-model="input"
          type="text"
          placeholder="输入选股策略，例如：筛选低估值且净利润增长为正的主板股票"
          class="flex-1 bg-transparent border-none focus:ring-0 text-sm py-3 px-2 text-[var(--color-text-primary)] placeholder-slate-400 outline-none"
          @keydown.enter="handleSend"
        />
        <button
          class="p-2 mr-1 text-blue-600 hover:text-blue-500 disabled:opacity-30 disabled:hover:text-blue-600 transition-colors cursor-pointer"
          :disabled="!input.trim() || isRunning"
          @click="handleSend"
        >
          <Send class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>
