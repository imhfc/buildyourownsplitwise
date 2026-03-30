#!/bin/bash
#
# 檢查 Worktree 分支的 Commit 訊息合規性
#
# 使用方式：
#   ./check-worktree-commits.sh <worktree_base> <branch1> <branch2> ...
#
# 範例：
#   ./check-worktree-commits.sh /path/to/worktrees fix/branch1 fix/branch2

set -e

if [ $# -lt 2 ]; then
  echo "使用方式: $0 <worktree_base> <branch1> [branch2] ..."
  echo ""
  echo "範例："
  echo "  $0 ../crm-worktrees fix/p0-csv-header fix/p0-index-bounds"
  exit 1
fi

WORKTREE_BASE="$1"
shift
BRANCHES=("$@")

echo "=========================================="
echo "檢查 Worktree Commit 訊息合規性"
echo "=========================================="
echo ""

violations=0
total_checked=0

for branch in "${BRANCHES[@]}"; do
  total_checked=$((total_checked + 1))

  echo ">>> 檢查分支: $branch"

  branch_path="$WORKTREE_BASE/$branch"
  if [ ! -d "$branch_path" ]; then
    echo "  ⚠️  Worktree 不存在: $branch_path"
    echo ""
    continue
  fi

  cd "$branch_path" || continue

  # 獲取最新 commit 訊息
  commit_msg=$(git log -1 --pretty=format:"%B")
  commit_hash=$(git log -1 --pretty=format:"%h")

  echo "  Commit: $commit_hash"

  # 檢查 AI 標記
  if echo "$commit_msg" | grep -qi "co-authored-by.*claude\|co-authored-by.*gpt\|co-authored-by.*ai\|\[AI\]\|\[Claude\]\|\[GPT\]"; then
    echo "  ❌ 違規：含 AI 標記"
    violations=$((violations + 1))
  else
    echo "  ✅ 通過：無 AI 標記"
  fi

  # 檢查 Conventional Commits 格式
  first_line=$(echo "$commit_msg" | head -1)
  if ! echo "$first_line" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert|merge)(\(.+\))?: .+'; then
    echo "  ⚠️  建議：使用 Conventional Commits 格式"
  fi

  echo ""
done

echo "=========================================="
echo "檢查完成"
echo "=========================================="
echo ""
echo "總計檢查：$total_checked 個分支"
echo "發現違規：$violations 個"
echo ""

if [ $violations -gt 0 ]; then
  echo "❌ 有違規項目需要修正"
  echo ""
  echo "修正方法："
  echo "  cd $WORKTREE_BASE/<branch>"
  echo "  git commit --amend"
  echo "  # 移除 Co-Authored-By: Claude 行"
  exit 1
else
  echo "✅ 所有分支通過檢查"
  exit 0
fi
