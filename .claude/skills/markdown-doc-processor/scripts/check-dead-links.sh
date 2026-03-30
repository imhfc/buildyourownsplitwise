#!/bin/bash
# 檢查 Markdown 文件中的死連結

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 統計變數
total_files=0
total_links=0
broken_links=0

# 輸出檔案
output_file=".claude/skills/markdown-doc-processor/scripts/dead-links-report.txt"
> "$output_file"  # 清空檔案

echo "檢查 Markdown 文件中的死連結..."
echo "======================================"
echo ""

# 找出所有需要檢查的 Markdown 文件
files=$(find . -type f -name "*.md" | grep -E "(ai-docs|claude|gemini|github|agent)" | grep -v node_modules | grep -v ".git/")

for file in $files; do
    total_files=$((total_files + 1))

    # 提取所有 Markdown 連結 [text](path)
    # 排除 http/https 連結，只檢查本地文件連結
    links=$(grep -oP '\[.*?\]\(\K[^)]+' "$file" | grep -v "^http" | grep -v "^#" || true)

    if [ -n "$links" ]; then
        while IFS= read -r link; do
            total_links=$((total_links + 1))

            # 取得文件所在目錄
            file_dir=$(dirname "$file")

            # 處理連結（移除錨點）
            clean_link=$(echo "$link" | sed 's/#.*//')

            # 跳過空連結
            if [ -z "$clean_link" ]; then
                continue
            fi

            # 解析相對路徑
            if [[ "$clean_link" == /* ]]; then
                # 絕對路徑（從專案根目錄）
                target_path=".${clean_link}"
            else
                # 相對路徑
                target_path="${file_dir}/${clean_link}"
            fi

            # 標準化路徑
            target_path=$(realpath -m "$target_path" 2>/dev/null || echo "$target_path")

            # 檢查檔案是否存在
            if [ ! -e "$target_path" ]; then
                broken_links=$((broken_links + 1))
                echo -e "${RED}✗${NC} 死連結: $file"
                echo "  └─ [$link]"
                echo "  └─ 目標不存在: $target_path"
                echo ""

                # 寫入報告
                echo "死連結: $file" >> "$output_file"
                echo "  原始連結: $link" >> "$output_file"
                echo "  目標路徑: $target_path" >> "$output_file"
                echo "" >> "$output_file"
            fi
        done <<< "$links"
    fi
done

# 輸出統計
echo "======================================"
echo "統計結果:"
echo "  - 檢查文件數: $total_files"
echo "  - 總連結數: $total_links"
echo -e "  - 死連結數: ${RED}$broken_links${NC}"
echo ""

if [ $broken_links -eq 0 ]; then
    echo -e "${GREEN}✓ 沒有發現死連結！${NC}"
else
    echo -e "${YELLOW}發現 $broken_links 個死連結${NC}"
    echo "  詳細報告: $output_file"
fi
