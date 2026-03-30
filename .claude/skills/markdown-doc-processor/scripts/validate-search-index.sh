#!/bin/bash

# 索引驗證腳本
# 功能: 檢查 SEARCH-INDEX.md 中所有連結的檔案是否存在
# 版本: 1.0 (2026-01-27)

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 工作目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEARCH_INDEX="$PROJECT_ROOT/.ai-docs/SEARCH-INDEX.md"

# 檢查 SEARCH-INDEX.md 是否存在
if [ ! -f "$SEARCH_INDEX" ]; then
    echo -e "${RED}錯誤: 找不到 SEARCH-INDEX.md${NC}"
    exit 1
fi

echo "========================================="
echo "開始驗證 SEARCH-INDEX.md 中的連結"
echo "========================================="
echo ""

# 提取所有 .md 和 .yaml 連結
# 排除外部連結（../.claude/）
missing_files=()
checked_files=0
valid_files=0

# 使用 grep 提取所有相對路徑（./ 開頭）
while IFS= read -r line; do
    # 提取 [text](./path) 格式的連結
    if [[ $line =~ \]\((\.\/[^\)]+)\) ]]; then
        rel_path="${BASH_REMATCH[1]}"

        # 移除 ./ 前綴
        clean_path="${rel_path#./}"

        # 解析相對路徑為絕對路徑
        full_path="$PROJECT_ROOT/.ai-docs/$clean_path"

        checked_files=$((checked_files + 1))

        if [ -f "$full_path" ] || [ -d "$full_path" ]; then
            valid_files=$((valid_files + 1))
            echo -e "${GREEN}✓${NC} $rel_path"
        else
            missing_files+=("$rel_path")
            echo -e "${RED}✗${NC} $rel_path (檔案不存在)"
        fi
    fi
done < "$SEARCH_INDEX"

# 檢查 ../.claude/ 連結
while IFS= read -r line; do
    if [[ $line =~ \]\(\.\.\/\.claude\/([^\)]+)\) ]]; then
        rel_path="../.claude/${BASH_REMATCH[1]}"
        full_path="$PROJECT_ROOT/.claude/${BASH_REMATCH[1]}"

        checked_files=$((checked_files + 1))

        if [ -f "$full_path" ] || [ -d "$full_path" ]; then
            valid_files=$((valid_files + 1))
            echo -e "${GREEN}✓${NC} $rel_path"
        else
            missing_files+=("$rel_path")
            echo -e "${RED}✗${NC} $rel_path (檔案不存在)"
        fi
    fi
done < "$SEARCH_INDEX"

echo ""
echo "========================================="
echo "驗證結果摘要"
echo "========================================="
echo "檢查檔案總數: $checked_files"
echo -e "${GREEN}有效檔案: $valid_files${NC}"
echo -e "${RED}缺失檔案: ${#missing_files[@]}${NC}"
echo ""

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "${RED}以下檔案不存在:${NC}"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    echo ""
    exit 1
else
    echo -e "${GREEN}所有連結驗證通過！${NC}"
    exit 0
fi
