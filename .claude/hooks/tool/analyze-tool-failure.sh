#!/bin/bash
# .claude/hooks/tool/analyze-tool-failure.sh
# Hook: PostToolUseFailure
# 用途：分析 pytest / npm 測試失敗原因
# 已適配：Python/FastAPI + React Native/Expo 專案

set -euo pipefail

# 讀取 stdin（JSON 格式）
input=$(cat)

# 提取工具資訊
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
command=$(echo "$input" | jq -r '.tool_input.command // empty')
error_msg=$(echo "$input" | jq -r '.error_message // ""')

# 只處理 Bash 工具
if [[ "$tool_name" != "Bash" ]]; then
    exit 0
fi

# ============================================
# 1. 分析 pytest 測試失敗
# ============================================
if [[ "$command" =~ pytest ]] && [[ "$error_msg" =~ (FAILED|ERROR|failed) ]]; then
    context=""

    # Import 錯誤
    if echo "$error_msg" | grep -qE "ImportError|ModuleNotFoundError"; then
        context="[ERROR] Python Import 錯誤

**建議修正**：
1. 檢查 import 路徑是否正確
2. 確認套件已安裝：pip install -r requirements.txt
3. 確認虛擬環境已啟動"

    # 資料庫連線錯誤
    elif echo "$error_msg" | grep -qE "ConnectionRefusedError|OperationalError|asyncpg"; then
        context="[ERROR] 資料庫連線失敗

**建議修正**：
1. 確認測試 DB 已啟動：docker compose -f docker-compose.test.yml up -d db-test
2. 確認 TEST_DATABASE_URL 設定正確（port 5433）
3. 檢查 PostgreSQL 日誌"

    # 斷言失敗
    elif echo "$error_msg" | grep -qE "AssertionError|assert"; then
        context="[ERROR] 測試斷言失敗

**建議修正**：
1. 檢查測試預期值是否正確
2. 檢查 API 回傳的 status code 和 body
3. 使用 pytest -v 查看詳細差異"

    # Pydantic 驗證錯誤
    elif echo "$error_msg" | grep -qE "ValidationError|pydantic"; then
        context="[ERROR] Pydantic 驗證失敗

**建議修正**：
1. 檢查 schema 欄位定義是否與測試資料一致
2. 確認必填欄位都有提供
3. 檢查資料型別（特別是 Decimal vs float）"

    # 其他 pytest 錯誤
    else
        context="[ERROR] pytest 測試失敗

**建議修正**：
1. 執行 pytest tests/ -v --tb=long 查看完整 traceback
2. 檢查 conftest.py fixtures 是否正確
3. 確認測試 DB 狀態"
    fi

    jq -nc --arg ctx "$context" '{
      "hookSpecificOutput": {
        "additionalContext": $ctx
      }
    }'
    exit 0
fi

# ============================================
# 2. 分析 npm/expo 失敗
# ============================================
if [[ "$command" =~ (npx|npm|expo) ]] && [[ -n "$error_msg" ]]; then
    context=""

    # TypeScript 類型錯誤
    if echo "$error_msg" | grep -qE "TS[0-9]+|TypeError"; then
        context="[ERROR] TypeScript 類型錯誤

**建議修正**：
1. 檢查 props 類型定義
2. 確認 import 的類型是否正確
3. 執行 npx tsc --noEmit 查看所有類型錯誤"

    # Metro bundler 錯誤
    elif echo "$error_msg" | grep -qE "SyntaxError|Metro"; then
        context="[ERROR] Metro Bundler 錯誤

**建議修正**：
1. 檢查 babel.config.js 設定
2. 確認 metro.config.js 的 unstable_enablePackageExports = false
3. 清除快取：npx expo start --clear"

    # npm install 失敗
    elif echo "$error_msg" | grep -qE "ERESOLVE|peer dep|npm ERR"; then
        context="[ERROR] npm 套件安裝失敗

**建議修正**：
1. 執行 npx expo-doctor 檢查版本相容性
2. 檢查 package.json 版本釘選（react, react-dom 不能有 ^）
3. 參考 QUALITY_SLA.md 的設定不變式"
    fi

    if [[ -n "$context" ]]; then
        jq -nc --arg ctx "$context" '{
          "hookSpecificOutput": {
            "additionalContext": $ctx
          }
        }'
        exit 0
    fi
fi

# 其他失敗：不提供額外建議
exit 0
