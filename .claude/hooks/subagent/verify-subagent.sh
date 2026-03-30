#!/bin/bash
# .claude/hooks/subagent/verify-subagent.sh
# Hook: SubagentStop
# 用途：驗證測試相關子代理執行結果
# 已適配：Python/FastAPI + React Native/Expo 專案

set -euo pipefail

# 讀取 stdin（JSON 格式）
input=$(cat)

# 提取子代理資訊
agent_type=$(echo "$input" | jq -r '.agent_type // empty')
transcript_path=$(echo "$input" | jq -r '.agent_transcript_path // empty')

# ============================================
# 只驗證測試相關 Agent
# ============================================
if [[ "$agent_type" =~ ^(test-writer|test-runner|module-developer)$ ]]; then
    if [[ -f "$transcript_path" ]]; then
        # 檢查 pytest 通過
        if grep -qE "passed|PASSED" "$transcript_path" 2>/dev/null && ! grep -qE "failed|FAILED|ERROR" "$transcript_path" 2>/dev/null; then
            echo "[OK] 子代理 [$agent_type] 測試通過"
            exit 0

        # 檢查 pytest 失敗
        elif grep -qE "failed|FAILED|ERROR" "$transcript_path" 2>/dev/null; then
            jq -nc --arg agent "$agent_type" '{
              "decision": "block",
              "reason": ("[ERROR] 子代理 [" + $agent + "] 測試失敗\n\n請修正測試錯誤後再繼續。\n\n執行：cd backend && pytest tests/ -v --tb=short")
            }'
            exit 0

        # 未執行測試
        else
            jq -nc --arg agent "$agent_type" '{
              "decision": "block",
              "reason": ("[WARN] 子代理 [" + $agent + "] 未執行測試\n\n請確保執行測試：\n後端：cd backend && pytest tests/\n前端：cd mobile && npx jest")
            }'
            exit 0
        fi
    fi
fi

# 其他 agent 類型：允許繼續
echo "[OK] 子代理 [$agent_type] 完成"
exit 0
