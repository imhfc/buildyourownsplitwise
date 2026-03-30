---
name: xlsx
description: 使用 Atomic Agents 組合處理 Excel 試算表的建立、編輯、驗證與分析。
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# XLSX 試算表處理

> 使用 Atomic Agents 組合處理 Excel 試算表建立、編輯、分析與公式計算
>
> 使用 Atomic Agents: file-finder + compliance-auditor + pattern-checker + code-editor + code-formatter
> 詳見 @.claude/agents/atomic/README.md

---


## 觸發與路由


**Use this skill when:**
- 「建立 Excel 試算表」
- 「編輯現有 XLSX」
- 「XLSX → CSV 轉換」
- 「計算 selectIndex」

**DO NOT trigger for:**
- 「處理 Word」 → 使用 docx
- 「處理 Markdown」 → 使用 markdown-doc-processor

## 快速使用

### 建立 Excel 試算表

```bash
# 自然語言請求
"建立一個 Excel 試算表包含資料表"
"產生批次規格欄位比對表 XLSX"
"將 CSV 資料轉換為 Excel 格式"
```

AI 會使用 openpyxl 建立結構化的 Excel 試算表

### 編輯現有試算表

```bash
# 自然語言請求
"修改這個 XLSX 的工作表資料"
"更新 Excel 試算表的公式"
"在試算表中新增圖表"
```

AI 會：
1. 讀取現有 XLSX
2. 執行編輯操作
3. 重新計算公式（如需要）
4. 保存修改後的試算表

### 分析試算表內容

```bash
# 自然語言請求
"分析這個 XLSX 試算表的結構"
"提取 Excel 中的資料表"
"讀取試算表的儲存格值"
```

## 核心功能

### 工作流程

1. **file-finder**: 收集 Excel 文件（.xlsx, .xlsm, .csv）
2. **compliance-auditor + pattern-checker**: 並行驗證結構與格式
3. **code-editor**: 修正問題（公式、儲存格值、格式）
4. **code-formatter**: 格式化試算表並重新計算公式

詳細步驟見 [guide.md](./guide.md)

### 四大職責

1. **試算表建立** - 使用 openpyxl 建立結構化 Excel 試算表
2. **內容編輯** - 修改儲存格、工作表、公式
3. **公式計算** - 支援 Excel 公式與函數
4. **資料分析** - 提取資料、統計、圖表

### 支援操作

#### 建立試算表
- 新建工作簿
- 新增工作表
- 設定儲存格值
- 設定儲存格格式
- 合併儲存格
- 新增圖表

#### 編輯試算表
- 修改儲存格內容
- 更新公式
- 調整欄寬/列高
- 設定樣式與顏色
- 插入/刪除列/欄

#### 公式與函數
- 基本運算 (+, -, *, /)
- SUM, AVERAGE, COUNT
- IF, VLOOKUP, INDEX/MATCH
- 日期函數
- 文字函數

#### 資料分析
- 讀取儲存格值
- 提取資料範圍
- 計算統計資訊
- 產生樞紐分析表
- 匯出為 CSV/TSV

## 使用場景

| 場景 | 使用此 Skill? | 功能 |
|------|--------------|------|
| 建立批次規格欄位比對表 |  Yes | 試算表建立 + 格式 |
| 編輯現有 Excel 試算表 |  Yes | 內容編輯 + 公式 |
| XLSX → CSV 轉換 |  Yes | 資料分析 + 匯出 |
| CSV → XLSX 轉換 |  Yes | 試算表建立 |
| 計算 selectIndex |  Yes | 公式計算 |
| 資料視覺化圖表 |  Yes | 圖表建立 |
| 大數據處理 (>1M 列) |  No | 使用資料庫 |
| 複雜統計分析 |  No | 使用 pandas |

## 工具與技術

### openpyxl 套件

```python
from openpyxl import Workbook, load_workbook

# 建立試算表
wb = Workbook()
ws = wb.active
ws['A1'] = 'Header'
ws['A2'] = 42

# 設定公式
ws['B2'] = '=A2*2'

# 保存
wb.save('output.xlsx')
```

### 主要功能

- 新增工作表、設定儲存格值、設定公式
- 合併儲存格、設定格式
- 讀取儲存格、迭代列

詳細 API 參考見 [guide.md](./guide.md)

## 檔案格式支援

### 輸入格式
- `.xlsx` (Excel 2007+)
- `.xlsm` (Excel 含巨集)
- `.csv` (逗號分隔)
- `.tsv` (Tab 分隔)

### 輸出格式
- `.xlsx` (標準 Excel 格式)
- `.csv` (資料匯出)
- `.tsv` (資料匯出)


## 相關規範

- **Office Open XML (OOXML)**: `.xlsx` 格式標準
- **openpyxl Documentation**: 官方套件文檔
- **Excel 函數參考**: Microsoft Excel 函數列表

## 相關工具

- **Excel 處理工具**: `.claude/skills/markdown-doc-processor/scripts/README.md`
  - extract_excel_markitdown.py - 提取欄位比對表並計算 selectIndex
  - convert_docx_markitdown.py - Excel 轉 Markdown


## 最佳實踐

### 推薦

1. **零公式錯誤** - 使用 recalc.py 驗證所有公式
2. **使用公式而非硬編碼** - 保持試算表動態可更新

### 避免

1. **硬編碼計算** - 在 Python 計算值並寫入（應使用 Excel 公式）
2. **忽略公式錯誤** - #REF!, #DIV/0! 等錯誤應全部修正

## 相關 Skills

### 協作 Skills
- `reconcile-batch-spec-converter` - 使用 XLSX 計算 selectIndex
- `docx` - Word 文檔處理
- `markdown-doc-processor` - 整合規格文檔

## 詳細說明

完整 API 參考、範例、公式計算請參閱：[guide.md](./guide.md)
