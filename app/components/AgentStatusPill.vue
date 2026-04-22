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
    return "border-blue-500/50 bg-blue-500/10 shadow-[0_0_10px_rgba(59,130,246,0.3)]";
  }
  if (props.status === "success") {
    return "border-green-500/30 bg-green-500/10 text-green-400";
  }
  return "border-white/5 bg-white/5 text-gray-500";
});
</script>

<template>
  <div class="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border glass-panel transition-all" :class="cardClass">
    <template v-if="status === 'loading'">
      <Loader2 class="w-3.5 h-3.5 animate-spin text-blue-400" />
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
