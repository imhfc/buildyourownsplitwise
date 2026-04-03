#!/usr/bin/env bash
# BYOSW Mobile Quality Gate
# 執行：bash mobile/scripts/quality-gate.sh
# 任一項 FAIL → exit 1，禁止繼續提交或部署

set -euo pipefail

MOBILE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

green() { printf "\033[32m  PASS\033[0m %s\n" "$1"; }
red()   { printf "\033[31m  FAIL\033[0m %s\n" "$1"; FAIL=$((FAIL+1)); }

echo ""
echo "=== BYOSW Mobile Quality Gate ==="
echo ""

# ── C-1：tailwind.config.js 必須有 darkMode: "class" ──────────────────────────
if grep -q 'darkMode.*class' "$MOBILE_DIR/tailwind.config.js" 2>/dev/null; then
  green "C-1  tailwind darkMode: \"class\" 已設定"
else
  red   "C-1  tailwind.config.js 缺少 darkMode: \"class\"（會造成 NativeWind dark mode crash）"
fi

# ── C-2：babel.config.js 必須含 babel-plugin-transform-import-meta ─────────────
if grep -q 'babel-plugin-transform-import-meta\|transform-import-meta' "$MOBILE_DIR/babel.config.js" 2>/dev/null; then
  green "C-2  babel-plugin-transform-import-meta 已在 babel.config.js"
else
  red   "C-2  babel.config.js 缺少 babel-plugin-transform-import-meta（會造成 import.meta SyntaxError）"
fi

# ── C-3：metro.config.js 必須有 unstable_enablePackageExports = false ──────────
if grep -q 'unstable_enablePackageExports.*false' "$MOBILE_DIR/metro.config.js" 2>/dev/null; then
  green "C-3  metro.config.js unstable_enablePackageExports = false 已設定"
else
  red   "C-3  metro.config.js 缺少 unstable_enablePackageExports = false（Zustand ESM 會引發 SyntaxError）"
fi

# ── C-4：i18n/index.ts 必須有 detection: { caches: [] } ──────────────────────
if grep -q 'caches.*\[\]' "$MOBILE_DIR/i18n/index.ts" 2>/dev/null; then
  green "C-4  i18n detection.caches: [] 已設定"
else
  red   "C-4  i18n/index.ts 缺少 detection: { caches: [] }（i18next 會讀 localStorage 覆蓋語言設定）"
fi

# ── C-5：package.json react 版本不能有 ^ ────────────────────────────────────
REACT_VER=$(node -e "console.log(require('$MOBILE_DIR/package.json').dependencies.react || '')" 2>/dev/null)
if [[ "$REACT_VER" == ^* ]]; then
  red   "C-5  package.json react=\"$REACT_VER\" 含 ^，請改為精確版本（Expo SDK 不相容風險）"
else
  green "C-5  package.json react 版本已釘選：$REACT_VER"
fi

# ── C-6：package.json react-dom 版本不能有 ^ ─────────────────────────────────
REACT_DOM_VER=$(node -e "console.log(require('$MOBILE_DIR/package.json').dependencies['react-dom'] || '')" 2>/dev/null)
if [[ "$REACT_DOM_VER" == ^* ]]; then
  red   "C-6  package.json react-dom=\"$REACT_DOM_VER\" 含 ^，請改為精確版本（Expo SDK 不相容風險）"
else
  green "C-6  package.json react-dom 版本已釘選：$REACT_DOM_VER"
fi

# ── C-7：expo-crypto 禁止使用 canary 版本 ─────────────────────────────────────
EXPO_CRYPTO_VER=$(node -e "console.log(require('$MOBILE_DIR/package.json').dependencies['expo-crypto'] || '')" 2>/dev/null)
if echo "$EXPO_CRYPTO_VER" | grep -q '\-canary\-'; then
  red   "C-7  package.json expo-crypto=\"$EXPO_CRYPTO_VER\" 含 canary 版本（會造成 Metro InternalError / App 轉圈圈）。請改用穩定版如 ~55.0.10"
else
  green "C-7  package.json expo-crypto 版本正常：$EXPO_CRYPTO_VER"
fi

# ── C-8：stores/auth.ts 禁止使用 onRehydrateStorage ─────────────────────────
if grep -q 'onRehydrateStorage' "$MOBILE_DIR/stores/auth.ts" 2>/dev/null; then
  red   "C-8  stores/auth.ts 含 onRehydrateStorage（Zustand 5 同步 toThenable 下 useAuthStore 尚未初始化，setState 靜默失敗 → hasHydrated 永遠 false → App 轉圈圈）。改用 useAuthStore.persist.onFinishHydration()"
else
  green "C-8  stores/auth.ts 未使用 onRehydrateStorage（Zustand 5 相容）"
fi

# ── C-9：_layout.tsx redirect 必須涵蓋已登入在 root index 的情境 ─────────────
if grep -q 'inTabsGroup' "$MOBILE_DIR/app/_layout.tsx" 2>/dev/null; then
  green "C-9  _layout.tsx redirect 邏輯涵蓋 inTabsGroup 情境"
else
  red   "C-9  _layout.tsx redirect 邏輯缺少 inTabsGroup 判斷（已登入用戶在 root index 時兩個 if 都不成立 → spinner 永遠不跳轉）"
fi

# ── C-10：group/[id].tsx Modal 表單 API 錯誤必須用 inline error state ──────────
if grep -q 'setAddError' "$MOBILE_DIR/app/group/[id].tsx" 2>/dev/null; then
  green "C-10 group/[id].tsx 使用 inline error state（setAddError）顯示 API 錯誤"
else
  red   "C-10 group/[id].tsx 缺少 setAddError（Modal 表單 API 錯誤必須用 inline error state 顯示，禁止用 Alert.alert）"
fi

# ── C-11：router.back() 必須搭配 canGoBack 檢查 ─────────────────────────────
C11_FAIL=0
for f in $(grep -rl 'router\.back()' "$MOBILE_DIR/app/" 2>/dev/null); do
  if ! grep -q 'canGoBack' "$f" 2>/dev/null; then
    C11_FAIL=1
    break
  fi
done
if [ "$C11_FAIL" -eq 0 ]; then
  green "C-11 所有 router.back() 皆有 canGoBack 防護"
else
  red   "C-11 發現 router.back() 未搭配 canGoBack 檢查（Expo Web 無歷史時會拋 GO_BACK not handled）：$f"
fi

# ── C-14：group/[id].tsx 結清按鈕只能顯示給付款方 ──────────────────────────
GROUP_FILE="$MOBILE_DIR/app/group/[id].tsx"
if [ -f "$GROUP_FILE" ]; then
  # 檢查策略：結清按鈕（含 settle_up 文字）前必須有 from_user_id 單獨守衛
  # 且該守衛不能是 from_user_id || to_user_id 的 OR 條件
  if grep -q 'from_user_id === user.*&&' "$GROUP_FILE" 2>/dev/null && \
     ! grep -B2 't("settle_up")' "$GROUP_FILE" 2>/dev/null | grep -q 'to_user_id === user.*&&'; then
    green "C-14 group/[id].tsx 結清按鈕限定付款方（from_user_id === user）"
  else
    red   "C-14 group/[id].tsx 結清按鈕未限定付款方（必須用 from_user_id === user?.id 守衛，禁止讓收款方也能發起結清）"
  fi
else
  green "C-14 group/[id].tsx 不存在（跳過）"
fi

# ── C-15：settlement_service.py 必須驗證 from_user != to_user ────────────────
SETTLE_SVC="$(cd "$MOBILE_DIR/.." && pwd)/backend/app/services/settlement_service.py"
if [ -f "$SETTLE_SVC" ]; then
  if grep -q 'from_user_id == data.to_user' "$SETTLE_SVC" 2>/dev/null; then
    green "C-15 settlement_service.py 已驗證 from_user != to_user"
  else
    red   "C-15 settlement_service.py 缺少 from_user_id != to_user 驗證（會允許自己對自己結清）"
  fi
else
  green "C-15 settlement_service.py 不存在（跳過）"
fi

# ── C-16：group_service.py is_settled 必須同時檢查 expense_count > 0 ─────────
GROUP_SVC="$(cd "$MOBILE_DIR/.." && pwd)/backend/app/services/group_service.py"
GROUPS_API="$(cd "$MOBILE_DIR/.." && pwd)/backend/app/api/groups.py"
if [ -f "$GROUP_SVC" ] && [ -f "$GROUPS_API" ]; then
  if grep -q 'expense_count' "$GROUP_SVC" 2>/dev/null && grep -q 'expense_count > 0' "$GROUPS_API" 2>/dev/null; then
    green "C-16 is_settled 判斷包含 expense_count > 0（零費用群組不會被標記為已結清）"
  else
    red   "C-16 is_settled 判斷缺少 expense_count > 0 條件（新群組會被誤判為已結清）"
  fi
else
  green "C-16 group_service.py 或 groups.py 不存在（跳過）"
fi

# ── C-17：log_activity action 值必須全部存在於 ActivityType Literal ──────────
BACKEND_DIR="$(cd "$MOBILE_DIR/.." && pwd)/backend"
SCHEMA_FILE="$BACKEND_DIR/app/schemas/activity.py"
if [ -f "$SCHEMA_FILE" ]; then
  # 從所有 service 檔案中擷取 log_activity 的 action 參數值
  MISSING=""
  for action_val in $(grep -roh 'action="[^"]*"' "$BACKEND_DIR/app/services/" 2>/dev/null | sed 's/action="//;s/"//' | sort -u); do
    if ! grep -q "\"$action_val\"" "$SCHEMA_FILE" 2>/dev/null; then
      MISSING="$MISSING $action_val"
    fi
  done
  if [ -z "$MISSING" ]; then
    green "C-17 所有 log_activity action 值皆已定義在 ActivityType Literal"
  else
    red   "C-17 以下 action 值在 service 中使用但未定義在 ActivityType Literal:$MISSING（會導致活動列表 500）"
  fi
else
  green "C-17 schemas/activity.py 不存在（跳過）"
fi

# ── C-19：backend/.env TEST_DATABASE_URL 必須指向本機 ────────────────────────
BACKEND_ENV="$(cd "$MOBILE_DIR/.." && pwd)/backend/.env"
if [ -f "$BACKEND_ENV" ]; then
  TEST_DB_URL=$(grep '^TEST_DATABASE_URL=' "$BACKEND_ENV" 2>/dev/null | head -1 | cut -d= -f2-)
  if [ -z "$TEST_DB_URL" ]; then
    red   "C-19 backend/.env 缺少 TEST_DATABASE_URL（測試 DB 未設定）"
  elif echo "$TEST_DB_URL" | grep -q '127\.0\.0\.1' && echo "$TEST_DB_URL" | grep -q 'ssl=disable'; then
    green "C-19 TEST_DATABASE_URL 指向本機（127.0.0.1 + ssl=disable）"
  else
    red   "C-19 TEST_DATABASE_URL 未指向本機：$TEST_DB_URL（必須包含 127.0.0.1 且 ssl=disable，禁止指向雲端 DB）"
  fi
else
  green "C-19 backend/.env 不存在（跳過）"
fi

# ── 結果 ──────────────────────────────────────────────────────────────────────
echo ""
echo "=== 結果：PASS=$PASS  FAIL=$FAIL ==="
echo ""

if [ "$FAIL" -gt 0 ]; then
  printf "\033[31m品質關卡未通過（%d 項 FAIL）。修復後再提交。\033[0m\n\n" "$FAIL"
  exit 1
else
  printf "\033[32m所有組態不變式通過。\033[0m\n\n"
  exit 0
fi
