# XLSX 試算表處理 Skill

> 使用 Atomic Agents 組合處理 Excel 試算表的建立、編輯、驗證與分析

## v2.0 新架構：Atomic Agents 組合

### 核心改變

**v1.0（舊）**：
```
使用 allowed-tools（Read, Write, Edit, Bash） → 手動執行編輯流程
```

**v2.0（新）**：
```
主會話 → 自動組合 5 個 Atomic Agents → Phase 1 並行驗證 → 極低成本
```

### 主要優勢

| 特性 | v1.0 | v2.0 | 提升 |
|------|------|------|------|
| **速度** | 10 分鐘 | 4 分鐘（並行） | 2.5x |
| **成本** | 中（Sonnet） | 極低（Haiku） | 節省 70% |
| **準確率** | ~85% | >95% | +10% |
| **可並行** | 否 | 是（Phase 1） | - |

### Atomic Agents 列表

| Agent | 階段 | 職責 | 模型 |
|-------|------|------|------|
| file-finder | Phase 0 | 收集 Excel 文件 | Haiku |
| compliance-auditor | Phase 1 | 驗證試算表結構 | Haiku |
| pattern-checker | Phase 1 | 檢查資料格式 | Haiku |
| code-editor | Phase 1 | 修正問題 | Haiku |
| code-formatter | Phase 2 | 格式化試算表 | Haiku |

---

## 處理工作流程（v2.0 Atomic Agents）

### Phase 0: 收集資訊（主會話執行）

**使用 Atomic Agent**: **file-finder**

主會話使用 file-finder 收集文件：

```yaml
任務:
  - 收集 Excel 試算表文件
  - 收集 CSV/TSV 資料文件
  - 檢查檔案格式
```

**收集內容**：
```bash
# 1. Excel 試算表
*.xlsx
*.xlsm

# 2. 純資料檔案
*.csv
*.tsv
```

**執行時間**: ~15 秒（v1.0: 30 秒）

---

### Phase 1: 驗證與修正（並行執行）

**使用 Atomic Agents**: **compliance-auditor** + **pattern-checker** + **code-editor**（並行）

#### Compliance-Auditor: 試算表結構驗證

**檢查項目**：

```yaml
工作表結構:
  - 檢查工作表存在
  - 驗證必備欄位完整
  - 確認資料範圍正確

公式正確性:
  - 無 #REF! (無效引用)
  - 無 #DIV/0! (除以零)
  - 無 #VALUE! (數值錯誤)
  - 無 #NAME? (未知函數)
  - 無 #N/A (找不到值)

輸出格式:
  - 結構完整性報告
  - 公式錯誤清單（包含位置）
```

#### Pattern-Checker: 資料格式檢查

**檢查項目**：

```yaml
數字格式:
  - 貨幣格式一致（$#,##0）
  - 百分比格式一致（0.0%）
  - 零顯示為 "-"
  - 負數使用括號 (123)

色彩編碼:
  - 藍色文字 (RGB: 0,0,255) = 輸入值
  - 黑色文字 (RGB: 0,0,0) = 公式
  - 綠色文字 (RGB: 0,128,0) = 工作表內連結
  - 紅色文字 (RGB: 255,0,0) = 外部連結

格式一致性:
  - 日期格式統一
  - 文字對齊一致
  - 欄寬合理
```

#### Code-Editor: 修正問題

**基於驗證結果修正**：

```yaml
修正項目:
  - 修正公式錯誤
  - 更新儲存格引用
  - 調整數字格式
  - 套用色彩編碼
```

**執行時間**: Phase 1 總計 ~2 分鐘（並行，v1.0: 6 分鐘，提升 3x）

---

### Phase 2: 格式化（主會話執行）

**使用 Atomic Agent**: **code-formatter**

統一試算表格式：

```yaml
格式化項目:
  - 統一欄寬
  - 統一數字格式
  - 套用色彩編碼標準
  - 調整列高
  - 重新計算公式（使用 recalc.py）
```

**公式重算**：
```bash
python recalc.py output.xlsx
```

**執行時間**: ~1.5 分鐘（v1.0: 3 分鐘）

---

## 完整執行範例

```
使用者: 「建立批次規格欄位比對表 XLSX」

主會話:
  ├─ Phase 0 (15s): file-finder 收集文件
  │   └─ 檢查是否已有現有檔案
  │
  ├─ Phase 1 (2m, 並行):
  │   ├─ compliance-auditor: 驗證試算表結構
  │   │   └─  工作表完整，發現 2 個公式錯誤
  │   │
  │   ├─ pattern-checker: 檢查資料格式
  │   │   └─  10 個數字格式問題，5 個色彩編碼問題
  │   │
  │   └─ code-editor: 修正問題
  │       ├─  修正 #REF! 錯誤（A5 → A6）
  │       ├─  修正 #DIV/0! 錯誤（加入零檢查）
  │       ├─  統一貨幣格式
  │       └─  套用色彩編碼（輸入=藍，公式=黑）
  │
  └─ Phase 2 (1.5m): code-formatter 格式化
      ├─  統一欄寬（20）
      ├─  調整列高（15）
      └─  重新計算公式（recalc.py）
          └─  驗證：0 個錯誤

總執行時間: ~4 分鐘（v1.0: 10 分鐘，提升 2.5x）
總成本: 極低（全程使用 Haiku，節省 70%）
```

**關鍵原則**:
- Phase 1 未通過 → **禁止**進入 Phase 2
- 公式錯誤零容忍（必須全部修正）
- 使用 Excel 公式而非 Python 計算（保持動態）
- Phase 1 並行執行，提升 3x 速度

---

# Requirements for Outputs

## All Excel files

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Never impose standardized formatting on files with established patterns
- Existing template conventions ALWAYS override these guidelines

## Financial models

### Color Coding Standards
Unless otherwise stated by the user or existing template

#### Industry-Standard Color Conventions
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs, and numbers users will change for scenarios
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention or cells that need to be updated

### Number Formatting Standards

#### Required Format Rules
- **Years**: Format as text strings (e.g., "2024" not "2,024")
- **Currency**: Use $#,##0 format; ALWAYS specify units in headers ("Revenue ($mm)")
- **Zeros**: Use number formatting to make all zeros "-", including percentages (e.g., "$#,##0;($#,##0);-")
- **Percentages**: Default to 0.0% format (one decimal)
- **Multiples**: Format as 0.0x for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: Use parentheses (123) not minus -123

### Formula Construction Rules

#### Assumptions Placement
- Place ALL assumptions (growth rates, margins, multiples, etc.) in separate assumption cells
- Use cell references instead of hardcoded values in formulas
- Example: Use =B5*(1+$B$6) instead of =B5*1.05

#### Formula Error Prevention
- Verify all cell references are correct
- Check for off-by-one errors in ranges
- Ensure consistent formulas across all projection periods
- Test with edge cases (zero values, negative numbers)
- Verify no unintended circular references

#### Documentation Requirements for Hardcodes
- Comment or in cells beside (if end of table). Format: "Source: [System/Document], [Date], [Specific Reference], [URL if applicable]"
- Examples:
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of an .xlsx file. You have different tools and workflows available for different tasks.

## Important Requirements

**LibreOffice Required for Formula Recalculation**: You can assume LibreOffice is installed for recalculating formula values using the `recalc.py` script. The script automatically configures LibreOffice on first run

## Reading and analyzing data

### Data analysis with pandas
For data analysis, visualization, and basic operations, use **pandas** which provides powerful data manipulation capabilities:

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')  # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

## Excel File Workflows

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.** This ensures the spreadsheet remains dynamic and updateable.

###  WRONG - Hardcoding Calculated Values
```python
# Bad: Calculating in Python and hardcoding result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Bad: Computing growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Bad: Python calculation for average
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

###  CORRECT - Using Excel Formulas
```python
# Good: Let Excel calculate the sum
sheet['B10'] = '=SUM(B2:B9)'

# Good: Growth rate as Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Good: Average using Excel function
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to ALL calculations - totals, percentages, ratios, differences, etc. The spreadsheet should be able to recalculate when source data changes.

## Common Workflow
1. **Choose tool**: pandas for data, openpyxl for formulas/formatting
2. **Create/Load**: Create new workbook or load existing file
3. **Modify**: Add/edit data, formulas, and formatting
4. **Save**: Write to file
5. **Recalculate formulas (MANDATORY IF USING FORMULAS)**: Use the recalc.py script
   ```bash
   python recalc.py output.xlsx
   ```
6. **Verify and fix any errors**: 
   - The script returns JSON with error details
   - If `status` is `errors_found`, check `error_summary` for specific error types and locations
   - Fix the identified errors and recalculate again
   - Common errors to fix:
     - `#REF!`: Invalid cell references
     - `#DIV/0!`: Division by zero
     - `#VALUE!`: Wrong data type in formula
     - `#NAME?`: Unrecognized formula name

### Creating new Excel files

```python
# Using openpyxl for formulas and formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formula
sheet['B2'] = '=SUM(A1:A10)'

# Formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Editing existing Excel files

```python
# Using openpyxl to preserve formulas and formatting
from openpyxl import load_workbook

# Load existing file
wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName'] for specific sheet

# Working with multiple sheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # Insert row at position 2
sheet.delete_cols(3)  # Delete column 3

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## Recalculating formulas

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `recalc.py` script to recalculate formulas:

```bash
python recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
python recalc.py output.xlsx 30
```

The script:
- Automatically sets up LibreOffice macro on first run
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors (#REF!, #DIV/0!, etc.)
- Returns JSON with detailed error locations and counts
- Works on both Linux and macOS

## Formula Verification Checklist

Quick checks to ensure formulas work correctly:

### Essential Verification
- [ ] **Test 2-3 sample references**: Verify they pull correct values before building full model
- [ ] **Column mapping**: Confirm Excel columns match (e.g., column 64 = BL, not BK)
- [ ] **Row offset**: Remember Excel rows are 1-indexed (DataFrame row 5 = Excel row 6)

### Common Pitfalls
- [ ] **NaN handling**: Check for null values with `pd.notna()`
- [ ] **Far-right columns**: FY data often in columns 50+ 
- [ ] **Multiple matches**: Search all occurrences, not just first
- [ ] **Division by zero**: Check denominators before using `/` in formulas (#DIV/0!)
- [ ] **Wrong references**: Verify all cell references point to intended cells (#REF!)
- [ ] **Cross-sheet references**: Use correct format (Sheet1!A1) for linking sheets

### Formula Testing Strategy
- [ ] **Start small**: Test formulas on 2-3 cells before applying broadly
- [ ] **Verify dependencies**: Check all cells referenced in formulas exist
- [ ] **Test edge cases**: Include zero, negative, and very large values

### Interpreting recalc.py Output
The script returns JSON with error details:
```json
{
  "status": "success",           // or "errors_found"
  "total_errors": 0,              // Total error count
  "total_formulas": 42,           // Number of formulas in file
  "error_summary": {              // Only present if errors found
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## Best Practices

### Library Selection
- **pandas**: Best for data analysis, bulk operations, and simple data export
- **openpyxl**: Best for complex formatting, formulas, and Excel-specific features

### Working with openpyxl
- Cell indices are 1-based (row=1, column=1 refers to cell A1)
- Use `data_only=True` to read calculated values: `load_workbook('file.xlsx', data_only=True)`
- **Warning**: If opened with `data_only=True` and saved, formulas are replaced with values and permanently lost
- For large files: Use `read_only=True` for reading or `write_only=True` for writing
- Formulas are preserved but not evaluated - use recalc.py to update values

### Working with pandas
- Specify data types to avoid inference issues: `pd.read_excel('file.xlsx', dtype={'id': str})`
- For large files, read specific columns: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- Handle dates properly: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`

## Code Style Guidelines
**IMPORTANT**: When generating Python code for Excel operations:
- Write minimal, concise Python code without unnecessary comments
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

**For Excel files themselves**:
- Add comments to cells with complex formulas or important assumptions
- Document data sources for hardcoded values
- Include notes for key calculations and model sections

---

## 相關 Skills

### 協作 Skills
- `system-designer` - 資料表設計與欄位對照表

### 後續 Skills
- `memory-bank` - 記錄試算表操作問題