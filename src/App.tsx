import { useState, useEffect, useCallback } from "react"
import { useElectron } from "./hooks/useElectron"
import { translations, type Lang } from "./translations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Dna, 
  Settings2, 
  Play, 
  Eraser, 
  Download, 
  Database, 
  Languages,
  Loader2,
  FileSpreadsheet,
  FileCode,
  Layers,
  Type,
  Ruler,
  Palette,
  Sun,
  Moon
} from "lucide-react"
import { cn } from "@/lib/utils"

const sampleGenes = `GmCBL1	50399334	50405613	Chr04
GmCBL2	6731396	6740875	Chr05
GmCBL3	39770219	39774659	Chr05
GmCBL4	10581579	10588773	Chr06
GmCBL5	824696	827823	Chr07
GmCBL6	44230392	44236986	Chr07
GmCBL7	1884590	1887532	Chr08
GmCBL8	15628395	15631841	Chr08
GmCBL9	44992808	44997458	Chr08
GmCBL10	1233158	1239867	Chr09
GmCBL11	2773817	2777295	Chr11
GmCBL12	434853	441609	Chr17
GmCBL13	12354772	12359193	Chr17
GmCBL14	38443770	38448625	Chr17
GmCBL15	7033194	7037977	Chr18`

const sampleChrLens = `Chr01	57932355
Chr02	50400358
Chr03	46951866
Chr04	51203389
Chr05	42274530
Chr06	50945864
Chr07	44949256
Chr08	47227184
Chr09	50572668
Chr10	51638687
Chr11	39643745
Chr12	41531199
Chr13	45225048
Chr14	49893278
Chr15	53754295
Chr16	38112070
Chr17	41740656
Chr18	58286270
Chr19	51272880
Chr20	47846026`

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
Chr03\tsample\tgene\t5000000\t6000000\t.\t+\t.\tID=gene13
Chr03\tsample\tgene\t40000000\t41000000\t.\t+\t.\tID=gene14`

export default function App() {
  const electron = useElectron()
  const [lang, setLang] = useState<Lang>("en")
  const [isDark, setIsDark] = useState(false)
  const t = translations[lang]

  useEffect(() => {
    const root = window.document.documentElement
    if (isDark) {
      root.classList.add("dark")
    } else {
      root.classList.remove("dark")
    }
  }, [isDark])

  const [geneInput, setGeneInput] = useState("")
  const [chrLenInput, setChrLenInput] = useState("")
  const [excelData, setExcelData] = useState<{ name: string; content: string } | null>(null)
  const [gffData, setGffData] = useState<{ name: string; content: string } | null>(null)
  const [exportData, setExportData] = useState<any>(null)

  const [chrsPerRow, setChrsPerRow] = useState(10)
  const [figWidth, setFigWidth] = useState(15)
  const [rowHeight, setRowHeight] = useState(8)
  const [rulerOffset, setRulerOffset] = useState(0.8)
  const [majorTickInt, setMajorTickInt] = useState(10)
  const [tickLineLen, setTickLineLen] = useState(0.2)
  const [showMinor, setShowMinor] = useState(true)
  const [useDensity, setUseDensity] = useState(false)
  const [windowSize, setWindowSize] = useState("1.0")
  const [colormap, setColormap] = useState("Grayscale_Print")
  const [chrWidth, setChrWidth] = useState(0.4)
  const [labelSpacing, setLabelGap] = useState(1.2)
  const [fontSize, setFontSize] = useState(10)
  const [labelColor, setLabelColor] = useState("#000000")
  const [chrFillColor, setChrFillColor] = useState("")

  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [plotSrc, setPlotImage] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    setGeneInput(sampleGenes)
    setChrLenInput(sampleChrLens)
  }, [])

  const handleGenerate = useCallback(async () => {
    if (isGenerating) return
    setError(null)

    let genes: any = []
    if (excelData) {
      genes = { _is_path: true, path: excelData.content }
    } else if (geneInput.trim()) {
      const lines = geneInput.trim().split('\n').filter(l => l.trim())
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
    }

    const chrLens: Record<string, number> = {}
    if (chrLenInput.trim()) {
      for (const line of chrLenInput.trim().split('\n').filter(l => l.trim())) {
        const parts = line.trim().split(/\s+/)
        if (parts.length >= 2) chrLens[parts[0]] = parseFloat(parts[1])
      }
    }

    if (Object.keys(chrLens).length === 0) {
      setError(t.errChrLen)
      return
    }
    if (genes.length === 0 && !genes._is_path) {
      setError(t.errGeneData)
      return
    }

    setIsGenerating(true)
    try {
      const params = {
        genes,
        chr_lens: chrLens,
        gff_content: gffData ? gffData.content : (useDensity ? sampleGff : null),
        settings: {
          chrs_per_row: chrsPerRow,
          fig_width: figWidth,
          row_height: rowHeight,
          ruler_offset: rulerOffset,
          major_tick_int: majorTickInt,
          tick_line_len: tickLineLen,
          show_minor: showMinor,
          use_density_color: useDensity,
          window_size_mb: parseFloat(windowSize),
          colormap_name: colormap,
          chr_width: chrWidth,
          label_spacing: labelSpacing,
          font_size: fontSize,
          label_color: labelColor,
          chr_fill_color: chrFillColor
        }
      }

      const resultStr = await electron.generateChart(params)
      const result = JSON.parse(resultStr)
      if (result.error) {
        throw new Error(result.error)
      }
      setPlotImage('data:image/png;base64,' + result.png)
      setExportData(result)
    } catch (e: any) {
      setError(typeof e === 'string' ? e : (e.message || t.genFailed))
    } finally {
      setIsGenerating(false)
    }
  }, [lang, geneInput, chrLenInput, excelData, gffData, useDensity, chrsPerRow, figWidth, rowHeight, rulerOffset, majorTickInt, tickLineLen, showMinor, windowSize, colormap, chrWidth, labelSpacing, fontSize, labelColor, chrFillColor])

  const handleExcelUpload = async () => {
    const result = await electron.openFile([{ name: 'Excel', extensions: ['xlsx', 'xls'] }])
    if (result) {
      const name = result.split('/').pop() || result.split('\\').pop() || "Excel File"
      setExcelData({ name, content: result })
    }
  }

  const handleGffUpload = async () => {
    const result = await electron.openFile([{ name: 'GFF3', extensions: ['gff3', 'gff'] }])
    if (result) {
      const name = result.split('/').pop() || result.split('\\').pop() || "GFF3 File"
      const content = await electron.readText(result)
      setGffData({ name, content })
      setUseDensity(true)
    }
  }

  const handleExport = async (fmt: string) => {
    if (!exportData || !exportData[fmt]) return
    const extMap: any = { png: 'png', svg: 'svg', pdf: 'pdf' }
    const ext = extMap[fmt]
    const path = await electron.saveFile('chromomap.' + ext, [{ name: fmt.toUpperCase(), extensions: [ext] }])
    if (path) {
      const buf = Uint8Array.from(atob(exportData[fmt]), c => c.charCodeAt(0))
      await electron.writeBinary(path, buf)
    }
  }

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden font-sans text-foreground">
      <aside className="w-[360px] flex flex-col border-r border-border bg-background shrink-0">
        <div className="h-16 flex items-center justify-between px-6 shrink-0 bg-background border-b border-border">
          <div className="flex items-center gap-3">
            <div className="shrink-0">
              <img src="./icon.svg" alt="ChromoMap" className="w-8 h-8 rounded-lg" />
            </div>
            <h1 className="font-semibold text-xl tracking-tight leading-none uppercase">{t.title}</h1>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="rounded-full" onClick={() => setIsDark(!isDark)}>
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </Button>
            <Button variant="ghost" size="icon" className="rounded-full" onClick={() => setLang(l => l === "en" ? "zh" : "en")}>
              <Languages size={18} />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-10">
          <section className="space-y-6">
            <div className="flex items-center gap-2 px-1">
              <Database size={14} strokeWidth={2.5} />
              <h2 className="text-[11px] font-bold uppercase tracking-[0.2em]">{t.dataInput}</h2>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <Label className="text-xs font-semibold ml-1 uppercase tracking-wider">{t.geneData}</Label>
                <Tabs defaultValue="paste" className="w-full">
                  <TabsList className="w-full bg-muted p-1 rounded-lg border border-border h-10">
                    <TabsTrigger value="paste" className="rounded-md text-xs font-semibold transition-all data-[active]:bg-background data-[active]:shadow-sm">{t.paste}</TabsTrigger>
                    <TabsTrigger value="excel" className="rounded-md text-xs font-semibold transition-all data-[active]:bg-background data-[active]:shadow-sm">{t.excel}</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="paste" className="mt-3 outline-none">
                    <div className="rounded-lg border border-border bg-background p-1.5 focus-within:ring-1 focus-within:ring-primary transition-all">
                      <Textarea 
                        className="min-h-[140px] text-xs font-mono border-none shadow-none focus-visible:ring-0 resize-none bg-transparent" 
                        placeholder="GeneID Start End Chr [Color]"
                        value={geneInput}
                        onChange={(e) => setGeneInput(e.target.value)}
                      />
                    </div>
                  </TabsContent>
                  <TabsContent value="excel" className="mt-3 outline-none">
                    <Button variant="outline" className="w-full h-24 border-border border-dashed rounded-lg flex-col gap-3 bg-muted hover:bg-background transition-all group" onClick={handleExcelUpload}>
                      <div className="p-2 bg-background rounded-full border border-border group-hover:border-primary transition-all">
                        <FileSpreadsheet size={20} className="text-muted-foreground group-hover:text-primary transition-all" />
                      </div>
                      <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">{excelData ? excelData.name : t.uploadExcel}</span>
                    </Button>
                  </TabsContent>
                </Tabs>
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-semibold ml-1 uppercase tracking-wider">{t.chrLengths}</Label>
                <div className="rounded-lg border border-border bg-background p-1.5 focus-within:ring-1 focus-within:ring-primary transition-all">
                  <Textarea 
                    className="min-h-[100px] text-xs font-mono border-none shadow-none focus-visible:ring-0 resize-none bg-transparent" 
                    placeholder="Chr01 10000000"
                    value={chrLenInput}
                    onChange={(e) => setChrLenInput(e.target.value)}
                  />
                </div>
              </div>

              <div
                className="space-y-3"
                onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={async e => {
                  e.preventDefault()
                  setIsDragging(false)
                  const file = e.dataTransfer.files[0]
                  if (!file) return
                  const path = (file as any).path
                  if (!path) return
                  const name = path.split('/').pop() || path.split('\\').pop() || "GFF3 File"
                  const content = await electron.readText(path)
                  setGffData({ name, content })
                  setUseDensity(true)
                }}
              >
                <Label className="text-xs font-semibold ml-1 uppercase tracking-wider">{t.gffFile}</Label>
                <div className={cn(
                  "relative rounded-lg border-2 border-dashed transition-all",
                  isDragging ? "border-primary bg-primary/5" : "border-border"
                )}>
                  <Button variant="outline" className={cn(
                    "w-full h-20 gap-2 justify-start px-4 rounded-lg bg-background hover:bg-muted transition-all flex-col items-center",
                    isDragging && "bg-transparent border-transparent"
                  )} onClick={handleGffUpload}>
                    <FileCode size={20} className="text-muted-foreground" />
                    <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider truncate">
                      {isDragging ? "Drop GFF3 file here" : (gffData ? gffData.name : t.selectGff)}
                    </span>
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1 text-[11px] font-bold h-10 rounded-lg border-border uppercase tracking-widest hover:bg-muted" onClick={() => { setGeneInput(sampleGenes); setChrLenInput(sampleChrLens); }}>
                {t.loadSample}
              </Button>
              <Button variant="ghost" className="flex-1 text-[11px] font-bold h-10 rounded-lg uppercase tracking-widest text-muted-foreground hover:text-foreground" onClick={() => { setGeneInput(""); setChrLenInput(""); setExcelData(null); setGffData(null); }}>
                <Eraser size={14} className="mr-2" /> {t.clearData}
              </Button>
            </div>
          </section>

          <div className="h-px border-t border-border mx-2 opacity-50" />

          <section className="space-y-6">
            <div className="flex items-center gap-2 px-1">
              <Settings2 size={14} strokeWidth={2.5} />
              <h2 className="text-[11px] font-bold uppercase tracking-[0.2em]">{t.visualSettings}</h2>
            </div>

            <div className="space-y-8 px-1">
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-2">
                    <Layers size={13} className="text-muted-foreground" />
                    {t.layout}
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.chrPerRow}</Label>
                    <Input 
                      type="number" 
                      value={chrsPerRow} 
                      onChange={(e) => setChrsPerRow(parseInt(e.target.value) || 1)} 
                      className="h-9 rounded-lg border-border bg-muted focus:bg-background transition-colors text-xs font-semibold" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.widthIn}</Label>
                    <Input 
                      type="number" 
                      step="0.5" 
                      value={figWidth} 
                      onChange={(e) => setFigWidth(parseFloat(e.target.value) || 5)} 
                      className="h-9 rounded-lg border-border bg-muted focus:bg-background transition-colors text-xs font-semibold" 
                    />
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.rowHeight}</Label>
                    <span className="text-[10px] font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">{rowHeight.toFixed(1)}</span>
                  </div>
                  <Slider 
                    value={rowHeight} 
                    min={2} 
                    max={20} 
                    step={0.5} 
                    onValueChange={(val) => setRowHeight(val)} 
                  />
                </div>
              </div>

              <div className="space-y-5">
                <h3 className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-2">
                  <Ruler size={13} className="text-muted-foreground" />
                  {t.ruler}
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.rulerOffset}</Label>
                    <span className="text-[10px] font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">{rulerOffset.toFixed(1)}</span>
                  </div>
                  <Slider 
                    value={rulerOffset} 
                    min={0.1} 
                    max={4} 
                    step={0.1} 
                    onValueChange={(val) => setRulerOffset(val)} 
                  />
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.tickMb}</Label>
                    <Input 
                        type="number" 
                        value={majorTickInt} 
                        onChange={(e) => setMajorTickInt(parseInt(e.target.value))} 
                        className="h-9 rounded-lg border-border bg-muted focus:bg-background transition-colors text-xs font-semibold" 
                    />
                  </div>
                  <div className="space-y-4">
                     <div className="flex justify-between items-center">
                        <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.tickLen}</Label>
                        <span className="text-[10px] font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">{tickLineLen.toFixed(2)}</span>
                     </div>
                    <Slider 
                        value={tickLineLen} 
                        min={0.05} 
                        max={0.5} 
                        step={0.05} 
                        onValueChange={(val) => setTickLineLen(val)} 
                    />
                  </div>
                </div>
                <div className="flex items-center gap-3 py-1 group cursor-pointer" onClick={() => setShowMinor(!showMinor)}>
                   <div className={cn(
                       "w-4 h-4 rounded-full border-2 transition-all flex items-center justify-center",
                       showMinor ? "bg-primary border-primary" : "border-border bg-muted"
                   )}>
                       {showMinor && <div className="w-1.5 h-1.5 bg-background rounded-full" />}
                   </div>
                   <Label className="text-[11px] font-semibold cursor-pointer uppercase tracking-wider">{t.showMinor}</Label>
                </div>
              </div>

              <div className="space-y-5">
                <h3 className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-2">
                    <Palette size={13} className="text-muted-foreground" />
                    {t.density}
                </h3>
                <div className="flex items-center gap-3 py-1 group cursor-pointer" onClick={() => setUseDensity(!useDensity)}>
                   <div className={cn(
                       "w-4 h-4 rounded-full border-2 transition-all flex items-center justify-center",
                       useDensity ? "bg-primary border-primary" : "border-border bg-muted"
                   )}>
                       {useDensity && <div className="w-1.5 h-1.5 bg-background rounded-full" />}
                   </div>
                   <Label className="text-[11px] font-semibold cursor-pointer uppercase tracking-wider">{t.enableDensity}</Label>
                </div>
                {useDensity && (
                    <div className="grid grid-cols-2 gap-4 mt-2">
                        <div className="space-y-2">
                            <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.windowMb}</Label>
                            <Select value={windowSize} onValueChange={(v) => v && setWindowSize(v)}>
                                <SelectTrigger className="h-9 rounded-lg border-border bg-muted hover:bg-background transition-colors text-xs font-semibold">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="rounded-lg">
                                    <SelectItem value="0.1">0.1</SelectItem>
                                    <SelectItem value="0.5">0.5</SelectItem>
                                    <SelectItem value="1.0">1.0</SelectItem>
                                    <SelectItem value="2.0">2.0</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.colormap}</Label>
                            <Select value={colormap} onValueChange={(v) => v && setColormap(v)}>
                                <SelectTrigger className="h-9 rounded-lg border-border bg-muted hover:bg-background transition-colors text-xs font-semibold">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="rounded-lg">
                                    <SelectItem value="Grayscale_Print">Grayscale</SelectItem>
                                    <SelectItem value="Mako">Mako</SelectItem>
                                    <SelectItem value="Reds">Reds</SelectItem>
                                    <SelectItem value="viridis">Viridis</SelectItem>
                                    <SelectItem value="Blues">Blues</SelectItem>
                                    <SelectItem value="Greens">Greens</SelectItem>
                                    <SelectItem value="Purples">Purples</SelectItem>
                                    <SelectItem value="Oranges">Oranges</SelectItem>
                                    <SelectItem value="YlOrRd">Yellow-Orange-Red</SelectItem>
                                    <SelectItem value="YlGnBu">Yellow-Green-Blue</SelectItem>
                                    <SelectItem value="hot">Hot</SelectItem>
                                    <SelectItem value="turbo">Turbo</SelectItem>
                                    <SelectItem value="cividis">Cividis</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                )}
              </div>

              <div className="space-y-5 pb-4">
                 <h3 className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-2">
                    <Type size={13} className="text-muted-foreground" />
                    {t.labels}
                </h3>
                <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.chrWidth}</Label>
                            <span className="text-[10px] font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">{chrWidth.toFixed(2)}</span>
                        </div>
                        <Slider 
                            value={chrWidth} 
                            min={0.1} 
                            max={1.0} 
                            step={0.05} 
                            onValueChange={(val) => setChrWidth(val)} 
                        />
                    </div>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.labelGap}</Label>
                            <span className="text-[10px] font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">{labelSpacing.toFixed(1)}</span>
                        </div>
                        <Slider 
                            value={labelSpacing} 
                            min={0.1} 
                            max={5} 
                            step={0.1} 
                            onValueChange={(val) => setLabelGap(val)} 
                        />
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-6 pt-2">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.fontSize}</Label>
                            <span className="text-[10px] font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">{fontSize}</span>
                        </div>
                        <Slider 
                            value={fontSize} 
                            min={6} 
                            max={20} 
                            step={1} 
                            onValueChange={(val) => setFontSize(val)} 
                        />
                    </div>
                    <div className="space-y-2">
                        <Label className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.color}</Label>
                        <div className="flex gap-2">
                            <div className="relative w-11 h-9 shrink-0">
                                <Input type="color" value={labelColor} onChange={e => setLabelColor(e.target.value)} className="w-full h-full p-0 border-none cursor-pointer rounded-full overflow-hidden absolute inset-0 opacity-0 z-10" />
                                <div className="w-full h-full rounded-full border border-border pointer-events-none" style={{ backgroundColor: labelColor }} />
                            </div>
                            <Input type="text" value={labelColor} onChange={e => setLabelColor(e.target.value)} className="h-9 rounded-lg border-border bg-muted focus:bg-background transition-colors text-[10px] font-mono font-bold uppercase tracking-tight" />
                        </div>
                    </div>
                </div>
              </div>

              <div className="space-y-5">
                <h3 className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-2">
                  <Palette size={13} className="text-muted-foreground" />
                  {t.chrFill}
                </h3>
                <div className="flex gap-2">
                  <div className="relative w-11 h-9 shrink-0">
                    <Input
                      type="color"
                      value={chrFillColor || '#e5e7eb'}
                      onChange={e => setChrFillColor(e.target.value)}
                      className="w-full h-full p-0 border-none cursor-pointer rounded-full overflow-hidden absolute inset-0 opacity-0 z-10"
                    />
                    <div
                      className="w-full h-full rounded-full border border-border pointer-events-none"
                      style={{ backgroundColor: chrFillColor || '#e5e7eb' }}
                    />
                  </div>
                  <Input
                    type="text"
                    value={chrFillColor}
                    onChange={e => setChrFillColor(e.target.value)}
                    placeholder="#e5e7eb"
                    className="h-9 rounded-lg border-border bg-muted focus:bg-background transition-colors text-[10px] font-mono font-bold uppercase tracking-tight"
                  />
                </div>
              </div>
            </div>
          </section>
        </div>

        <div className="p-6 bg-background border-t border-border">
          <Button className="w-full gap-3 h-12 text-[13px] font-bold rounded-lg uppercase tracking-[0.15em] bg-primary text-primary-foreground hover:opacity-90 active:scale-[0.98] transition-all" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? <Loader2 className="animate-spin" size={20} strokeWidth={2.5} /> : <Play size={20} fill="currentColor" />}
            {t.runAnalysis}
          </Button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0 relative bg-background">
        {error && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50">
                <div className="bg-amber-500 text-white px-6 py-3 rounded-lg text-[11px] font-bold tracking-widest shadow-2xl flex items-center gap-3">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    {error}
                    <button className="ml-2 hover:opacity-70" onClick={() => setError(null)}>✕</button>
                </div>
            </div>
        )}

        <div className="flex-1 flex flex-col items-center justify-center p-12 overflow-auto bg-background">
          {!plotSrc && !isGenerating && (
            <div className="max-w-[540px] text-center space-y-6">
              <h1 className="text-4xl font-medium tracking-tight leading-tight">{t.ready}</h1>
              <p className="text-body leading-relaxed text-[15px] font-normal px-8 text-muted-foreground">
                {t.configGenomic.split('**').map((part, i) => i % 2 === 1 ? <strong key={i} className="text-foreground font-semibold">{part}</strong> : part)}
              </p>
            </div>
          )}

          {isGenerating && (
             <div className="flex flex-col items-center gap-8">
                <div className="relative">
                    <Loader2 className="animate-spin text-primary" size={80} strokeWidth={1.2} />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Dna size={32} className="text-muted-foreground opacity-50" />
                    </div>
                </div>
                <p className="text-[12px] font-bold text-muted-foreground uppercase tracking-[0.3em] animate-pulse">{t.processing}</p>
             </div>
          )}

          {plotSrc && !isGenerating && (
            <div className="w-full h-full flex flex-col overflow-hidden">
              <div className="flex-1 relative bg-background flex items-center justify-center overflow-hidden p-4">
                 <img 
                    src={plotSrc} 
                    alt="ChromoMap" 
                    className="w-full h-full object-contain"
                 />
              </div>
              
              <div className="flex items-center justify-center gap-4 p-3 bg-muted border-t border-border shrink-0">
                <Button variant="ghost" size="sm" className="rounded-lg text-[11px] font-bold h-9 px-4 uppercase tracking-widest text-muted-foreground hover:text-foreground" onClick={() => handleExport('png')}>
                    <Download size={15} className="mr-2" /> PNG
                </Button>
                <Button variant="ghost" size="sm" className="rounded-lg text-[11px] font-bold h-9 px-4 uppercase tracking-widest text-muted-foreground hover:text-foreground" onClick={() => handleExport('svg')}>
                    SVG
                </Button>
                <Button variant="ghost" size="sm" className="rounded-lg text-[11px] font-bold h-9 px-4 uppercase tracking-widest text-muted-foreground hover:text-foreground" onClick={() => handleExport('pdf')}>
                    PDF
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="h-10 border-t border-border flex items-center justify-between px-8 text-[9px] text-muted-foreground tracking-[0.2em] font-bold uppercase bg-background">
           <div className="flex items-center gap-4">
              <span>ChromoMap Physical Mapper</span>
              <span className="text-border-strong opacity-50">/</span>
              <span>v2.0.0</span>
           </div>
           <div className="flex items-center gap-6">
              <span className="opacity-60 hover:opacity-100 transition-opacity cursor-default">Electron + Python</span>
              <span className="text-border-strong opacity-50">·</span>
              <span className="opacity-60 hover:opacity-100 transition-opacity cursor-default">Privacy Guaranteed</span>
           </div>
        </div>
      </main>
    </div>
  )
}
