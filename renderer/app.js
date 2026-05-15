const api = window.TauriAPI

let excelData = null
let gffData = null
let exportData = null
let isGenerating = false
let currentLang = 'en'

const $ = id => document.getElementById(id)
const qs = (sel, ctx) => (ctx || document).querySelector(sel)
const qsa = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)]

/* ---- Language Toggle ---- */
function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'zh' : 'en'
  document.documentElement.lang = currentLang
  
  const translatable = qsa('[data-zh]')
  translatable.forEach(el => {
    if (!el._en) el._en = el.textContent
    el.textContent = currentLang === 'zh' ? el.dataset.zh : el._en
  })
}

$('langToggle').addEventListener('click', toggleLanguage)

/* ---- Sample Data ---- */
const sampleGenes = `Glyma.01G000100 10000000 12000000 Chr01 #FF3B30
Glyma.01G000200 50000000 52000000 Chr01 #34C759
Glyma.01G000300 85000000 87000000 Chr01 #007AFF
Glyma.02G000100 20000000 22000000 Chr02 #FF9500
Glyma.02G000200 60000000 62000000 Chr02 #AF52DE
Glyma.03G000100 40000000 42000000 Chr03 #5856D6
Glyma.03G000200 110000000 112000000 Chr03 #FF2D55`

const sampleChrLens = `Chr01 100000000
Chr02 120000000
Chr03 150000000`

const sampleGff = `##gff-version 3
# Sample GFF3 for density demonstration
Chr01\tsample\tgene\t1000000\t2000000\t.\t+\t.\tID=gene1
Chr01\tsample\tgene\t1500000\t2500000\t.\t+\t.\tID=gene2
Chr01\tsample\tgene\t5000000\t6000000\t.\t+\t.\tID=gene3
Chr01\tsample\tgene\t5500000\t6500000\t.\t+\t.\tID=gene4
Chr01\tsample\tgene\t5800000\t6800000\t.\t+\t.\tID=gene5
Chr01\tsample\tgene\t80000000\t81000000\t.\t+\t.\tID=gene6
Chr02\tsample\tgene\t10000000\t11000000\t.\t+\t.\tID=gene7
Chr02\tsample\tgene\t15000000\t16000000\t.\t+\t.\tID=gene8
Chr02\tsample\tgene\t20000000\t21000000\t.\t+\t.\tID=gene9
Chr02\tsample\tgene\t25000000\t26000000\t.\t+\t.\tID=gene10
Chr02\tsample\tgene\t30000000\t31000000\t.\t+\t.\tID=gene11
Chr02\tsample\tgene\t100000000\t110000000\t.\t+\t.\tID=gene12
Chr03\tsample\tgene\t5000000\t6000000\t.\t+\t.\tID=gene13
Chr03\tsample\tgene\t40000000\t41000000\t.\t+\t.\tID=gene14
Chr03\tsample\tgene\t45000000\t46000000\t.\t+\t.\tID=gene15
Chr03\tsample\tgene\t50000000\t51000000\t.\t+\t.\tID=gene16
Chr03\tsample\tgene\t55000000\t56000000\t.\t+\t.\tID=gene17
Chr03\tsample\tgene\t130000000\t140000000\t.\t+\t.\tID=gene18`

$('sampleBtn').addEventListener('click', () => {
  $('geneInput').value = sampleGenes
  $('chrLenInput').value = sampleChrLens
  
  // Load sample GFF for density heatmap
  gffData = { name: 'sample.gff3', content: sampleGff }
  $('gffName').textContent = gffData.name
  $('useDensity').checked = true
  $('densityOptions').classList.remove('hidden')

  // Switch to text tab if not active
  const textTab = qs('.tab[data-tab="gene-text"]')
  if (textTab) textTab.click()
  generate()
})

$('clearBtn').addEventListener('click', () => {
  $('geneInput').value = ''
  $('chrLenInput').value = ''
  excelData = null
  $('excelName').textContent = ''
  gffData = null
  $('gffName').textContent = ''
  $('useDensity').checked = false
  $('densityOptions').classList.add('hidden')
})

/* ---- Arch Badge ---- */
if (api) {
  api.arch().then(a => {
    $('archBadge').textContent = a === 'arm64' ? 'ARM' : a
  })
}

/* ---- Collapsible Panels ---- */
qsa('.panel-header').forEach(h => {
  h.addEventListener('click', () => {
    h.closest('.panel').classList.toggle('collapsed')
  })
})

/* ---- Tab Switching ---- */
qsa('.tab-bar').forEach(bar => {
  bar.addEventListener('click', e => {
    const tab = e.target.closest('.tab')
    if (!tab) return
    const parent = tab.closest('.field')
    qsa('.tab', parent).forEach(t => t.classList.remove('active'))
    qsa('.tab-content', parent).forEach(t => t.classList.remove('active'))
    tab.classList.add('active')
    const target = $(tab.dataset.tab)
    if (target) target.classList.add('active')
  })
})

/* ---- File Selection ---- */
$('excelBtn').addEventListener('click', async () => {
  if (!api) return
  const result = await api.openFile([{ name: 'Excel', extensions: ['xlsx', 'xls'] }])
  if (result) {
    const name = result.split('/').pop() || result.split('\\').pop()
    excelData = { name, content: result, binary: true }
    $('excelName').textContent = name
  }
})

$('gffBtn').addEventListener('click', async () => {
  if (!api) return
  const result = await api.openFile([{ name: 'GFF3', extensions: ['gff3', 'gff'] }])
  if (result) {
    const name = result.split('/').pop() || result.split('\\').pop()
    const content = await api.readTextFile(result)
    gffData = { name, content }
    $('gffName').textContent = name
  }
})

/* ---- Density toggle ---- */
$('useDensity').addEventListener('change', () => {
  $('densityOptions').classList.toggle('hidden', !$('useDensity').checked)
})

/* ---- Range slider live values ---- */
const rangeSliders = [
  'rowHeight', 'rulerOffset', 'tickLineLen',
  'chrWidth', 'labelSpacing', 'fontSize'
]
rangeSliders.forEach(id => {
  const el = $(id)
  const valEl = $(id + 'Val')
  if (el && valEl) {
    el.addEventListener('input', () => { valEl.textContent = el.value })
  }
})

/* ---- Collect params ---- */
function collectParams() {
  const activeTab = qs('.tab-bar .tab.active')
  const isTextMode = activeTab && activeTab.dataset.tab === 'gene-text'
  const isExcelMode = activeTab && activeTab.dataset.tab === 'gene-excel'
  const geneText = $('geneInput').value.trim()

  let genes = []
  if (isTextMode && geneText) {
    const lines = geneText.split('\n').filter(l => l.trim())
    for (const line of lines) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 4) {
        genes.push({
          Gene: parts[0],
          Start: parseFloat(parts[1]),
          End: parseFloat(parts[2]),
          Chr: parts[3],
          Color: parts[4] || ''
        })
      }
    }
  } else if (isExcelMode && excelData) {
    genes = { _is_path: true, path: excelData.content }
  }

  const chrLenText = $('chrLenInput').value.trim()
  const chrLens = {}
  if (chrLenText) {
    for (const line of chrLenText.split('\n').filter(l => l.trim())) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 2) chrLens[parts[0]] = parseFloat(parts[1])
    }
  }

  return {
    genes,
    chr_lens: chrLens,
    gff_content: gffData ? gffData.content : null,
    settings: {
      chrs_per_row: parseInt($('chrsPerRow').value) || 10,
      fig_width: parseFloat($('figWidth').value) || 15,
      row_height: parseFloat($('rowHeight').value) || 8,
      ruler_offset: parseFloat($('rulerOffset').value) || 0.8,
      major_tick_int: parseInt($('majorTickInt').value) || 10,
      tick_line_len: parseFloat($('tickLineLen').value) || 0.2,
      show_minor: $('showMinor').checked,
      use_density_color: $('useDensity').checked,
      window_size_mb: parseFloat($('windowSize').value) || 1.0,
      colormap_name: $('colormap').value,
      chr_width: parseFloat($('chrWidth').value) || 0.4,
      label_spacing: parseFloat($('labelSpacing').value) || 1.2,
      font_size: parseInt($('fontSize').value) || 10,
      label_color: $('labelColor').value
    }
  }
}

/* ---- Generate ---- */
async function generate() {
  if (isGenerating || !api) return
  const params = collectParams()

  if (!params.chr_lens || Object.keys(params.chr_lens).length === 0) {
    const msg = currentLang === 'zh' ? '请输入染色体长度' : 'Please enter chromosome lengths'
    showError(msg)
    return
  }
  if (!params.genes || (Array.isArray(params.genes) && params.genes.length === 0)) {
    const msg = currentLang === 'zh' ? '请输入基因数据' : 'Please enter gene data'
    showError(msg)
    return
  }

  isGenerating = true
  $('generateBtn').disabled = true
  $('loadingOverlay').classList.remove('hidden')
  $('emptyState').classList.add('hidden')
  hideError()

  try {
    const resultStr = await api.generateChart(params)
    const result = JSON.parse(resultStr)
    $('plotImage').src = 'data:image/png;base64,' + result.png
    $('plotContainer').classList.remove('hidden')
    exportData = result
    $('exportRow').classList.remove('hidden')
  } catch (e) {
    const defaultMsg = currentLang === 'zh' ? '生成失败' : 'Generation failed'
    showError(typeof e === 'string' ? e : (e.message || defaultMsg))
    $('emptyState').classList.remove('hidden')
    $('plotContainer').classList.add('hidden')
  }

  isGenerating = false
  $('generateBtn').disabled = false
  $('loadingOverlay').classList.add('hidden')
}

/* ---- Export ---- */
qsa('.btn-export').forEach(btn => {
  btn.addEventListener('click', async () => {
    if (!exportData || !api) return
    const fmt = btn.dataset.fmt
    const data = exportData[fmt]
    if (!data) return
    const extMap = { png: 'png', svg: 'svg', pdf: 'pdf' }
    const ext = extMap[fmt]
    const path = await api.saveFile('chromomap.' + ext, [{ name: fmt.toUpperCase(), extensions: [ext] }])
    if (path) {
      const buf = Uint8Array.from(atob(data), c => c.charCodeAt(0))
      await api.writeBinaryFile(path, buf)
    }
  })
})

/* ---- Error display ---- */
function showError(msg) {
  const el = $('errorToast')
  el.textContent = msg
  el.classList.remove('hidden')
  setTimeout(() => el.classList.add('hidden'), 8000)
}
function hideError() { $('errorToast').classList.add('hidden') }

/* ---- Events ---- */
$('generateBtn').addEventListener('click', generate)

document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') generate()
})

// Initialize with sample data on first load
window.addEventListener('DOMContentLoaded', () => {
  $('geneInput').value = sampleGenes
  $('chrLenInput').value = sampleChrLens
})

console.log('ChromoMap v12.9 ready')
