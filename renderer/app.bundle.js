// renderer/app.js
import { invoke } from "@tauri-apps/api/core";
import { arch } from "@tauri-apps/api/os";
import { open, save } from "@tauri-apps/plugin-dialog";
import { readTextFile, writeBinaryFile } from "@tauri-apps/plugin-fs";
var excelData = null;
var gffData = null;
var exportData = null;
var isGenerating = false;
var $ = (id) => document.getElementById(id);
var qs = (sel, ctx) => (ctx || document).querySelector(sel);
var qsa = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];
arch().then((a) => {
  $("archBadge").textContent = a === "arm64" ? "Apple Silicon" : a;
});
qsa(".panel-header").forEach((h) => {
  h.addEventListener("click", () => {
    h.closest(".panel").classList.toggle("collapsed");
  });
});
qsa(".tab-bar").forEach((bar) => {
  bar.addEventListener("click", (e) => {
    const tab = e.target.closest(".tab");
    if (!tab) return;
    const parent = tab.closest(".field");
    qsa(".tab", parent).forEach((t) => t.classList.remove("active"));
    qsa(".tab-content", parent).forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const target = $(tab.dataset.tab);
    if (target) target.classList.add("active");
  });
});
$("excelBtn").addEventListener("click", async () => {
  const result = await open({
    multiple: false,
    filters: [{ name: "Excel", extensions: ["xlsx", "xls"] }]
  });
  if (result) {
    const name = result.split("/").pop() || result.split("\\").pop();
    excelData = { name, content: result, binary: true };
    $("excelName").textContent = name;
  }
});
$("gffBtn").addEventListener("click", async () => {
  const result = await open({
    multiple: false,
    filters: [{ name: "GFF3", extensions: ["gff3", "gff"] }]
  });
  if (result) {
    const name = result.split("/").pop() || result.split("\\").pop();
    const content = await readTextFile(result);
    gffData = { name, content };
    $("gffName").textContent = name;
  }
});
$("useDensity").addEventListener("change", () => {
  $("densityOptions").classList.toggle("hidden", !$("useDensity").checked);
});
var rangeSliders = [
  "rowHeight",
  "rulerOffset",
  "tickLineLen",
  "chrWidth",
  "labelSpacing",
  "fontSize"
];
rangeSliders.forEach((id) => {
  const el = $(id);
  const valEl = $(id + "Val");
  if (el && valEl) {
    el.addEventListener("input", () => {
      valEl.textContent = el.value;
    });
  }
});
function collectParams() {
  const activeTab = qs(".tab-bar .tab.active");
  const isTextMode = activeTab && activeTab.dataset.tab === "gene-text";
  const geneText = $("geneInput").value.trim();
  let genes = [];
  if (isTextMode && geneText) {
    const lines = geneText.split("\n").filter((l) => l.trim());
    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      if (parts.length >= 4) {
        genes.push({
          Gene: parts[0],
          Start: parseFloat(parts[1]),
          End: parseFloat(parts[2]),
          Chr: parts[3],
          Color: parts[4] || ""
        });
      }
    }
  } else if (excelData) {
    try {
      const bytes = atob(excelData.content);
      const arr = new Uint8Array(bytes.length);
      for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
      genes = [{ _excel: true, _data: Array.from(arr) }];
    } catch (e) {
      console.error("Excel parse error:", e);
    }
  }
  const chrLenText = $("chrLenInput").value.trim();
  const chrLens = {};
  if (chrLenText) {
    for (const line of chrLenText.split("\n").filter((l) => l.trim())) {
      const parts = line.trim().split(/\s+/);
      if (parts.length >= 2) chrLens[parts[0]] = parseFloat(parts[1]);
    }
  }
  return {
    genes,
    chr_lens: chrLens,
    gff_content: gffData ? gffData.content : null,
    settings: {
      chrs_per_row: parseInt($("chrsPerRow").value) || 10,
      fig_width: parseFloat($("figWidth").value) || 15,
      row_height: parseFloat($("rowHeight").value) || 8,
      ruler_offset: parseFloat($("rulerOffset").value) || 0.8,
      major_tick_int: parseInt($("majorTickInt").value) || 10,
      tick_line_len: parseFloat($("tickLineLen").value) || 0.2,
      show_minor: $("showMinor").checked,
      use_density_color: $("useDensity").checked,
      window_size_mb: parseFloat($("windowSize").value) || 1,
      colormap_name: $("colormap").value,
      chr_width: parseFloat($("chrWidth").value) || 0.4,
      label_spacing: parseFloat($("labelSpacing").value) || 1.2,
      font_size: parseInt($("fontSize").value) || 10,
      label_color: $("labelColor").value
    }
  };
}
async function generate() {
  if (isGenerating) return;
  const params = collectParams();
  if (!params.chr_lens || Object.keys(params.chr_lens).length === 0) {
    showError("Please enter chromosome lengths / \u8BF7\u8F93\u5165\u67D3\u8272\u4F53\u957F\u5EA6");
    return;
  }
  if (!params.genes || params.genes.length === 0) {
    showError("Please enter gene data / \u8BF7\u8F93\u5165\u57FA\u56E0\u6570\u636E");
    return;
  }
  if (params.genes[0] && params.genes[0]._excel) {
    showError("Excel files are not yet supported in this version");
    return;
  }
  isGenerating = true;
  $("generateBtn").disabled = true;
  $("loadingOverlay").classList.remove("hidden");
  $("emptyState").classList.add("hidden");
  hideError();
  try {
    const resultStr = await invoke("generate_chart", { params: JSON.stringify(params) });
    const result = JSON.parse(resultStr);
    $("plotImage").src = "data:image/png;base64," + result.png;
    $("plotContainer").classList.remove("hidden");
    exportData = result;
    $("exportRow").classList.remove("hidden");
  } catch (e) {
    showError(typeof e === "string" ? e : e.message || "Generation failed / \u751F\u6210\u5931\u8D25");
    $("emptyState").classList.remove("hidden");
    $("plotContainer").classList.add("hidden");
  }
  isGenerating = false;
  $("generateBtn").disabled = false;
  $("loadingOverlay").classList.add("hidden");
}
qsa(".btn-export").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!exportData) return;
    const fmt = btn.dataset.fmt;
    const data = exportData[fmt];
    if (!data) return;
    const extMap = { png: "png", svg: "svg", pdf: "pdf" };
    const ext = extMap[fmt];
    const path = await save({
      defaultPath: "chromomap." + ext,
      filters: [{ name: fmt.toUpperCase(), extensions: [ext] }]
    });
    if (path) {
      const buf = Uint8Array.from(atob(data), (c) => c.charCodeAt(0));
      await writeBinaryFile(path, buf);
    }
  });
});
function showError(msg) {
  const el = $("errorToast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 8e3);
}
function hideError() {
  $("errorToast").classList.add("hidden");
}
$("generateBtn").addEventListener("click", generate);
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") generate();
});
console.log("ChromoMap v12.9 ready");
