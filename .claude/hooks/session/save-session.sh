#!/bin/bash
# .claude/hooks/session/save-session.sh
# Hook: SessionEnd
# 用途：檢查並提示未完成任務
# 版本:2.0 (2026-01-26) - 簡化為只記錄未完成任務

set -euo pipefail

# 讀取 stdin（JSON 格式）
input=$(cat)

# 提取會話資訊（加入錯誤處理）
reason=$(echo "$input" | jq -r '.reason // "other"' 2>/dev/null || echo "other")
transcript_path=$(echo "$input" | jq -r '.transcript_path // empty' 2>/dev/null || echo "")

echo "==== 會話結束（${reason:-unknown}）===="
echo ""

# ============================================
# 檢查未完成的 TODO
# ============================================
if [[ -f "$transcript_path" ]]; then
    incomplete_todos=$(grep -c '"status".*"pending\|in_progress"' "$transcript_path" 2>/dev/null || echo "0")

    if [[ "$incomplete_todos" -gt 0 ]]; then
        echo "[WARN] 未完成的任務："
        echo "  - 有 $incomplete_todos 個未完成的 TODO"
        echo ""
        echo "下次會話建議："
        echo "  - 繼續完成未完成的任務"
        echo "  - 檢查 Memory Bank 是否需要更新"
        echo ""
    else
        echo "[OK] 所有任務已完成"
        echo ""
    fi
fi

echo "============================"
exit 0
