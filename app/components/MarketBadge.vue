<script setup lang="ts">
defineProps<{
  market: "SH" | "SZ";
}>();
</script>

<template>
  <span
    class="text-[10px] font-bold px-1.5 py-0.5 rounded mr-1.5 font-mono"
    :class="market === 'SH' ? 'bg-fuchsia-900/40 text-fuchsia-400' : 'bg-sky-900/40 text-sky-400'"
  >
    {{ market }}
  </span>
</template>

