#!/bin/bash
################################################################################
# Build Your Own Splitewise 專案環境變量配置
#
# 用途：在任何目錄都能正確定位專案路徑
# 使用：source .claude/skills/shared/env.sh
#
# 自動導出以下環境變量：
#   PROJECT_ROOT     - 專案根目錄
#   BYOSW_CLAUDE     - .claude/ 目錄
#   BYOSW_SCRIPTS    - .claude/skills/shared/ 目錄
#   BYOSW_SKILLS     - .claude/skills/ 目錄
#   BYOSW_AGENTS     - .claude/agents/ 目錄
#   BYOSW_BACKEND    - backend/ 目錄
#   BYOSW_MOBILE     - mobile/ 目錄
################################################################################

# 自動偵測專案根目錄
detect_project_root() {
    # 方法 1: 從 .claude 目錄找
    if [ -f ".claude/skills/shared/env.sh" ]; then
        echo "$(pwd)"
        return 0
    elif [ -f "../.claude/skills/shared/env.sh" ]; then
        echo "$(cd .. && pwd)"
        return 0
    fi

    # 方法 2: 從當前腳本位置推導
    if [ -n "${BASH_SOURCE[0]}" ]; then
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        # .claude/skills/shared/env.sh → 往上三層到專案根目錄
        local root_dir="$(cd "$script_dir/../../.." && pwd)"
        if [ -d "$root_dir/.claude" ] && [ -d "$root_dir/backend" ]; then
            echo "$root_dir"
            return 0
        fi
    fi

    # 方法 3: 向上搜尋最多 3 層
    local current_dir="$(pwd)"
    for i in {0..3}; do
        local test_dir="$current_dir"
        for j in $(seq 1 $i); do
            test_dir="$(dirname "$test_dir")"
        done

        if [ -d "$test_dir/.claude" ] && [ -d "$test_dir/backend" ]; then
            echo "$test_dir"
            return 0
        fi
    done

    echo ""
    return 1
}

# 偵測並設定專案路徑
PROJECT_ROOT="$(detect_project_root)"

if [ -z "$PROJECT_ROOT" ]; then
    echo "錯誤：無法找到專案根目錄" >&2
    echo "請確認當前目錄或上層目錄包含 .claude/ 和 backend/" >&2
    return 1 2>/dev/null || exit 1
fi

# 導出環境變量
export PROJECT_ROOT
export BYOSW_CLAUDE="$PROJECT_ROOT/.claude"
export BYOSW_SCRIPTS="$BYOSW_CLAUDE/skills/shared"
export BYOSW_SKILLS="$BYOSW_CLAUDE/skills"
export BYOSW_AGENTS="$BYOSW_CLAUDE/agents"
export BYOSW_BACKEND="$PROJECT_ROOT/backend"
export BYOSW_MOBILE="$PROJECT_ROOT/mobile"

# 顯示配置（調試模式）
if [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
    echo "專案環境變量已設定："
    echo "  PROJECT_ROOT  = $PROJECT_ROOT"
    echo "  BYOSW_CLAUDE  = $BYOSW_CLAUDE"
    echo "  BYOSW_BACKEND = $BYOSW_BACKEND"
    echo "  BYOSW_MOBILE  = $BYOSW_MOBILE"
fi

return 0 2>/dev/null || exit 0
