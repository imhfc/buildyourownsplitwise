#!/bin/bash
# .claude/hooks/setup-project.sh
# Hook: Setup
# 用途：專案初始化和維護（執行 claude --init 或 --maintenance 時觸發）

set -euo pipefail

# 讀取 stdin（JSON 格式）
input=$(cat)

# 提取 trigger 類型
trigger=$(echo "$input" | jq -r '.trigger // "init"')

# 取得專案目錄
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

echo "==== 專案設定（$trigger）===="
echo ""

# ============================================
# 1. 安裝 Git Hooks
# ============================================
if [[ -f "$PROJECT_DIR/.claude/hooks/install.sh" ]]; then
    echo "📦 安裝 Git Hooks..."
    if bash "$PROJECT_DIR/.claude/hooks/install.sh" &> /dev/null; then
        echo "  ✓ Git Hooks 安裝成功"
    else
        echo "  ⚠️ Git Hooks 安裝失敗（可能已安裝）"
    fi
else
    echo "  ⚠️ Git Hooks 安裝腳本不存在"
fi

echo ""

# ============================================
# 2. 檢查必要工具
# ============================================
echo "🔍 檢查開發工具..."

tools_status=()

# jq（JSON 處理）
if command -v jq &> /dev/null; then
    version=$(jq --version 2>/dev/null || echo "unknown")
    tools_status+=("  ✓ jq: $version")
else
    tools_status+=("  ✗ jq: 未安裝（hooks 必需）")
fi

# yq（YAML 處理）
if command -v yq &> /dev/null; then
    version=$(yq --version 2>/dev/null | head -1 || echo "unknown")
    tools_status+=("  ✓ yq: $version")
else
    tools_status+=("  ⚠️ yq: 未安裝（建議安裝）")
fi

# google-java-format（Java 格式化）
if command -v google-java-format &> /dev/null; then
    tools_status+=("  ✓ google-java-format: 已安裝")
else
    tools_status+=("  ⚠️ google-java-format: 未安裝（建議安裝）")
fi

# prettier（JS/TS/MD 格式化）
if command -v prettier &> /dev/null; then
    version=$(prettier --version 2>/dev/null || echo "unknown")
    tools_status+=("  ✓ prettier: $version")
else
    tools_status+=("  ⚠️ prettier: 未安裝（建議安裝）")
fi

# Python 3（Unicode 檢測）
if command -v python3 &> /dev/null; then
    version=$(python3 --version 2>/dev/null || echo "unknown")
    tools_status+=("  ✓ python3: $version")
else
    tools_status+=("  ✗ python3: 未安裝（hooks 必需）")
fi

# 輸出工具狀態
printf '%s\n' "${tools_status[@]}"

echo ""

# ============================================
# 3. 初始化 Memory Bank
# ============================================
echo "📁 檢查 Memory Bank..."

memory_dir="$PROJECT_DIR/.claude/memory-bank/project-context"
if [[ ! -d "$memory_dir" ]]; then
    echo "  建立 Memory Bank 目錄..."
    mkdir -p "$memory_dir"
    echo "  ✓ Memory Bank 目錄已建立"
else
    echo "  ✓ Memory Bank 目錄已存在"
fi

# 檢查必要的 YAML 檔案
required_files=(
    "preferences.yaml"
    "decisions.yaml"
    "lessons-learned.yaml"
    "progress.yaml"
)

for file in "${required_files[@]}"; do
    if [[ -f "$memory_dir/$file" ]]; then
        echo "  ✓ $file"
    else
        echo "  ⚠️ $file 不存在"
    fi
done

echo ""

# ============================================
# 4. 驗證 settings.json
# ============================================
echo "⚙️  檢查 settings.json..."

settings_file="$PROJECT_DIR/.claude/settings.json"
if [[ -f "$settings_file" ]]; then
    # 檢查是否包含 hooks 配置
    if jq -e '.hooks' "$settings_file" &> /dev/null; then
        hook_count=$(jq '.hooks | length' "$settings_file" 2>/dev/null || echo "0")
        echo "  ✓ Hooks 配置已啟用（$hook_count 個事件）"
    else
        echo "  ⚠️ 未配置 Hooks"
    fi

    # 檢查是否包含 plugins 配置
    if jq -e '.enabledPlugins' "$settings_file" &> /dev/null; then
        enabled_plugins=$(jq '.enabledPlugins | to_entries | map(select(.value == true)) | length' "$settings_file" 2>/dev/null || echo "0")
        echo "  ✓ Plugins 配置已啟用（$enabled_plugins 個啟用）"
    fi
else
    echo "  ⚠️ settings.json 不存在"
fi

echo ""

# ============================================
# 5. 設定環境變數（持久化）
# ============================================
if [[ -n "${CLAUDE_ENV_FILE:-}" ]]; then
    echo "🔧 設定環境變數..."

    # 設定專案目錄
    if ! grep -q "MAGNOLIA_PROJECT_DIR" "$CLAUDE_ENV_FILE" 2>/dev/null; then
        echo "export MAGNOLIA_PROJECT_DIR=\"$PROJECT_DIR\"" >> "$CLAUDE_ENV_FILE"
        echo "  ✓ MAGNOLIA_PROJECT_DIR 已設定"
    fi

    # 設定 setup 目錄
    if [[ -d "$PROJECT_DIR/setup" ]]; then
        if ! grep -q "MAGNOLIA_SETUP" "$CLAUDE_ENV_FILE" 2>/dev/null; then
            echo "export MAGNOLIA_SETUP=\"$PROJECT_DIR/setup\"" >> "$CLAUDE_ENV_FILE"
            echo "  ✓ MAGNOLIA_SETUP 已設定"
        fi
    fi
fi

echo ""

# ============================================
# 6. 建議安裝命令
# ============================================
missing_tools=()

command -v jq &> /dev/null || missing_tools+=("jq")
command -v yq &> /dev/null || missing_tools+=("yq")
command -v google-java-format &> /dev/null || missing_tools+=("google-java-format")
command -v prettier &> /dev/null || missing_tools+=("prettier")

if [[ ${#missing_tools[@]} -gt 0 ]]; then
    echo "💡 建議安裝的工具："
    echo ""

    if [[ " ${missing_tools[@]} " =~ " jq " ]]; then
        echo "  # JSON 處理（必需）"
        echo "  brew install jq"
        echo ""
    fi

    if [[ " ${missing_tools[@]} " =~ " yq " ]]; then
        echo "  # YAML 處理"
        echo "  brew install yq"
        echo ""
    fi

    if [[ " ${missing_tools[@]} " =~ " google-java-format " ]]; then
        echo "  # Java 代碼格式化"
        echo "  brew install google-java-format"
        echo ""
    fi

    if [[ " ${missing_tools[@]} " =~ " prettier " ]]; then
        echo "  # JS/TS/Markdown 格式化"
        echo "  npm install -g prettier"
        echo ""
    fi
fi

echo "============================"
echo "✓ 專案設定完成"
echo ""
echo "下一步："
echo "  1. 安裝建議的工具（如有需要）"
echo "  2. 檢查 Memory Bank 檔案是否完整"
echo "  3. 開始使用 Claude Code！"
echo ""

exit 0
