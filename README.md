# ChromoMap (v12.9)

染色体物理图谱生成工具 — 桌面独立应用。

## 核心功能

- **数据驱动绘图**：输入基因位置和染色体长度，自动生成物理图谱。
- **现代化 UI**：采用极简白底黑字设计，提供如 ChatGPT 般的流畅体验。
- **多语言支持**：支持中英文界面一键切换。
- **多种导入方式**：支持文本粘贴和 Excel (`.xlsx`, `.xls`) / CSV 文件上传。
- **密度热力图**：支持上传 GFF3 文件并根据基因密度进行热力图着色。
- **多格式导出**：支持导出 PNG、SVG、PDF 格式。
- **示例数据**：内置示例数据，点击即可一键预览效果。

## 项目结构

```
MyChromoMap/
├── renderer/                 # 前端 UI (HTML + CSS + JS) - 现代白底黑字风格
├── python/                   # 计算引擎 (Matplotlib 3.10)
│   ├── main.py              # CLI 入口
│   ├── plotter.py           # 绘图核心 (Noto Sans/Noto Serif + DejaVu 字体支持)
│   └── fonts/               # 字体包
├── src-tauri/                # Tauri/Rust 后端
└── scripts/                  # 构建脚本 (Python 运行时打包与精简)
```

## 快速开始 (开发人员)

### 1. 环境准备
- **Node.js**: 最新 LTS 版本
- **Rust**: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- **Python**: 3.11+ (仅开发阶段需要)

### 2. 初始化项目
```bash
npm install
bash scripts/build-python.sh
```

### 3. 运行与打包
- **开发模式**: `npm run dev`
- **打包 Apple Silicon 版**: `npm run build:mac` (产出位于 `src-tauri/target/aarch64.../bundle/dmg/`)
- **打包 Intel 版**: `npm run build:mac-x64`

## 交接说明

- **Excel 解析**: 前端将文件路径传给 Python，Python 使用 `pandas.read_excel` 进行解析。
- **字体管理**: `plotter.py` 已配置优先使用 Noto Sans / Noto Serif CJK SC，如需更改可在 `_register_fonts` 中修改。
- **样式定制**: 侧边栏样式在 `renderer/style.css` 中通过 `!important` 强制定义，确保 UI 统一性。
- **打包逻辑**: 应用自带便携式 Python 运行时，用户端无需安装任何环境。

## 常见维护
- **更新 Python 库**: 修改 `python/requirements.txt` 后运行 `bash scripts/build-python.sh`。
- **修改多语言**: 在 `renderer/index.html` 中通过 `data-zh` 属性添加中文翻译。

---
*ChromoMap - 让基因组可视化更简单。*
