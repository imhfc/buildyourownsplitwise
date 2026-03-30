# Atomic Agents 規範映射表

> 定義每個 Atomic Agent 應該載入的專案規範

---

## 映射策略

每個 Atomic Agent 透過 frontmatter 的 `context` 欄位載入相關規範：

```yaml
---
name: agent-name
model: haiku
tools: Tool1, Tool2
description: 描述
context:
---
```

---

## 規範分類

### 核心規範（Core Standards）

| 規範 | 路徑 | 適用對象 |
|------|------|---------|

### 設計模式（Design Patterns）

| 模式 | 路徑 | 適用對象 |
|------|------|---------|

### ADR（Architecture Decision Records）

| ADR | 路徑 | 適用對象 |
|-----|------|---------|

---

## 按 Agent 類別映射

### COORDINATOR 類

#### review-coordinator
```yaml
context:
```

**理由**：需要理解代碼審查標準、文件放置規則和架構標準以規劃審查策略

#### parallel-coordinator
```yaml
context:
```

**理由**：需要理解並行開發流程、文件放置規則和架構標準以規劃並行任務

---

### SEARCH 類

#### file-finder, code-searcher, symbol-locator, dependency-tracer
```yaml
context: []  # 無需特定規範（純工具型任務）
```

**理由**：搜索類 agents 執行純工具型任務，不涉及代碼生成或設計決策

---

### CODE 類

#### code-generator
```yaml
context:
```

**理由**：需要 AI-GIT-BEHAVIOR.md 以確保不在 commit 中添加 AI 標記

#### code-editor
```yaml
context:
```

**理由**：需要 AI-GIT-BEHAVIOR.md 以確保不在 commit 中添加 AI 標記

#### code-deleter
```yaml
context:
```

**理由**：刪除代碼時需要理解架構決策，避免誤刪重要文件；需要 AI-GIT-BEHAVIOR.md 以確保不在 commit 中添加 AI 標記

#### code-formatter
```yaml
context: []  # 無需特定規範（純格式化任務）
```

**理由**：格式化是純工具型任務，依賴 Checkstyle/Prettier 等工具

---

### REFACTOR 類

#### code-simplifier
```yaml
context:
```

**理由**：簡化代碼時需要遵循開發指南和 null 處理規範

#### duplicate-remover
```yaml
context:
```

**理由**：移除重複代碼時需要遵循開發指南

#### naming-improver
```yaml
context:
```

**理由**：改善命名時需要遵循開發指南

#### performance-tuner
```yaml
context:
```

**理由**：性能優化時需要遵循開發指南

---

### DATA 類

#### schema-designer 
```yaml
context:
```

**理由**：已正確配置

#### query-writer
```yaml
context:
```

**理由**：撰寫 SQL 時需要遵循開發指南

#### migration-generator
```yaml
context:
```

**理由**：生成遷移腳本時需要遵循開發指南

#### data-validator
```yaml
context:
```

**理由**：驗證數據時需要遵循開發指南

---

### TEST 類

#### test-writer
```yaml
context:
```

**理由**：需要 AI-GIT-BEHAVIOR.md 以確保不在 commit 中添加 AI 標記

#### test-runner
```yaml
context:
```

**理由**：執行測試時需要理解測試標準

#### coverage-analyzer
```yaml
context:
```

**理由**：分析覆蓋率時需要理解測試標準

#### test-fixer
```yaml
context:
```

**理由**：修復測試時需要遵循測試標準和 BDD 結構；需要 AI-GIT-BEHAVIOR.md 以確保不在 commit 中添加 AI 標記

---

### REVIEW 類

#### code-reviewer
```yaml
context:
```

**理由**：審查代碼時需要理解審查標準、文件放置規則和六層架構

#### security-scanner
```yaml
context:
```

**理由**：掃描安全問題時需要理解審查標準

#### pattern-checker
```yaml
context:
```

**理由**：檢查設計模式時需要理解所有模式規範

#### compliance-auditor
```yaml
context:
```

**理由**：審計合規性時需要理解審查標準、文件放置規則和六層架構

---

### DESIGN 類

#### api-designer 
```yaml
context:
```

**理由**：已正確配置

#### architecture-planner
```yaml
context:
```

**理由**：規劃架構時需要理解文件放置、架構測試、六層架構和 ArchUnit 測試

#### interface-designer
```yaml
context:
```

**理由**：設計接口時需要理解開發指南和 DTO 轉換模式

#### workflow-designer
```yaml
context:
```

**理由**：設計工作流程時需要遵循開發指南

---

### CONFIG 類

#### env-manager, property-editor, docker-configurator, ci-configurator
```yaml
context: []  # 無需特定規範（純配置任務）
```

**理由**：配置類 agents 執行純配置任務，不涉及代碼生成或架構決策

---

## 維護指南

### 新增 Atomic Agent 時

1. 根據職責確定所屬類別
2. 參考同類別的規範映射
3. 在 frontmatter 中添加 `context` 欄位
4. 更新本文檔

### 新增規範文件時

1. 確定規範類型（Standard/Pattern/ADR）
2. 評估哪些 Atomic Agents 需要載入
3. 更新相關 Agents 的 `context` 欄位
4. 更新本文檔

### 驗證規範載入

```bash
# 檢查所有 Atomic Agents 的 context 欄位
grep -A 10 "^context:" .claude/agents/atomic/**/*.md

# 驗證規範文件存在
for file in $(grep -h "  - " .claude/agents/atomic/**/*.md | sed 's/  - //'); do
  if [ ! -f "$file" ]; then
    echo "Missing: $file"
  fi
done
```

---

## 統計

| 類別 | Agents 數量 | 需要規範 | 已配置 | 待配置 |
|------|------------|---------|--------|--------|
| COORDINATOR | 2 | 2 | 2 | 0 |
| SEARCH | 4 | 4 | 4 | 0 |
| CODE | 4 | 4 | 4 | 0 |
| REFACTOR | 4 | 4 | 4 | 0 |
| DATA | 4 | 4 | 4 | 0 |
| TEST | 4 | 4 | 4 | 0 |
| REVIEW | 5 | 5 | 5 | 0 |
| DESIGN | 4 | 4 | 4 | 0 |
| CONFIG | 4 | 0 | 0 | 0 |
| **總計** | **35** | **31** | **31** | **0** |

**完成度**：100% (31/31)

---

**版本**：2.0
**最後更新**：2026-01-25
**維護者**：AI Team
**變更**：更新統計資料，所有應配置 context 的 agents 已 100% 完成
