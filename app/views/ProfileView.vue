<script setup lang="ts">
import { User, Settings, Database, Shield, CreditCard, ChevronRight } from "lucide-vue-next";
</script>

<template>
  <div class="p-4 space-y-4 bg-[var(--color-background)] min-h-full">
    <div class="flex items-center space-x-4 p-4 glass-panel rounded-xl bg-[var(--color-surface)] mb-6">
      <div class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-600 to-indigo-800 flex items-center justify-center border-2 border-white/10 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
        <User class="w-8 h-8 text-white" />
      </div>
      <div>
        <h2 class="text-xl font-bold tracking-wide text-white mb-1">量化分析师 Pro</h2>
        <div class="flex items-center space-x-2 text-xs">
          <span class="px-2 py-0.5 rounded-sm bg-yellow-500/20 text-yellow-500 font-bold uppercase border border-yellow-500/30">VIP 终身会员</span>
          <span class="text-gray-400">ID: 1029348</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3 mb-6">
      <div class="glass-panel p-4 rounded-xl flex flex-col items-center justify-center space-y-2">
        <span class="text-3xl font-mono font-bold text-white tracking-tight">32</span>
        <span class="text-xs text-gray-400 uppercase tracking-wider">本周策略运行次数</span>
      </div>
      <div class="glass-panel p-4 rounded-xl flex flex-col items-center justify-center space-y-2">
        <span class="text-3xl font-mono font-bold text-blue-400 tracking-tight">18.5%</span>
        <span class="text-xs text-gray-400 uppercase tracking-wider">模拟盘年化收益</span>
      </div>
    </div>

    <div class="glass-panel rounded-xl overflow-hidden divide-y divide-[var(--color-surface-border)]">
      <button class="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors cursor-pointer text-left">
        <div class="flex items-center space-x-4">
          <Database class="w-5 h-5 text-blue-400" />
          <div>
            <div class="text-sm font-medium text-white">数据源配置</div>
            <div class="text-[10px] text-gray-500 mt-0.5 uppercase tracking-wider">iFinD / Wind / Tushare</div>
          </div>
        </div>
        <ChevronRight class="w-4 h-4 text-gray-600" />
      </button>

      <button class="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors cursor-pointer text-left">
        <div class="flex items-center space-x-4">
          <Shield class="w-5 h-5 text-green-400" />
          <div>
            <div class="text-sm font-medium text-white">风控模型设置</div>
            <div class="text-[10px] text-gray-500 mt-0.5 uppercase tracking-wider">最大回撤 / 止损比例</div>
          </div>
        </div>
        <ChevronRight class="w-4 h-4 text-gray-600" />
      </button>

      <button class="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors cursor-pointer text-left">
        <div class="flex items-center space-x-4">
          <CreditCard class="w-5 h-5 text-yellow-400" />
          <div>
            <div class="text-sm font-medium text-white">订阅与账单</div>
          </div>
        </div>
        <ChevronRight class="w-4 h-4 text-gray-600" />
      </button>

      <button class="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors cursor-pointer text-left">
        <div class="flex items-center space-x-4">
          <Settings class="w-5 h-5 text-gray-400" />
          <div>
            <div class="text-sm font-medium text-white">系统设置</div>
          </div>
        </div>
        <ChevronRight class="w-4 h-4 text-gray-600" />
      </button>
    </div>

    <div class="mt-8 text-center">
      <button class="text-red-400 text-sm font-medium hover:text-red-300 transition-colors cursor-pointer px-4 py-2 border border-red-500/20 rounded-lg bg-red-500/10">
        退出登录
      </button>
    </div>
  </div>
</template>
