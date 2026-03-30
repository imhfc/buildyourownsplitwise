#!/bin/bash

# 用途：從 git diff 中提取關鍵變更摘要
# 輸入：文件路徑、最大行數（可選，預設 5）
# 輸出：關鍵變更的簡短描述
#
# 用法：
#   source ./change-extractor.sh
#   extract_key_changes "src/main/java/User.java"
#   extract_key_changes "src/main/java/User.java" 3  # 最多 3 行

extract_key_changes() {
    local file="$1"
    local max_lines="${2:-5}"

    # 檢查輸入
    if [[ -z "$file" ]]; then
        echo "無文件指定"
        return 1
    fi

    # 获取暫存區的新增行（sorted changes）
    local added=$(git diff --cached -- "$file" 2>/dev/null | grep '^+[^+]' | head -"$max_lines")

    # 如果沒有暫存的變更，嘗試獲取工作目錄的變更
    if [[ -z "$added" ]]; then
        added=$(git diff -- "$file" 2>/dev/null | grep '^+[^+]' | head -"$max_lines")
    fi

    # 如果仍然沒有變更
    if [[ -z "$added" ]]; then
        echo "無新增內容"
        return 0
    fi

    # 提取關鍵資訊
    # 1. 移除行首的 '+'
    # 2. 截斷長行為 60 字符
    # 3. 將多行用 '; ' 分隔
    # 4. 移除末尾的分隔符
    echo "$added" | sed 's/^+//' | cut -c1-60 | tr '\n' ';' | sed 's/;$//'
}

# 提取涉及的方法名稱（適用於 Java 代碼）
extract_method_names() {
    local file="$1"

    # 只對 Java 文件進行處理
    if [[ "$file" != *.java ]]; then
        return
    fi

    # 查找 git diff 中的方法簽名（+ 開頭的行中包含 public/private 和括號）
    git diff --cached -- "$file" 2>/dev/null | \
        grep '^+[[:space:]]*\(public\|private\|protected\|static\)' | \
        grep -oE '[a-zA-Z_][a-zA-Z0-9_]*\s*\(' | \
        cut -d' ' -f1 | sort -u | tr '\n' ',' | sed 's/,$//'
}

# 提取類名（適用於 Java 代碼）
extract_class_names() {
    local file="$1"

    # 只對 Java 文件進行處理
    if [[ "$file" != *.java ]]; then
        return
    fi

    # 查找類定義行
    git diff --cached -- "$file" 2>/dev/null | \
        grep '^+[[:space:]]*\(public\|private\).*class' | \
        grep -oE 'class\s+[a-zA-Z_][a-zA-Z0-9_]*' | \
        cut -d' ' -f2 | tr '\n' ',' | sed 's/,$//'
}

# 如果直接執行此腳本（非 source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${2:-summary}" in
        methods)
            extract_method_names "$1"
            ;;
        classes)
            extract_class_names "$1"
            ;;
        *)
            extract_key_changes "$1" "$2"
            ;;
    esac
fi
