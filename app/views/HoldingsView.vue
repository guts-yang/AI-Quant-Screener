<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { FileUp, ClipboardPaste, UploadCloud, WalletCards, Trash2 } from "lucide-vue-next";
import { useAppStore, type Holding } from "../store";

const { holdings, holdingsMessage, loadHoldings, uploadHoldings } = useAppStore();

const pasteText = ref("");
const parsedHoldings = ref<Holding[]>([]);
const parseError = ref("");
const isUploading = ref(false);
const replaceExisting = ref(true);

const headerAliases: Record<string, keyof Holding> = {
  "代码": "ths_code",
  "股票代码": "ths_code",
  "证券代码": "ths_code",
  code: "ths_code",
  ths_code: "ths_code",
  ts_code: "ths_code",
  "名称": "sec_name",
  "股票名称": "sec_name",
  "证券名称": "sec_name",
  name: "sec_name",
  sec_name: "sec_name",
  "持仓": "quantity",
  "数量": "quantity",
  "持仓数量": "quantity",
  quantity: "quantity",
  shares: "quantity",
  "成本": "cost_price",
  "成本价": "cost_price",
  cost: "cost_price",
  cost_price: "cost_price",
  "现价": "latest_price",
  "最新价": "latest_price",
  price: "latest_price",
  latest_price: "latest_price",
  "备注": "note",
  note: "note",
};

const parseNumber = (value: string | undefined) => {
  const normalized = String(value ?? "").replace(/,/g, "").replace(/%/g, "").trim();
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
};

const normalizeCode = (raw: string) => {
  const code = raw.trim().toUpperCase();
  if (!code) return "";
  if (code.includes(".")) return code;
  return code.startsWith("6") || code.startsWith("9") ? `${code}.SH` : `${code}.SZ`;
};

const splitLine = (line: string) => {
  const delimiter = line.includes("\t") ? "\t" : ",";
  return line.split(delimiter).map((item) => item.trim().replace(/^"|"$/g, ""));
};

const parseTableText = (text: string) => {
  parseError.value = "";
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    parsedHoldings.value = [];
    parseError.value = "请至少提供表头和一行持仓数据。";
    return;
  }

  const headers = splitLine(lines[0]).map((item) => headerAliases[item] ?? headerAliases[item.toLowerCase()] ?? null);
  const codeIndex = headers.findIndex((item) => item === "ths_code");
  if (codeIndex < 0) {
    parsedHoldings.value = [];
    parseError.value = "没有找到股票代码列，可使用“代码”或“证券代码”作为表头。";
    return;
  }

  parsedHoldings.value = lines.slice(1).map((line) => {
    const cells = splitLine(line);
    const item: Holding = {
      ths_code: "",
      sec_name: "",
      quantity: 0,
      cost_price: 0,
      latest_price: 0,
      note: "",
    };

    headers.forEach((key, index) => {
      if (!key) return;
      const value = cells[index] ?? "";
      if (key === "ths_code") item.ths_code = normalizeCode(value);
      else if (key === "sec_name") item.sec_name = value;
      else if (key === "quantity") item.quantity = parseNumber(value);
      else if (key === "cost_price") item.cost_price = parseNumber(value);
      else if (key === "latest_price") item.latest_price = parseNumber(value);
      else if (key === "note") item.note = value;
    });

    if (!item.sec_name) item.sec_name = item.ths_code.split(".")[0];
    return item;
  }).filter((item) => item.ths_code);
};

const handleFileChange = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const text = await file.text();
  pasteText.value = text;
  parseTableText(text);
};

const parsePaste = () => {
  parseTableText(pasteText.value);
};

const submitHoldings = async () => {
  if (parsedHoldings.value.length === 0) {
    parseTableText(pasteText.value);
  }
  if (parsedHoldings.value.length === 0) return;

  isUploading.value = true;
  try {
    await uploadHoldings(parsedHoldings.value, replaceExisting.value);
    parsedHoldings.value = [];
    pasteText.value = "";
  } finally {
    isUploading.value = false;
  }
};

const clearDraft = () => {
  pasteText.value = "";
  parsedHoldings.value = [];
  parseError.value = "";
};

const totalMarketValue = computed(() => holdings.value.reduce((sum, item) => sum + Number(item.market_value ?? item.quantity * item.latest_price), 0));
const totalPnl = computed(() => holdings.value.reduce((sum, item) => sum + Number(item.pnl ?? 0), 0));
const totalCost = computed(() => holdings.value.reduce((sum, item) => sum + item.quantity * item.cost_price, 0));
const totalPnlPct = computed(() => (totalCost.value ? (totalPnl.value / totalCost.value) * 100 : 0));

const formatMoney = (value: number) => value.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const formatPct = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
const pnlClass = (value: number) => (value >= 0 ? "text-[var(--color-up)]" : "text-[var(--color-down)]");

onMounted(async () => {
  try {
    await loadHoldings();
  } catch {
    // 后端未启动时页面仍可用于本地解析预览。
  }
});
</script>

<template>
  <div class="p-4 md:p-5 space-y-4 bg-[var(--color-background)] min-h-full">
    <section class="glass-panel rounded-xl p-4">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-lg bg-blue-100 border border-blue-200 flex items-center justify-center">
            <WalletCards class="w-5 h-5 text-blue-700" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-slate-900">我的持仓</h2>
            <p class="text-xs text-slate-500 mt-1">上传 CSV、制表符表格，或直接从券商软件复制粘贴。</p>
          </div>
        </div>
        <label class="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500 cursor-pointer">
          <FileUp class="w-4 h-4" />
          选择文件
          <input type="file" accept=".csv,.txt,.tsv" class="hidden" @change="handleFileChange" />
        </label>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-xs text-slate-500">持仓市值</div>
          <div class="mt-1 text-xl font-semibold">{{ formatMoney(totalMarketValue) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-xs text-slate-500">浮动盈亏</div>
          <div class="mt-1 text-xl font-semibold" :class="pnlClass(totalPnl)">{{ formatMoney(totalPnl) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-xs text-slate-500">收益率</div>
          <div class="mt-1 text-xl font-semibold" :class="pnlClass(totalPnlPct)">{{ formatPct(totalPnlPct) }}</div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] gap-4">
      <div class="glass-panel rounded-xl p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold inline-flex items-center gap-2">
            <ClipboardPaste class="w-4 h-4 text-blue-600" />
            粘贴持仓表
          </h3>
          <button class="text-xs text-slate-500 hover:text-red-600 inline-flex items-center gap-1" @click="clearDraft">
            <Trash2 class="w-3.5 h-3.5" />
            清空
          </button>
        </div>
        <textarea
          v-model="pasteText"
          class="w-full min-h-[210px] rounded-lg border border-slate-200 bg-white p-3 text-sm outline-none focus:border-blue-400 font-mono"
          placeholder="代码,名称,数量,成本价,最新价,备注&#10;600519,贵州茅台,100,1580,1700,核心持仓&#10;300750,宁德时代,200,180,195,观察加仓"
        />
        <div class="flex items-center justify-between gap-2 flex-wrap">
          <label class="inline-flex items-center gap-2 text-xs text-slate-600">
            <input v-model="replaceExisting" type="checkbox" class="h-4 w-4 accent-blue-600" />
            覆盖原有持仓
          </label>
          <div class="flex items-center gap-2">
            <button class="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm text-slate-700 hover:border-blue-300" @click="parsePaste">
              预览
            </button>
            <button
              class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500 inline-flex items-center gap-1.5 disabled:opacity-50"
              :disabled="isUploading"
              @click="submitHoldings"
            >
              <UploadCloud class="w-4 h-4" />
              {{ isUploading ? "上传中" : "上传持仓" }}
            </button>
          </div>
        </div>
        <p v-if="parseError" class="text-xs text-red-600">{{ parseError }}</p>
        <p v-else-if="parsedHoldings.length" class="text-xs text-blue-700">已识别 {{ parsedHoldings.length }} 条，确认无误后即可上传。</p>
        <p v-if="holdingsMessage" class="text-xs text-emerald-700">{{ holdingsMessage }}</p>
      </div>

      <div class="glass-panel rounded-xl overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-semibold">当前持仓明细</h3>
          <span class="text-xs text-slate-500">{{ holdings.length }} 条</span>
        </div>

        <div v-if="holdings.length === 0" class="min-h-[260px] flex items-center justify-center text-sm text-slate-500 text-center p-6">
          暂无持仓。可以上传文件，也可以把券商导出的表格直接粘贴到左侧。
        </div>

        <div v-else class="overflow-auto custom-scrollbar">
          <table class="w-full text-left text-sm">
            <thead class="bg-slate-50 border-b border-slate-200">
              <tr>
                <th class="px-3 py-3 font-medium text-slate-500">代码</th>
                <th class="px-3 py-3 font-medium text-slate-500">名称</th>
                <th class="px-3 py-3 font-medium text-slate-500 text-right">数量</th>
                <th class="px-3 py-3 font-medium text-slate-500 text-right">成本价</th>
                <th class="px-3 py-3 font-medium text-slate-500 text-right">最新价</th>
                <th class="px-3 py-3 font-medium text-slate-500 text-right">盈亏</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in holdings" :key="item.ths_code" class="border-b border-slate-100">
                <td class="px-3 py-2 font-mono text-slate-700">{{ item.ths_code }}</td>
                <td class="px-3 py-2 font-medium text-slate-800">{{ item.sec_name }}</td>
                <td class="px-3 py-2 text-right font-mono">{{ item.quantity }}</td>
                <td class="px-3 py-2 text-right font-mono">{{ item.cost_price.toFixed(2) }}</td>
                <td class="px-3 py-2 text-right font-mono">{{ item.latest_price.toFixed(2) }}</td>
                <td class="px-3 py-2 text-right font-mono" :class="pnlClass(Number(item.pnl ?? 0))">
                  {{ formatMoney(Number(item.pnl ?? 0)) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>
