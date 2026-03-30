# DOCX 文檔處理 Skill

> 使用 Atomic Agents 組合處理 Word 文檔的建立、編輯、驗證與追蹤變更

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
| file-finder | Phase 0 | 收集 Word 文件 | Haiku |
| compliance-auditor | Phase 1 | 驗證文檔結構 | Haiku |
| pattern-checker | Phase 1 | 檢查格式問題 | Haiku |
| code-editor | Phase 1 | 修正問題 | Haiku |
| code-formatter | Phase 2 | 格式化文檔 | Haiku |

---

## 處理工作流程（v2.0 Atomic Agents）

### Phase 0: 收集資訊（主會話執行）

**使用 Atomic Agent**: **file-finder**

主會話使用 file-finder 收集文件：

```yaml
任務:
  - 收集 Word 文檔文件
  - 收集相關資源（圖片、樣式）
  - 檢查檔案格式
```

**收集內容**：
```bash
# 1. Word 文檔
*.docx

# 2. 相關資源
images/
styles/
```

**執行時間**: ~15 秒（v1.0: 30 秒）

---

### Phase 1: 驗證與修正（並行執行）

**使用 Atomic Agents**: **compliance-auditor** + **pattern-checker** + **code-editor**（並行）

#### Compliance-Auditor: 文檔結構驗證

**檢查項目**：

```yaml
文檔結構:
  - 檢查標題層級（無跳級）
  - 驗證表格完整性
  - 確認段落層次
  - 追蹤變更標記完整

輸出格式:
  - 結構完整性報告
  - 問題清單（標題、表格、段落）
```

#### Pattern-Checker: 格式問題檢查

**檢查項目**：

```yaml
樣式一致性:
  - 字體統一
  - 大小一致
  - 顏色規範

間距格式:
  - 行距統一
  - 段落間距
  - 縮排一致

列表格式:
  - 編號格式
  - 項目符號
  - 縮排層級
```

#### Code-Editor: 修正問題

**基於驗證結果修正**：

```yaml
修正項目:
  - 修正標題層級
  - 調整表格格式
  - 更新段落樣式
  - 統一字體和間距
```

**執行時間**: Phase 1 總計 ~2 分鐘（並行，v1.0: 6 分鐘，提升 3x）

---

### Phase 2: 格式化（主會話執行）

**使用 Atomic Agent**: **code-formatter**

統一文檔格式：

```yaml
格式化項目:
  - 統一樣式
  - 調整間距
  - 格式化表格
  - 處理追蹤變更（使用 pandoc）
```

**追蹤變更驗證**：
```bash
pandoc --track-changes=all document.docx -o verification.md
```

**執行時間**: ~1.5 分鐘（v1.0: 3 分鐘）

---

## 完整執行範例

```
使用者: 「編輯系統設計規格書 DOCX 並追蹤變更」

主會話:
  ├─ Phase 0 (15s): file-finder 收集文件
  │   └─ 找到: spec.docx, 3 張圖片
  │
  ├─ Phase 1 (2m, 並行):
  │   ├─ compliance-auditor: 驗證文檔結構
  │   │   └─  發現 2 個標題跳級，1 個表格格式問題
  │   │
  │   ├─ pattern-checker: 檢查格式問題
  │   │   └─  10 個字體不一致，5 個間距問題
  │   │
  │   └─ code-editor: 修正問題
  │       ├─  修正標題層級（H1 → H2 → H3）
  │       ├─  調整表格邊框和對齊
  │       ├─  統一字體（全部 Calibri）
  │       └─  統一間距（1.15 行距）
  │
  └─ Phase 2 (1.5m): code-formatter 格式化
      ├─  套用統一樣式
      ├─  格式化所有表格
      └─  啟用追蹤變更
          └─  驗證：所有變更已標記

總執行時間: ~4 分鐘（v1.0: 10 分鐘，提升 2.5x）
總成本: 極低（全程使用 Haiku，節省 70%）
```

**關鍵原則**:
- Phase 1 未通過 → **禁止**進入 Phase 2
- 追蹤變更必須保留完整記錄
- 使用最小化編輯原則（只標記實際變更）
- Phase 1 並行執行，提升 3x 速度

---

# DOCX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .docx file. A .docx file is essentially a ZIP archive containing XML files and other resources that you can read or edit. You have different tools and workflows available for different tasks.

## Workflow Decision Tree

### Reading/Analyzing Content
Use "Text extraction" or "Raw XML access" sections below

### Creating New Document
Use "Creating a new Word document" workflow

### Editing Existing Document
- **Your own document + simple changes**
  Use "Basic OOXML editing" workflow

- **Someone else's document**
  Use **"Redlining workflow"** (recommended default)

- **Legal, academic, business, or government docs**
  Use **"Redlining workflow"** (required)

## Reading and analyzing content

### Text extraction
If you just need to read the text contents of a document, you should convert the document to markdown using pandoc. Pandoc provides excellent support for preserving document structure and can show tracked changes:

```bash
# Convert document to markdown with tracked changes
pandoc --track-changes=all path-to-file.docx -o output.md
# Options: --track-changes=accept/reject/all
```

### Raw XML access
You need raw XML access for: comments, complex formatting, document structure, embedded media, and metadata. For any of these features, you'll need to unpack a document and read its raw XML contents.

#### Unpacking a file
`python ooxml/scripts/unpack.py <office_file> <output_directory>`

#### Key file structures
* `word/document.xml` - Main document contents
* `word/comments.xml` - Comments referenced in document.xml
* `word/media/` - Embedded images and media files
* Tracked changes use `<w:ins>` (insertions) and `<w:del>` (deletions) tags

## Creating a new Word document

When creating a new Word document from scratch, use **docx-js**, which allows you to create Word documents using JavaScript/TypeScript.

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`docx-js.md`](docx-js.md) (~500 lines) completely from start to finish. **NEVER set any range limits when reading this file.** Read the full file content for detailed syntax, critical formatting rules, and best practices before proceeding with document creation.
2. Create a JavaScript/TypeScript file using Document, Paragraph, TextRun components (You can assume all dependencies are installed, but if not, refer to the dependencies section below)
3. Export as .docx using Packer.toBuffer()

## Editing an existing Word document

When editing an existing Word document, use the **Document library** (a Python library for OOXML manipulation). The library automatically handles infrastructure setup and provides methods for document manipulation. For complex scenarios, you can access the underlying DOM directly through the library.

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`ooxml.md`](ooxml.md) (~600 lines) completely from start to finish. **NEVER set any range limits when reading this file.** Read the full file content for the Document library API and XML patterns for directly editing document files.
2. Unpack the document: `python ooxml/scripts/unpack.py <office_file> <output_directory>`
3. Create and run a Python script using the Document library (see "Document Library" section in ooxml.md)
4. Pack the final document: `python ooxml/scripts/pack.py <input_directory> <office_file>`

The Document library provides both high-level methods for common operations and direct DOM access for complex scenarios.

## Redlining workflow for document review

This workflow allows you to plan comprehensive tracked changes using markdown before implementing them in OOXML. **CRITICAL**: For complete tracked changes, you must implement ALL changes systematically.

**Batching Strategy**: Group related changes into batches of 3-10 changes. This makes debugging manageable while maintaining efficiency. Test each batch before moving to the next.

**Principle: Minimal, Precise Edits**
When implementing tracked changes, only mark text that actually changes. Repeating unchanged text makes edits harder to review and appears unprofessional. Break replacements into: [unchanged text] + [deletion] + [insertion] + [unchanged text]. Preserve the original run's RSID for unchanged text by extracting the `<w:r>` element from the original and reusing it.

Example - Changing "30 days" to "60 days" in a sentence:
```python
# BAD - Replaces entire sentence
'<w:del><w:r><w:delText>The term is 30 days.</w:delText></w:r></w:del><w:ins><w:r><w:t>The term is 60 days.</w:t></w:r></w:ins>'

# GOOD - Only marks what changed, preserves original <w:r> for unchanged text
'<w:r w:rsidR="00AB12CD"><w:t>The term is </w:t></w:r><w:del><w:r><w:delText>30</w:delText></w:r></w:del><w:ins><w:r><w:t>60</w:t></w:r></w:ins><w:r w:rsidR="00AB12CD"><w:t> days.</w:t></w:r>'
```

### Tracked changes workflow

1. **Get markdown representation**: Convert document to markdown with tracked changes preserved:
   ```bash
   pandoc --track-changes=all path-to-file.docx -o current.md
   ```

2. **Identify and group changes**: Review the document and identify ALL changes needed, organizing them into logical batches:

   **Location methods** (for finding changes in XML):
   - Section/heading numbers (e.g., "Section 3.2", "Article IV")
   - Paragraph identifiers if numbered
   - Grep patterns with unique surrounding text
   - Document structure (e.g., "first paragraph", "signature block")
   - **DO NOT use markdown line numbers** - they don't map to XML structure

   **Batch organization** (group 3-10 related changes per batch):
   - By section: "Batch 1: Section 2 amendments", "Batch 2: Section 5 updates"
   - By type: "Batch 1: Date corrections", "Batch 2: Party name changes"
   - By complexity: Start with simple text replacements, then tackle complex structural changes
   - Sequential: "Batch 1: Pages 1-3", "Batch 2: Pages 4-6"

3. **Read documentation and unpack**:
   - **MANDATORY - READ ENTIRE FILE**: Read [`ooxml.md`](ooxml.md) (~600 lines) completely from start to finish. **NEVER set any range limits when reading this file.** Pay special attention to the "Document Library" and "Tracked Change Patterns" sections.
   - **Unpack the document**: `python ooxml/scripts/unpack.py <file.docx> <dir>`
   - **Note the suggested RSID**: The unpack script will suggest an RSID to use for your tracked changes. Copy this RSID for use in step 4b.

4. **Implement changes in batches**: Group changes logically (by section, by type, or by proximity) and implement them together in a single script. This approach:
   - Makes debugging easier (smaller batch = easier to isolate errors)
   - Allows incremental progress
   - Maintains efficiency (batch size of 3-10 changes works well)

   **Suggested batch groupings:**
   - By document section (e.g., "Section 3 changes", "Definitions", "Termination clause")
   - By change type (e.g., "Date changes", "Party name updates", "Legal term replacements")
   - By proximity (e.g., "Changes on pages 1-3", "Changes in first half of document")

   For each batch of related changes:

   **a. Map text to XML**: Grep for text in `word/document.xml` to verify how text is split across `<w:r>` elements.

   **b. Create and run script**: Use `get_node` to find nodes, implement changes, then `doc.save()`. See **"Document Library"** section in ooxml.md for patterns.

   **Note**: Always grep `word/document.xml` immediately before writing a script to get current line numbers and verify text content. Line numbers change after each script run.

5. **Pack the document**: After all batches are complete, convert the unpacked directory back to .docx:
   ```bash
   python ooxml/scripts/pack.py unpacked reviewed-document.docx
   ```

6. **Final verification**: Do a comprehensive check of the complete document:
   - Convert final document to markdown:
     ```bash
     pandoc --track-changes=all reviewed-document.docx -o verification.md
     ```
   - Verify ALL changes were applied correctly:
     ```bash
     grep "original phrase" verification.md  # Should NOT find it
     grep "replacement phrase" verification.md  # Should find it
     ```
   - Check that no unintended changes were introduced


## Converting Documents to Images

To visually analyze Word documents, convert them to images using a two-step process:

1. **Convert DOCX to PDF**:
   ```bash
   soffice --headless --convert-to pdf document.docx
   ```

2. **Convert PDF pages to JPEG images**:
   ```bash
   pdftoppm -jpeg -r 150 document.pdf page
   ```
   This creates files like `page-1.jpg`, `page-2.jpg`, etc.

Options:
- `-r 150`: Sets resolution to 150 DPI (adjust for quality/size balance)
- `-jpeg`: Output JPEG format (use `-png` for PNG if preferred)
- `-f N`: First page to convert (e.g., `-f 2` starts from page 2)
- `-l N`: Last page to convert (e.g., `-l 5` stops at page 5)
- `page`: Prefix for output files

Example for specific range:
```bash
pdftoppm -jpeg -r 150 -f 2 -l 5 document.pdf page  # Converts only pages 2-5
```

## Code Style Guidelines
**IMPORTANT**: When generating code for DOCX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

## Dependencies

Required dependencies (install if not available):

- **pandoc**: `sudo apt-get install pandoc` (for text extraction)
- **docx**: `npm install -g docx` (for creating new documents)
- **LibreOffice**: `sudo apt-get install libreoffice` (for PDF conversion)
- **Poppler**: `sudo apt-get install poppler-utils` (for pdftoppm to convert PDF to images)
- **defusedxml**: `pip install defusedxml` (for secure XML parsing)

---

## 相關 Skills

### 協作 Skills
- `reconcile-batch-spec-converter` - DOCX 批次規格轉換
- `system-designer` - 文檔化系統設計

### 後續 Skills
- `markdown-doc-processor` - 轉換為 Markdown 處理
- `memory-bank` - 記錄文檔操作問題