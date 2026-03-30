#!/bin/bash

# 版本標記格式遷移腳本
# 功能: 批次更新檔案的版本標記格式至統一標準
# 版本: 1.0 (2026-01-27) - 初始版本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 工作目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 統計
total_files=0
updated_files=0
skipped_files=0

echo "========================================="
echo "版本標記格式遷移工具"
echo "========================================="
echo ""
echo "規範格式："
echo "  Markdown: **版本**: X.X.X (YYYY-MM-DD)"
echo "  YAML:     # 版本: X.X.X (YYYY-MM-DD)"
echo "  Shell:    # 版本: X.X.X (YYYY-MM-DD)"
echo ""
echo "開始掃描..."
echo ""

# 函數: 修正全形冒號
fix_fullwidth_colon() {
    local file="$1"
    local updated=false

    # 檢查是否包含全形冒號
    if grep -q "版本：" "$file"; then
        sed -i '' 's/版本：/版本:/g' "$file"
        updated=true
        echo -e "${GREEN}✓${NC} $file: 修正全形冒號"
    fi

    echo "$updated"
}

# 函數: 處理 Markdown 檔案
process_markdown() {
    local file="$1"

    # 檢查是否有版本標記
    if ! head -10 "$file" | grep -q "版本"; then
        return 1
    fi

    # 修正全形冒號
    local fixed=$(fix_fullwidth_colon "$file")

    # 檢查格式是否符合規範
    if ! head -10 "$file" | grep -qE '\*\*版本\*\*: [0-9]+\.[0-9]+(\.[0-9]+)? \([0-9]{4}-[0-9]{2}-[0-9]{2}\)'; then
        # 嘗試修正格式
        # 模式 1: > 版本: X.X → **版本**: X.X
        if head -10 "$file" | grep -qE '> 版本: [0-9]+\.[0-9]+'; then
            sed -i '' 's/> 版本: \([0-9]\+\.[0-9]\+\)/\*\*版本\*\*: \1/g' "$file"
            echo -e "${GREEN}✓${NC} $file: 修正格式 (> 版本 → **版本**)"
            return 0
        fi

        # 模式 2: ## v X.X → **版本**: X.X
        if head -10 "$file" | grep -qE '## v [0-9]+\.[0-9]+'; then
            # 需要更複雜的處理，暫時跳過
            echo -e "${YELLOW}!${NC} $file: 需要手動修正 (章節標題格式)"
            return 1
        fi

        echo -e "${YELLOW}!${NC} $file: 格式不符合規範，需要手動檢查"
        return 1
    fi

    if [ "$fixed" = "true" ]; then
        return 0
    fi

    return 1
}

# 函數: 處理 YAML 檔案
process_yaml() {
    local file="$1"

    # 檢查是否有版本標記
    if ! head -10 "$file" | grep -q "版本"; then
        return 1
    fi

    # 修正全形冒號
    local fixed=$(fix_fullwidth_colon "$file")

    # 檢查格式是否符合規範
    if ! head -10 "$file" | grep -qE '# 版本: [0-9]+\.[0-9]+(\.[0-9]+)? \([0-9]{4}-[0-9]{2}-[0-9]{2}\)'; then
        echo -e "${YELLOW}!${NC} $file: 格式不符合規範，需要手動檢查"
        return 1
    fi

    if [ "$fixed" = "true" ]; then
        return 0
    fi

    return 1
}

# 函數: 處理 Shell 腳本
process_shell() {
    local file="$1"

    # 檢查是否有版本標記
    if ! head -10 "$file" | grep -q "版本"; then
        return 1
    fi

    # 修正全形冒號
    local fixed=$(fix_fullwidth_colon "$file")

    # 檢查格式是否符合規範
    if ! head -10 "$file" | grep -qE '# 版本: [0-9]+\.[0-9]+(\.[0-9]+)? \([0-9]{4}-[0-9]{2}-[0-9]{2}\)'; then
        echo -e "${YELLOW}!${NC} $file: 格式不符合規範，需要手動檢查"
        return 1
    fi

    if [ "$fixed" = "true" ]; then
        return 0
    fi

    return 1
}

# 掃描並處理檔案

# 處理 Markdown 檔案
echo -e "${BLUE}處理 Markdown 檔案...${NC}"
while IFS= read -r file; do
    total_files=$((total_files + 1))

    # 跳過知識型文檔
    if [[ "$file" =~ /knowledge/universal/adr/|/knowledge/universal/patterns/|/knowledge/universal/guides/ ]]; then
        continue
    fi

    if process_markdown "$file"; then
        updated_files=$((updated_files + 1))
    else
        skipped_files=$((skipped_files + 1))
    fi
done < <(find "$PROJECT_ROOT/.ai-docs" "$PROJECT_ROOT/.claude" -name "*.md" -type f)

# 處理 YAML 檔案
echo ""
echo -e "${BLUE}處理 YAML 檔案...${NC}"
while IFS= read -r file; do
    total_files=$((total_files + 1))

    if process_yaml "$file"; then
        updated_files=$((updated_files + 1))
    else
        skipped_files=$((skipped_files + 1))
    fi
done < <(find "$PROJECT_ROOT/.claude/memory-bank" -name "*.yaml" -o -name "*.yml")

# 處理 Shell 腳本
echo ""
echo -e "${BLUE}處理 Shell 腳本...${NC}"
while IFS= read -r file; do
    total_files=$((total_files + 1))

    if process_shell "$file"; then
        updated_files=$((updated_files + 1))
    else
        skipped_files=$((skipped_files + 1))
    fi
done < <(find "$PROJECT_ROOT/.claude/hooks" -name "*.sh" -type f)

echo ""
echo "========================================="
echo "遷移結果摘要"
echo "========================================="
echo "掃描檔案總數: $total_files"
echo -e "${GREEN}已更新檔案: $updated_files${NC}"
echo -e "${YELLOW}跳過檔案: $skipped_files${NC}"
echo ""

if [ $updated_files -gt 0 ]; then
    echo -e "${GREEN}遷移完成！${NC}"
    echo ""
    echo "建議執行以下命令檢查變更："
    echo "  git diff"
    echo ""
    echo "確認無誤後可以 commit："
    echo "  git add -A"
    echo "  git commit -m 'docs: 統一版本標記格式'"
else
    echo -e "${GREEN}所有檔案已符合規範！${NC}"
fi
