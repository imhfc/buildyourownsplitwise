#!/bin/bash
# .claude/hooks/session/load-memory.sh
# Hook: SessionStart
# 用途：載入專案記憶庫（偏好、進度、經驗教訓）
# 已適配：Build Your Own Splitewise 專案

set -euo pipefail

# 取得專案目錄
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
MEMORY_DIR="$PROJECT_DIR/.claude/memory-bank/project-context"
export CLAUDE_PROJECT_ROOT="$PROJECT_DIR"

# 載入日誌工具
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../lib/logging.sh" ]; then
    source "$SCRIPT_DIR/../lib/logging.sh"
    init_logging "load-memory"
fi

# 檢查記憶庫目錄
if [[ ! -d "$MEMORY_DIR" ]]; then
    echo "[WARN] 記憶庫目錄不存在：$MEMORY_DIR"
    exit 0
fi

cat <<EOF
==== 記憶庫載入 ====

**專案**：Build Your Own Splitewise（分帳應用）
**技術棧**：FastAPI + SQLAlchemy (async) + PostgreSQL | Expo + React Native + NativeWind + Zustand

**專案偏好**：
- 語言：繁體中文（zh-TW）
- 禁止 Emoji
- 後端測試：pytest tests/（需先啟動 db-test）
- 前端品質關卡：bash mobile/scripts/quality-gate.sh

EOF

# 載入最近進度
if [[ -f "$MEMORY_DIR/progress.yaml" ]]; then
    echo "**最近進度**："
    last_update=$(grep "last_update_detail:" "$MEMORY_DIR/progress.yaml" | cut -d: -f2- | xargs 2>/dev/null || echo "")
    if [[ -n "$last_update" && "$last_update" != '""' ]]; then
        echo "- $last_update"
    else
        echo "- （無記錄）"
    fi
    echo ""
fi

# 載入當前任務
if [[ -f "$MEMORY_DIR/progress.yaml" ]]; then
    sprint=$(grep "current_sprint:" "$MEMORY_DIR/progress.yaml" | cut -d: -f2- | xargs 2>/dev/null | tr -d '"')
    if [[ -n "$sprint" ]]; then
        echo "**當前衝刺**："
        echo "- $sprint"
        echo ""
    fi
fi

cat <<EOF
====================

[INFO] 可用 Skills：
- /review-code    代碼審查（多維度自動分析）
- /write-tests    撰寫測試 + 執行 + 覆蓋率分析
- /git-ops        標準化 Git 操作
- /memory-bank    記憶管理（決策、進度、偏好）

EOF

exit 0
