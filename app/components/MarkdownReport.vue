<script setup lang="ts">
const props = defineProps<{
  className?: string;
  content?: string;
}>();
</script>

<template>
  <div class="markdown-content prose prose-invert max-w-none text-sm leading-relaxed" :class="props.className">
    <template v-if="props.content">
      <pre class="whitespace-pre-wrap break-words text-[var(--color-text-secondary)] font-sans text-sm leading-7">{{ props.content }}</pre>
    </template>
    <template v-else>
      <h1>首席投资官（CIO）深度研报</h1>
      <p>等待新的筛选结果后，这里会自动展示后端生成的 Markdown 研报内容。</p>
      <h2>如何开始</h2>
      <ul>
        <li>在左侧聊天区输入你的选股指令。</li>
        <li>等待 Data / Quant / Risk / CIO 工作流执行完成。</li>
        <li>系统将自动刷新股票池与研报内容。</li>
      </ul>
    </template>
  </div>
</template>
