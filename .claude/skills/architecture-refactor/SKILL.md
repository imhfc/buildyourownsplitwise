---
name: architecture-refactor
description: 自動規劃並執行大型架構重構，使用 Atomic Agents 組合完成六階段流程。
allowed-tools: [Read, Glob, Grep, Bash, Task]
---

# 架構重構

> 使用 Atomic Agents 組合執行大型架構重構的標準作業流程


## 觸發與路由


**Use this skill when:**
- 「執行架構重構」
- 「大型架構修正」（>20 個文件）
- 「架構標準變更」
- 「新增架構層級」
- 「全代碼庫符號重命名」

**DO NOT trigger for:**
- 「審查代碼」 → 使用 review-code
- 「驗證架構」 → 使用 architecture-audit

## 快速使用

### 執行完整架構重構

```bash
# 自然語言請求
"執行架構重構：將所有 Accessor 改名為 Mapper"
"重構架構：調整 infrastructure 層結構"
"修正 >20 個檔案的架構違規"
```

主會話會自動組合 Atomic Agents 執行六階段流程：
1. **識別違規** - file-finder + code-searcher + compliance-auditor
2. **評估影響** - dependency-tracer + code-searcher
3. **規劃批次** - architecture-planner (Haiku，極快且省成本)
4. **執行重構** - code-editor + code-formatter
5. **驗證測試** - test-runner + compliance-auditor + code-reviewer（並行）
6. **同步收尾** - 主會話處理文檔更新

### 檢查架構違規

```bash
# 自然語言請求
"檢查架構違規"
"執行 ArchUnit 測試"
"使用 ARCH-01 決策樹驗證"
```

主會話會執行 Phase 1（識別違規）並產生違規清單

## 核心功能

### 六階段工作流程（使用 Atomic Agents）

```
開始重構
    ↓
Phase 1: 識別違規（主會話執行）
    ├─► file-finder: 收集需檢查的文件
    ├─► code-searcher: 使用 ast-grep 搜索架構違規
    ├─► compliance-auditor: 執行 ArchUnit 測試，驗證 ARCH-01
    └─► 輸出：違規清單文檔
    ↓
Phase 2: 評估影響範圍（主會話執行）
    ├─► dependency-tracer: 分析文件依賴關係
    ├─► code-searcher: 搜索符號引用
    └─► 輸出：影響評估報告
    ↓
Phase 3: 規劃重構批次（使用 architecture-planner）
    ├─► 分析違規清單與影響範圍
    ├─► 確定分批策略（獨立/分層/共用組件優先/時間分片）
    ├─► 生成重構批次計劃（YAML 格式）
    └─► 輸出：重構批次計劃
    ↓
Phase 4: 執行重構 ← ─ ─ ─ ┐（主會話執行）
    ├─► 建立重構分支        │
    ├─► code-editor: 執行檔案移動和修改│
    ├─► code-formatter: 格式化代碼    │
    ├─► 編譯驗證            │
    └─► Commit 變更        │
    ↓                      │
Phase 5: 驗證測試（並行執行）│
    ├─► test-runner: 執行完整測試套件│
    ├─► compliance-auditor: 驗證架構合規│
    └─► code-reviewer: 代碼品質檢查   │
    ↓                      │
還有下一批次？─ ─ 是 ─ ─ ─┘
    │ 否
    ↓
Phase 6: 同步收尾（主會話執行）
    ├─► 同步其他開發分支
    ├─► 更新專案文檔
    ├─► 建立重構總結報告
    └─► 知識分享會議
    ↓
完成
```

### Atomic Agents 特性

所有階段使用專業化的 Atomic Agents：

| Agent | 用途 | 模型 | 階段 |
|-------|------|------|------|
| **file-finder** | 搜索需檢查的文件 | Haiku | Phase 1 |
| **code-searcher** | AST 結構化搜索 | Haiku | Phase 1, 2 |
| **compliance-auditor** | 架構合規驗證 | Haiku | Phase 1, 5 |
| **dependency-tracer** | 依賴關係分析 | Haiku | Phase 2 |
| **architecture-planner** | 規劃重構批次 | Haiku | Phase 3 |
| **code-editor** | 文件移動和修改 | Haiku | Phase 4 |
| **code-formatter** | 代碼格式化 | Haiku | Phase 4 |
| **test-runner** | 執行測試套件 | Haiku | Phase 5 |
| **code-reviewer** | 代碼品質檢查 | Haiku | Phase 5 |

**總成本**: 極低（全程使用 Haiku）

### 備選工具（可選）

在特定情況下，可使用以下工具輔助 Phase 4：

#### Serena 符號操作

| 工具 | 用途 | 使用時機 |
|------|------|---------|
| `rename_symbol` | 全代碼庫重命名符號 | 需要精確重命名類/方法 |
| `replace_symbol_body` | 替換方法實作 | 需要修改方法邏輯 |
| `search_for_pattern` | 搜索代碼模式 | 需要複雜模式匹配 |
| `find_referencing_symbols` | 查找符號引用 | 需要精確引用分析 |

#### ralph-wiggum 批量自動化

適用於大量重複性任務（>10 個相似操作）：

```bash
# 批量重命名類別
/ralph-wiggum:ralph-loop "依序重命名以下類別為新名稱:
CustomerAccessor → CustomerMapper
OrderAccessor → OrderMapper" --max-iterations 10

# 批量修正 import
/ralph-wiggum:ralph-loop "修正以下檔案的 import 路徑:
File1.java, File2.java, File3.java
從 com.old.package 改為 com.new.package" --max-iterations 20
```

**注意**: 優先使用 Atomic Agents（code-editor），只在特殊情況使用 Serena/ralph-wiggum

## 使用場景

| 場景 | 使用此 Skill? | 說明 |
|------|--------------|------|
| 大量架構違規修正 (>20 個檔案) |  Yes | 使用六階段完整流程 |
| 架構標準變更 |  Yes | 使用六階段完整流程 |
| 新增架構層級 |  Yes | 使用六階段完整流程 |
| 全代碼庫符號重命名 |  Yes | 使用 Phase 4 code-editor |
| 小型重構 (<10 個檔案) |  No | 直接在主會話中使用 code-editor |
| 單元測試重構 |  No | 使用 `/write-tests` skill |

## 執行策略

### Phase 1-2: 分析階段（可並行）

主會話同時調用：
- **file-finder** + **code-searcher** (並行搜索)
- **compliance-auditor** (驗證)
- **dependency-tracer** (分析依賴)

### Phase 3: 規劃階段（使用 Haiku）

調用 **architecture-planner** 生成重構計劃：
```yaml
refactor_plan:
  strategy: "shared_components_first"  # 或 sequential_layers / time_sliced
  batches:
    - batch: 1
      name: "建立共用組件"
      files: [...]
    - batch: 2
      name: "並行重構模組"
      parallel: true
      modules: [...]
  estimates:
    total_time: "3-4 小時"
    risk_level: "medium"
```

### Phase 4: 執行階段

主會話依序調用：
1. **code-editor** - 移動和修改文件
2. **code-formatter** - 格式化代碼
3. Bash - 編譯驗證
4. Bash - Commit 變更

### Phase 5: 驗證階段（並行）

主會話同時調用：
- **test-runner** (執行測試)
- **compliance-auditor** (驗證架構)
- **code-reviewer** (品質檢查)

### Phase 6: 收尾階段

主會話執行：
- Git 分支同步
- 文檔更新
- 報告生成

## 適用範圍

###  適用

- 大量架構違規修正 (>20 個檔案)
- 架構標準變更
- 新增架構層級
- 全代碼庫符號重命名

###  不適用

- 小型重構 (<10 個檔案) - 直接使用 Atomic Agents
- 單元測試重構 - 使用 `/write-tests` skill
- 單一檔案優化 - 直接使用 code-editor

## 效能指標

### 速度提升

| 階段 | 傳統方式 | Atomic Agents | 提升 |
|------|---------|--------------|------|
| Phase 1 識別 | 15 分鐘 | 5 分鐘（並行） | 3x |
| Phase 2 評估 | 10 分鐘 | 4 分鐘（並行） | 2.5x |
| Phase 3 規劃 | 30 分鐘 | 5 秒（Haiku） | 360x |
| Phase 5 驗證 | 20 分鐘 | 8 分鐘（並行） | 2.5x |

### 成本節省

- **Phase 3**: 使用 Haiku 模型，成本降低 80%
- **Phase 1, 2, 4, 5**: 全程使用 Haiku，成本降低 80%
- **整體**: 預估節省 60-70% 成本

### 準確率

- 架構違規檢測：> 95%（code-searcher + compliance-auditor）
- 依賴分析：> 90%（dependency-tracer）
- 重構規劃：> 90%（architecture-planner）

## 最佳實踐

###  推薦

1. **明確範圍** - 「將所有 Accessor 改名為 Mapper」比「重構代碼」更好
2. **利用並行** - Phase 1, 2, 5 可並行執行多個 Atomic Agents
3. **信任規劃** - architecture-planner 生成的計劃通常是最優的
4. **小批次迭代** - 按 Phase 3 生成的批次計劃逐批執行，降低風險

###  避免

1. **跳過 Phase 1-2** - 未分析就執行重構，風險極高
2. **忽略 Phase 5** - 未驗證就合併，可能引入 bug
3. **手動規劃** - Phase 3 應交給 architecture-planner，避免人為疏漏

## 詳細文檔位置


主要章節:
- `01-overview.md` - 總覽
- `02-phase1-identify-violations.md` - 識別違規
- `03-phase2-impact-assessment.md` - 評估影響
- `04-phase3-batch-planning.md` - 規劃批次
- `05-phase4-execute-refactoring.md` - 執行重構
- `06-phase5-validation-testing.md` - 驗證測試
- `07-phase6-sync-completion.md` - 同步收尾
- `08-tools-automation.md` - 工具與自動化

## 相關規範

- **Atomic Agents**: `.claude/agents/atomic/README.md`

## 相關 Skills

### 前置 Skills
- `system-analyst` - 分析架構問題和需求

### 協作 Skills
- `/review-code` - 重構後的代碼審查
- `/write-tests` - 補充測試覆蓋

### 後續 Skills
- `memory-bank` - 記錄重構經驗與模式

## 詳細說明

完整流程、Atomic Agents 組合、最佳實踐請參閱：[guide.md](./guide.md)

