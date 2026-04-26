<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  className?: string;
  content?: string;
}>();

type TextBlock = {
  type: "heading" | "paragraph" | "list";
  level?: number;
  text?: string;
  items?: string[];
};

type TableBlock = {
  type: "table";
  headers: string[];
  rows: string[][];
};

type ReportBlock = TextBlock | TableBlock;

const stripInlineMarkdown = (value: string) =>
  value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/__(.*?)__/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
    .trim();

const isTableDivider = (line: string) => /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
const isTableRow = (line: string) => line.includes("|") && !isTableDivider(line);

const parseTableCells = (line: string) =>
  line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => stripInlineMarkdown(cell));

const blocks = computed<ReportBlock[]>(() => {
  const raw = props.content?.trim();
  if (!raw) return [];

  const lines = raw.split(/\r?\n/);
  const result: ReportBlock[] = [];
  let paragraph: string[] = [];
  let listItems: string[] = [];

  const flushParagraph = () => {
    if (paragraph.length > 0) {
      result.push({ type: "paragraph", text: stripInlineMarkdown(paragraph.join(" ")) });
      paragraph = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0) {
      result.push({ type: "list", items: listItems });
      listItems = [];
    }
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    if (isTableRow(line) && index + 1 < lines.length && isTableDivider(lines[index + 1])) {
      flushParagraph();
      flushList();
      const headers = parseTableCells(line);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && isTableRow(lines[index])) {
        rows.push(parseTableCells(lines[index]));
        index += 1;
      }
      index -= 1;
      result.push({ type: "table", headers, rows });
      continue;
    }

    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      result.push({
        type: "heading",
        level: headingMatch[1].length,
        text: stripInlineMarkdown(headingMatch[2]),
      });
      continue;
    }

    const listMatch = line.match(/^[-*]\s+(.+)$/) || line.match(/^\d+[.)]\s+(.+)$/);
    if (listMatch) {
      flushParagraph();
      listItems.push(stripInlineMarkdown(listMatch[1]));
      continue;
    }

    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();
  return result;
});
</script>

<template>
  <div class="markdown-content max-w-none text-sm leading-relaxed" :class="props.className">
    <template v-if="blocks.length">
      <template v-for="(block, index) in blocks" :key="index">
        <h1 v-if="block.type === 'heading' && block.level === 1">{{ block.text }}</h1>
        <h2 v-else-if="block.type === 'heading' && block.level === 2">{{ block.text }}</h2>
        <h3 v-else-if="block.type === 'heading'">{{ block.text }}</h3>
        <p v-else-if="block.type === 'paragraph'">{{ block.text }}</p>
        <ul v-else-if="block.type === 'list'">
          <li v-for="item in block.items" :key="item">{{ item }}</li>
        </ul>
        <div v-else-if="block.type === 'table'" class="overflow-auto custom-scrollbar my-3 rounded-lg border border-slate-200">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50">
              <tr>
                <th v-for="header in block.headers" :key="header" class="px-3 py-2 font-semibold text-slate-600 border-b border-slate-200">
                  {{ header }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in block.rows" :key="rowIndex" class="border-b border-slate-100 last:border-0">
                <td v-for="(cell, cellIndex) in row" :key="cellIndex" class="px-3 py-2 text-slate-700 whitespace-nowrap">
                  {{ cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>
    <template v-else>
      <h1>首席投资官研报</h1>
      <p>运行一次选股策略后，这里会展示结构化研报、风险提示和标的点评。</p>
      <h2>开始方式</h2>
      <ul>
        <li>在 AI 对话页输入你的选股思路。</li>
        <li>选择沪深300、中证500、中证1000或本地股票池。</li>
        <li>等待工作流完成后查看结论。</li>
      </ul>
    </template>
  </div>
</template>
