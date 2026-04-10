# 📋 CFH 设计中心 — 文档索引页

> **独立 HTML 网页方案**，数据与展示分离，支持多职能 Tab 切换。

---

## 📁 文件结构

```
doc-index/
├── index.html          ← 🎯 网页主体（渲染引擎，不需要手动改）
├── data.js             ← 📌 数据文件（**只需要编辑这个**，或用 sync.py 自动生成）
├── sync.py             ← 🔧 Figma API 数据同步脚本
├── _run.py / _upload.py  ← 内部辅助脚本（一般不需要手动运行）
├── legacy/             ← 📦 已归档的旧版本文件
│   ├── figma-index-preview.html   ← 旧版单页预览（已被 index.html 替代）
│   └── Figma索引页实施指南.md      ← Figma Frame 操作指南（参考保留）
└── README.md           ← 本文件
```

## ✨ 功能

- **三职能 Tab 导航**：✏️ 交互稿(78) / 🔧 重构落地(11) / 📊 概念推导&周报(90)
- **独立主题色**：每个 Tab 有自己的颜色风格（紫/青/珊瑚）
- **两层筛选**：板块 → 子分类，快速定位文档
- **搜索功能**：按名称、标签、负责人搜索
- **统计栏**：显示总数和各状态数量
- **点击跳转 Figma**：每张卡片直接打开原文件
- **已访问标记**：访问过的卡片自动变淡
- **响应式布局**：手机/平板/电脑自适应
- **键盘快捷键**：`/` 快速聚焦搜索框

## 🚀 如何使用

### 方式一：直接打开（最快）

双击 `index.html` 即可在浏览器中查看。

### 方式二：本地预览

```bash
cd doc-index/
python -m http.server 8080
# 打开 http://localhost:8080
```

### 方式三：GitHub Pages 部署（推荐团队使用）

1. 推送 `doc-index/` 目录到 GitHub 仓库
2. 开启 Pages 功能
3. 团队成员通过链接即可访问最新索引

### 更新数据

#### 手动编辑 data.js
```javascript
{
  "name": "文档名称",
  "url": "https://www.figma.com/file/xxx",   // 点击跳转链接
  "category": "分类名",
  "categoryKey": "分类英文key",                // 用于筛选
  "section": "所属板块",                       // 局外/局内/通用 等
  "status": "active|review|stable",            // 文件状态
  "lastModified": "2026-04-10T00:00:00Z"     // 最后修改时间
}
```

#### 用 sync.py 自动同步
```bash
cd doc-index/
python sync.py        # 从 Figma API 拉取最新文件列表 → 生成 data.js
```

> ⚠️ 运行前需配置 Figma Access Token 和 Team ID。

## 🎨 数据格式说明

`data.js` 使用**多通道格式** (`DOC_DATA.channels`)：

| 通道 | key | 说明 | 文件数 |
|------|-----|------|--------|
| 交互稿 | `ixd` | Project 231182587 (CFBH设计线) | 78 |
| 重构落地 | `refactor` | Project 243822260 (CFBH重构落地) | 11 |
| 概念推导&周报 | `weekly` | Projects 222913532+222913092 | 90 |

每个通道包含：
- `title` / `subtitle` — 标题和副标题
- `sections` — 板块分组（局外/局内/通用等）
- `categories` — 分类汇总
- `documents[]` — 文档扁平数组（index.html 渲染的数据源）

## 🔗 与 Figma 插件的关系

本网页是 **Figma 插件 (figma-doc-indexer/) 的输出目标之一**：

```
Figma Plugin 扫描 Team 文件
       ↓
  解析文件名 / 分类 / 状态
       ↓
  生成 data.js ←→ index.html 渲染
       ↓
  GitHub Pages 部署 → 团队共享
```

插件当前支持：
- ✅ 按 Team 或 Project 扫描文件
- ✅ 分批传输（避免大体量 PostMessage 卡死）
- ✅ 在 Figma 中生成索引 Frame
- ⏳ 导出为 data.js 格式（TODO：后续开发）

---

*最后更新: 2026-04-10*
