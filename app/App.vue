<script setup lang="ts">
import { computed } from "vue";
import { useRoute, RouterView } from "vue-router";
import { MessageSquare, LayoutGrid, FileText, User, Terminal } from "lucide-vue-next";
import DashboardView from "./views/DashboardView.vue";
import MobileBottomSheet from "./components/MobileBottomSheet.vue";

interface NavItem {
  to: string;
  label: string;
  icon: typeof MessageSquare;
}

const route = useRoute();
const activePath = computed(() => route.path);

const navItems: NavItem[] = [
  { to: "/chat", label: "AI 对话", icon: MessageSquare },
  { to: "/pool", label: "股票池", icon: LayoutGrid },
  { to: "/report", label: "研报", icon: FileText },
  { to: "/profile", label: "我的", icon: User },
];
</script>

<template>
  <div class="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] font-sans overflow-hidden flex flex-col md:flex-row select-none">
    <div class="hidden md:flex flex-1 w-full h-screen overflow-hidden">
      <DashboardView />
    </div>

    <div class="md:hidden flex flex-col h-screen w-full relative">
      <header class="h-14 shrink-0 border-b border-[var(--color-surface-border)] bg-[var(--color-surface)] flex items-center justify-between px-4 sticky top-0 z-20 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
        <div class="flex items-center space-x-2">
          <Terminal class="w-5 h-5 text-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.6)]" />
          <span class="font-bold text-sm tracking-wide bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">AI Quant Screener</span>
        </div>
        <div class="flex items-center space-x-1.5 text-[10px] text-green-400 bg-green-500/10 px-2 py-1 rounded-full border border-green-500/20 shadow-[0_0_8px_rgba(46,189,133,0.3)] font-medium tracking-wide uppercase">
          <div class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span>Screener Online</span>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto pb-[calc(env(safe-area-inset-bottom)+70px)] scroll-smooth relative bg-[var(--color-background)]">
        <RouterView />
      </main>

      <nav class="fixed bottom-0 left-0 right-0 z-30 bg-[var(--color-surface)] border-t border-[var(--color-surface-border)] pb-[env(safe-area-inset-bottom)] shadow-[0_-4px_20px_rgba(0,0,0,0.6)]">
        <div class="flex justify-around items-center h-16 px-2">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex flex-col items-center justify-center w-full h-full space-y-1 transition-all duration-300 relative"
            :class="activePath === item.to ? 'text-blue-500' : 'text-[var(--color-text-secondary)] hover:text-white'"
          >
            <div
              v-if="activePath === item.to"
              class="absolute top-0 w-10 h-[2px] bg-blue-500 rounded-b-md shadow-[0_2px_8px_rgba(59,130,246,0.8)]"
            />
            <component
              :is="item.icon"
              class="w-5 h-5 transition-transform duration-300"
              :class="activePath === item.to ? '-translate-y-1' : ''"
            />
            <span
              class="text-[10px] font-bold tracking-wider uppercase transition-opacity duration-300"
              :class="activePath === item.to ? 'opacity-100' : 'opacity-70'"
            >
              {{ item.label }}
            </span>
          </RouterLink>
        </div>
      </nav>

      <MobileBottomSheet />
    </div>
  </div>
</template>
