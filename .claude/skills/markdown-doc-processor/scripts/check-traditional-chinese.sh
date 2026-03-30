#!/bin/bash
# 檢查專案中是否有簡體中文
# 用途：確保所有程式碼和文檔僅使用繁體中文（ADR-014）

set -e

# 簡體中文特有字符清單（從 ADR-014）
# 注意：僅包含簡體特有字，不包含繁簡共用字
SIMPLIFIED_CHARS="设计认证获标识录记据库显实验响应户请参类处执创复杂结构统维态错误义业东两门马书长车风飞鱼鸟龙开关发现机过给当进让头将无话经电间见听学"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 計數器
ERROR_COUNT=0
FILE_COUNT=0

echo "檢查簡體中文..."
echo "================================================"

# 檢查函數
check_file() {
    local file=$1
    local file_type=$2

    if grep -q "[$SIMPLIFIED_CHARS]" "$file"; then
        echo -e "${RED}發現簡體中文: $file${NC}"
        echo "   前 5 處簡體字："
        grep -n "[$SIMPLIFIED_CHARS]" "$file" | head -5 | while read line; do
            echo "   $line"
        done
        echo ""
        ((ERROR_COUNT++))
    fi
    ((FILE_COUNT++))
}

# 檢查 Java 檔案
echo "📂 檢查 Java 源碼..."
if [ -d "services" ]; then
    find services/*/src -name "*.java" -type f 2>/dev/null | while read file; do
        check_file "$file" "Java"
    done
fi

# 檢查 Markdown 檔案
echo "📂 檢查 Markdown 文檔..."
if [ -d ".ai-docs" ]; then
    find .ai-docs -name "*.md" -type f 2>/dev/null | while read file; do
        check_file "$file" "Markdown"
    done
fi

# 檢查 CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    check_file "CLAUDE.md" "Markdown"
fi

echo "================================================"
if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}檢查完成：未發現簡體中文${NC}"
    echo "檢查檔案數：$FILE_COUNT"
    exit 0
else
    echo -e "${RED}檢查失敗：發現 $ERROR_COUNT 個檔案包含簡體中文${NC}"
    echo "請依據 ADR-014 規範改用繁體中文"
    exit 1
fi
