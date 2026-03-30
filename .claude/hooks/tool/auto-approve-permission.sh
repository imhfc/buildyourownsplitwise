#!/bin/bash
# .claude/hooks/tool/auto-approve-permission.sh
# Hook: PermissionRequest
# 用途：自動批准常用命令，自動拒絕危險命令，減少重複的權限確認
# 已適配：Python/FastAPI + React Native/Expo 專案

set -euo pipefail

# 讀取 stdin（JSON 格式）
input=$(cat)

# 提取工具名稱和參數
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# 只處理 Bash 工具
if [[ "$tool_name" != "Bash" ]]; then
    exit 0
fi

# ============================================
# 1. 自動批准：Git 命令（只讀）
# ============================================
if [[ "$command" =~ ^git\ (status|diff|log|show|branch|remote|fetch|stash\ list) ]]; then
    jq -nc '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow"
        }
      }
    }'
    exit 0
fi

# ============================================
# 2. 自動批准：只讀命令
# ============================================
if [[ "$command" =~ ^(ls|pwd|which|whoami|date|hostname)($| ) ]]; then
    jq -nc '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow"
        }
      }
    }'
    exit 0
fi

# ============================================
# 3. 自動批准：Python 測試和後端命令
# ============================================
if [[ "$command" =~ ^(cd\ backend\ &&\ )?(pytest|python\ -m\ pytest) ]] ||
   [[ "$command" =~ ^(cd\ backend\ &&\ )?python\ -m\ py_compile ]] ||
   [[ "$command" =~ ^(cd\ backend\ &&\ )?alembic ]] ||
   [[ "$command" =~ ^pip\ (list|show|freeze) ]]; then
    jq -nc '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow"
        }
      }
    }'
    exit 0
fi

# ============================================
# 4. 自動批准：前端開發命令
# ============================================
if [[ "$command" =~ ^(cd\ mobile\ &&\ )?(npx\ (expo|jest|tsc|expo-doctor)|npm\ (test|run)) ]] ||
   [[ "$command" =~ ^bash\ mobile/scripts/quality-gate\.sh ]]; then
    jq -nc '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow"
        }
      }
    }'
    exit 0
fi

# ============================================
# 5. 自動批准：Docker 檢視命令
# ============================================
if [[ "$command" =~ ^docker\ (ps|images|logs|inspect|compose.*ps|compose.*logs) ]] ||
   [[ "$command" =~ ^docker\ compose\ -f\ docker-compose\.test\.yml\ up\ -d ]]; then
    jq -nc '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow"
        }
      }
    }'
    exit 0
fi

# ============================================
# 6. 自動批准：查看檔案內容（grep, find）
# ============================================
if [[ "$command" =~ ^(grep|find|rg|ag)($|\ ) ]]; then
    jq -nc '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow"
        }
      }
    }'
    exit 0
fi

# ============================================
# 7. 自動拒絕：Git Hooks 繞過 (--no-verify)
# ============================================
if [[ "$command" =~ git\ .*(--no-verify|-n)($|\ ) ]]; then
    jq -nc --arg cmd "$command" '{
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "deny",
          "message": ("[BLOCK] Git Hooks 繞過需要人類批准\n\n命令：" + $cmd + "\n\n使用 --no-verify 會繞過重要的代碼品質檢查。\n若確實需要繞過，請手動執行命令並明確說明原因。"),
          "interrupt": true
        }
      }
    }'
    exit 0
fi

# 其他命令：顯示權限對話框（不做決定）
exit 0
