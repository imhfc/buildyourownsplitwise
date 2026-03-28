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
