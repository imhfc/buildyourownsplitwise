#!/bin/bash

# 用途：根據文件路徑檢測文件類型
# 輸入：文件路徑
# 輸出：文件類型（config, doc, code, test, script, other）
#
# 用法：
#   source ./file-type.sh
#   detect_file_type "path/to/file.java"  # 輸出：code
#   detect_file_type "config.yaml"         # 輸出：config

detect_file_type() {
    local file="$1"

    # 檢查輸入
    if [[ -z "$file" ]]; then
        echo "other"
        return 1
    fi

    # 優先檢查：測試文件（匹配特定命名模式）
    case "$file" in
        *Test.java|*Tests.java|*Spec.java|*IT.java)
            echo "test"
            return 0
            ;;
    esac

    # 按檔案副檔名分類
    case "$file" in
        # 配置文件
        *.yaml|*.yml|*.properties|*.json|*.xml|*.gradle|*.maven|*.pom)
            echo "config"
            ;;
        # 文檔文件
        *.md|*.txt|*.adoc|*.rst|*.asciidoc)
            echo "doc"
            ;;
        # 代碼文件
        *.java|*.kt|*.groovy|*.scala)
            echo "code"
            ;;
        # 腳本文件
        *.sh|*.bash|*.zsh|*.ps1)
            echo "script"
            ;;
        # 其他文件
        *)
            echo "other"
            ;;
    esac
}

# 如果直接執行此腳本（非 source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    detect_file_type "$1"
fi
