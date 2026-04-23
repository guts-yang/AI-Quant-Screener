<script setup lang="ts">
import { computed } from "vue";
import { Loader2, Check, Clock } from "lucide-vue-next";
import type { AgentStatusType } from "../store";

const props = defineProps<{
  name: string;
  status: AgentStatusType;
}>();

const cardClass = computed(() => {
  if (props.status === "loading") {
    return "border-blue-300 bg-blue-50 text-blue-700 shadow-[0_6px_14px_rgba(37,99,235,0.15)]";
  }
  if (props.status === "success") {
    return "border-emerald-300 bg-emerald-50 text-emerald-700";
  }
  return "border-slate-200 bg-white text-slate-500";
});
</script>

<template>
  <div class="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all" :class="cardClass">
    <template v-if="status === 'loading'">
      <Loader2 class="w-3.5 h-3.5 animate-spin text-blue-600" />
      <span>{{ name }} 分析中...</span>
    </template>
    <template v-else-if="status === 'success'">
      <Check class="w-3.5 h-3.5" />
      <span>{{ name }} 已完成</span>
    </template>
    <template v-else>
      <Clock class="w-3.5 h-3.5 opacity-50" />
      <span>{{ name }} 待机</span>
    </template>
  </div>
</template>
