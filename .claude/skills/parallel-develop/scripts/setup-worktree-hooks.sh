#!/bin/bash
#
# 為所有 Worktree 配置完整的 Git Hooks
#
# 功能：
# 1. 配置 Git core.hooksPath 讓所有 worktree 共用 hooks
# 2. 為每個 worktree 創建 hooks 符號連結（備用方案）
# 3. 驗證所有 hooks 可執行
#
# 使用方式：
#   ./setup-worktree-hooks.sh <main_repo> [worktree_base]
#
# 範例：
#   ./setup-worktree-hooks.sh /path/to/Service_custr-relationship-mgmt /path/to/crm-worktrees

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# 參數處理
# ============================================

if [ $# -lt 1 ]; then
  echo "使用方式: $0 <main_repo> [worktree_base]"
  echo ""
  echo "範例："
  echo "  $0 /Users/Shared/Work/Projects/Service_custr-relationship-mgmt"
  echo "  $0 /Users/Shared/Work/Projects/Service_custr-relationship-mgmt /Users/Shared/Work/Projects/crm-worktrees"
  exit 1
fi

MAIN_REPO="$1"
WORKTREE_BASE="${2:-}"

# 驗證主倉庫
if [ ! -d "$MAIN_REPO/.git" ]; then
  echo -e "${RED}❌ 錯誤：$MAIN_REPO 不是有效的 Git 倉庫${NC}"
  exit 1
fi

cd "$MAIN_REPO"

echo -e "${BLUE}=========================================="
echo "配置 Worktree Git Hooks"
echo -e "==========================================${NC}"
echo ""

# ============================================
# 方案 1：配置 core.hooksPath（推薦）
# ============================================

echo -e "${BLUE}>>> 方案 1：配置 core.hooksPath${NC}"

# 取得 hooks 的絕對路徑
HOOKS_PATH="$MAIN_REPO/.git/hooks"

# 檢查 hooks 目錄是否存在
if [ ! -d "$HOOKS_PATH" ]; then
  echo -e "${RED}❌ Hooks 目錄不存在: $HOOKS_PATH${NC}"
  exit 1
fi

# 配置 Git 使用絕對路徑的 hooks
git config --local core.hooksPath "$HOOKS_PATH"

echo -e "${GREEN}✓ 已配置 core.hooksPath = $HOOKS_PATH${NC}"
echo ""

# 驗證配置
current_hooks_path=$(git config --local --get core.hooksPath || echo "")
if [ "$current_hooks_path" = "$HOOKS_PATH" ]; then
  echo -e "${GREEN}✓ 配置驗證成功${NC}"
else
  echo -e "${YELLOW}⚠️  配置可能未生效，當前值: $current_hooks_path${NC}"
fi

echo ""

# ============================================
# 方案 2：為每個 Worktree 設置（備用）
# ============================================

if [ -n "$WORKTREE_BASE" ] && [ -d "$WORKTREE_BASE" ]; then
  echo -e "${BLUE}>>> 方案 2：為每個 Worktree 配置 hooks${NC}"
  echo ""

  # 列出所有 worktree
  worktrees=$(git worktree list --porcelain | grep "^worktree " | cut -d' ' -f2)

  worktree_count=0
  for worktree_path in $worktrees; do
    # 跳過主倉庫
    if [ "$worktree_path" = "$MAIN_REPO" ]; then
      continue
    fi

    worktree_count=$((worktree_count + 1))

    echo -e "${BLUE}處理 Worktree: $worktree_path${NC}"

    # 檢查 worktree 是否存在
    if [ ! -d "$worktree_path" ]; then
      echo -e "${YELLOW}  ⚠️  Worktree 不存在，跳過${NC}"
      continue
    fi

    cd "$worktree_path"

    # 配置此 worktree 的 core.hooksPath
    git config --local core.hooksPath "$HOOKS_PATH"

    echo -e "${GREEN}  ✓ 已配置 hooks 路徑${NC}"
    echo ""
  done

  if [ $worktree_count -eq 0 ]; then
    echo -e "${YELLOW}未發現額外的 worktree${NC}"
  else
    echo -e "${GREEN}✓ 已配置 $worktree_count 個 worktree${NC}"
  fi
else
  echo -e "${YELLOW}未提供 worktree_base，跳過方案 2${NC}"
fi

echo ""

# ============================================
# 驗證所有 Hooks 可執行
# ============================================

echo -e "${BLUE}>>> 驗證 Hooks 可執行權限${NC}"
echo ""

cd "$MAIN_REPO"

hooks_found=0
hooks_executable=0

for hook_file in "$HOOKS_PATH"/*; do
  # 跳過 .sample 檔案和目錄
  if [[ "$hook_file" == *.sample ]] || [ -d "$hook_file" ]; then
    continue
  fi

  # 跳過非檔案
  if [ ! -f "$hook_file" ]; then
    continue
  fi

  hooks_found=$((hooks_found + 1))
  hook_name=$(basename "$hook_file")

  # 檢查是否可執行
  if [ -x "$hook_file" ]; then
    echo -e "${GREEN}✓ $hook_name${NC} (可執行)"
    hooks_executable=$((hooks_executable + 1))
  else
    echo -e "${YELLOW}⚠️  $hook_name${NC} (不可執行，正在修正...)"
    chmod +x "$hook_file"
    echo -e "${GREEN}  ✓ 已設置執行權限${NC}"
    hooks_executable=$((hooks_executable + 1))
  fi
done

echo ""
echo -e "${GREEN}找到 $hooks_found 個 hooks，$hooks_executable 個可執行${NC}"
echo ""

# ============================================
# 列出所有可用的 Hooks
# ============================================

echo -e "${BLUE}>>> 可用的 Git Hooks:${NC}"
echo ""

for hook_file in "$HOOKS_PATH"/*; do
  if [[ "$hook_file" == *.sample ]] || [ -d "$hook_file" ] || [ ! -f "$hook_file" ]; then
    continue
  fi

  hook_name=$(basename "$hook_file")

  # 讀取第一行註釋作為描述
  description=$(head -5 "$hook_file" | grep -E "^#.*用途|^#.*功能" | head -1 | sed 's/^#[[:space:]]*//' || echo "")

  if [ -n "$description" ]; then
    echo -e "${GREEN}✓ $hook_name${NC}"
    echo -e "  ${description}"
  else
    echo -e "${GREEN}✓ $hook_name${NC}"
  fi
  echo ""
done

# ============================================
# 測試 Hooks（可選）
# ============================================

echo -e "${BLUE}>>> 測試建議${NC}"
echo ""
echo "您可以執行以下命令測試 hooks："
echo ""
echo "  # 測試 pre-commit"
echo "  git commit --allow-empty -m 'test' --dry-run"
echo ""
echo "  # 測試 commit-msg"
echo "  echo 'test commit' | git commit --allow-empty -F -"
echo ""
echo "  # 執行完整測試套件"
echo "  cd $MAIN_REPO"
echo "  .git/hooks/test-hooks.sh"
echo ""

# ============================================
# 生成驗證報告
# ============================================

echo -e "${BLUE}=========================================="
echo "配置完成"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ Core.hooksPath 配置完成${NC}"
echo -e "  路徑: $HOOKS_PATH"
echo ""
echo -e "${GREEN}✓ 所有 hooks 可執行${NC}"
echo -e "  共 $hooks_executable 個 hooks"
echo ""

if [ -n "$WORKTREE_BASE" ]; then
  echo -e "${GREEN}✓ Worktree hooks 配置完成${NC}"
  echo -e "  共 $worktree_count 個 worktree"
  echo ""
fi

echo "所有 Git Worktree 現在都會使用這些 hooks："
echo ""
git worktree list
echo ""

# ============================================
# 下一步建議
# ============================================

echo -e "${BLUE}下一步建議：${NC}"
echo ""
echo "1. 測試 hooks 是否正常工作："
echo "   cd $MAIN_REPO/.git/hooks"
echo "   ./test-hooks.sh"
echo ""
echo "2. 在 worktree 中測試 commit："
echo "   cd <worktree_path>"
echo "   # 嘗試提交一些測試變更"
echo ""
echo "3. 如果需要更新 hooks，在主倉庫更新後，所有 worktree 會自動使用新版本"
echo ""
