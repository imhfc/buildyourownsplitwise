# /memory-bank sync-tasks 命令實現指南

> 跨會話任務進度同步功能

---

## 命令概述

`/memory-bank sync-tasks` 是一個自動將當前會話的 Task 清單同步到進度追蹤檔案的命令。

**目標**：解決長期開發中會話中斷導致任務進度丟失的問題

---

## 功能特性

### 核心功能

1. **自動讀取當前 Task**
   - 掃描會話中的所有 pending 和 in_progress Task
   - 提取 Task ID、標題、狀態、日期等資訊

2. **結構化保存**
   - 將 Task 轉換為標準 YAML 格式
   - 存儲到 `progress.yaml` 的 `sprint_sync.tasks` 部分

3. **元資料追蹤**
   - 自動記錄同步時間（ISO 8601 格式）
   - 記錄同步來源會話 ID
   - 保留原始 created_at 和新增 updated_at

4. **跨會話恢復**
   - 下次會話開始時可讀取同步的 Task
   - 恢復任務狀態和進度

---

## 使用場景

### 場景 1: 會話結束前保存進度

```bash
# 用戶請求
"同步任務到進度檔案"
或
"/memory-bank sync-tasks"
或
"保存當前 Task"
```

**行為**：
```
1. 讀取當前會話中的 Task 清單
   Task 1: 修複單元測試 (pending)
   Task 2: 代碼品質改進 (in_progress)
   
2. 轉換為標準格式
   id: 1, 2, ...
   subject: "任務標題"
   status: "pending | in_progress"
   ...
   
3. 寫入 progress.yaml
   sprint_sync:
     synced_at: "2026-02-01T15:30:45Z"
     sync_source: "session-uuid-xxxxx"
     tasks:
       - id: 1
         subject: "修複單元測試"
         ...
       - id: 2
         subject: "代碼品質改進"
         ...
```

### 場景 2: 並行開發工作流程

多個會話同時進行不同的 Task：

```
會話 A                      會話 B
├─ Task 1 (in_progress)    ├─ Task 3 (pending)
├─ Task 2 (pending)        └─ Task 4 (in_progress)
└─ sync-tasks              └─ sync-tasks
   ↓                          ↓
進度檔案 (統一視圖)
├─ Task 1 (from Session A)
├─ Task 2 (from Session A)
├─ Task 3 (from Session B)
└─ Task 4 (from Session B)
```

---

## 同步格式詳解

### YAML 結構

```yaml
current_sprint: "v1.0 開發"
sprint_goal: "完成品質改進"

# Task 同步資訊
sprint_sync:
  # 最後同步時間 (ISO 8601)
  synced_at: "2026-02-01T15:30:45Z"
  
  # 同步來源會話
  sync_source: "session-abc123def456"
  
  # Task 清單
  tasks:
    - id: 1                           # 遞增任務 ID
      subject: "修複 40 個失敗測試"   # 任務標題
      status: "pending"               # pending | in_progress | completed
      created_at: "2026-02-01"        # 任務建立日期
      updated_at: "2026-02-01"        # 最後更新日期
      priority: "high"                # low | medium | high
      notes: "BatchNaviPropertiesTest" # 詳細說明
      
    - id: 2
      subject: "代碼品質改進 TASK 12"
      status: "in_progress"
      created_at: "2026-01-31"
      updated_at: "2026-02-01"
      priority: "high"
      notes: "CUSVD4, CUSVAA (120 檔案)"
```

### 欄位說明

| 欄位 | 說明 | 範例 |
|------|------|------|
| `id` | 任務 ID（遞增） | 1, 2, 3, ... |
| `subject` | 任務標題 | "修複單元測試" |
| `status` | 任務狀態 | pending, in_progress, completed |
| `created_at` | 建立日期 | 2026-02-01 |
| `updated_at` | 更新日期 | 2026-02-01 |
| `priority` | 優先級 | low, medium, high |
| `notes` | 備註說明 | "詳細描述" |
| `synced_at` | 同步時間 | 2026-02-01T15:30:45Z |
| `sync_source` | 同步會話 | session-uuid |

---

## 實現流程

### Phase 0: 定位文件（15 秒）

```bash
目標文件：.claude/memory-bank/project-context/progress.yaml

執行：
1. 定位 progress.yaml 檔案
2. 讀取現有內容
3. 驗證 sprint_sync 結構存在
```

### Phase 1: 格式驗證（30 秒）

```bash
驗證項目：
✓ progress.yaml YAML 語法正確
✓ sprint_sync 結構完整
✓ tasks 陣列格式有效
✓ 現有 Task 欄位完整
```

### Phase 2: 更新內容（1 分鐘）

```bash
操作步驟：
1. 讀取當前會話 Task 清單
2. 遍歷 pending 和 in_progress Task
3. 轉換為標準格式
   - 計算 Task ID（現有最大 ID + 1 起算）
   - 標準化日期格式
   - 提取優先級和備註
4. 計算同步時間戳記（ISO 8601）
5. 記錄會話 ID
6. 寫入 progress.yaml
7. 驗證寫入成功
```

---

## 命令觸發

### 1. 命令方式

```bash
/memory-bank sync-tasks
```

### 2. 自然語言方式

```
"同步任務清單"
"保存當前任務"
"同步 Task 到進度檔案"
"保存進度"
"/memory-bank sync-tasks"
```

### 3. 自動觸發（可選）

- 會話即將結束時
- Context 即將超過 80% 時
- 並行開發完成時

---

## 輸出格式

### 成功同步

```markdown
已同步 Task 清單到進度檔案

同步摘要：
- 同步時間：2026-02-01T15:30:45Z
- 會話 ID：session-abc123
- 同步任務數：2 個
  - Task 1: 修複單元測試 (pending)
  - Task 2: 代碼品質改進 (in_progress)

位置：.claude/memory-bank/project-context/progress.yaml
部分：sprint_sync.tasks

下次會話開啟時，可透過以下方式恢復：
/memory-bank recover-tasks [會話 ID]
```

### 同步失敗

```markdown
同步 Task 清單失敗

原因：progress.yaml 格式驗證失敗

建議：
1. 檢查 progress.yaml 是否有語法錯誤
2. 確認 sprint_sync 結構完整
3. 確認 tasks 陣列格式正確
```

---

## 最佳實踐

### 推薦用法

1. **會話結束前**
   - 在關閉會話前執行 `/memory-bank sync-tasks`
   - 確保任務進度被保存

2. **並行開發中**
   - 每個會話定期同步（如每個階段完成後）
   - 保持進度更新

3. **長期任務**
   - 定期同步中間進度
   - 避免大量未保存的工作

### 避免事項

1. **不要**在會話開始時立即同步
   - 等待確實有 Task 產生後再同步

2. **不要**重複同步相同 Task
   - 系統會自動去重

3. **不要**修改已同步的 Task 格式
   - 保持 YAML 一致性

---

## 與進度追蹤的關係

### progress.yaml 結構

```
progress.yaml
├── last_updated              (全局時間戳記)
├── current_sprint            (當前衝刺名稱)
├── sprint_goal               (衝刺目標)
├── sprint_sync  ◄─────────── Task 同步資訊（新增）
│   ├── synced_at             同步時間
│   ├── sync_source           會話 ID
│   └── tasks                 Task 清單
├── current_tasks             當前工作（人工維護）
├── recent_completed          完成任務（人工維護）
├── dev_plans                 開發計畫
└── milestones                里程碑
```

### 區別

| 部分 | 維護方式 | 用途 | 週期 |
|------|---------|------|------|
| `sprint_sync` | 自動（sync-tasks） | 會話任務同步 | 按需或定期 |
| `current_tasks` | 人工 | 手工追蹤進度 | 手動更新 |
| `recent_completed` | 人工 | 記錄已完成工作 | 任務完成後 |

---

## 常見問題

### Q: 如何恢復已同步的 Task？

A: 讀取 progress.yaml 的 sprint_sync.tasks 部分即可查看：

```bash
# 查看 Task 清單
grep -A 20 "sprint_sync:" progress.yaml
```

### Q: 同步的 Task 如何對應當前會話？

A: 透過 `sync_source` 欄位記錄會話 ID，可以識別來源：

```yaml
sprint_sync:
  sync_source: "session-abc123"  # ← 會話識別
  synced_at: "2026-02-01T15:30:45Z"
```

### Q: 如何清除舊的同步記錄？

A: 手動編輯 progress.yaml，刪除舊的 tasks 項目或替換整個 sprint_sync 部分。

### Q: Task ID 衝突怎麼辦？

A: 系統自動遞增，若發現重複會跳過，從最大 ID 開始遞增。

---

## 版本說明

| 版本 | 日期 | 更新 |
|------|------|------|
| 1.0 | 2026-02-01 | 初始實現 |
| | | - Task 自動同步 |
| | | - ISO 8601 時間戳記 |
| | | - 會話 ID 追蹤 |
| | | - YAML 格式驗證 |

---

## 相關文檔

- [Memory Bank SKILL.md](./SKILL.md) - 概述
- [Memory Bank guide.md](./guide.md) - 詳細操作指南
- [progress.yaml](../project-context/progress.yaml) - 進度追蹤檔案
- [TASK-ROUTING-GUIDE](../../docs/TASK-ROUTING-GUIDE.md) - Task 管理

---

**最後更新**：2026-02-01
**狀態**：已實現
**維護者**：Memory Bank Skill
