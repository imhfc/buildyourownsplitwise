# Atomic Agents 實作指南

> 基於單一職責原則（SRP）的細分 Agent 架構

---

## 概覽

本目錄包含所有 **Atomic Agents**（原子級 Agents）的定義，每個 Agent 只負責一件事。

**所有 Atomic Agents 使用 `haiku` 模型**，提供快速響應和經濟效益。

---

## 已實作的 Agents

### COORDINATOR 類

- [task-router](./coordinator/task-router/README.md) - 智能任務路由：分析任務類型和複雜度，推薦最佳執行策略
- [parallel-coordinator](./coordinator/parallel-coordinator.md) - 並行開發任務規劃與協調
- [review-coordinator](./coordinator/review-coordinator.md) - 代碼審查任務規劃與協調

### SEARCH 類

- [file-finder](./search/file-finder.md) - 根據條件查找文件
- [code-searcher](./search/code-searcher.md) - 在代碼中搜索特定內容（使用 ast-grep）
- [symbol-locator](./search/symbol-locator.md) - 定位代碼符號（類、函數）
- [dependency-tracer](./search/dependency-tracer.md) - 追蹤依賴關係

### CODE 類

- [code-generator](./code/code-generator.md) - 生成全新的代碼
- [code-editor](./code/code-editor.md) - 編輯現有代碼
- [code-deleter](./code/code-deleter.md) - 刪除不需要的代碼
- [code-formatter](./code/code-formatter.md) - 格式化代碼

### REFACTOR 類

- [code-simplifier](./refactor/code-simplifier.md) - 簡化複雜代碼
- [duplicate-remover](./refactor/duplicate-remover.md) - 移除重複代碼
- [performance-tuner](./refactor/performance-tuner.md) - 優化性能
- [naming-improver](./refactor/naming-improver.md) - 改善命名

### DATA 類

- [schema-designer](./data/schema-designer.md) - 設計資料庫 schema
- [query-writer](./data/query-writer.md) - 撰寫 SQL 查詢
- [migration-generator](./data/migration-generator.md) - 生成資料庫遷移
- [data-validator](./data/data-validator.md) - 驗證數據正確性

### TEST 類

- [test-writer](./test/test-writer.md) - 撰寫測試代碼
- [test-runner](./test/test-runner.md) - 執行測試
- [coverage-analyzer](./test/coverage-analyzer.md) - 分析測試覆蓋率
- [test-fixer](./test/test-fixer.md) - 修復失敗的測試

### REVIEW 類

- [code-reviewer](./review/code-reviewer.md) - 審查代碼品質
- [security-scanner](./review/security-scanner.md) - 掃描安全問題
- [pattern-checker](./review/pattern-checker.md) - 檢查設計模式
- [hexagonal-architecture-compliance-auditor](./review/hexagonal-architecture-compliance-auditor.md) - 審計六角形架構合規（Ports and Adapters）
- [compliance-auditor](./review/compliance-auditor.md) - 審計通用合規（許可證、GDPR、代碼品質）
- [spec-validator](./review/spec-validator.md) - 驗證規格符合度
- [test-validator](./review/test-validator.md) - 驗證測試規範（BDD、命名、覆蓋率）
- [doc-validator](./review/doc-validator.md) - 驗證文檔規範（ADR、Pattern、Markdown）

### DESIGN 類

- [api-designer](./design/api-designer.md) - 設計 API 介面
- [architecture-planner](./design/architecture-planner.md) - 規劃系統架構
- [interface-designer](./design/interface-designer.md) - 設計介面定義
- [workflow-designer](./design/workflow-designer.md) - 設計業務流程

### CONFIG 類

- [env-manager](./config/env-manager.md) - 管理環境變數
- [property-editor](./config/property-editor.md) - 編輯屬性配置文件
- [docker-configurator](./config/docker-configurator.md) - 配置 Docker
- [ci-configurator](./config/ci-configurator.md) - 配置 CI/CD

### LOG-ANALYSIS 類

- [log-analysis-coordinator](./log-analysis/log-analysis-coordinator.md) - 日誌分析協調
- [error-pattern-analyzer](./log-analysis/error-pattern-analyzer.md) - 錯誤模式分析
- [exception-tracer](./log-analysis/exception-tracer.md) - 例外追蹤
- [markdown-report-generator](./log-analysis/markdown-report-generator.md) - Markdown 報告產生
- [report-consolidator](./log-analysis/report-consolidator.md) - 報告整合

### 其他

- [plan-reviewer](./coordinator/plan-reviewer.md) - 計畫審查（以資深工程師角度審查計畫）

---

## 實作優先順序

### Phase 1：核心功能（100% - 完成）

- [x] file-finder
- [x] code-searcher（v2.0 - 使用 ast-grep）
- [x] code-generator
- [x] code-editor
- [x] test-writer
- [x] test-runner

### Phase 2：開發流程完整（100% - 完成）

- [x] symbol-locator
- [x] code-deleter
- [x] code-formatter
- [x] code-reviewer
- [x] api-designer
- [x] schema-designer

### Phase 3：進階功能（100% - 完成）

- [x] code-simplifier
- [x] duplicate-remover
- [x] naming-improver
- [x] query-writer
- [x] migration-generator
- [x] coverage-analyzer
- [x] test-fixer
- [x] security-scanner
- [x] pattern-checker
- [x] architecture-planner
- [x] interface-designer
- [x] env-manager
- [x] property-editor

### Phase 4：專業功能（100% - 完成）

- [x] dependency-tracer
- [x] performance-tuner
- [x] data-validator
- [x] compliance-auditor
- [x] workflow-designer
- [x] docker-configurator
- [x] ci-configurator

### Phase 5：審查專業化（100% - 完成）

- [x] test-validator - 測試規範驗證
- [x] doc-validator - 文檔規範驗證
- [x] review-coordinator - 審查任務協調（已移除 Serena MCP，全面使用 AST-GREP）

### Phase 6：通用化（100% - 完成）

- [x] log-analysis-coordinator - 日誌分析協調
- [x] error-pattern-analyzer - 錯誤模式分析
- [x] exception-tracer - 例外追蹤
- [x] markdown-report-generator - Markdown 報告產生
- [x] report-consolidator - 報告整合

---

## 模型配置

### 為何選擇 Haiku？

所有 Atomic Agents 統一使用 **haiku 模型**：

**優勢**：
- **快速響應**：Haiku 比 Sonnet 快 2-3 倍
- **經濟實惠**：成本降低 80%
- **足夠能力**：單一職責任務不需要複雜推理
- **可組合**：多個快速 Agents 組合完成複雜任務

**Frontmatter 格式**：
```yaml
---
name: agent-name
model: haiku  # 所有 Atomic Agents 使用 haiku
tools: Tool1, Tool2
description: |
  簡短描述
  優先使用 ast-grep 進行代碼結構搜索（LL-001）  # 代碼相關 agents
context:
---
```

**何時使用更強模型**：
- 複雜架構設計 → architect (sonnet)
- 多步驟規劃 → orchestrator (sonnet)
- 高層決策 → 主會話 (sonnet)

---

## 配置優化（2026-01-27）

### 統一規範載入

所有代碼相關 Atomic Agents 現在統一載入核心規範：

**必須載入** (13 個 agents)：
- `CODE-SEARCH-BEST-PRACTICES.md` - AST-GREP 優先策略（LL-001）
  - SEARCH：file-finder
  - CODE：code-generator, code-editor, code-deleter, code-formatter
  - REFACTOR：code-simplifier, duplicate-remover, naming-improver, performance-tuner
  - TEST：test-writer, test-fixer
  - DESIGN：api-designer, interface-designer

**代碼生成 agents** (4 個)：
- `ADR-003` 六層架構規範
  - code-generator, code-editor, code-simplifier, test-writer

### 移除重複配置

已修復 11 個 agents 的重複 context 配置：
- ✅ 每個規範文件只載入一次
- ✅ Context 配置標準化
- ✅ 所有 description 統一格式

### 審查工具

新增自動化審查腳本（位於 `.claude/agents/scripts/`）：

```bash
# 審查所有 agents 配置
./claude/scripts/audit-atomic-agents.sh

# 檢查項目：
# 1. 重複的 context 配置
# 2. 缺少 CODE-SEARCH-BEST-PRACTICES.md
# 3. 缺少 ADR-003 架構規範
```

---

## 組合策略

單個 Atomic Agent 只完成一個小任務，但透過組合可以完成複雜工作。

**詳細說明**：參考 [組合策略文檔](./COMPOSITION-STRATEGY.md)

**快速範例**：

### 簡單修改流程
```bash
file-finder → code-editor → test-runner
```

### 完整開發流程
```bash
api-designer → schema-designer →
code-generator → code-editor →
test-writer → test-runner →
code-reviewer
```

### 品質保證流程
```bash
code-reviewer → security-scanner →
pattern-checker → compliance-auditor →
test-runner → coverage-analyzer
```

---

## 如何實作新的 Atomic Agent

### 1. 建立定義文件

在 `.claude/agents/atomic/` 建立 `{agent-name}.md`：

```markdown
---
name: agent-name
model: haiku  # 必須使用 haiku
tools: Tool1, Tool2
description: 一句話描述
---

# Agent Name

> 單一職責：明確的職責描述

## 職責範圍

###  只負責
- 職責 1
- 職責 2

###  不負責
- 不做的事 1
- 不做的事 2

## 工具限制

- **Tool1**: 用途
- **Tool2**: 用途

[其餘章節...]
```

### 2. 定義職責邊界

明確定義：
- 這個 Agent **只做**什麼
- 這個 Agent **不做**什麼
- 與哪些 Agents 配合

### 3. 限制可用工具

根據職責選擇最少的工具：

| 職責類型 | 可用工具 |
|---------|---------|
| 只讀（搜索） | Read, Glob, Grep, Bash |
| 只寫（生成） | Write, Bash |
| 編輯 | Read, Edit, Bash |
| 執行 | Bash |

### 4. 編寫使用場景

提供 3-5 個具體的使用場景

### 5. 定義輸出格式

統一的輸出格式，方便組合

### 6. 測試

驗證 Agent 能正確執行單一職責

---

## 命名慣例

### 格式

```
{動詞}-{對象}
```

### 範例

- file-finder （找 file）
- code-searcher （搜 code）
- schema-designer （設計 schema）
- test-runner （運行 test）

### 動詞選擇

| 動詞 | 用途 | 範例 |
|------|-----|------|
| finder | 查找 | file-finder |
| searcher | 搜索 | code-searcher |
| locator | 定位 | symbol-locator |
| tracer | 追蹤 | dependency-tracer |
| generator | 生成 | code-generator |
| editor | 編輯 | code-editor |
| deleter | 刪除 | code-deleter |
| formatter | 格式化 | code-formatter |
| simplifier | 簡化 | code-simplifier |
| remover | 移除 | duplicate-remover |
| tuner | 調整 | performance-tuner |
| improver | 改善 | naming-improver |
| designer | 設計 | api-designer |
| planner | 規劃 | architecture-planner |
| writer | 撰寫 | test-writer |
| runner | 執行 | test-runner |
| analyzer | 分析 | coverage-analyzer |
| fixer | 修復 | test-fixer |
| reviewer | 審查 | code-reviewer |
| scanner | 掃描 | security-scanner |
| checker | 檢查 | pattern-checker |
| auditor | 審計 | compliance-auditor |
| manager | 管理 | env-manager |
| configurator | 配置 | docker-configurator |
| validator | 驗證 | data-validator |

---

## 品質檢查清單

### 在提交新的 Agent 之前，確認：

- [ ] 職責是否單一且明確？
- [ ] 與其他 Agents 是否有重疊？
- [ ] 工具是否限制到最少？
- [ ] 是否提供了使用場景？
- [ ] 是否定義了輸出格式？
- [ ] 是否說明了如何與其他 Agents 配合？
- [ ] frontmatter 是否正確？
  - name
  - **model: haiku** （必須）
  - tools
  - description

---

## 使用方式

### 方式 1：直接調用（手動）

```bash
# 主會話中直接啟動 agent
使用 file-finder 找出所有 Controller 文件
```

### 方式 2：透過智能任務路由（自動）

主會話會自動使用 task-router agent 分析任務並推薦最適合的執行策略：

```bash
# AI 自動分析任務類型和複雜度
用戶: "找出所有 Controller 文件"
→ task-router 自動分析
→ 建議: file-finder（簡單任務）
→ 自動執行

用戶: "審查 15 個批次檔案"
→ task-router 自動分析
→ 建議: review-coordinator（複雜任務）
→ 規劃並執行
```


### 方式 3：組合使用

```bash
# 多個 agents 組合完成複雜任務
1. file-finder: 找文件
2. code-searcher: 搜索內容
3. code-editor: 修改代碼
4. test-runner: 驗證修改
```

---

## 參考文檔

- [組合策略文檔](./COMPOSITION-STRATEGY.md) - **必讀**：如何組合 Atomic Agents 完成複雜任務
- [SRP 架構總覽](../ARCHITECTURE-SRP.md)
- [智能任務路由](../../docs/TASK-ROUTING-GUIDE.md) - 自動分析任務並推薦執行策略
- [原有 Agents](../README.md)

---

## 效能優勢

使用 Haiku 模型的 Atomic Agents 組合相比單一 Sonnet Agent：

| 指標 | Sonnet (單一) | Haiku (組合) | 改善 |
|------|--------------|--------------|------|
| 響應速度 | 慢 | 快 | **3x** |
| Token 成本 | 高 | 低 | **-80%** |
| 可組合性 | 單體 | 靈活 |  |
| 可維護性 | 複雜 | 簡單 |  |
| 可測試性 | 困難 | 容易 |  |

**範例場景**：修改 10 個 Controller 文件

```
Sonnet (單一 Agent):
- 時間: ~60 秒
- 成本: 高
- 不可並行

Haiku (Atomic Agents 組合):
- 時間: ~20 秒  (快 3 倍)
- 成本: 低      (節省 80%)
- 可並行執行
```

---

**版本**：6.0
**最後更新**：2026-03-29
**重大變更**：
- 移除 project-specific agents（gbp-contract-comparator、review/project/ 子目錄）
- REVIEW 類統一為 8 個通用 agents
- 總計 45 個 Atomic Agents
