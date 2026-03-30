# Project Context

## 檔案結構

| 檔案 | 用途 | 更新者 |
|------|------|--------|
| **preferences.yaml** | Git 操作框架、並行開發配置（被 Skills 引用） | AI/手動 |
| **progress.yaml** | 當前衝刺與任務狀態 | AI |
| **decisions.yaml** | 非正式技術決策記錄 | AI/手動 |

## 設計原則

- 語言/禁止事項/核心原則由 `CLAUDE.md` 定義（Single Source of Truth）
- 本目錄僅保留被 Skills 直接引用的結構化配置，以及需要跨會話追蹤的狀態

## 更新 progress.yaml

AI 可在任務開始/完成時更新：

```yaml
current_sprint: "SPRINT-NAME"
sprint_goal: "完成目標描述"

current_tasks:
  - task: "任務描述"
    status: "in_progress"  # ready | in_progress | done
    branch: "feature/xxx"
```
