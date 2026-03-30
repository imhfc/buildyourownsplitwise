#!/bin/bash
# .claude/hooks/validation/validate-bash.sh
# Hook: PreToolUse (Bash)
# 用途：驗證 Bash 命令安全性（防止危險命令）

set -euo pipefail

# 載入日誌工具
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../lib/logging.sh" ]; then
    PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
    export CLAUDE_PROJECT_ROOT="$PROJECT_DIR"
    # shellcheck source=../lib/logging.sh
    source "$SCRIPT_DIR/../lib/logging.sh"
    init_logging "validate-bash"
fi

# 讀取 stdin（JSON 格式）
input=$(cat)

# 提取工具名稱和命令
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# 只處理 Bash 工具
if [[ "$tool_name" != "Bash" ]]; then
    exit 0
fi

# ============================================
# 1. 檢查極度危險的命令（阻止）
# ============================================
CRITICAL_PATTERNS=(
    "rm\s+-rf\s+/"          # 刪除根目錄
    "rm\s+-rf\s+\*"         # 刪除所有檔案
    ":(){ :|:& };:"         # Fork 炸彈
    "mkfs\."                # 格式化磁碟
    "dd\s+if=/dev/zero"     # 覆寫磁碟
    "chmod\s+-R\s+777\s+/"  # 修改根目錄權限
)

for pattern in "${CRITICAL_PATTERNS[@]}"; do
    if echo "$command" | grep -qE "$pattern"; then
        log_error "阻止危險命令 - 模式: $pattern - 命令: ${command:0:100}" 2>/dev/null || true
        finalize_logging 2 2>/dev/null || true

        # 使用 jq 構建 JSON 以避免轉義問題
        jq -nc --arg pattern "$pattern" --arg command "$command" '{
          "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": ("[BLOCK] 危險命令被阻止：檢測到可能破壞系統的命令模式 \"" + $pattern + "\"。\n\n命令：" + $command + "\n\n此操作已被安全策略拒絕。")
          }
        }'
        exit 2  # 阻止操作
    fi
done

# ============================================
# 2. 檢查需要確認的命令（提供警告）
# ============================================
WARNING_PATTERNS=(
    "rm\s+-rf"              # 遞迴刪除
    "git\s+push\s+--force"  # 強制推送
    "git\s+reset\s+--hard"  # 硬重置
    "npm\s+install\s+-g"    # 全局安裝
    "sudo"                  # 需要 root 權限
)

for pattern in "${WARNING_PATTERNS[@]}"; do
    if echo "$command" | grep -qE "$pattern"; then
        # 使用 jq 構建 JSON 以避免轉義問題
        jq -nc --arg pattern "$pattern" --arg command "$command" '{
          "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": ("[WARN] 安全警告：\n\n檢測到潛在風險命令：\"" + $pattern + "\"\n命令：" + $command + "\n\n建議：\n- 確認此操作是必要的\n- 檢查命令參數是否正確\n- 考慮是否有更安全的替代方案\n\n繼續執行請手動確認。")
          }
        }'
        # 不阻止，只是警告
        exit 0
    fi
done

# ============================================
# 3. 建議使用專用工具替代 Bash（優化建議）
# ============================================
# 檢查是否使用了應該用專用工具的命令
if echo "$command" | grep -qE "^(find|grep|cat|head|tail|sed|awk|echo)[[:space:]]"; then
    tool_suggestion=""

    if echo "$command" | grep -qE "^find[[:space:]]"; then
        tool_suggestion="Glob 工具（更快、更準確）"
    elif echo "$command" | grep -qE "^grep[[:space:]]"; then
        tool_suggestion="Grep 工具（支持更多選項）"
    elif echo "$command" | grep -qE "^(cat|head|tail)[[:space:]]"; then
        tool_suggestion="Read 工具（自動處理大檔案）"
    elif echo "$command" | grep -qE "^(sed|awk)[[:space:]]"; then
        tool_suggestion="Edit 工具（更安全的編輯）"
    elif echo "$command" | grep -qE "^echo[[:space:]].*>"; then
        tool_suggestion="Write 工具（更適合檔案寫入）"
    fi

    if [[ -n "$tool_suggestion" ]]; then
        # 使用 jq 構建 JSON 以避免轉義問題
        jq -nc --arg command "$command" --arg suggestion "$tool_suggestion" '{
          "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": ("[INFO] 優化建議：\n\n檢測到可以使用專用工具的命令：\n命令：" + $command + "\n\n建議使用：" + $suggestion + "\n\n根據 Claude Code 最佳實踐，專用工具提供更好的性能和錯誤處理。\n\n如果此 Bash 命令確實必要（如 git, npm, docker 等），可以忽略此建議。")
          }
        }'
    fi
fi

# 全部檢查通過
log_info "命令驗證通過" 2>/dev/null || true
finalize_logging 0 2>/dev/null || true
exit 0
