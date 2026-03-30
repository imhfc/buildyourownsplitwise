---

# 架構重構 Skill

> 使用 Atomic Agents 組合執行大型架構重構的標準作業流程
> 來源: DOC-05-architecture-refactoring-sop

---

## 用途

本 Skill 用於：
- 大量架構違規修正 (>20 個檔案)
- 架構標準變更
- 新增架構層級
- 全代碼庫符號重命名

---

##  v3.0 新架構：Atomic Agents 組合

### 核心改變

**v2.0（舊）**：
```
單一 Agent → 手動執行六階段 → 使用 Serena/ralph-wiggum 工具
```

**v3.0（新）**：
```
主會話 → 自動組合 Atomic Agents → 並行執行 → 極低成本
```

### 主要優勢

| 特性 | v2.0 | v3.0 | 提升 |
|------|------|------|------|
| **速度** | 75 分鐘 | 22 分鐘（並行） | 3.4x |
| **成本** | 高（Sonnet） | 極低（Haiku） | 節省 80% |
| **準確率** | ~85% | >95% | +10% |
| **可並行** | 否 | 是（Phase 1,2,5） | - |
| **自動規劃** | 否 | 是（Phase 3） | - |

### Atomic Agents 列表

| Agent | 階段 | 職責 | 模型 |
|-------|------|------|------|
| file-finder | Phase 1 | 收集需檢查的文件 | Haiku |
| code-searcher | Phase 1,2 | AST 結構化搜索 | Haiku |
| compliance-auditor | Phase 1,5 | 架構合規驗證 | Haiku |
| dependency-tracer | Phase 2 | 依賴關係分析 | Haiku |
| architecture-planner | Phase 3 | 規劃重構批次 | Haiku |
| code-editor | Phase 4 | 文件移動和修改 | Haiku |
| code-formatter | Phase 4 | 代碼格式化 | Haiku |
| test-runner | Phase 5 | 執行測試套件 | Haiku |
| code-reviewer | Phase 5 | 代碼品質檢查 | Haiku |

---

##  備選工具（可選）

### Serena 符號操作

| 階段 | Serena 工具 | 用途 |
|------|------------|------|
| Phase 1 | `search_for_pattern` | 搜尋架構違規 |
| Phase 2 | `find_referencing_symbols` | 分析影響範圍 |
| Phase 4 | `rename_symbol` | 批量重命名 |
| Phase 4 | `replace_symbol_body` | 替換實作 |
| 全程 | `think_about_task_adherence` | 確認方向正確 |

### ralph-wiggum 批量自動化

適用於 **Phase 4 執行重構** 中的重複性任務：

```bash
# 批量重命名類別
/ralph-wiggum:ralph-loop "依序重命名以下類別為新名稱:
CustomerAccessor → CustomerMapper
OrderAccessor → OrderMapper
ProductAccessor → ProductMapper" --max-iterations 10

# 批量修正 import
/ralph-wiggum:ralph-loop "修正以下檔案的 import 路徑:
File1.java, File2.java, File3.java
從 com.old.package 改為 com.new.package" --max-iterations 20

# 批量測試驗證
/ralph-wiggum:ralph-loop "依序執行以下模組的測試:
module-a, module-b, module-c
報告失敗的測試" --max-iterations 5
```

### 使用時機判斷

| 情境 | 工具選擇 |
|------|---------|
| 重命名單一符號 | Serena `rename_symbol` |
| 重命名 >5 個符號 | ralph-wiggum 迴圈 |
| 分析影響範圍 | Serena `find_referencing_symbols` |
| 搜尋違規模式 | Serena `search_for_pattern` |
| 批量執行相似操作 | ralph-wiggum 迴圈 |

---

## 重構流程 (6 階段)

```
開始重構
    ↓
Phase 1: 識別違規 → Phase 2: 評估影響 → Phase 3: 規劃批次
    ↓
Phase 4: 執行重構 ← ─ ─ ─ ┐
    ↓                     │
Phase 5: 驗證測試          │
    ↓                     │
還有下一批次？─ ─ 是 ─ ─ ┘
    │ 否
    ↓
Phase 6: 同步收尾
    ↓
完成
```

---

## Phase 1: 識別架構違規（主會話執行，可並行）

### 使用的 Atomic Agents

```
主會話並行調用：
├─ file-finder: 收集 src/main/java/**/*.java
├─ code-searcher: 使用 ast-grep 搜索違規模式
└─ compliance-auditor: 執行 ArchUnit 測試，驗證 ARCH-01
```

### 執行步驟

1. **file-finder**: 收集需檢查的文件
   - 搜索所有 Java 源文件
   - 過濾測試文件
   - 輸出文件列表

2. **code-searcher**: 搜索架構違規模式
   - Service 直接依賴 Accessor
   - Controller 包含業務邏輯
   - 跨層依賴

3. **compliance-auditor**: 驗證架構合規
   - 執行 ArchUnit 測試
   - 驗證 ARCH-01 決策樹
   - 生成違規報告

### 輸出

違規清單文檔（violations.md）：
```markdown
# 架構違規清單

## 跨層依賴 (12 處)
1. UserService.java:45 - 直接依賴 UserAccessor
2. OrderService.java:67 - 直接依賴 OrderAccessor
...

## 業務邏輯錯放 (8 處)
1. UserController.java:89 - 包含資料驗證邏輯
...
```

**時間**: ~5 分鐘（並行）

---

## Phase 2: 評估影響範圍（主會話執行，可並行）

### 使用的 Atomic Agents

```
主會話並行調用：
├─ dependency-tracer: 分析文件依賴關係
└─ code-searcher: 搜索符號引用
```

### 執行步驟

1. **dependency-tracer**: 分析依賴關係
   - 分析 import 語句
   - 建立依賴圖
   - 識別共用組件

2. **code-searcher**: 搜索符號引用
   - 查找所有對違規類/方法的引用
   - 評估影響範圍
   - 識別風險點

### 輸出

影響評估報告（impact-assessment.md）：
```markdown
# 影響評估報告

## 影響範圍
- 受影響文件: 35 個
- 需修改引用: 120 處
- 風險等級: 中

## 依賴分析
- UserService → UserMapper (新建)
- OrderService → OrderMapper (新建)
...

## 風險點
- UserService 被 15 個 Controller 依賴
...
```

**時間**: ~4 分鐘（並行）

---

## Phase 3: 規劃重構批次（使用 architecture-planner）

### 使用的 Atomic Agent

```
主會話調用：
└─ architecture-planner (Haiku): 分析並生成重構計劃
```

### 執行步驟

1. **architecture-planner**: 規劃重構批次
   - 讀取違規清單
   - 讀取影響評估報告
   - 確定分批策略
   - 生成執行計劃（YAML 格式）

### 輸出

重構批次計劃（refactor-plan.yaml）：
```yaml
refactor_plan:
  strategy: "shared_components_first"

  batches:
    - batch: 1
      name: "建立 Mapper 介面"
      parallel: false
      tasks:
        - 建立 UserMapper.java
        - 建立 OrderMapper.java
      risk: low

    - batch: 2
      name: "重構 Service 層"
      parallel: true
      tasks:
        - 修改 UserService 使用 UserMapper
        - 修改 OrderService 使用 OrderMapper
      risk: medium

  estimates:
    total_time: "3-4 小時"
    risk_level: "medium"

  recommendations:
    - "先執行 batch 1，確保 Mapper 正確"
    - "batch 2 可並行執行，注意測試"
```

**時間**: ~5 秒（Haiku 極快）

---

## Phase 4: 執行重構（主會話執行）

### 使用的 Atomic Agents

```
主會話依序調用：
├─ code-editor: 移動和修改文件
├─ code-formatter: 格式化代碼
└─ Bash: 編譯驗證 + Commit
```

### 執行步驟

1. **建立重構分支**
   ```bash
   git checkout -b refactor/accessor-to-mapper
   ```

2. **code-editor**: 執行文件移動和修改
   - 建立新文件（Mapper）
   - 修改現有文件（Service）
   - 更新 import 語句

3. **code-formatter**: 格式化代碼
   - 統一代碼格式
   - 調整縮排

4. **Bash**: 編譯驗證
   ```bash
   ./gradlew clean build
   ```

5. **Bash**: Commit 變更
   ```bash
   git add .
   git commit -m "refactor: rename Accessor to Mapper"
   ```

### 備選工具（可選）

在特殊情況下可使用：
- **Serena `rename_symbol`**: 全代碼庫精確重命名
- **ralph-wiggum**: 批量重複操作

**時間**: ~10-15 分鐘（視批次大小）

---

## Phase 5: 驗證測試（主會話執行，並行）

### 使用的 Atomic Agents

```
主會話並行調用：
├─ test-runner: 執行測試套件
├─ compliance-auditor: 驗證架構合規
└─ code-reviewer: 代碼品質檢查
```

### 執行步驟

1. **test-runner**: 執行完整測試套件
   ```bash
   ./gradlew test
   ./gradlew test --tests "*ArchTest*"
   ```

2. **compliance-auditor**: 驗證架構合規
   - 重新執行 ArchUnit 測試
   - 確認違規已修正
   - 生成驗證報告

3. **code-reviewer**: 代碼品質檢查
   - 檢查代碼風格
   - 檢查複雜度
   - 檢查潛在問題

### 輸出

驗證報告（validation-report.md）：
```markdown
# 驗證報告

## 測試結果
- 單元測試:  234/234 通過
- 架構測試:  15/15 通過

## 架構合規
- 違規數量: 0（修正前: 20）
- 合規率: 100%

## 代碼品質
- 代碼風格:  符合
- 複雜度:  正常
- 潛在問題: 0
```

**時間**: ~8 分鐘（並行）

---

## Phase 6: 同步收尾（主會話執行）

### 執行步驟

1. **同步其他開發分支**
   ```bash
   git checkout master
   git pull
   git checkout refactor/accessor-to-mapper
   git rebase master
   ```

2. **更新專案文檔**
   - 更新架構文檔
   - 更新 ADR（如需要）
   - 更新 README

3. **建立重構總結報告**
   - 重構前後對比
   - 修正的違規數量
   - 經驗教訓

4. **知識分享**
   - 團隊會議分享
   - 記錄到 memory-bank

**時間**: ~10 分鐘

---

## 完整執行範例

### 範例：將所有 Accessor 改名為 Mapper

```
用戶：「執行架構重構：將所有 Accessor 改名為 Mapper」

Phase 1（5 分鐘，並行）:
├─ file-finder: 找到 15 個 Accessor 文件
├─ code-searcher: 搜索違規模式
└─ compliance-auditor: 確認 20 處違規

Phase 2（4 分鐘，並行）:
├─ dependency-tracer: 分析依賴（35 個文件受影響）
└─ code-searcher: 搜索引用（120 處引用）

Phase 3（5 秒）:
└─ architecture-planner: 生成 3 批次計劃

Phase 4（批次 1，10 分鐘）:
├─ code-editor: 建立 15 個 Mapper 文件
├─ code-formatter: 格式化
└─ Bash: 編譯 + Commit

Phase 5（8 分鐘，並行）:
├─ test-runner: 測試全通過
├─ compliance-auditor: 違規清零
└─ code-reviewer: 品質符合

Phase 4-5（批次 2-3，重複）...

Phase 6（10 分鐘）:
├─ 同步分支
├─ 更新文檔
└─ 記錄經驗

總時間: ~22 分鐘
總成本: 極低（全程 Haiku）
```

---

## 詳細文檔


主要章節:
- `01-overview.md` - 總覽
- `02-phase1-identify-violations.md` - 識別違規
- `03-phase2-impact-assessment.md` - 評估影響
- `04-phase3-batch-planning.md` - 規劃批次
- `05-phase4-execute-refactoring.md` - 執行重構
- `06-phase5-validation-testing.md` - 驗證測試
- `07-phase6-sync-completion.md` - 同步收尾
- `08-tools-automation.md` - 工具與自動化
- `09-appendix.md` - 附錄


---

## 相關 Skills

### 前置 Skills
- `project-architect` - 識別架構違規與重構需求
- `aidocs-navigator` - 查找架構標準與模式

### 協作 Skills
- `project-developer` - 執行架構重構實作
- `project-qa` - 重構後回歸測試

### 後續 Skills
- `project-reviewer` - 重構代碼審查
- `memory-bank` - 記錄重構經驗與模式