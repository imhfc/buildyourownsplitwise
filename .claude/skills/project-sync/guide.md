# Project Sync 實作指南

> 從主專案同步通用特性到目標專案的完整實作流程

## 實作策略

### 核心原則

1. **智能過濾** - 自動識別並排除專案特定內容
2. **路徑轉換** - 處理不同專案間的路徑差異
3. **內容調整** - 自動更新配置文件為通用版本
4. **安全執行** - 提供 dry-run 預覽，避免誤操作

### 主會話執行流程

本 skill 不使用獨立 agent，而是在**主會話中執行**，原因：
- 需要靈活處理路徑轉換
- 需要互動確認（如衝突處理）
- 使用基本工具（Bash, Read, Write, Edit）即可完成

## 實作步驟

### Step 1: 解析參數

```bash
# 解析用戶請求，提取參數
TARGET_PATH=""
CATEGORY="all"
SINCE=""
DRY_RUN=false
AUTO_COMMIT=false
AUTO_PUSH=false
DELETE_ORPHANS=false

# 從自然語言提取
# 例如：「將 Git Hooks 同步到 /path/to/project」
# → TARGET_PATH=/path/to/project
# → CATEGORY=hooks
```

### Step 2: 驗證目標路徑

```bash
# 檢查目標路徑
if [ ! -d "$TARGET_PATH" ]; then
  echo "錯誤：目標路徑不存在"
  exit 1
fi

# 檢查是否為 Git repository
if [ ! -d "$TARGET_PATH/.git" ]; then
  echo "錯誤：目標不是 Git repository"
  exit 1
fi
```

### Step 3: 載入排除規則

```bash
# 專案特定 skills（排除）
EXCLUDE_SKILLS=(
  "drda-integration"
  "fcs-bpmn"
  "reconcile-batch-spec-converter"
  "project-workflow"
  "project-sync"
)

# 通用 skills（包含）
INCLUDE_SKILLS=(
  "agent-router"
  "architecture-refactor"
  "ast-grep"
  "docs"
  "docx"
  "general-assistant"
  "governance-checker"
  "markdown-doc-processor"
  "memory-bank"
  "openspec"
  "parallel-develop"
  "review-code"
  "skill-creator"
  "speckit-converter"
  "write-tests"
  "xlsx"
)
```

### Step 4: 根據 Category 選擇文件

```bash
case "$CATEGORY" in
  hooks)
    FILES=(
      # Claude Code Hooks（按功能分類）
      ".claude/hooks/session/"
      ".claude/hooks/validation/"
      ".claude/hooks/tool/"
      ".claude/hooks/subagent/"
      ".claude/hooks/lib/"
      ".claude/hooks/README.md"
      ".claude/settings.json"
      # Git Hooks
      "setup/git-hooks/"
    )
    ;;

  agents)
    FILES=(
      ".claude/agents/atomic/"
      ".claude/agents/README.md"
      ".claude/agents/system-analyst.md"
      ".claude/agents/general-assistant.md"
    )
    ;;

  skills)
    # 動態生成，只包含通用 skills
    for skill in "${INCLUDE_SKILLS[@]}"; do
      if [ -d ".claude/skills/$skill" ]; then
        FILES+=(".claude/skills/$skill")
      fi
    done
    ;;

  docs)
    FILES=(
      ".claude/MCP-BEST-PRACTICES.md"
    )
    ;;

  config)
    FILES=(
      ".claude/statusline.sh"
      ".claude/mcp-tool-search.sh"
      ".claude/skills/shared/check-tool.sh"
      ".claude/MCP-BEST-PRACTICES.md"
    )
    ;;

  memory-bank)
    FILES=(
      ".claude/memory-bank/project-context/preferences.yaml"
      ".claude/memory-bank/project-context/decisions.yaml"
      ".claude/memory-bank/project-context/lessons-learned.yaml"
      ".claude/memory-bank/project-context/progress.yaml"
    )
    ;;

  all)
    # 組合所有類別
    ;;
esac
```

### Step 5: 過濾日期（如指定 --since）

```bash
if [ -n "$SINCE" ]; then
  # 使用 git log 找出指定日期後變更的文件
  CHANGED_FILES=$(git log --since="$SINCE" --name-only --pretty=format: | sort -u)

  # 只保留在 FILES 中且在 CHANGED_FILES 中的文件
  FILTERED_FILES=()
  for file in "${FILES[@]}"; do
    if echo "$CHANGED_FILES" | grep -q "$file"; then
      FILTERED_FILES+=("$file")
    fi
  done

  FILES=("${FILTERED_FILES[@]}")
fi
```

### Step 6: Dry-run 預覽（如指定）

```bash
if [ "$DRY_RUN" = true ]; then
  echo "=== 同步預覽 ==="
  echo "目標：$TARGET_PATH"
  echo "類別：$CATEGORY"
  echo ""
  echo "將要複製的文件："

  for file in "${FILES[@]}"; do
    echo "  $file"
  done

  echo ""
  echo "總計：${#FILES[@]} 個文件/目錄"
  echo ""
  echo "排除的專案特定內容："
  for skill in "${EXCLUDE_SKILLS[@]}"; do
    echo "  - $skill skill"
  done

  echo ""
  echo "移除 --dry-run 以實際執行"
  exit 0
fi
```

### Step 7: 執行文件複製

```bash
echo "=== 同步進行中 ==="

COPIED_COUNT=0

for file in "${FILES[@]}"; do
  SRC="$file"
  DST="$TARGET_PATH/$file"

  # 確保目標目錄存在
  mkdir -p "$(dirname "$DST")"

  # 複製文件/目錄
  if [ -d "$SRC" ]; then
    cp -r "$SRC" "$DST"
  elif [ -f "$SRC" ]; then
    cp "$SRC" "$DST"
  fi

  ((COPIED_COUNT++))
  echo "✓ $file"
done

echo ""
echo "=== 同步完成 ==="
echo "成功：$COPIED_COUNT 個文件/目錄"
```

### Step 8: 處理特殊文件

```bash
# 更新 CLAUDE.md 為通用版本
if [ -f "$TARGET_PATH/CLAUDE.md" ]; then
  # 使用 Read 讀取主專案的通用 CLAUDE.md 模板
  # 使用 Edit 或 Write 更新目標專案的 CLAUDE.md
  # 移除 Project 專案特定內容
fi

# 更新 SEARCH-INDEX.md
  # 移除專案特定文檔引用
fi

# 調整 preferences.yaml
if [ -f "$TARGET_PATH/.claude/memory-bank/project-context/preferences.yaml" ]; then
  # 移除 Project 專案特定配置
fi
```

### Step 9: 刪除多餘文件（如指定 --delete）

```bash
if [ "$DELETE_ORPHANS" = true ]; then
  echo "=== 掃描多餘文件 ==="

  DELETED_COUNT=0

  # --- Skills：刪除不在 INCLUDE_SKILLS 清單中的目錄 ---
  TARGET_SKILLS_DIR="$TARGET_PATH/.claude/skills"
  if [ -d "$TARGET_SKILLS_DIR" ]; then
    for target_skill_dir in "$TARGET_SKILLS_DIR"/*/; do
      skill_name=$(basename "$target_skill_dir")
      found=false
      for s in "${INCLUDE_SKILLS[@]}"; do
        [ "$s" = "$skill_name" ] && found=true && break
      done

      if [ "$found" = false ]; then
        echo "  [多餘] .claude/skills/$skill_name/"
        if [ "$DRY_RUN" = false ]; then
          rm -rf "$target_skill_dir"
          echo "  ✓ 已刪除"
          ((DELETED_COUNT++))
        fi
      fi
    done
  fi

  # --- Agents：刪除不在來源 atomic 目錄中的 agent ---
  TARGET_AGENTS_DIR="$TARGET_PATH/.claude/agents/atomic"
  SRC_AGENTS_DIR=".claude/agents/atomic"
  if [ -d "$TARGET_AGENTS_DIR" ] && [ -d "$SRC_AGENTS_DIR" ]; then
    for target_agent in "$TARGET_AGENTS_DIR"/*.md; do
      agent_name=$(basename "$target_agent")
      if [ ! -f "$SRC_AGENTS_DIR/$agent_name" ]; then
        echo "  [多餘] .claude/agents/atomic/$agent_name"
        if [ "$DRY_RUN" = false ]; then
          rm -f "$target_agent"
          echo "  ✓ 已刪除"
          ((DELETED_COUNT++))
        fi
      fi
    done
  fi

  # --- Hooks：不刪除（hooks 均為通用，無專案特定） ---

  if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "（dry-run）移除 --dry-run 以實際刪除"
  else
    echo ""
    echo "=== 清理完成 ==="
    echo "刪除：$DELETED_COUNT 個文件/目錄"
  fi
fi
```

### Step 11: 安裝 Git Hooks（如包含 hooks）

```bash
if [[ "$CATEGORY" == "hooks" || "$CATEGORY" == "all" ]]; then
  cd "$TARGET_PATH"
  bash setup/git-hooks/install-all.sh

  echo ""
  echo "Git Hooks 已安裝"
  echo "Claude Code Hooks 配置已同步至 .claude/settings.json"
fi
```

### Step 12: Git Commit（如指定 --auto-commit）

```bash
if [ "$AUTO_COMMIT" = true ]; then
  cd "$TARGET_PATH"

  git add -A

  # 生成 commit message
  COMMIT_MSG="feat: 從主專案同步通用特性（$(date +%Y-%m-%d)）

## 同步內容
$(generate_sync_summary)

## 排除內容
$(list_excluded_content)

## 同步來源
source-ai-agent
類別: $CATEGORY

Sync from: source-ai-agent"

  git commit -m "$COMMIT_MSG"

  echo "✓ Git commit 完成"
fi
```

### Step 13: Git Push（如指定 --auto-push）

```bash
if [ "$AUTO_PUSH" = true ]; then
  if [ "$AUTO_COMMIT" = false ]; then
    echo "錯誤：--auto-push 需要先啟用 --auto-commit"
    exit 1
  fi

  cd "$TARGET_PATH"
  git push

  echo "✓ Git push 完成"
fi
```

## 特殊處理邏輯

### CLAUDE.md 調整

```bash
# 讀取主專案的 fine-tune 版本 CLAUDE.md（如存在）
# 或使用模板生成

cat > "$TARGET_PATH/CLAUDE.md" << 'EOF'
# {Project Name}

> 通用 AI Agent 開發框架 + Atomic Agents 組合

## 快速開始

**使用自然語言即可**，所有角色功能透過 Agents/Skills 自動啟用。

---

## Atomic Agents 組合

```bash
/review-code         # 代碼審查
/write-tests         # 測試撰寫
/parallel-develop    # 並行開發規劃
```

詳細說明：@.claude/agents/atomic/README.md

---

## 核心規範

### 代碼搜索策略


### 核心禁止

- ❌ Commit 訊息包含 AI 標記
- ❌ 代碼搜索優先用 Grep

---

[其他章節...]
EOF
```

### preferences.yaml 調整

```yaml
# 移除 Project 專案特定配置，保留通用配置

global:
  language: "zh-TW"
  output_language: "zh-TW"

  development_workflow:
    code_search_strategy:
      priority:
        - "ast-grep"
        - "code-searcher"
        - "grep"
```

## 測試驗證

### 同步後測試清單

```bash
# 1. Git Hooks 測試（如包含 hooks）
cd $TARGET_PATH
# Git Hooks 已透過 setup/git-hooks/install-all.sh 安裝
# Claude Code Hooks 配置在 .claude/settings.json

# 2. Skills 可用性測試
# 測試幾個關鍵 skills
# /docs
# /write-tests
# /review-code

# 3. Atomic Agents 架構完整性
ls -la .claude/agents/atomic/

# 4. 文檔索引測試
```

## 錯誤處理範例

```bash
# 處理文件衝突
handle_conflict() {
  local src=$1
  local dst=$2

  if [ -f "$dst" ]; then
    # 比較文件差異
    if ! diff -q "$src" "$dst" > /dev/null; then
      echo "衝突：$dst 已存在且內容不同"
      echo "選項："
      echo "  1. 覆蓋"
      echo "  2. 跳過"
      echo "  3. 備份後覆蓋"

      # 等待用戶選擇（在主會話中互動）
    fi
  fi
}

# 處理權限錯誤
handle_permission_error() {
  echo "錯誤：無法寫入目標目錄"
  echo "請檢查權限：ls -la $(dirname $TARGET_PATH)"
}
```

## 完整範例腳本

參考實際執行時的完整 Bash 腳本邏輯（見實作時的 Bash 命令組合）

## 維護建議

### 定期更新排除規則

隨著主專案新增專案特定內容，需要更新：
- `EXCLUDE_SKILLS` 列表
- 特殊處理邏輯

### 版本追蹤

在主專案維護同步歷史：
```
.claude/skills/project-sync/SYNC-HISTORY.md

# 同步歷史

## 2026-01-25: fine-tune-ai-agent
- 同步類別: all
- 文件數: 101 files
- 主要特性: Atomic Agents v4.0, Git Hooks, Skills 模型配置

## 2026-01-XX: another-project
...
```

## 相關資源

- [Atomic Agents 架構](@.claude/agents/atomic/README.md)
- [Git Hooks 文檔](@.claude/hooks/README.md)
- [Skills 列表](@.claude/skills/)
- [同步總結範例](/tmp/sync-summary.md)
