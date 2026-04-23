<script setup lang="ts">
import { computed } from "vue";
import { useRoute, RouterView } from "vue-router";
import { MessageSquare, LayoutGrid, FileText, User, Terminal, PanelLeftClose } from "lucide-vue-next";
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

const pageTitle = computed(() => {
  const target = navItems.find((item) => item.to === activePath.value);
  return target?.label ?? "AI Quant Screener";
});
</script>

<template>
  <div class="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] font-sans overflow-hidden select-none">
    <div class="hidden md:flex h-screen">
      <aside class="w-60 border-r border-[var(--color-surface-border)] bg-[var(--color-surface)] p-4 flex flex-col">
        <div class="flex items-center gap-2 mb-6">
          <div class="w-8 h-8 rounded-lg bg-blue-100 border border-blue-200 flex items-center justify-center">
            <Terminal class="w-4 h-4 text-blue-700" />
          </div>
          <div>
            <p class="text-sm font-bold bg-gradient-to-r from-blue-700 to-indigo-500 bg-clip-text text-transparent">AI Quant Screener</p>
            <p class="text-[10px] text-slate-500">Vue + FastAPI + LangGraph</p>
          </div>
        </div>

        <nav class="space-y-1">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors"
            :class="activePath === item.to ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'text-slate-600 hover:bg-slate-100'"
          >
            <component :is="item.icon" class="w-4 h-4" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div class="mt-auto rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p class="text-xs text-slate-500 mb-1">工作流状态</p>
          <div class="text-[11px] inline-flex items-center gap-1 text-emerald-700 bg-emerald-100 border border-emerald-200 px-2 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Online
          </div>
        </div>
      </aside>

      <main class="flex-1 min-w-0 flex flex-col">
        <header class="h-14 border-b border-[var(--color-surface-border)] bg-[var(--color-surface)] px-6 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <PanelLeftClose class="w-4 h-4 text-slate-400" />
            <h1 class="text-sm font-semibold text-[var(--color-text-primary)]">{{ pageTitle }}</h1>
          </div>
          <div class="text-[10px] text-slate-500">Desktop Workspace</div>
        </header>
        <div class="flex-1 overflow-y-auto p-5">
          <RouterView />
        </div>
      </main>
    </div>

    <div class="md:hidden flex flex-col h-screen w-full relative">
      <header class="h-14 shrink-0 border-b border-[var(--color-surface-border)] bg-[var(--color-surface)] flex items-center justify-between px-4 sticky top-0 z-20 shadow-[0_8px_20px_rgba(15,23,42,0.08)]">
        <div class="flex items-center space-x-2">
          <Terminal class="w-5 h-5 text-blue-600" />
          <span class="font-bold text-sm tracking-wide bg-gradient-to-r from-blue-700 to-indigo-500 bg-clip-text text-transparent">AI Quant Screener</span>
        </div>
        <div class="flex items-center space-x-1.5 text-[10px] text-emerald-700 bg-emerald-100 px-2 py-1 rounded-full border border-emerald-200 font-medium tracking-wide uppercase">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Screener Online</span>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto pb-[calc(env(safe-area-inset-bottom)+70px)] scroll-smooth relative bg-[var(--color-background)]">
        <RouterView />
      </main>

      <nav class="fixed bottom-0 left-0 right-0 z-30 bg-[var(--color-surface)] border-t border-[var(--color-surface-border)] pb-[env(safe-area-inset-bottom)] shadow-[0_-8px_20px_rgba(15,23,42,0.08)]">
        <div class="flex justify-around items-center h-16 px-2">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex flex-col items-center justify-center w-full h-full space-y-1 transition-all duration-300 relative"
            :class="activePath === item.to ? 'text-blue-700' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'"
          >
            <div v-if="activePath === item.to" class="absolute top-0 w-10 h-[2px] bg-blue-600 rounded-b-md" />
            <component :is="item.icon" class="w-5 h-5 transition-transform duration-300" :class="activePath === item.to ? '-translate-y-1' : ''" />
            <span class="text-[10px] font-bold tracking-wider uppercase transition-opacity duration-300" :class="activePath === item.to ? 'opacity-100' : 'opacity-70'">
              {{ item.label }}
            </span>
          </RouterLink>
        </div>
      </nav>

      <MobileBottomSheet />
    </div>
  </div>
</template>
