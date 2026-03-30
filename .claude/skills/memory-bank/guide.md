# Memory Bank Skill

> 動態記憶管理 - 跨會話維持專案上下文（v2.0 Atomic Agents 架構）

---

## v2.0 工作流程（Atomic Agents）

### Phase 0: 定位文件

**執行者**: file-finder (Haiku)

**目標**: 定位需要操作的記憶文件

```bash
# 根據用戶請求定位文件
"記錄這個決策..." → decisions.yaml
"更新進度..." → progress.yaml
"記住偏好..." → preferences.yaml
"記錄問題..." → troubleshooting.yaml
"經驗教訓..." → lessons-learned.yaml
```

**輸出**:
- 文件路徑列表
- 文件當前內容

**時間**: ~15 秒

---

### Phase 1: 格式驗證

**執行者**: pattern-checker (Haiku)

**目標**: 驗證 YAML 格式正確性

**檢查項目**:
1. YAML 語法正確（無縮排錯誤）
2. 必備欄位存在
3. 日期格式正確（YYYY-MM-DD）
4. ID 編號格式正確（DEC-XXX, TS-XXX）
5. ID 無重複

**驗證範例**:
```yaml
# ✅ 正確格式
- id: DEC-015
  date: 2026-01-25
  context: "需要統一的 DTO 轉換方案"
  decision: "使用 MapStruct 進行 DTO 轉換"
  rationale: "類型安全、編譯時檢查、效能佳"
  status: active

# ❌ 錯誤格式
- id: DEC15              # 缺少連字號
  date: 2026/01/25       # 錯誤日期格式
  decision: "..."        # 缺少 context 欄位
```

**輸出**:
- 驗證結果（通過/失敗）
- 錯誤清單（如有）

**時間**: ~30 秒

---

### Phase 2: 更新內容

**執行者**: code-editor (Haiku)

**目標**: 更新記憶內容，保持格式一致性

**操作**:
1. 計算新 ID（查找最大 ID + 1）
2. 新增記憶條目
3. 保持 YAML 縮排一致
4. 更新時間戳記
5. 保存文件

**更新範例**:
```yaml
# 原有內容
decisions:
  - id: DEC-014
    date: 2026-01-24
    ...

# 新增內容（自動計算 ID）
  - id: DEC-015          # 自動遞增
    date: 2026-01-25     # 今天日期
    context: "..."
    decision: "..."
    rationale: "..."
    status: active
```

**輸出**:
- 更新成功確認
- 新記憶條目 ID

**時間**: ~1.25 分鐘

---

## 完整執行範例

### 場景 1: 記錄技術決策

**用戶請求**: "記錄這個決策：我們決定使用 MapStruct 進行 DTO 轉換"

**Phase 0 - file-finder** (15 秒):
```bash
定位文件: .claude/memory-bank/project-context/decisions.yaml
讀取現有內容，發現最大 ID: DEC-014
```

**Phase 1 - pattern-checker** (30 秒):
```bash
驗證 decisions.yaml 格式:
✓ YAML 語法正確
✓ 所有條目包含必備欄位
✓ 日期格式統一 YYYY-MM-DD
✓ ID 格式統一 DEC-XXX
✓ 無重複 ID
```

**Phase 2 - code-editor** (1 分鐘):
```bash
計算新 ID: DEC-015
新增決策條目:
  - id: DEC-015
    date: 2026-01-25
    context: "需要統一的 DTO 轉換方案"
    decision: "使用 MapStruct 進行 DTO 轉換"
    rationale: "類型安全、編譯時檢查、效能佳"
    status: active
    related_docs: []

保存文件完成
```

**總時間**: ~2 分鐘

---

### 場景 2: 更新開發進度

**用戶請求**: "更新進度：order-mgmt v1.0 開發完成"

**Phase 0 - file-finder** (15 秒):
```bash
定位文件: .claude/memory-bank/project-context/progress.yaml
讀取現有內容
```

**Phase 1 - pattern-checker** (30 秒):
```bash
驗證 progress.yaml 格式:
✓ YAML 語法正確
✓ modules 結構完整
✓ 日期格式統一
```

**Phase 2 - code-editor** (1 分鐘):
```bash
更新進度:
modules:
  order-mgmt:
    v1.0:
      status: "completed"     # 更新狀態
      completion: 100         # 更新完成度
      last_updated: 2026-01-25

更新完成清單:
recent_completed:
  - task: "order-mgmt v1.0 開發完成"
    completed_date: 2026-01-25
    commit: "..."
    notes: "所有 API 和批次已完成"
```

**總時間**: ~2 分鐘

---

### 場景 3: 同步任務清單

**用戶請求**: "同步當前 Task 清單到進度檔案"

**Phase 0 - file-finder** (15 秒):
```bash
定位文件: .claude/memory-bank/project-context/progress.yaml
讀取當前會話的 Task 清單
```

**Phase 1 - pattern-checker** (30 秒):
```bash
驗證 progress.yaml 格式:
✓ YAML 語法正確
✓ current_sprint 結構完整
✓ Task 結構有效
```

**Phase 2 - code-editor** (1 分鐘):
```bash
更新任務清單:
current_sprint:
  synced_at: 2026-02-01T10:00:00
  sync_source: "session-uuid"
  tasks:
    - id: 1
      subject: "修複單元測試"
      status: pending
      created_at: 2026-02-01
      updated_at: 2026-02-01
      priority: high
      notes: "修復 40 個失敗測試"
    - id: 2
      subject: "代碼品質改進"
      status: in_progress
      created_at: 2026-01-31
      updated_at: 2026-02-01
      priority: high
      notes: "TASK 12-13"
```

**總時間**: ~2 分鐘

**用途**：
- 跨會話保留任務進度
- 會話結束前保存當前任務狀態
- 支援並行開發的任務追蹤
- 自動計算同步時間和來源會話

---

### 場景 4: 記錄問題解決方案

**用戶請求**: "記錄這個問題：ArchUnit 測試失敗，原因是 Service 直接依賴 Accessor"

**Phase 0 - file-finder** (15 秒):
```bash
定位文件: .claude/memory-bank/entities/troubleshooting.yaml
讀取現有內容，發現最大 ID: TS-002
```

**Phase 1 - pattern-checker** (30 秒):
```bash
驗證 troubleshooting.yaml 格式:
✓ YAML 語法正確
✓ 所有條目包含必備欄位
✓ category 值有效
```

**Phase 2 - code-editor** (1 分鐘):
```bash
計算新 ID: TS-003
新增問題記錄:
  - id: TS-003
    date: 2026-01-25
    category: "runtime"
    problem: "ArchUnit 測試失敗"
    symptoms:
      - "測試報告顯示 Service 直接依賴 Accessor"
      - "違反架構約束"
    root_cause: "Service 未透過 Mapper 存取資料"
    solution: |
      1. 建立對應的 Mapper 介面
      2. Service 注入 Mapper 而非 Accessor
      3. 重新執行 ArchUnit 測試
    prevention: "遵循 ADR-003 六層架構規範"
```

**總時間**: ~2 分鐘

---

##  Memory Bank vs Serena Memory 分工

本專案有兩套記憶系統，各有專長：

| 系統 | 位置 | 用途 | 特性 |
|------|------|------|------|
| **Serena Memory** | Serena 內部 | 快速筆記、臨時資訊 | 輕量、即時、個人使用 |

### 使用指南

| 情境 | 使用系統 | 理由 |
|------|---------|------|
| 記錄技術決策 | **Memory Bank** (`decisions.yaml`) | 需要結構化、可追蹤 |
| 追蹤模組進度 | **Memory Bank** (`progress.yaml`) | 團隊共享、長期追蹤 |
| 記錄用戶偏好 | **Memory Bank** (`preferences.yaml`) | 跨會話持久 |
| 問題解決方案 | **Memory Bank** (`troubleshooting.yaml`) | 可升級為 Pattern |
| 臨時筆記 | **Serena** (`write_memory`) | 快速、不需結構 |
| 會話間快速傳遞 | **Serena** (`read_memory`) | 輕量、即時 |

### Serena Memory 工具

```python
# 寫入快速筆記
write_memory("note-name", "內容...")

# 讀取筆記
read_memory("note-name")

# 列出所有筆記
list_memories()
```

### 升級路徑

```
Serena Memory (臨時)
  ↓ 如果重要/需結構化
Memory Bank YAML
  ↓ 如果影響架構/需團隊共識
ADR / Pattern / Guide
```

---

## 職責

管理專案的動態記憶系統，包括：

1. **記錄決策** - 捕捉重要的技術決策 (→ Memory Bank)
2. **追蹤進度** - 更新任務和模組完成狀態 (→ Memory Bank)
3. **記住偏好** - 維護用戶和團隊偏好設定 (→ Memory Bank)
4. **問題解決** - 記錄問題和解決方案 (→ Memory Bank)
5. **會話摘要** - 重要會話的知識提取 (→ Memory Bank)
6. **快速筆記** - 臨時資訊傳遞 (→ Serena Memory)

---

## 觸發時機

- 「記錄這個決策」「記住這個」
- 「更新進度」「標記完成」
- 「同步 Task」「保存任務」「/memory-bank sync-tasks」
- 「我偏好...」「以後都用這種方式」
- 「這個問題怎麼解決的」「記錄這個解法」
- 「總結這次會話」「保存這次討論」
- 「會話結束」「保存進度」（自動同步任務）

---

## 記憶檔案位置

```
├── project-context/
│   ├── decisions.yaml       # 決策記錄
│   ├── preferences.yaml     # 偏好設定
│   ├── progress.yaml        # 進度追蹤
│   └── lessons-learned.yaml # 經驗教訓
├── sessions/
│   └── YYYY-MM-DD-topic.yaml
└── entities/
    ├── components.yaml      # 元件知識
    └── troubleshooting.yaml # 問題解決
```

---

## 操作指南

### 1. 記錄決策


```yaml
- id: DEC-XXX           # 遞增編號
  date: YYYY-MM-DD      # 今天日期
  context: "決策背景"    # 為什麼需要這個決策
  decision: "決策內容"   # 做出的決定
  rationale: "決策理由"  # 為什麼選擇這個方案
  status: active        # active | superseded | deprecated
  related_docs: []      # 相關文檔連結
```

**判斷標準**：
- 如果是架構級別、影響範圍大 → 建議升級為 ADR
- 如果是實作細節、臨時約定 → 記錄在 decisions.yaml

### 2. 更新進度


```yaml
modules:
  module-name:
    status: "completed"  # planning | in_progress | review | completed | blocked
    completion: 100
    last_updated: YYYY-MM-DD
```

### 2.5. 同步任務清單（新功能）

讀取當前會話的 Task 清單並更新 `.claude/memory-bank/project-context/progress.yaml`：

**命令**：
```bash
/memory-bank sync-tasks
```

**自動更新結構**：
```yaml
current_sprint:
  synced_at: "ISO-8601 時間戳記"      # 同步時間
  sync_source: "{會話 ID}"             # 來源會話
  tasks:
    - id: {遞增數字}
      subject: "{任務標題}"
      status: "pending | in_progress | completed"
      created_at: "YYYY-MM-DD"
      updated_at: "YYYY-MM-DD"
      priority: "low | medium | high"
      notes: "{任務說明}"
```

**行為**：
- 讀取當前會話的所有 pending 和 in_progress Task
- 將 Task 結構化為上述格式
- 自動計算同步時間（ISO 8601 格式）
- 保留現有的 completed Task（可選）
- 更新 last_updated 時間戳記

**使用場景**：
- 會話結束前保存當前進度
- 多會話協作開發時同步狀態
- 長期運行任務的進度追蹤
- 並行開發工作流程支援

### 3. 記錄偏好


```yaml
coding:
  new_preference: "value"
```

### 4. 記錄問題解決


```yaml
- id: TS-XXX
  date: YYYY-MM-DD
  category: "setup"     # setup | build | runtime | integration | performance
  problem: "問題描述"
  symptoms: []          # 症狀列表
  root_cause: "根因"
  solution: "解決步驟"
  prevention: "預防措施"
```

### 5. 建立會話摘要


```yaml
# YYYY-MM-DD-topic.yaml
date: YYYY-MM-DD
topic: "會話主題"
duration: "Xmin"

summary: |
  會話摘要...

decisions:
  - "決策 1"
  - "決策 2"

action_items:
  - "待辦事項 1"
  - "待辦事項 2"

artifacts:
  - "產出的檔案路徑"
```

---

## 記憶升級路徑

當記憶累積到一定程度，應考慮升級：

| 來源 | 升級條件 | 目標 |
|------|---------|------|
| `decisions.yaml` | 影響架構、需要團隊共識 | ADR |
| `troubleshooting.yaml` | 通用解法、可重複使用 | Pattern |
| `lessons-learned.yaml` | 可教學化、有教育價值 | Guide |

---

## 會話開始時

自動載入以下記憶以提供上下文：

1. `progress.yaml` - 了解當前狀態
2. `preferences.yaml` - 遵循用戶偏好
3. 最近的 `sessions/*.yaml` - 延續之前的討論

---

## Context 監控與自動保存

### 監控閾值

| 等級 | 閾值 | 動作 |
|------|------|------|
| 正常 | < 70% | 正常執行 |
| 注意 | 70-80% | 精簡輸出 |
| 警告 | 80-90% |  自動保存 + 警告 |
| 危險 | > 90% |  保存 + 建議重啟 |

### 自動保存觸發

當 Context > 80% 時自動執行：

```yaml
# 1. 建立或更新 session 檔案
session:
  status: "paused"
  context_level: "warning"  # warning | critical
  paused_at: "{timestamp}"

# 2. 記錄當前狀態
current_state:
  task: "{當前任務}"
  phase: "{當前階段}"
  progress: "{已完成}/{總數}"

# 3. 寫入恢復指令
recovery:
  resume_instructions: |
    已完成: ...
    待完成: ...
    下一步: ...
```

### 警告訊息輸出

```markdown
 Context 警告: ~{percentage}%

已自動保存進度:
- Session: {session-id}
- 進度: {completed}/{total}

建議:
1. 執行 /compact 壓縮對話
2. 或開新會話，說「繼續 session {id}」
```

### 恢復檢測

每次會話開始時檢查：

```markdown
2. 若有 status: "paused" 的 session:
   - 提示: 「發現未完成 session，是否繼續？」
3. 使用者確認後載入並繼續
```

---

## 注意事項

- 保持記憶精簡，避免冗餘
- 定期清理過期記憶（90 天未更新）
- 重要決策應提示用戶考慮建立 ADR
- 記憶格式統一使用 YAML
- 日期格式統一使用 YYYY-MM-DD
- **Context > 70% 時精簡所有輸出**
- **Context > 80% 時必須保存進度**

---

## 相關文檔



---

## 相關 Skills

### 協作 Skills
- 所有 Skills - 記錄各 Skill 執行過程中的決策、進度、問題與經驗

### 使用場景
- `system-analyst` - 記錄需求分析決策
- `system-designer` - 記錄設計決策與考量因素
- `project-developer` - 記錄開發決策與經驗教訓
- `project-architect` - 記錄架構決策理由
- `project-qa` - 記錄測試經驗與常見問題
- `project-reviewer` - 記錄審查經驗與常見問題
- `drda-integration` - 記錄 DRDA 問題解決方案
- `fcs-bpmn` - 記錄 BPMN 設計模式
- `architecture-refactor` - 記錄重構經驗與模式