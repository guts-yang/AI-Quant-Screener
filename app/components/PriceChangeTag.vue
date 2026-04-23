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
    class="font-mono rounded px-2 py-0.5 inline-flex items-center justify-center font-bold border"
    :class="[
      isUp ? 'bg-[var(--color-up-bg)] text-[var(--color-up)] border-red-200' : 'bg-[var(--color-down-bg)] text-[var(--color-down)] border-green-200',
      className,
    ]"
  >
    {{ displayValue }}
  </span>
</template>
