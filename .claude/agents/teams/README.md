# Agent Teams 整合指南

> Claude Agent Teams + Atomic Agents 分層混合架構

## 架構概覽

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Teams 層                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ Lead    │──│ TM: ModuleA │  │ TM: ModuleB │  │ TM: ModuleC  │     │
│  │(協調者) │  │(客戶)   │  │(協議)   │  │(個資)   │     │
│  └─────────┘  └────┬────┘  └────┬────┘  └────┬────┘     │
│                    │            │            │           │
│  ┌─────────────────┴────────────┴────────────┴─────────┐│
│  │              共享 Task List + Mailbox                ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                         ↓ 每個 Teammate 內部
┌─────────────────────────────────────────────────────────┐
│                 Atomic Agents 層                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Coordinator  │  │ Coordinator  │  │ Coordinator  │   │
│  │ (規劃)       │  │ (規劃)       │  │ (規劃)       │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         ↓                 ↓                 ↓           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Atomic Agent │  │ Atomic Agent │  │ Atomic Agent │   │
│  │ (Haiku)      │  │ (Haiku)      │  │ (Haiku)      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 啟用方式

已在 `settings.json` 設定：
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## 使用時機決策

| 場景 | 單一會話 + Atomic | Agent Teams + Atomic |
|------|-------------------|---------------------|
| 單模組修改 | 適用 | 過度 |
| 3-7 檔案開發 | 適用 | 過度 |
| **跨服務重構** | 困難 | 適用 |
| **並行代碼審查** | 可行 | 更優 |
| **競爭假設除錯** | 困難 | 適用 |
| **全系統研究** | 慢 | 適用 |

## 核心原則

### 1. 分層職責

- **Agent Team Lead**：總體協調、任務分配、結果整合
- **Teammates**：執行特定領域任務，內部使用 Atomic Agents
- **Atomic Agents**：細粒度專業任務（Haiku 模型）

### 2. Teammate 內部使用 Atomic Agents

每個 Teammate 載入相同的 CLAUDE.md，因此可以使用：
- Task tool 調用 Atomic Agents
- Coordinator Agents 規劃複雜任務
- 所有已定義的 Skills

### 3. 避免檔案衝突

**關鍵規則**：不同 Teammates 不能編輯相同檔案

建議分工方式：
- 按微服務分：每個 Teammate 負責一個服務
- 按層級分：Frontend / Backend / Test
- 按職責分：Security / Performance / Coverage

## 相關文件

- [TEAMMATE-ROLES.md](./TEAMMATE-ROLES.md) - Teammate 角色定義
- [SCENARIOS.md](./SCENARIOS.md) - 場景模板
- [Atomic Agents](../atomic/README.md) - Atomic Agents 架構

## 已知限制

| 限制 | 影響 | 緩解策略 |
|------|------|---------|
| Session 恢復不含 Teammates | `/resume` 後需重建 | 使用 split-pane 模式、建立檢查點 |
| Task 狀態可能延遲 | 依賴任務被阻塞 | Lead 定期同步、使用 Hooks |
| 無法巢狀 Teams | Teammates 不能 spawn teammates | 使用 subagents（Task tool）替代 |
| Lead 固定 | 無法更換協調者 | 規劃前確認 Lead 設定 |
| 權限繼承 | 所有 Teammates 繼承 Lead 權限 | 預先在 settings 批准常用操作 |
| 一次一個 Team | 需清理後才能建新 Team | 分批執行大型任務 |

詳細緩解策略見 [BEST-PRACTICES.md](./BEST-PRACTICES.md)

## 相關文件

- [TEAMMATE-ROLES.md](./TEAMMATE-ROLES.md) - Teammate 角色定義
- [SCENARIOS.md](./SCENARIOS.md) - 場景模板
- [BEST-PRACTICES.md](./BEST-PRACTICES.md) - 最佳實踐與限制緩解
- [Atomic Agents](../atomic/README.md) - Atomic Agents 架構

## 版本

v1.1.0 (2026-02-08)
- 新增已知限制章節與緩解策略
