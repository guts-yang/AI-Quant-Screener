<script setup lang="ts">
import { useAppStore } from "../store";
import ReportView from "../views/ReportView.vue";

const { isMobileSheetOpen, closeMobileSheet } = useAppStore();
</script>

<template>
  <Transition name="fade">
    <div
      v-if="isMobileSheetOpen"
      class="fixed inset-0 bg-slate-900/30 z-40 md:hidden backdrop-blur-[2px]"
      @click="closeMobileSheet"
    />
  </Transition>

  <Transition name="slide-up">
    <div
      v-if="isMobileSheetOpen"
      class="fixed bottom-0 left-0 right-0 h-[75vh] bg-[var(--color-surface)] border-t border-[var(--color-surface-border)] rounded-t-3xl z-50 md:hidden flex flex-col shadow-[0_-10px_40px_rgba(0,0,0,0.5)] overflow-hidden"
    >
      <div
        class="w-full flex justify-center pt-3 pb-2 cursor-pointer bg-[var(--color-surface)] sticky top-0 z-10"
        @click="closeMobileSheet"
      >
        <div class="w-12 h-1.5 rounded-full bg-slate-300" />
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar px-6 pb-20">
        <ReportView :is-desktop="false" />
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>

