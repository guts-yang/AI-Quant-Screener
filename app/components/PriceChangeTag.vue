<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    value: number;
    className?: string;
    showSign?: boolean;
  }>(),
  {
    className: "",
    showSign: true,
  },
);

const isUp = computed(() => props.value >= 0);
const displayValue = computed(() => {
  const prefix = props.showSign ? (isUp.value ? "+" : "") : "";
  return `${prefix}${props.value.toFixed(2)}%`;
});
</script>

<template>
  <span
    class="font-mono rounded px-2 py-0.5 inline-flex items-center justify-center font-bold"
    :class="[
      isUp ? 'bg-[#3A1015] text-[var(--color-up)]' : 'bg-[#0A291A] text-[var(--color-down)]',
      className,
    ]"
  >
    {{ displayValue }}
  </span>
</template>

