#!/bin/bash

# 用途：處理 Git 操作錯誤，返回結構化錯誤訊息
# 輸入：錯誤輸出或錯誤類型
# 輸出：錯誤類型、修復建議、是否可恢復
#
# 用法：
#   source ./error-handler.sh
#   error_type=$(detect_error_type "emoji detected")
#   suggestion=$(suggest_fix "$error_type")

# 檢測錯誤類型
detect_error_type() {
    local output="$1"

    # 檢查是否為空
    if [[ -z "$output" ]]; then
        echo "UNKNOWN"
        return 1
    fi

    # 按優先順序檢測錯誤類型
    case "$output" in
        *"emoji"*|*"😀"*|*"😁"*|*"😂"*|*"🎉"*|*"✓"*|*"✅"*|*"❌"*|*"⚠️"*|*"🔔"*)
            echo "EMOJI_DETECTED"
            ;;
        *"AI 標記"*|*"AI标记"*|*"Co-Authored-By"*|*"Claude"*)
            echo "AI_MARKER_DETECTED"
            ;;
        *"簡體中文"*|*"简体中文"*|*"UTF-8"*|*"GB2312"*)
            echo "SIMPLIFIED_CHINESE"
            ;;
        *"pre-commit"*|*"pre-push"*|*"hook failed"*|*"hook 失敗"*|*"hook 失败"*)
            echo "HOOK_FAILED"
            ;;
        *"conflict"*|*"衝突"*|*"冑突"*|*"merging"*|*"CONFLICT"*)
            echo "MERGE_CONFLICT"
            ;;
        *"nothing to commit"*|*"無變更"*|*"没有变更"*)
            echo "NOTHING_TO_COMMIT"
            ;;
        *"not a git repository"*|*"不是 git 倉庫"*|*"不是 git 仓库"*)
            echo "NOT_GIT_REPO"
            ;;
        *"authentication failed"*|*"Permission denied"*|*"認證失敗"*)
            echo "AUTH_FAILED"
            ;;
        *"file not found"*|*"not found"*|*"找不到"*)
            echo "FILE_NOT_FOUND"
            ;;
        *"already exists"*|*"已存在"*|*"already"*)
            echo "BRANCH_EXISTS"
            ;;
        *"no such"*|*"不存在"*|*"doesn't exist"*)
            echo "BRANCH_NOT_FOUND"
            ;;
        *"uncommitted changes"*|*"未提交"*|*"working tree dirty"*)
            echo "UNCOMMITTED_CHANGES"
            ;;
        *)
            echo "UNKNOWN"
            ;;
    esac
}

# 建議修復方法
suggest_fix() {
    local error_type="$1"

    case "$error_type" in
        "EMOJI_DETECTED")
            echo "移除文件中的 emoji 字符"
            ;;
        "AI_MARKER_DETECTED")
            echo "移除 commit message 中的 AI 標記（如 Co-Authored-By: Claude）"
            ;;
        "SIMPLIFIED_CHINESE")
            echo "將簡體中文轉換為繁體中文（例：使用 opencc 工具或手動調整）"
            ;;
        "HOOK_FAILED")
            echo "檢查 pre-commit/pre-push hook 輸出，修復指出的問題"
            ;;
        "MERGE_CONFLICT")
            echo "解決合併衝突後重新提交 (git add . && git commit)"
            ;;
        "NOTHING_TO_COMMIT")
            echo "沒有變更需要提交，請先使用 git add 添加文件"
            ;;
        "NOT_GIT_REPO")
            echo "當前目錄不是 Git 倉庫，請執行 git init 或切換至正確的倉庫目錄"
            ;;
        "AUTH_FAILED")
            echo "認證失敗，檢查 Git 認證資訊或使用 SSH 密鑰"
            ;;
        "FILE_NOT_FOUND")
            echo "文件不存在，檢查文件路徑是否正確"
            ;;
        "BRANCH_EXISTS")
            echo "分支已存在，請使用其他名稱或先刪除現有分支"
            ;;
        "BRANCH_NOT_FOUND")
            echo "分支不存在，檢查分支名稱是否正確"
            ;;
        "UNCOMMITTED_CHANGES")
            echo "工作目錄有未提交的變更，先提交或使用 git stash 暫存"
            ;;
        *)
            echo "請檢查錯誤訊息並手動修復"
            ;;
    esac
}

# 判斷錯誤是否可恢復
is_recoverable() {
    local error_type="$1"

    case "$error_type" in
        "EMOJI_DETECTED"|"AI_MARKER_DETECTED"|"SIMPLIFIED_CHINESE"|"HOOK_FAILED"|"NOTHING_TO_COMMIT"|"MERGE_CONFLICT"|"BRANCH_EXISTS"|"UNCOMMITTED_CHANGES")
            echo "true"
            ;;
        "NOT_GIT_REPO"|"AUTH_FAILED"|"FILE_NOT_FOUND"|"BRANCH_NOT_FOUND")
            echo "false"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# 取得詳細的錯誤說明
get_error_description() {
    local error_type="$1"

    case "$error_type" in
        "EMOJI_DETECTED")
            echo "代碼或提交訊息中包含 emoji 字符，違反了項目的代碼風格規範。"
            ;;
        "AI_MARKER_DETECTED")
            echo "提交訊息中包含 AI 標記（Co-Authored-By），違反了項目政策。所有提交應由人類創建。"
            ;;
        "SIMPLIFIED_CHINESE")
            echo "代碼或提交訊息中包含簡體中文，項目要求使用繁體中文（zh-TW）。"
            ;;
        "HOOK_FAILED")
            echo "Pre-commit 或 pre-push hook 檢查失敗，通常是由於代碼質量或格式問題。"
            ;;
        "MERGE_CONFLICT")
            echo "多個分支的變更發生衝突，需要手動解決衝突並提交。"
            ;;
        "NOTHING_TO_COMMIT")
            echo "沒有新的變更可以提交，可能是文件未被添加到暫存區。"
            ;;
        "NOT_GIT_REPO")
            echo "當前目錄不在任何 Git 倉庫中。"
            ;;
        "AUTH_FAILED")
            echo "認證失敗，可能是密鑰不匹配或認證令牌過期。"
            ;;
        "FILE_NOT_FOUND")
            echo "指定的文件不存在。"
            ;;
        "BRANCH_EXISTS")
            echo "分支已存在，無法建立同名分支。"
            ;;
        "BRANCH_NOT_FOUND")
            echo "分支不存在，可能已被刪除或名稱輸入錯誤。"
            ;;
        "UNCOMMITTED_CHANGES")
            echo "工作目錄中存在未提交的變更，需要先提交或暫存。"
            ;;
        *)
            echo "發生未知錯誤。"
            ;;
    esac
}

# 取得錯誤嚴重程度
get_error_severity() {
    local error_type="$1"

    case "$error_type" in
        "AI_MARKER_DETECTED"|"HOOK_FAILED"|"MERGE_CONFLICT"|"AUTH_FAILED"|"BRANCH_NOT_FOUND")
            echo "CRITICAL"
            ;;
        "EMOJI_DETECTED"|"SIMPLIFIED_CHINESE"|"NOTHING_TO_COMMIT"|"BRANCH_EXISTS"|"UNCOMMITTED_CHANGES")
            echo "WARNING"
            ;;
        "NOT_GIT_REPO"|"FILE_NOT_FOUND")
            echo "ERROR"
            ;;
        *)
            echo "UNKNOWN"
            ;;
    esac
}

# 如果直接執行此腳本（非 source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 接受命令行參數：detect, suggest, recover, describe, severity
    command="${1:-detect}"
    input="$2"

    case "$command" in
        detect)
            detect_error_type "$input"
            ;;
        suggest)
            suggest_fix "$input"
            ;;
        recover)
            is_recoverable "$input"
            ;;
        describe)
            get_error_description "$input"
            ;;
        severity)
            get_error_severity "$input"
            ;;
        *)
            echo "用法: error-handler.sh {detect|suggest|recover|describe|severity} [input]"
            exit 1
            ;;
    esac
fi
