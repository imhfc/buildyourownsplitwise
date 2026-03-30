#!/bin/bash

# Git 衝突解決輔助工具
# 用途：檢測、分析和解決 Git 衝突
# 版本：1.0
# 使用方式：
#   ./conflict-resolver.sh --detect                    # 檢測當前衝突
#   ./conflict-resolver.sh --analyze [file]            # 分析單個檔案衝突
#   ./conflict-resolver.sh --resolve [file] [strategy] # 解決衝突

set -e

# 取得腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

# 載入錯誤處理函數
source "$SCRIPT_DIR/lib/error-handler.sh"

# ============================================================================
# 顏色定義
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# 幫助文檔
# ============================================================================
show_help() {
    cat << EOF
Git 衝突解決輔助工具

用法：
  $(basename "$0") --detect                    # 檢測當前衝突
  $(basename "$0") --analyze [file]            # 分析單個檔案衝突
  $(basename "$0") --resolve [file] [strategy] # 解決衝突

選項：
  --detect                  檢測當前是否有衝突，列出所有衝突檔案和複雜度
  --analyze [file]          分析指定檔案的衝突詳情，包括衝突標記位置和內容
  --resolve [file] [stg]    解決指定檔案的衝突
                            策略：ours（保留我們的版本）
                                  theirs（保留他們的版本）
                                  manual（標記為已手動解決）
  --help                    顯示此幫助訊息

範例：
  # 檢測衝突
  ./conflict-resolver.sh --detect

  # 分析 UserService.java 的衝突
  ./conflict-resolver.sh --analyze src/UserService.java

  # 使用 ours 策略解決 pom.xml 衝突
  ./conflict-resolver.sh --resolve pom.xml ours

  # 標記檔案為已手動解決
  ./conflict-resolver.sh --resolve src/Service.java manual

EOF
}

# ============================================================================
# 日誌函數
# ============================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_title() {
    echo -e "\n${CYAN}=== $1 ===${NC}\n"
}

# ============================================================================
# 檔案複雜度判斷
# ============================================================================
get_conflict_complexity() {
    local file="$1"
    local marker_count=$(grep -c "^<<<<<<< HEAD" "$file" 2>/dev/null || echo 0)

    # 根據衝突標記數量判斷複雜度
    if [[ $marker_count -le 1 ]]; then
        echo "low"
    elif [[ $marker_count -le 3 ]]; then
        echo "medium"
    else
        echo "high"
    fi
}

# ============================================================================
# 檢測衝突
# ============================================================================
detect_conflicts() {
    log_title "檢測衝突"

    # 檢查是否有未解決的衝突
    local conflict_files=$(git diff --name-only --diff-filter=U 2>/dev/null || true)

    if [[ -z "$conflict_files" ]]; then
        log_success "沒有檢測到衝突"
        echo ""
        echo "YAML 輸出："
        cat << EOF
conflicts:
  status: "no_conflicts"
  count: 0
  files: []
  suggestion: "工作區乾淨，沒有待解決的衝突"
EOF
        return 0
    fi

    log_warning "檢測到衝突"
    echo ""

    # 統計衝突檔案
    local total_files=$(echo "$conflict_files" | wc -l)

    echo "YAML 輸出："
    echo "conflicts:"
    echo "  status: \"has_conflicts\""
    echo "  count: $total_files"
    echo "  files:"

    # 分析每個衝突檔案
    while IFS= read -r file; do
        if [[ -z "$file" ]]; then
            continue
        fi

        # 計算衝突標記數量
        local markers=$(grep -c "^<<<<<<< HEAD" "$file" 2>/dev/null || echo 0)

        # 計算我們的和他們的變更行數
        local ours_lines=$(sed -n '/^<<<<<<< HEAD/,/^=======/p' "$file" | wc -l)
        local theirs_lines=$(sed -n '/^=======/,/^>>>>>>>/p' "$file" | wc -l)

        local complexity=$(get_conflict_complexity "$file")

        echo "    - file: \"$file\""
        echo "      conflict_markers: $markers"
        echo "      ours_changes: \"+$ours_lines lines\""
        echo "      theirs_changes: \"+$theirs_lines lines\""
        echo "      complexity: \"$complexity\""
    done <<< "$conflict_files"

    # 提供建議
    echo "  suggestion: \"建議先解決簡單檔案（複雜度 low），再處理複雜檔案\""

    return 0
}

# ============================================================================
# 提取衝突範圍
# ============================================================================
extract_conflict_ranges() {
    local file="$1"
    local temp_file="$2"

    local line_num=0
    local marker_index=0
    local in_conflict=false
    local conflict_start=0
    local separator_line=0

    # 逐行讀取檔案並提取衝突
    while IFS= read -r line; do
        ((line_num++))

        # 檢測衝突開始
        if [[ "$line" == "<<<<<<< HEAD" ]]; then
            in_conflict=true
            conflict_start=$line_num
            ((marker_index++))
            echo "    - index: $marker_index" >> "$temp_file"
            echo "      start_line: $conflict_start" >> "$temp_file"
        fi

        # 檢測分隔符
        if [[ "$line" == "=======" ]] && [[ "$in_conflict" == true ]]; then
            separator_line=$line_num
            echo "      separator_line: $separator_line" >> "$temp_file"
        fi

        # 檢測衝突結束
        if [[ "$line" == ">>>>>>> "* ]]; then
            in_conflict=false
            local conflict_end=$line_num
            echo "      end_line: $conflict_end" >> "$temp_file"
            echo "      size_lines: $((conflict_end - conflict_start + 1))" >> "$temp_file"
        fi
    done < "$file"
}

# ============================================================================
# 分析單個檔案的衝突
# ============================================================================
analyze_conflict() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        log_error "檔案不存在：$file"
        exit 1
    fi

    # 檢查檔案是否有衝突
    if ! grep -q "^<<<<<<< HEAD" "$file" 2>/dev/null; then
        log_warning "檔案 $file 中沒有衝突標記"
        return 0
    fi

    log_title "分析衝突：$file"

    echo "YAML 輸出："
    echo "conflict_analysis:"
    echo "  file: \"$file\""
    echo "  markers:"

    # 建立臨時檔案儲存衝突範圍
    local temp_file=$(mktemp)
    extract_conflict_ranges "$file" "$temp_file"
    cat "$temp_file"
    rm -f "$temp_file"

    # 檢查檔案類型以提供建議
    local file_extension="${file##*.}"
    echo "  file_type: \"$file_extension\""

    # 根據檔案類型提供建議
    case "$file_extension" in
        "xml"|"yaml"|"json"|"properties")
            echo "  recommendation: \"此為配置檔案，衝突通常為簡單的屬性值衝突。建議檢查兩個版本的關鍵屬性差異。\""
            ;;
        "java"|"js"|"py"|"sh")
            echo "  recommendation: \"此為代碼檔案，衝突可能涉及邏輯變更。建議仔細比較兩個版本的代碼邏輯，選擇更合理的實現。\""
            ;;
        *)
            echo "  recommendation: \"請手動檢視衝突標記，選擇合適的版本或合併兩個版本。\""
            ;;
    esac

    return 0
}

# ============================================================================
# 解決衝突
# ============================================================================
resolve_conflict() {
    local file="$1"
    local strategy="$2"

    if [[ -z "$file" ]] || [[ -z "$strategy" ]]; then
        log_error "缺少參數：檔案和策略都是必需的"
        show_help
        exit 1
    fi

    if [[ ! -f "$file" ]]; then
        log_error "檔案不存在：$file"
        exit 1
    fi

    log_title "解決衝突：$file（策略：$strategy）"

    case "$strategy" in
        "ours")
            # 保留我們的版本（HEAD）
            git checkout --ours "$file"
            log_success "已使用 ours 策略保留我們的版本"
            ;;
        "theirs")
            # 保留他們的版本（MERGE_HEAD）
            git checkout --theirs "$file"
            log_success "已使用 theirs 策略保留他們的版本"
            ;;
        "manual")
            # 標記為已手動解決
            git add "$file"
            log_success "已標記為手動解決並添加到暫存區"
            ;;
        *)
            log_error "未知的策略：$strategy"
            log_info "支援的策略：ours, theirs, manual"
            exit 1
            ;;
    esac

    # 如果不是 manual 模式，需要添加到暫存區
    if [[ "$strategy" != "manual" ]]; then
        git add "$file"
        log_success "已將檔案添加到暫存區"
    fi

    # 獲取剩餘衝突數量
    local remaining=$(git diff --name-only --diff-filter=U 2>/dev/null | wc -l)

    echo ""
    echo "YAML 輸出："
    cat << EOF
result:
  status: "success"
  file: "$file"
  strategy: "$strategy"
  message: "已使用 $strategy 策略解決衝突"
  remaining_conflicts: $remaining
EOF

    if [[ $remaining -gt 0 ]]; then
        log_info "還有 $remaining 個衝突檔案待解決"
    else
        log_success "所有衝突已解決！"
    fi

    return 0
}

# ============================================================================
# 主程式
# ============================================================================
main() {
    # 檢查是否在 Git 倉庫內
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "不在 Git 倉庫內"
        exit 1
    fi

    # 解析命令行參數
    local command="$1"

    case "$command" in
        "")
            log_error "缺少命令"
            show_help
            exit 1
            ;;
        "--help"|"-h")
            show_help
            exit 0
            ;;
        "--detect")
            detect_conflicts
            ;;
        "--analyze")
            if [[ -z "$2" ]]; then
                log_error "--analyze 需要指定檔案路徑"
                exit 1
            fi
            analyze_conflict "$2"
            ;;
        "--resolve")
            if [[ -z "$2" ]] || [[ -z "$3" ]]; then
                log_error "--resolve 需要指定檔案和策略"
                exit 1
            fi
            resolve_conflict "$2" "$3"
            ;;
        *)
            log_error "未知的命令：$command"
            show_help
            exit 1
            ;;
    esac
}

# 執行主程式
main "$@"
