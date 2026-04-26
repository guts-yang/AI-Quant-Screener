<script setup lang="ts">
defineProps<{
  market: "SH" | "SZ";
}>();
</script>

<template>
  <span
    class="text-[10px] font-bold px-1.5 py-0.5 rounded mr-1.5 font-mono border"
    :class="market === 'SH' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'"
  >
    {{ market === "SH" ? "沪市" : "深市" }}
  </span>
</template>
