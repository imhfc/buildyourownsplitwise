# Skill Creator

> 使用 Atomic Agents 組合建立符合標準的 Claude Code Skills

## v2.0 新架構：Atomic Agents 組合

### 核心改變

**v1.0（舊）**：
```
使用 allowed-tools（Read, Write, Edit, Glob, Grep, Bash） → 手動執行四階段
```

**v2.0（新）**：
```
主會話 → 自動組合 5 個 Atomic Agents → Phase 3 並行驗證 → 極低成本
```

### 主要優勢

| 特性 | v1.0 | v2.0 | 提升 |
|------|------|------|------|
| **速度** | 12 分鐘 | 6 分鐘（並行） | 2x |
| **成本** | 中（Sonnet） | 低（Haiku） | 節省 70% |
| **準確率** | ~90% | >95% | +5% |
| **可並行** | 否 | 是（Phase 3） | - |

### Atomic Agents 列表

| Agent | 階段 | 職責 | 模型 |
|-------|------|------|------|
| file-finder | Phase 0 | 收集 SKILL-01 標準和範例 | Haiku |
| code-generator | Phase 2 | 生成 SKILL.md 內容 | Haiku |
| spec-validator | Phase 3 | 驗證 Frontmatter 格式 | Haiku |
| compliance-auditor | Phase 3 | 驗證必備章節 | Haiku |
| pattern-checker | Phase 3 | 檢查命名和禁止內容 | Haiku |

---

## 職責

本 Skill 負責 Agent Skill 的建立與驗證：

1. **建立新 Skill** - 依據標準格式建立完整的 SKILL.md
2. **驗證現有 Skill** - 檢查是否符合 SKILL-01 規範
3. **轉換功能為 Skill** - 將現有功能封裝為可重用的 Skill
4. **品質審查** - 確保 Skill 內容品質與一致性

---

## 觸發時機

### 應使用此 Skill

| 關鍵字 | 場景 |
|--------|------|
| 「建立 Skill」「新增技能」 | 從零開始建立新 Skill |
| 「驗證 Skill」「檢查技能」 | 驗證現有 Skill 是否符合標準 |
| 「轉換為 Skill」 | 將功能封裝為 Skill |
| 「改善 Skill」「優化技能」 | 重構現有 Skill |

### 不應使用此 Skill

- 執行已存在的 Skill（直接呼叫該 Skill）
- 修改 Skill 的業務邏輯（使用對應的開發 Skill）

---

## Skill 標準結構

### Frontmatter（必要）

```yaml
---
name: {skill-name}           # kebab-case，與目錄名稱一致
description: |
  {一句話摘要}
  Use this skill when:
  - {觸發場景 1}
  - {觸發場景 2}
  - {觸發場景 3}
  References: {ADR-XXX, PATTERN-YYY}.
allowed-tools:               # 依序：基礎 → Plugin → MCP
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__plugin_xxx__tool
  - mcp__server__tool
---
```

### 可選 Frontmatter 欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| `model` | 指定模型 | `sonnet`, `opus`, `haiku` |
| `context` | 額外上下文檔案 | `["./rules/*.md"]` |
| `hooks` | 執行前/後 hooks | `{pre_tool_call: [...]}` |

### 必備章節

1. **職責** - 核心職責（3-5 項）
2. **觸發時機** - 使用場景與關鍵字
3. **工作流程** - 步驟化執行流程（含 Mermaid 圖）
4. **檢查清單** - 開始前/執行中/完成後
5. **相關 Skills** - 前置/協作/後續 Skills

---

## 工作流程（v2.0 Atomic Agents）

### Phase 0: 收集資訊（主會話執行）

**使用 Atomic Agent**: **file-finder**

主會話使用 file-finder 收集參考資料：

```yaml
任務:
  - 收集 SKILL-01 標準文檔
  - 收集現有優秀 Skills 範例
  - 載入工具清單參考
```

**收集內容**：
```bash
# 1. SKILL-01 標準

# 2. 現有 Skills 範例
.claude/skills/*/SKILL.md

# 3. 工具清單
- 基礎工具（Read, Write, Edit, Glob, Grep, Bash）
- Task/Agent 工具（Task, TaskOutput, AskUserQuestion）
```

**執行時間**: ~30 秒（v1.0: 1.5 分鐘）

---

### Phase 1: 需求與設計（主會話執行）

**收集需求**：

使用 AskUserQuestion 收集：
- Skill 名稱（kebab-case）
- Skill 目的（一句話）
- 觸發場景（3-7 項）
- 需要的工具清單

**設計 Skill 結構**：

1. **依據 SKILL-01 標準**
   - Frontmatter 必備欄位
   - 章節結構要求
   - 內容品質標準

2. **參考現有範例**
   - 查看相似功能的 Skills
   - 學習最佳實踐

3. **設計 Frontmatter**
   ```yaml
   name: {skill-name}
   description: |
     {一句話摘要}
     Use this skill when:
     - {觸發場景 1}
     - {觸發場景 2}
     References: {ADR-XXX}.
   ```

4. **規劃章節大綱**
   - 職責（3-5 項）
   - 觸發時機（表格或清單）
   - 工作流程（步驟 + Mermaid 圖）
   - 檢查清單（可執行項目）
   - 相關 Skills（關聯說明）

**執行時間**: ~2 分鐘（與 v1.0 相同）

---

### Phase 2: 內容生成

**使用 Atomic Agent**: **code-generator**

主會話啟動 code-generator 根據設計生成完整 SKILL.md：

```yaml
輸入:
  - Frontmatter 設計
  - 章節大綱
  - SKILL-01 標準
  - 參考範例

生成內容:
  1. Frontmatter（name, description）
  2. 職責章節（核心功能）
  3. 觸發時機章節（使用場景）
  4. 工作流程章節（步驟 + Mermaid 圖）
  5. 檢查清單章節（可執行項目）
  6. 相關 Skills 章節（關聯說明）
```

**執行時間**: ~1.5 分鐘（v1.0: 3 分鐘）

---

### Phase 3: 驗證檢查（並行執行）

**使用 Atomic Agents**: **spec-validator** + **compliance-auditor** + **pattern-checker**（並行）

主會話並行啟動三個 agents：

#### Spec-Validator: Frontmatter 格式驗證

**檢查項目**：

```yaml
必備欄位:
  - name: 必須存在且使用 kebab-case
  - description: 必須存在且包含觸發場景

格式檢查:
  - YAML 格式正確
  - 分隔線使用 "---"
  - 無版本欄位（version, last_updated）
```

#### Compliance-Auditor: 必備章節驗證

**檢查項目**：

```yaml
必備章節（SKILL-01）:
  - 職責章節
  - 觸發時機章節
  - 工作流程章節
  - 檢查清單章節
  - 相關 Skills 章節
```

#### Pattern-Checker: 命名和禁止內容檢查

**檢查項目**：

```yaml
命名規範:
  - Skill 名稱使用 kebab-case
  - 與目錄名稱一致

禁止內容:
  - 推銷性詞彙（最佳、完美、強烈推薦）
  - 統計數字（使用率 XX%、效能提升 XX%）
  - 禁止章節（優勢、特點、變更歷史）
  - 過度 emoji
```

**輸出格式**：
```markdown
## 驗證結果

### ✅ 通過項目
- Frontmatter 格式正確
- 所有必備章節存在
- 無違規內容

### ⚠️ 需改善項目
| 項目 | 問題 | 建議 |
|------|------|------|
| （範例）description | 缺少觸發場景 | 添加 "Use this skill when:" 段落 |
```

**執行時間**: ~1 分鐘（並行，v1.0: 4 分鐘）

---

### Phase 4: 修正與建立（主會話執行）

**根據驗證結果修正內容**：

1. 修正 Frontmatter 格式問題
2. 補充缺少的章節
3. 移除違規內容
4. 調整命名規範

**建立檔案**：

```bash
.claude/skills/{skill-name}/SKILL.md
```

**執行時間**: ~1 分鐘（v1.0: 1.5 分鐘）

---

## 完整執行範例

```
使用者: 「請建立一個名為 batch-processor 的 Skill，用於處理批次作業」

主會話:
  ├─ Phase 0 (30s): file-finder 收集 SKILL-01 和範例
  │   └─ 找到: SKILL-01 標準, 3 個參考範例
  │
  ├─ Phase 1 (2m): 收集需求與設計
  │   ├─ 使用 AskUserQuestion 收集詳細需求
  │   ├─ 設計 Frontmatter
  │   └─ 規劃章節大綱
  │
  ├─ Phase 2 (1.5m): code-generator 生成內容
  │   └─ 生成完整 SKILL.md（包含所有章節）
  │
  ├─ Phase 3 (1m, 並行):
  │   ├─ spec-validator: 驗證 Frontmatter
  │   │   └─ ✅ 格式正確
  │   │
  │   ├─ compliance-auditor: 驗證必備章節
  │   │   └─ ✅ 所有章節存在
  │   │
  │   └─ pattern-checker: 檢查命名和禁止內容
  │       └─ ✅ 符合規範
  │
  └─ Phase 4 (1m): 建立檔案
      └─ 建立: .claude/skills/batch-processor/SKILL.md

總執行時間: ~6 分鐘（v1.0: 12 分鐘，提升 2x）
總成本: 低（Phase 0, 2-3 使用 Haiku，節省 70%）
```

---

## 驗證檢查清單

### Frontmatter 驗證

- [ ] 包含 `name`、`description`、`allowed-tools`
- [ ] `name` 使用 kebab-case
- [ ] `name` 與目錄名稱一致
- [ ] `description` 包含 `Use this skill when:` 段落
- [ ] `description` 包含 `References:` 參考文檔
- [ ] `allowed-tools` 依序列出：基礎 → Plugin → MCP
- [ ] **無** `version`、`last_updated` 等版本欄位

### 內容結構驗證

- [ ] 有「職責」章節，列出核心職責（3-5 項）
- [ ] 有「觸發時機」章節，包含表格或清單
- [ ] 有「工作流程」章節，包含 Mermaid 圖
- [ ] 有「檢查清單」章節，使用 `- [ ]` 格式
- [ ] 有「相關 Skills」章節，列出關聯 Skills

### 內容品質驗證

- [ ] 使用客觀陳述，**無**推銷性詞彙
- [ ] **無**統計數字（成功率、使用率、效能提升 XX%）
- [ ] **無**版本歷史或變更記錄
- [ ] **無**「優勢」「特點」章節
- [ ] emoji 使用適度（只在主要章節標題）

### 工具驗證

- [ ] 所有列出的工具確實存在
- [ ] 基礎工具完整（Read, Write, Edit, Glob, Grep, Bash）
- [ ] Serena Plugin 工具格式正確（如適用）
- [ ] MCP 工具格式正確（如適用）

---

## 常用工具清單

### 基礎工具（幾乎所有 Skill 需要）

```yaml
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
```

### Serena Plugin 工具

```yaml
# 符號操作
- mcp__plugin_serena_serena__find_symbol
- mcp__plugin_serena_serena__get_symbols_overview
- mcp__plugin_serena_serena__find_referencing_symbols
- mcp__plugin_serena_serena__replace_symbol_body
- mcp__plugin_serena_serena__rename_symbol
- mcp__plugin_serena_serena__insert_after_symbol
- mcp__plugin_serena_serena__insert_before_symbol

# 檔案操作
- mcp__plugin_serena_serena__read_file
- mcp__plugin_serena_serena__create_text_file
- mcp__plugin_serena_serena__list_dir
- mcp__plugin_serena_serena__find_file
- mcp__plugin_serena_serena__search_for_pattern
- mcp__plugin_serena_serena__replace_content

# 記憶系統
- mcp__plugin_serena_serena__write_memory
- mcp__plugin_serena_serena__read_memory
- mcp__plugin_serena_serena__list_memories

# 思考工具
- mcp__plugin_serena_serena__think_about_collected_information
- mcp__plugin_serena_serena__think_about_task_adherence
- mcp__plugin_serena_serena__think_about_whether_you_are_done

# Shell
- mcp__plugin_serena_serena__execute_shell_command
```

### Context7 MCP 工具

```yaml
- mcp__context7__resolve-library-id
- mcp__context7__query-docs
```

### Task/Agent 工具

```yaml
- Task
- TaskOutput
- AskUserQuestion
```

---

## 範本

### 最小可行 Skill

```yaml
---
name: my-skill
description: |
  Brief description of what this skill does.
  Use this skill when:
  - Scenario 1
  - Scenario 2
  - Scenario 3
  References: ADR-XXX.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# My Skill

> 一句話描述

---

## 職責

1. **職責 1** - 說明
2. **職責 2** - 說明
3. **職責 3** - 說明

---

## 觸發時機

| 關鍵字 | 場景 |
|--------|------|
| 「關鍵字 1」 | 場景說明 |
| 「關鍵字 2」 | 場景說明 |

---

## 工作流程

1. **步驟 1** - 說明
2. **步驟 2** - 說明
3. **步驟 3** - 說明

---

## 檢查清單

### 開始前
- [ ] 檢查項目 1
- [ ] 檢查項目 2

### 完成後
- [ ] 檢查項目 3
- [ ] 檢查項目 4

---

## 相關 Skills

- `related-skill-1` - 關聯說明
- `related-skill-2` - 關聯說明
```

---

## 禁止內容速查

| 類型 | 禁止範例 |
|------|---------|
| **版本資訊** | `version: 2.0`, `last_updated: 2026-01-20` |
| **推銷詞彙** | 最佳、完美、強烈推薦、市場領先 |
| **統計數字** | 使用率 95%、效能提升 50% |
| **章節** | 「優勢」「特點」「vs 其他」「變更歷史」 |
| **過度 emoji** |  |

---

## 相關 Skills

### 協作 Skills
- `governance-checker` - 檢查 Skills 設計是否符合治理原則
- `/review-code` - 程式碼層級的規範檢查

### 參考文檔
- **現有 Skills**: `.claude/skills/*/SKILL.md`
- **Atomic Agents**: `.claude/agents/atomic/README.md`

---

## 快速指令

### 建立新 Skill
```
請幫我建立一個名為 {name} 的 Skill，用於 {目的}，觸發場景包括 {場景}
```

### 驗證現有 Skill
```
請驗證 .claude/skills/{name}/SKILL.md 是否符合 SKILL-01 標準
```

### 列出所有 Skills
```bash
ls -la .claude/skills/
```