# conflict-resolver.sh 使用指南

## 概述

`conflict-resolver.sh` 是一個 Git 衝突檢測和解決的輔助工具，提供結構化的衝突分析和自動化解決方案。

**文件位置**：`.claude/skills/git-ops/scripts/conflict-resolver.sh`

## 功能

### 1. 衝突檢測 (`--detect`)

檢測當前工作區是否存在未解決的 Git 衝突，並列出所有衝突檔案及其複雜度。

```bash
./conflict-resolver.sh --detect
```

**輸出格式**：
```yaml
conflicts:
  status: "has_conflicts" | "no_conflicts"
  count: <number>
  files:
    - file: "src/UserService.java"
      conflict_markers: 2
      ours_changes: "+15 lines"
      theirs_changes: "+10 lines"
      complexity: "low" | "medium" | "high"
  suggestion: "建議先解決簡單檔案（複雜度 low），再處理複雜檔案"
```

**複雜度分類**：
- `low`: 1 個衝突標記，容易解決
- `medium`: 2-3 個衝突標記，需要仔細檢查
- `high`: 4+ 個衝突標記，可能需要開發人員討論

### 2. 衝突分析 (`--analyze`)

詳細分析單個檔案的衝突情況，包括衝突標記的位置、範圍和內容。

```bash
./conflict-resolver.sh --analyze src/UserService.java
```

**輸出格式**：
```yaml
conflict_analysis:
  file: "src/UserService.java"
  markers:
    - index: 1
      start_line: 45
      separator_line: 52
      end_line: 60
      size_lines: 16
  file_type: "java"
  recommendation: "此為代碼檔案，衝突可能涉及邏輯變更。建議仔細比較..."
```

**檔案類型建議**：
- **配置檔案** (xml, yaml, json, properties)：衝突通常為簡單的屬性值衝突
- **代碼檔案** (java, js, py, sh)：衝突可能涉及邏輯變更，需要仔細比較
- **其他檔案**：手動檢視衝突標記

### 3. 衝突解決 (`--resolve`)

自動解決指定檔案的衝突，支援多種策略。

```bash
# 保留我們的版本（HEAD）
./conflict-resolver.sh --resolve src/UserService.java ours

# 保留他們的版本（MERGE_HEAD）
./conflict-resolver.sh --resolve pom.xml theirs

# 標記為已手動解決（使用於已手動編輯後）
./conflict-resolver.sh --resolve src/Service.java manual
```

**支援的策略**：
- `ours`: 保留我們的版本（HEAD）
- `theirs`: 保留他們的版本（MERGE_HEAD）
- `manual`: 標記為已手動解決（需要先手動編輯檔案，移除衝突標記）

**輸出格式**：
```yaml
result:
  status: "success"
  file: "src/UserService.java"
  strategy: "ours"
  message: "已使用 ours 策略解決衝突"
  remaining_conflicts: 2
```

## 使用工作流程

### 場景 1：自動化解決簡單衝突

```bash
# 1. 檢測所有衝突
./conflict-resolver.sh --detect

# 2. 優先解決簡單檔案（複雜度 low）
./conflict-resolver.sh --resolve pom.xml ours
./conflict-resolver.sh --resolve application.properties theirs

# 3. 手動解決複雜檔案
./conflict-resolver.sh --analyze src/UserService.java
# ... 手動編輯 src/UserService.java，移除衝突標記 ...
./conflict-resolver.sh --resolve src/UserService.java manual

# 4. 驗證所有衝突已解決
./conflict-resolver.sh --detect

# 5. 提交更改
git commit -m "解決合併衝突"
```

### 場景 2：分析並解決特定檔案

```bash
# 分析衝突詳情
./conflict-resolver.sh --analyze src/complex-file.java

# 根據建議決定解決方案
# 若決定保留我們的版本
./conflict-resolver.sh --resolve src/complex-file.java ours

# 或手動解決
# ... 編輯檔案 ...
./conflict-resolver.sh --resolve src/complex-file.java manual
```

### 場景 3：批量解決同類型衝突

```bash
# 檢測所有衝突
./conflict-resolver.sh --detect

# 按複雜度依序解決
# 1. 先解決所有配置檔案（low）
./conflict-resolver.sh --resolve pom.xml ours
./conflict-resolver.sh --resolve application.yaml ours

# 2. 再解決代碼檔案（medium/high）
./conflict-resolver.sh --analyze src/Service.java
./conflict-resolver.sh --resolve src/Service.java manual
```

## 集成到 Git 工作流程

### 合併後自動檢測

```bash
# 執行合併
git merge feature-branch

# 如果有衝突，自動檢測和分析
./conflict-resolver.sh --detect

# 查看詳細分析
./conflict-resolver.sh --analyze <conflicted-file>
```

### 與其他腳本集成

可與 `.claude/skills/git-ops/scripts/` 目錄下的其他腳本配合使用：

```bash
# 執行 Git 操作
./git-executor.sh merge feature-branch

# 如果遇到衝突，檢測並提供建議
./conflict-resolver.sh --detect

# 解決衝突
./conflict-resolver.sh --resolve <file> <strategy>

# 繼續提交
./git-executor.sh commit "解決合併衝突"
```

## 命令參考

| 命令 | 功能 | 範例 |
|------|------|------|
| `--detect` | 檢測所有衝突 | `./conflict-resolver.sh --detect` |
| `--analyze <file>` | 分析單個檔案 | `./conflict-resolver.sh --analyze src/Service.java` |
| `--resolve <file> <strategy>` | 解決衝突 | `./conflict-resolver.sh --resolve pom.xml ours` |
| `--help` | 顯示幫助 | `./conflict-resolver.sh --help` |

## 輸出說明

### 日誌輸出

所有日誌輸出包含顏色標記，便於快速識別：

- `[INFO]` (藍色)：資訊性訊息
- `[✓]` (綠色)：成功操作
- `[!]` (黃色)：警告訊息
- `[✗]` (紅色)：錯誤訊息

### YAML 輸出

所有結果都以 YAML 格式輸出，便於與其他工具整合或自動化處理。

## 常見問題

### Q: 使用 `ours` 或 `theirs` 後如何撤銷？

A: 使用 `git reset <file>` 重置檔案，回到衝突狀態。

```bash
git reset src/UserService.java
```

### Q: 如何判斷應該選擇 `ours` 還是 `theirs`？

A:
- 如果你的變更更正確或更新，使用 `ours`
- 如果對方的變更更正確或更新，使用 `theirs`
- 如果兩個版本都有重要部分，使用 `manual` 手動合併

### Q: 手動解決後如何標記為已解決？

A: 編輯檔案移除衝突標記後，使用 `manual` 策略：

```bash
# 編輯檔案，移除 <<<<<<<, =======, >>>>>>> 標記
vim src/UserService.java

# 標記為已解決
./conflict-resolver.sh --resolve src/UserService.java manual
```

### Q: 可以批量解決所有衝突嗎？

A: 不能自動批量解決，但可以逐個解決。建議：

1. 先用 `--detect` 檢測所有衝突
2. 按複雜度分類
3. 先自動解決簡單衝突（使用 `ours` 或 `theirs`）
4. 再手動解決複雜衝突

## 依賴

- Git（已安裝）
- `lib/error-handler.sh`（自動載入）
- Bash 4.0+

## 版本

- 版本：1.0
- 最後更新：2026-02-01
