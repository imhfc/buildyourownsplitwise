# AI 文檔工具集

> 文檔體系健康度檢查 + DOCX/Excel 轉換 + Markdown 格式修復與驗證 + 死連結檢查
> 版本: 7.1 (2026-02-01)
> 工具數量: 5 個 Bash 腳本 + 11 個 Python 腳本

---

## 工具清單

### 健康度檢查工具 (Bash)

| 工具 | 用途 |
|------|------|
| `check-docs-health.sh` | **文檔體系健康度檢查** - 驗證所有規範文件的完整性和引用正確性 (124 項檢查) |
| `validate-search-index.sh` | 檢查 SEARCH-INDEX.md 連結有效性（已整合到 check-docs-health.sh） |
| `migrate-version-format.sh` | 批量移除文檔中的版本標記（符合 DOC-00 標準） |

### 轉換工具 (Microsoft markitdown)

| 工具 | 用途 |
|------|------|
| `convert_docx_markitdown.py` | Microsoft markitdown 轉換 DOCX/Excel → Markdown |
| `extract_excel_markitdown.py` | 從 Excel 提取欄位比對表 + 計算 FCS selectIndex |

### 格式修復工具

| 工具 | 用途 |
|------|------|
| `fix_markdown_pipeline.py` | **統一 Pipeline** - 整合 9 步驟格式修復 (SOLID 架構) |
| `fix_markdown_tables.py` | 通用表格修復 (分隔線、對齊、全形空格) |
| `fix_readme_links.py` | 修正 README.md 斷鏈，標記 N/A 章節 |
| `fix-docx-markdown.py` | DOCX 轉出的 Markdown 格式修復 |

### 驗證工具

| 工具 | 用途 |
|------|------|
| `validate_pandoc_format.py` | **前置分析** - 掃描所有格式問題 + 偵測斷頭簽章表格 |
| `validate_batch_specs.py` | 批次規格驗證 (README 斷鏈、API 重複) |

### 死連結檢查工具

| 工具 | 用途 |
|------|------|
| `check-dead-links.sh` | 檢查 Markdown 文件中的死連結（Bash 版本） |
| `check-dead-links.py` | 檢查 Markdown 文件中的死連結（Python 版本） |
| `check-traditional-chinese.sh` | 檢查 Markdown 文件是否使用繁體中文 |
| `fix-dead-links.py` | 修復 Markdown 文件中的死連結 |

---

---

## 快速開始

### 健康度檢查

```bash
# 檢查文檔體系健康度（124 項檢查）
./scripts/ai-docs-tools/check-docs-health.sh

# 詳細模式（顯示所有檢查項目）
./scripts/ai-docs-tools/check-docs-health.sh -v

# 輸出範例：
# 檢查項目總數: 124
# 通過: 124
# 失敗: 0
# 健康度: 100% - 優秀 ✓
```

**檢查項目包含**:
- 6 個核心配置文件（CLAUDE.md, preferences.yaml 等）
- 4 個 ADR 架構決策（ADR-003, ADR-005, ADR-006, ADR-008）
- 7 個行為規範（ARCH-01, ROLE-01/02/03, GIT-01, DOC-00）
- 2 個設計模式（TEST-001, DES-004）
- 20 個 Guide 指南
- 4 個 AI 行為文檔
- 66 個 SEARCH-INDEX 連結
- 6 個微服務配置
- 記憶庫格式驗證

**健康度評級**:
- 95-100%: 優秀 ✓
- 85-94%: 良好
- 70-84%: 尚可 ⚠
- <70%: 需要改進 ✗

### DOCX/Excel 轉換 (markitdown)

```bash
# 安裝 markitdown
pip install 'markitdown[docx, xlsx]'

# 單一檔案轉換
python3 scripts/ai-docs-tools/convert_docx_markitdown.py spec.docx ./output

# 批次轉換 (org 模式)
python3 scripts/ai-docs-tools/convert_docx_markitdown.py /path/to/docx_folder /path/to/specs --org-mode

# 提取 Excel 欄位比對表 + 計算 selectIndex
python3 scripts/ai-docs-tools/extract_excel_markitdown.py 欄位比對表.xlsx --output 09-欄位比對表.md
```

### 格式修復 Pipeline

```bash
# 執行統一 Pipeline (9 步驟自動執行)
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs

# 預覽模式（不實際修改）
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs --dry-run

# 只執行特定步驟
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs --steps 1,2,3
```

### 驗證規格

```bash
# 批次驗證所有規格
python3 scripts/ai-docs-tools/validate_batch_specs.py ./reconcile-batch-specs

# 修正 README 斷鏈
python3 scripts/ai-docs-tools/fix_readme_links.py ./reconcile-batch-specs

# 前置分析格式問題
python3 scripts/ai-docs-tools/validate_pandoc_format.py /path/to/specs
```

---

## convert_docx_markitdown.py

使用 Microsoft markitdown 轉換 DOCX/Excel 為 Markdown。

### 特點

- **Python 原生**：無需系統依賴 (不需要 Pandoc)
- **開箱即用**：pip install 即可使用
- **直接 Pipe Table**：轉換結果直接為 Pipe Table 格式
- **支援 org 模式**：可輸出到 `spec_dir/org/` 目錄結構

### 使用方式

```bash
# 單一 DOCX 檔案轉換
python3 scripts/ai-docs-tools/convert_docx_markitdown.py spec.docx ./output

# 單一 Excel 檔案轉換
python3 scripts/ai-docs-tools/convert_docx_markitdown.py 欄位比對表.xlsx ./output

# 批次轉換目錄 (org 模式)
python3 scripts/ai-docs-tools/convert_docx_markitdown.py /path/to/docx_folder /path/to/specs --org-mode
```

### 輸出命名規則

| 檔案類型 | 輸出命名 |
|---------|---------|
| DOCX | `_原始文件_{filename}.md` |
| Excel | `{filename}.md` |

---

## extract_excel_markitdown.py

從 Excel 提取欄位比對表並計算 FCS BPMN 的 selectIndex。

### 功能

- 自動識別「是否比對」欄位
- 排除 REDEFINE 欄位
- 從 0 開始編號非 REDEFINE 欄位
- **計算 selectIndex** = Key 欄位索引 + Y 欄位索引

### selectIndex 計算規則

```
selectIndex = Key 欄位索引 + 「是否比對 = Y」欄位索引

步驟：
1. 排除 REDEFINE 欄位
2. 從 0 開始編號剩餘欄位
3. 找出 Key 欄位 (CUST-NO, TYPE) 的索引
4. 找出「是否比對 = Y」欄位的索引
5. 合併並排序

範例：
- Key: 0,1 (CUST-NO, TYPE)
- Y:   6,7 (NAME3, ROMNAME)
- 結果: selectIndex = "0,1,6,7"
```

### 使用方式

```bash
# 提取並顯示於終端
python3 scripts/ai-docs-tools/extract_excel_markitdown.py 欄位比對表.xlsx

# 提取並儲存為 Markdown
python3 scripts/ai-docs-tools/extract_excel_markitdown.py 欄位比對表.xlsx --output 09-欄位比對表.md
```

### 輸出格式

```markdown
# 欄位比對表

**來源**: `欄位比對表.xlsx`

## FCS selectIndex

```
selectIndex="0,1,6,7"
```

## 欄位列表

| index | 欄位名稱 | 是否比對 | 備註 |
|-------|---------|---------|------|
| 0 | CUST-NO | Y | Key, Y |
| 1 | TYPE | Y | Key, Y |
| ... | ... | ... | ... |
```

---

## fix_markdown_pipeline.py

統一格式修復 Pipeline，整合 9 個 Fixer (SOLID 架構)。

### 內建 9 個 Fixer

1. Grid Table → Pipe Table
2. 清理嵌入式 Grid 標記
3. 移除 Pandoc span 標記
4. 移除空表格行 (保護簽章表格)
5. 修復無效連結
6. 表格前後空行
7. 清理跳脫字元
8. 儲存格換行
9. 還原簽章表格

### 使用方式

```bash
# 執行完整 Pipeline
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs

# 預覽模式
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs --dry-run

# 只執行特定步驟
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs --steps 1,2,3
```

---

## fix_markdown_tables.py

修復 Markdown 表格格式問題。

### 處理的問題

| 問題 | 處理方式 |
|------|---------| | 缺失分隔線 | 自動在標題後插入 `|---|---|` |
| 多行標題 | 合併為單行 |
| 欄位數不一致 | 自動對齊 |
| 全形空格 | 轉換為半形 |
| EMF 路徑 | 替換為 .png |

### 使用方式

```bash
# 標準輸入/輸出
cat input.md | python3 fix_markdown_tables.py > output.md

# 檔案參數
python3 fix_markdown_tables.py input.md output.md

# 就地修改
python3 fix_markdown_tables.py input.md temp.md && mv temp.md input.md
```

---

## fix_readme_links.py

批次修正 README.md 斷鏈，自動標記 N/A 章節。

### 功能

- 檢測並修正斷鏈
- 不存在的章節 (04-DB, 06-FSD, 07-測試) 標記為 N/A
- 自動偵測 09-* 各種命名
- 保持一致的格式

### 使用方式

```bash
# 正式修正
python3 scripts/ai-docs-tools/fix_readme_links.py ./reconcile-batch-specs

# 預覽模式 (不寫入)
python3 scripts/ai-docs-tools/fix_readme_links.py ./reconcile-batch-specs --dry-run
```

---

## validate_batch_specs.py

批次規格驗證工具，一次檢查所有問題。

### 檢查項目

| 項目 | 說明 |
|------|------|
| README.md 斷鏈 | 引用不存在的 .md 檔案 |
| API 真實重複 | 相同 method + URI 組合出現多次 |

### 使用方式

```bash
python3 scripts/ai-docs-tools/validate_batch_specs.py ./reconcile-batch-specs
```

---

## validate_pandoc_format.py

前置分析工具，掃描所有格式問題。

### 檢查項目

- Grid Table 殘留
- Pandoc span 標記
- 無效連結
- 斷頭簽章表格
- 表格格式問題

### 使用方式

```bash
# 掃描所有格式問題
python3 scripts/ai-docs-tools/validate_pandoc_format.py /path/to/specs

# 產出問題報告
python3 scripts/ai-docs-tools/validate_pandoc_format.py /path/to/specs > report.txt
```

---

## 批次規格格式修復 SOP

> 適用於已轉換的 Markdown 規格文件

### 標準流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. 前置分析    │ ──► │  2. 格式修復    │ ──► │  3. 驗證確認    │
│  validate_pandoc│     │  9 步驟工具     │     │  validate_specs │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Step 1: 前置分析（一次做對）

**先分析再修復，避免增量式迭代**：

```bash
# 掃描所有格式問題，產出問題報告
python3 scripts/ai-docs-tools/validate_pandoc_format.py /path/to/specs
```

### Step 2: 格式修復（Pipeline）

```bash
# 執行統一 Pipeline (9 步驟自動執行)
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs

# 預覽模式
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs --dry-run

# 只執行特定步驟
python3 scripts/ai-docs-tools/fix_markdown_pipeline.py /path/to/specs --steps 1,2,3
```

### Step 3: 驗證與修正

```bash
# 1. 驗證所有規格
python3 scripts/ai-docs-tools/validate_batch_specs.py ./reconcile-batch-specs

# 2. 若有問題，批次修正 README
python3 scripts/ai-docs-tools/fix_readme_links.py ./reconcile-batch-specs

# 3. 再次驗證確認
python3 scripts/ai-docs-tools/validate_batch_specs.py ./reconcile-batch-specs
```

---

## Grid Table 轉換 SOP (LL-032) 

> **一次做對，避免迭代失敗**
>
> 適用於：Pandoc 轉換產生的 Grid Table 需要轉為 Pipe Table

### 問題背景

Pandoc 轉換 DOCX 時會產生 Grid Table 格式（使用 `+----+` 邊框），需要轉換為 GitHub Flavored Markdown 的 Pipe Table 格式。

**常見錯誤**：
-  多個腳本互相干擾，覆蓋彼此結果
-  發現問題太晚（轉換完才發現格式錯誤）
-  重複處理已正確的內容，導致二次破壞

### 4 Phase SOP（必須遵循）

| Phase | 時間 | 關鍵動作 | 產出 |
|-------|------|---------|------|
| **Phase 0: 完整分析** | 30 min | 識別所有 Grid Table 變體 | 變體清單、行範圍 |
| **Phase 1: 測試案例** | 20 min | 建立測試輸入/期望輸出 | 測試案例集 |
| **Phase 2: 單一腳本** | 40 min | 整合轉換 + 保護機制 | GridTableConverter |
| **Phase 3: 階段驗證** | 10 min | Checkpoint 驗證 | 驗證報告 |

### 檢查指令

```bash
# 1. 找出所有 Grid Table 變體
grep -E '^\+[-:=]+' input.md output.md

# 2. 檢查多層嵌套
grep -E '^\|.*\+[-:]+.*\|' input.md output.md

# 3. 識別假表格（非數據表格）
grep -E '^\|[^|]+\|' input.md output.md
```

### 時間效益

| 方式 | 時間 | 品質 |
|------|------|------|
| **反應式修復** | 2+ 小時 |  多次迭代 |
| **4 Phase SOP** | 100 分鐘 |  一次完成 |
| **節省** | ~50% | 更高品質 |

---

## 格式驗證檢查清單

### 表格格式
- [ ] 無 Grid Table 殘留 (`+---+`)
- [ ] 所有表格有分隔線 (`|---|`)
- [ ] 表格欄位數一致
- [ ] 無全形空格

### Markdown 語法
- [ ] 無 Pandoc span 標記 (`{.mark}`)
- [ ] 無無效連結 (`[text](.)`)
- [ ] 無跳脫字元問題 (`\_`)
- [ ] 簽章表格 header 完整

### README 連結
- [ ] 所有章節連結有效
- [ ] N/A 章節正確標記

---

## 圖片清理 SOP (LL-013)

> 清理不必要的圖片時，**必須先檢查引用再刪除**

### 正確流程

```
1. 分析階段（先看再動）
   ├── 列出所有圖片檔案: ls images/
   ├── 列出所有 markdown 圖片引用: grep -o 'images/[^)]*' *.md
   └── 建立「檔案 ↔ 引用」對照表

2. 分類階段（判斷重要性）
   ├── 有引用 + 內容重要 → 保留
   ├── 有引用 + 內容不重要 → 移除檔案 + 移除/註解引用
   └── 無引用 → 直接移除

3. 執行階段（同步操作）
   └── 移除檔案時**同時更新引用**

4. 驗證階段
   ├── 檢查保留圖片都有對應引用
   └── 檢查所有引用都指向存在的檔案
```

### 驗證指令

```bash
# 檢查有引用但檔案不存在
grep -roh 'images/[^)]*' *.md | sort -u | while read img; do
    [ ! -f "$img" ] && echo "缺少檔案: $img"
done

# 檢查有檔案但無引用
for img in images/*; do
    grep -q "$(basename $img)" *.md || echo "無引用: $img"
done
```

---

## 圖片位置驗證 SOP (LL-014)

> 驗證圖片位置，**確保圖片在語義正確的標題下**

### 常見錯位檢查

```bash
# 找出疑似錯位的檔案
for f in */org/_原始文件_*.md; do
    if grep -A 3 "新舊欄位比對表" "$f" | grep -q "image"; then
        echo "可能錯位: $f"
    fi
done
```

---

## check-dead-links.py / check-dead-links.sh

檢查 Markdown 文件中的死連結。

### 使用方式

```bash
# Python 版本

# Bash 版本
bash .claude/skills/markdown-doc-processor/scripts/check-dead-links.sh
```

### 功能

- 掃描所有 .md 檔案
- 檢查相對路徑連結是否存在
- 輸出死連結統計與分類
- Exit Code: 0（無死連結）或 99（發現死連結）

---

## check-traditional-chinese.sh

檢查 Markdown 文件是否使用繁體中文。

### 使用方式

```bash
bash .claude/skills/markdown-doc-processor/scripts/check-traditional-chinese.sh
```

---

## fix-dead-links.py / fix-aidocs-links.py

修復 Markdown 文件中的死連結。

### 使用方式

```bash
# 通用死連結修復
python3 .claude/skills/markdown-doc-processor/scripts/fix-dead-links.py

# AI-Docs 目錄專用修復
python3 .claude/skills/markdown-doc-processor/scripts/fix-aidocs-links.py
```

---

## 相關文檔

- [DOC-04 Markdown 文檔處理 SOP](../behavior/universal/standards/DOC-04-documentation-sop/README.md)
- [markdown-doc-processor Skill](../../.claude/skills/markdown-doc-processor/)
- [reconcile-batch-spec-converter Skill](../../.claude/skills/reconcile-batch-spec-converter/SKILL.md)

---

**建立日期**: 2026-01-05
**更新日期**: 2026-02-01
**維護者**: AI-Scrum Team

**變更記錄**:
- 2026-02-01: 合併 .claude/skills/markdown-doc-processor/scripts 死連結檢查工具至此目錄，版本 7.1（消除重複目錄結構）
- 2026-01-31: 新增文檔體系健康度檢查腳本 (check-docs-health.sh)，版本 7.0
- 2026-01-13: 加入 markitdown 轉換工具 (convert_docx_markitdown.py, extract_excel_markitdown.py)，版本 6.1
- 2026-01-13: 移除 Pandoc 相關轉換工具，保留格式檢核工具
- 2026-01-13: 新增 Grid Table 轉換 SOP (LL-032)
- 2026-01-07: SOLID 重構，統一 Pipeline
- 2026-01-05: 初版發布
