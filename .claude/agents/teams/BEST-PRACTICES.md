# Agent Teams 最佳實踐

> Lead 與 Coordinator 協作模式、Token 監控、常見問題解決

## Lead 與 Atomic Coordinator 協作模式

### 模式一：Lead 直接協調

Lead 直接指派任務給 Teammates，不使用 Coordinator。

```
Lead
  ├── 分析任務範圍
  ├── 建立 Task List
  ├── Spawn Teammates
  └── 整合結果

適用：簡單跨服務任務、明確分工
```

### 模式二：Lead 使用 Coordinator 規劃

Lead 先調用 Coordinator 規劃，再根據計劃建立 Team。

```
Lead
  ├── 調用 parallel-coordinator 規劃
  ├── 收到執行計劃（YAML）
  ├── 根據計劃 Spawn Teammates
  ├── 分配 Task List
  └── 整合結果

適用：複雜依賴關係、需要衝突檢測
```

### 模式三：Teammates 各自使用 Coordinator

每個 Teammate 獨立使用 Coordinator 規劃自己的子任務。

```
Lead
  └── Spawn Teammates
        ├── Teammate-A
        │     ├── 調用 review-coordinator
        │     └── 執行 Atomic Agents
        ├── Teammate-B
        │     ├── 調用 review-coordinator
        │     └── 執行 Atomic Agents
        └── Teammate-C
              ├── 調用 review-coordinator
              └── 執行 Atomic Agents

適用：獨立複雜任務、每個 Teammate 範圍大
```

---

## Token 使用監控

### 預估公式

```
總 Token 消耗 ≈ Lead 消耗 + (Teammate 數量 × 平均 Teammate 消耗)

其中：
- Lead 消耗：約 10K-30K tokens（協調開銷）
- Teammate 消耗：取決於任務複雜度
  - 簡單審查：15K-30K tokens
  - 中等開發：30K-80K tokens
  - 複雜重構：80K-150K tokens
```

### 場景估算

| 場景 | Teammates | 預估消耗 | 成本等級 |
|------|-----------|---------|---------|
| 並行審查（3 人） | 3 | 70K-120K | 中 |
| 跨服務重構（3 服務） | 3 | 120K-300K | 高 |
| 跨服務重構（6 服務） | 6 | 200K-500K | 極高 |
| 競爭假設（4 人） | 4 | 100K-200K | 中-高 |

### 成本優化策略

1. **限制 Teammate 數量**
   - 建議 3-5 個 Teammates
   - 超過 5 個時考慮分批執行

2. **使用 Delegate Mode**
   - Lead 只協調，不執行
   - 減少 Lead 的 Token 消耗

3. **Teammates 使用 Haiku Atomic Agents**
   - 細粒度任務使用 Haiku 模型
   - 節省 80% 成本

4. **早期檢查點**
   - 設定 Plan Approval 要求
   - 避免錯誤方向浪費 Token

---

## 常見問題解決

### 問題 1：Teammates 編輯相同檔案

**症狀**：修改被覆蓋、合併衝突

**解決方案**：
```
1. 按檔案分工：每個 Teammate 負責不同檔案
2. 按層級分工：Frontend / Backend / Test
3. 按服務分工：每個 Teammate 負責一個微服務
4. 使用 Lead 統一編輯共用檔案
```

### 問題 2：Teammate 停止回應

**症狀**：Teammate 長時間沒有進度

**解決方案**：
```
1. 使用 Shift+Up/Down 選擇 Teammate
2. 直接發送訊息詢問狀態
3. 如果卡住，考慮 Spawn 新 Teammate 接手
4. 檢查是否等待權限確認
```

### 問題 3：Task List 狀態不同步

**症狀**：Teammate 完成但任務仍顯示 pending

**解決方案**：
```
1. 告知 Lead 更新任務狀態
2. 直接訊息 Teammate 標記完成
3. 手動檢查並更新 Task List
```

### 問題 4：Lead 自己開始執行任務

**症狀**：Lead 沒有等待 Teammates

**解決方案**：
```
1. 啟用 Delegate Mode（Shift+Tab）
2. 明確指示 Lead："等待 Teammates 完成後再繼續"
3. 在 Spawn Prompt 中強調 Lead 只負責協調
```

### 問題 5：tmux 會話未清理

**症狀**：關閉後 tmux 會話仍存在

**解決方案**：
```bash
# 列出所有 tmux 會話
tmux ls

# 殺掉特定會話
tmux kill-session -t <session-name>

# 殺掉所有會話
tmux kill-server
```

---

## Teammate 最佳數量指南

### 決策樹

```
任務範圍評估
  │
  ├─ 1-2 個模組 → 不需要 Agent Teams（使用單一會話）
  │
  ├─ 3-5 個模組
  │     ├─ 無依賴 → 3-5 Teammates（全並行）
  │     └─ 有依賴 → 2-3 Teammates（分層）
  │
  └─ 6+ 個模組
        ├─ 資源充足 → 最多 6 Teammates
        └─ 資源有限 → 分批執行（每批 3 個）
```

### Project 微服務建議

| 任務 | 建議配置 |
|------|---------|
| 審查單一服務 | 不需要 Teams |
| 審查 2 個服務 | 不需要 Teams |
| 審查 3+ 個服務 | 3 Teammates |
| 跨 3 服務重構 | 3 Teammates |
| 跨 6 服務重構 | 分 2 批，每批 3 Teammates |
| 全系統研究 | 3 Teammates（架構/資料流/整合） |

---

## 檢查清單

### 啟動前

- [ ] 確認 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- [ ] 確認 tmux 已安裝（split pane 模式）
- [ ] 分析任務是否適合 Agent Teams
- [ ] 確認 Teammates 分工不會有檔案衝突
- [ ] 預估 Token 消耗

### 執行中

- [ ] 定期檢查 Teammates 進度
- [ ] 確認 Task List 狀態正確
- [ ] 監控 Token 使用量
- [ ] 及時介入解決卡住的 Teammate

### 結束後

- [ ] 確認所有 Teammates 已關閉
- [ ] 讓 Lead 執行 cleanup
- [ ] 檢查並清理 orphaned tmux 會話
- [ ] 整合所有結果

---

## 與現有 Skills 整合

### /review-code + Agent Teams

```
# 大型 PR 並行審查
建立 Agent Team 審查 PR #142：
- 使用 /review-code 的審查策略
- 每個 Teammate 負責不同審查維度
```

### /write-tests + Agent Teams

```
# 跨服務測試撰寫
建立 Agent Team 為 ModuleA、ModuleB、ModuleC 撰寫測試：
- 每個 Teammate 使用 /write-tests
- Lead 整合測試報告
```

### /parallel-develop + Agent Teams

```
# 超大規模並行開發
建立 Agent Team 進行 6 服務並行開發：
- Lead 使用 parallel-coordinator 規劃
- 每個 Teammate 負責一個服務
- 使用 /parallel-develop 的 Worktree 策略
```

---

## 限制緩解策略

### Session 恢復策略

**問題**：`/resume` 不會恢復 in-process teammates

**緩解方案**：

1. **使用 split-pane 模式**（推薦長時間任務）
   ```bash
   # tmux 會話獨立於 Claude session
   claude --teammate-mode tmux
   ```

2. **建立檢查點**
   - 每個 Phase 完成後讓 Lead 記錄進度到檔案
   - 恢復時提供進度檔案給新 Lead

3. **恢復後重建**
   ```
   之前的 session 中斷了。請根據 Task List 狀態：
   - 已完成的任務不需重做
   - 為未完成的任務 spawn 新 teammates
   ```

---

### 權限管理

**問題**：所有 Teammates 繼承 Lead 的權限設定

**緩解方案**：

1. **預批准常用操作**
   ```json
   // settings.json
   {
     "permissions": {
       "allow": [
         "Bash(git:*)",
         "Bash(./gradlew:*)",
         "Bash(npm:*)",
         "Edit(*)",
         "Write(*)"
       ]
     }
   }
   ```

2. **啟動前確認 Lead 模式**
   - 避免 `--dangerously-skip-permissions`
   - 或確保所有 Teammates 任務都安全

---

### 多批次執行

**問題**：一個 Lead 只能管理一個 Team

**緩解方案**：

```
第一批（服務 1-3）
  ├── 建立 Team
  ├── 完成任務
  ├── Lead 輸出結構化摘要
  └── 執行 cleanup

第二批（服務 4-6）
  ├── 提供第一批摘要作為上下文
  ├── 建立新 Team
  ├── 完成任務
  └── 執行 cleanup
```

**批次間資料格式**：
```yaml
batch_summary:
  batch: 1
  completed:
    - service: ModuleA
      changes: [file1.java, file2.java]
      tests: passed
    - service: ModuleB
      changes: [file3.java]
      tests: passed
  notes: "統一了 Customer API 格式"
```

---

### 巢狀限制澄清

**允許**：
- Teammates 使用 Task tool 調用 subagents（Atomic Agents）
- Subagents 和 Teammates 是不同概念

**禁止**：
- Teammates spawn 新的 teammates
- Teammates 建立子 Team

**我們架構的有效性**：
```
Teammate
  └── Task tool (subagent) → Coordinator → OK
  └── Task tool (subagent) → Atomic Agent → OK
  └── spawn teammate → BLOCKED
```

---

### 優雅關閉

**預估時間**：
- 簡單任務：5-30 秒
- 複雜 tool call：1-5 分鐘

**強制關閉**（最後手段）：
```bash
# 列出 tmux 會話
tmux ls

# 殺掉特定會話
tmux kill-session -t <session-name>
```

---

**版本**: 1.1.0
**最後更新**: 2026-02-08
**更新內容**: 新增限制緩解策略章節
