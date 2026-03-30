#!/usr/bin/env bash
# 工具可用性檢查與安裝提示腳本
# 版本：1.1

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢測是否為互動式終端
IS_INTERACTIVE=true
if [ ! -t 0 ] || [ ! -t 1 ]; then
    IS_INTERACTIVE=false
fi

# 全局參數
AUTO_YES=false

# 使用方式
usage() {
    cat << EOF
Usage: $0 [options] <tool-name>

Options:
  -y, --yes    自動確認安裝提示（非互動模式）
  -h, --help   顯示此說明

Examples:
  $0 ast-grep           # 檢查 ast-grep（互動式）
  $0 -y ast-grep        # 檢查並自動安裝 ast-grep
EOF
    exit 1
}

# 解析參數
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            AUTO_YES=true
            IS_INTERACTIVE=false
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo -e "${RED}未知參數: $1${NC}"
            usage
            ;;
        *)
            TOOL_NAME="$1"
            shift
            ;;
    esac
done

# 檢查是否提供工具名稱
if [ -z "$TOOL_NAME" ]; then
    echo -e "${RED}錯誤：未指定工具名稱${NC}"
    usage
fi

# 工具安裝指令映射
get_install_command() {
    case "$1" in
        ast-grep)
            echo "npm install -g @ast-grep/cli"
            ;;
        ImageMagick|convert)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "brew install imagemagick"
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                echo "sudo apt-get install imagemagick"
            else
                echo "請參考: https://imagemagick.org/script/download.php"
            fi
            ;;
        *)
            echo "Unknown tool"
            ;;
    esac
}

# 工具描述映射
get_tool_description() {
    case "$1" in
        ast-grep)
            echo "AST-based structural code search tool"
            ;;
        ImageMagick|convert)
            echo "Image manipulation tool"
            ;;
        *)
            echo "External tool"
            ;;
    esac
}

# 檢查工具是否已安裝
check_tool() {
    local tool="$1"

    if command -v "$tool" &> /dev/null; then
        local version=$(eval "$tool --version 2>&1" | head -n1)
        echo -e "${GREEN}✓${NC} $tool 已安裝: ${BLUE}$version${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} $tool 未安裝"
        return 1
    fi
}

# 主檢查邏輯
main() {
    local tool="$TOOL_NAME"
    local description=$(get_tool_description "$tool")

    echo -e "${BLUE}[Tool Check]${NC} 檢查 $tool ($description)..."
    echo ""

    if check_tool "$tool"; then
        exit 0
    else
        echo ""
        echo -e "${YELLOW}$tool 未安裝，但此任務需要此工具${NC}"
        echo ""
        echo -e "${BLUE}安裝指令:${NC}"
        local install_cmd=$(get_install_command "$tool")
        echo -e "  ${GREEN}$install_cmd${NC}"
        echo ""

        # 詢問是否自動安裝（支援非互動模式）
        local should_install=false

        if [ "$IS_INTERACTIVE" = true ] && [ "$AUTO_YES" = false ]; then
            read -p "是否現在安裝? (y/N): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                should_install=true
            fi
        elif [ "$AUTO_YES" = true ]; then
            echo -e "${BLUE}自動安裝模式啟用${NC}"
            should_install=true
        else
            echo -e "${YELLOW}非互動模式，跳過安裝（使用 -y 強制安裝）${NC}"
        fi

        if [ "$should_install" = true ]; then
            echo -e "${BLUE}正在安裝 $tool...${NC}"
            eval "$install_cmd"

            if check_tool "$tool"; then
                echo -e "${GREEN}✓ 安裝成功！${NC}"
                exit 0
            else
                echo -e "${RED}✗ 安裝失敗，請手動安裝${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}跳過安裝。請手動安裝後再試。${NC}"
            exit 1
        fi
    fi
}

main
