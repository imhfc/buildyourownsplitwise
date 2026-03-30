---
name: agent-team
description: 使用 Claude Agent Teams 進行跨服務協作開發、並行審查、競爭假設除錯。
allowed-tools: Task, Read, Glob, Bash
---

# Agent Team Skill

> Claude Agent Teams + Atomic Agents 分層混合架構

## 執行流程

```
Step 1: 分析任務需求，選擇場景模板
  ↓
Step 2: 建立 Agent Team（Lead + Teammates）
  ↓
Step 3: Teammates 各自使用 Atomic Agents 執行任務
  ↓
Step 4: Lead 整合結果並輸出報告
```

**重要**：此 Skill 需要啟用實驗功能 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`。

## 使用場景

### 1. 跨服務重構
- 同時修改多個微服務的 API
- 統一多個服務的資料格式
- 跨服務架構遷移

### 2. 並行代碼審查
- 多維度同時審查（安全、性能、測試）
- 大型 PR 分割審查
- 全面品質評估

### 3. 競爭假設除錯
- 多角度調查難以定位的 Bug
- 並行測試多個假設
- 辯論收斂到根因

### 4. 全系統研究
- 理解大型系統架構
- 探索多個模組的交互
- 生成系統文檔

## 使用方式

### 命令格式

```bash
# 場景 1: 跨服務重構
/agent-team cross-service-refactor --services ModuleA,ModuleB,PM --task "統一 Customer API 格式"

# 場景 2: 並行審查
/agent-team parallel-review --pr 142

# 場景 3: 競爭假設除錯
/agent-team competing-hypothesis --bug "連線超時問題"

# 場景 4: 全系統研究
/agent-team research --topic "認證系統架構"
```

### 自然語言觸發

```
建立 Agent Team 重構 ModuleA、ModuleB、PM 三個服務的 Customer API

建立 Agent Team 審查 PR #142，分別從安全、性能、測試三個角度

建立 Agent Team 調查連線超時問題，測試資料庫、快取、並發三個假設

建立 Agent Team 研究認證系統的完整架構
```

## 場景模板

### 跨服務重構模板

```
建立 Agent Team 重構所有微服務的 {API_NAME} API。

Spawn 以下 Teammates：
1. Service-Owner-{SERVICE1}：負責 {SERVICE1} 服務
   - 使用 api-designer 設計新 API
   - 使用 code-editor 修改實作
   - 使用 test-writer 更新測試

2. Service-Owner-{SERVICE2}：負責 {SERVICE2} 服務
   [同上]

3. Service-Owner-{SERVICE3}：負責 {SERVICE3} 服務
   [同上]

Lead 負責：
- 統一 API 規格
- 驗證跨服務一致性
- 執行整合測試
```

### 並行審查模板

```
建立 Agent Team 審查 PR #{NUMBER}。

Spawn 三個 Reviewers：
1. Security-Auditor：安全審查
   - 使用 security-scanner 掃描漏洞
   - 重點：OWASP Top 10、認證授權

2. Quality-Guard：品質審查
   - 使用 code-reviewer、pattern-checker
   - 重點：命名、設計模式、複雜度

3. Test-Specialist：測試審查
   - 使用 coverage-analyzer、test-validator
   - 重點：覆蓋率、斷言品質

Lead 整合三份報告成統一審查結果。
```

### 競爭假設模板

```
建立 Agent Team 調查 {BUG_DESCRIPTION}。

Spawn 以下 Investigators：
1. Researcher-A：假設是 {HYPOTHESIS_1}
2. Researcher-B：假設是 {HYPOTHESIS_2}
3. Researcher-C：假設是 {HYPOTHESIS_3}
4. Devil-Advocate：挑戰所有假設

Teammates 互相討論和挑戰，Lead 記錄辯論並決定結論。
```

## Teammate 角色

詳見 [TEAMMATE-ROLES.md](../../agents/teams/TEAMMATE-ROLES.md)

| 角色 | 用途 | 內部 Atomic Agents |
|------|------|-------------------|
| Service-Owner | 負責特定服務 | code-generator, test-writer |
| Quality-Guard | 代碼審查 | code-reviewer, pattern-checker |
| Security-Auditor | 安全掃描 | security-scanner |
| Test-Specialist | 測試覆蓋 | coverage-analyzer, test-validator |
| Researcher | 研究調查 | file-finder, code-searcher |
| Devil-Advocate | 挑戰假設 | - |
| Architect | 架構設計 | api-designer, architecture-planner |

## 與 Atomic Agents 整合

每個 Teammate 都是完整的 Claude Code 實例，載入相同的 CLAUDE.md，因此可以：

1. **使用 Task tool** 調用 Atomic Agents
2. **使用 Coordinator Agents** 規劃複雜任務
3. **使用 Skills** 執行標準化流程

```
Teammate 內部流程：
┌───────────────────────────────────────┐
│ Teammate (獨立 context window)         │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │ Coordinator (規劃)               │  │
│  └───────────┬─────────────────────┘  │
│              ↓                        │
│  ┌───────────┴─────────────────────┐  │
│  │ Atomic Agents (執行)             │  │
│  │ - code-generator (Haiku)        │  │
│  │ - test-writer (Haiku)           │  │
│  │ - code-reviewer (Haiku)         │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

## 注意事項

### Token 消耗
- Agent Teams 比單一會話消耗更多 tokens
- 每個 Teammate 有獨立的 context window
- 建議限制 3-5 個 Teammates

### 檔案衝突
- **關鍵規則**：不同 Teammates 不能編輯相同檔案
- 按微服務或層級分工避免衝突

### 已知限制與緩解

| 限制 | 緩解策略 |
|------|---------|
| Session 恢復不含 Teammates | 使用 split-pane 模式、建立檢查點 |
| Task 狀態可能延遲 | Lead 定期同步、使用 Hooks |
| 無法巢狀 Teams | 使用 Task tool 調用 subagents（允許） |
| 權限繼承 | 預批准常用操作到 settings.json |
| 一次一個 Team | 分批執行大型任務 |

**重要澄清**：Teammates 可以使用 Task tool 調用 Atomic Agents（subagents），這不違反巢狀限制。

詳細緩解策略見 [BEST-PRACTICES.md](../../agents/teams/BEST-PRACTICES.md)

## 決策指南

| 條件 | 選擇 |
|------|------|
| 單模組修改 | 單一會話 + Atomic Agents |
| 3-7 檔案開發 | 單一會話 + Atomic Agents |
| **跨服務重構** | Agent Teams |
| **並行代碼審查** | Agent Teams |
| **競爭假設除錯** | Agent Teams |
| **全系統研究** | Agent Teams |

## 自動觸發關鍵字

- **建立 Agent Team**、**建立團隊**
- **跨服務**、**cross-service**
- **並行審查**、**parallel review**
- **競爭假設**、**competing hypothesis**
- **全系統研究**、**full system research**

## 相關文檔

- [Agent Teams 整合指南](../../agents/teams/README.md)
- [Teammate 角色定義](../../agents/teams/TEAMMATE-ROLES.md)
- [場景模板](../../agents/teams/SCENARIOS.md)
- [Atomic Agents 架構](../../agents/atomic/README.md)
- [Claude Agent Teams 官方文檔](https://code.claude.com/docs/en/agent-teams)

---

**版本**: 1.1.0
**最後更新**: 2026-02-08
**前置條件**: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
