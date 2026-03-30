# Parallel Sessions (並行開發會話記憶)

> 用於多 Worktree + 多 Sub-Agents 並行開發的共享狀態層

---

## 概述

Parallel Sessions 是並行開發的核心記憶系統，解決以下問題：

| 問題 | 解決方案 |
|------|---------|
| 每個 Sub-Agent 的 context 獨立 | 透過 Memory Bank 共享狀態 |
| Context 用完無法恢復進度 | 讀取 session 檔案繼續執行 |
| Orchestrator 無法追蹤所有狀態 | 集中記錄在 session 檔案 |
| 跨電腦無法繼續執行 | 所有變更 Push 到遠端 |

---

## Git 配置

### 初始分支定義

| 情境 | 初始分支 | 確認方式 |
|------|---------|---------|
| 功能開發 | `dev/{version}` 或用戶指定 | `git branch --show-current` |
| 通用 | `main` / `master` | 預設 |

### 分支命名規則

```
parallel/<session-id>/<module>-<description>

格式說明:
- parallel/           固定前綴
- <session-id>        會話 ID (ps-YYYYMMDD-NNN)
- <module>            模組名稱
- <description>       簡短描述 (可選)

範例:
parallel/ps-20260120-001/shared-components      # 共用元件
parallel/ps-20260120-001/module-a-api-query     # 模組 A
parallel/ps-20260120-001/module-b-api-create    # 模組 B
```

### Push 規則 (強制)

**每個階段完成後必須 Push，以支援跨電腦執行**

| 階段 | 動作 |
|------|------|
| 共用元件完成 | `git push -u origin parallel/{session}/shared-components` |
| 共用元件合併 | `git push origin {base-branch}` |
| 各模組完成 | `git push -u origin parallel/{session}/{module}` |
| 最終合併 | `git push origin {base-branch}` |

---

## 目錄結構

```
parallel-sessions/
├── README.md                           # 本文件
├── active/                             # 進行中的會話
│   └── {session-id}.yaml               # 活躍會話狀態
├── completed/                          # 已完成的會話
│   └── {session-id}.yaml               # 歸檔會話
```

---

## 會話生命週期

```
┌─────────────────────────────────────────────────────────────────┐
│                    Parallel Session Lifecycle                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Phase 0          Phase 1           Phase 2          Phase 3   │
│   ┌────────┐      ┌─────────┐       ┌─────────┐     ┌────────┐  │
│   │Analyze │      │ Shared  │       │Parallel │     │ Merge  │  │
│   │& Plan  │─────▶│Component│──────▶│  Tasks  │────▶│&Cleanup│  │
│   └────────┘      └─────────┘       └─────────┘     └────────┘  │
│       │               │                  │               │       │
│       ▼               ▼                  ▼               ▼       │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              Memory Bank (shared state)                   │  │
│   │  active/{session-id}.yaml                                │  │
│   │  + Git Push (跨電腦同步)                                  │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   RECOVER (if context low or cross-machine)                     │
│   ┌────────────┐                                                │
│   │ New Claude │                                                │
│   │ Session    │─── Read Memory Bank + git fetch ──▶ Resume     │
│   └────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 會話檔案格式

```yaml
# active/{session-id}.yaml
session:
  id: "ps-20260120-001"
  created: "2026-01-20T10:00:00"
  type: "parallel-development"
  status: "in_progress"

# Git 配置
git:
  remote: "origin"
  base_branch: "dev/main"
  branch_prefix: "parallel/ps-20260120-001"

task:
  description: "批量開發多個模組"
  task_type: "independent"
  total_modules: 3
  completed_modules: 1

# Phase 0: 分析結果
analysis:
  status: "completed"
  shared_components_needed: true
  shared_components_list: ["SharedException"]
  independent_modules: ["module-a", "module-b"]
  conflict_analysis:
    hard_conflicts: []
    soft_conflicts: []
    parallel_groups: [["module-a", "module-b"]]

# Phase 1: 共用元件
shared_components:
  status: "completed"
  branch: "parallel/ps-20260120-001/shared-components"
  commit: "abc1234"
  pushed: true

# Phase 2: 並行任務
parallel_tasks:
  - module: "module-a"
    branch: "parallel/ps-20260120-001/module-a-api"
    worktree: "../worktree-module-a"
    agent_id: "agent-001"
    status: "completed"
    test_passed: true
    commit: "def5678"
    pushed: true
    result:
      files_created: 5
      files_modified: 2
      tests_passed: 15
      tests_total: 15

  - module: "module-b"
    branch: "parallel/ps-20260120-001/module-b-api"
    worktree: "../worktree-module-b"
    agent_id: "agent-002"
    status: "in_progress"
    current_phase: "development"
    test_passed: null
    commit: null
    pushed: false

# Phase 3: 合併
merge:
  status: "pending"
  merged_branches: []
  merge_conflicts: []
  final_commit: null
  pushed: false

recovery:
  last_checkpoint: "2026-01-20T11:30:00"
  context_level: "normal"
  resume_instructions: |
    1. shared-components 已完成並 push
    2. module-a 已完成並 push
    3. module-b 正在開發中
    4. 等待 module-b 完成後執行合併
  pending_actions:
    - "完成 module-b 開發"
    - "合併所有分支"
```

---

## 操作指南

### 開始新任務

```bash
# 1. 複製模板
cp templates/session-template.yaml active/ps-20260120-001.yaml

# 2. 填入基本資訊
# - session.id
# - git.base_branch
# - task.description

# 3. 執行分析，更新 analysis 區段

# 4. 開始執行各 Phase
```

### 跨電腦繼續

```bash
# 1. 新電腦或新會話
git fetch origin

# 2. 讀取 session 狀態
cat .claude/memory-bank/parallel-sessions/active/ps-20260120-001.yaml

# 3. 根據 recovery.resume_instructions 繼續

# 4. 對於已 push 的分支，checkout 即可
git worktree add ../worktree-{module} parallel/{session}/{module}
```

### Sub-Agent 完成時

```yaml
# 更新對應 parallel_tasks[] entry:
status: "completed"
test_passed: true
commit: "{commit_hash}"
pushed: true
result:
  files_created: N
  tests_passed: M
  tests_total: M
```

### 會話完成時

```bash
# 1. 確認所有測試通過 + 已 push
# 2. 執行合併
# 3. Push 最終結果
# 4. 更新 session.status = "completed"
# 5. 移動到 completed/
mv active/ps-20260120-001.yaml completed/
```

---

## 與 Skill/Agent 整合

### parallel-develop Skill

入口 Skill，負責：
- 判斷是否需要並行
- 啟動 parallel-coordinator agent

位置: `.claude/skills/parallel-develop/SKILL.md`

### parallel-coordinator Agent

協調 Agent，負責：
- 建立 session
- 分析衝突
- 規劃並行任務
- 監控進度

位置: `.claude/agents/atomic/coordinator/parallel-coordinator.md`

---

## 最佳實踐

### 1. 及時更新狀態

每個重要動作後立即更新 Memory Bank：

```
動作完成 → 更新 YAML → Push (如需要) → 繼續下一步
```

### 2. 強制 Push

每個階段完成必須 Push，確保：
- 跨電腦可繼續
- Context 用完可恢復
- 團隊成員可接手

### 3. 精簡記錄

只記錄恢復所需的資訊：
- 狀態 (pending/in_progress/completed/failed)
- 當前階段 (current_phase)
- Push 狀態 (pushed: true/false)
- 結果摘要 (不含詳細日誌)

### 4. 恢復指令清晰

`recovery.resume_instructions` 要明確說明：
- 哪些已完成不需處理
- 哪些分支已 push
- 從哪個點繼續
- 接下來要做什麼

### 5. 定期 Checkpoint

長時間任務每 5-10 分鐘更新 `last_checkpoint`

---

## 相關文檔

- [Parallel Develop Skill](../../skills/parallel-develop/SKILL.md)
- [Parallel Coordinator](../../agents/atomic/coordinator/parallel-coordinator.md)
- [Memory Bank README](../README.md)
