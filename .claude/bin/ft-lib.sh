#!/bin/bash
# Fine-Tune AI Agent 工具函數庫

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 版本
FT_VERSION="1.0.0"

# 顯示幫助
cmd_help() {
    echo "Fine-Tune AI Agent 命令行工具 v${FT_VERSION}"
    echo ""
    echo "使用方式:"
    echo "  ft <command> [options]"
    echo ""
    echo "命令:"
    echo "  init          初始化新專案的 AI Agent 配置"
    echo "  sync          從主專案同步更新"
    echo "  status        查看當前配置狀態"
    echo "  update        更新 Atomic Agents 和 Skills"
    echo "  hooks         管理 Git Hooks"
    echo "  help          顯示此幫助訊息"
    echo "  version       顯示版本資訊"
    echo ""
    echo "範例:"
    echo "  ft init                    # 初始化當前專案"
    echo "  ft sync                    # 同步最新更新"
    echo "  ft status                  # 查看狀態"
    echo "  ft hooks install           # 安裝 Git Hooks"
    echo "  ft update --agents         # 只更新 Agents"
    echo ""
    echo "詳細說明:"
    echo "  https://github.com/your-org/fine-tune-ai-agent"
}

# 顯示版本
cmd_version() {
    echo "Fine-Tune AI Agent v${FT_VERSION}"
}

# 初始化專案
cmd_init() {
    echo -e "${BLUE}初始化 AI Agent 配置...${NC}"

    # 檢查必要檔案
    if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
        echo -e "${YELLOW}⚠ CLAUDE.md 不存在，建立中...${NC}"
        cp "$CLAUDE_DIR/../CLAUDE.md.template" "$PROJECT_ROOT/CLAUDE.md" 2>/dev/null || {
            echo -e "${RED}✗ 無法建立 CLAUDE.md${NC}"
            exit 1
        }
    fi

    # 初始化 Memory Bank
    if [ ! -f "$CLAUDE_DIR/memory-bank/project-context/preferences.yaml" ]; then
        echo -e "${BLUE}初始化 Memory Bank...${NC}"
    fi

    # 安裝 Git Hooks
    bash "$CLAUDE_DIR/hooks/install.sh"

    echo
    echo -e "${GREEN}✓ 初始化完成！${NC}"
    echo
    echo -e "${BLUE}下一步:${NC}"
    echo "  1. 編輯 CLAUDE.md 配置專案資訊"
    echo "  2. 編輯 .claude/memory-bank/project-context/preferences.yaml 設定偏好"
    echo "  3. 開始使用: 啟動 Claude Code 並與 AI 互動"
}

# 同步更新
cmd_sync() {
    echo -e "${BLUE}同步功能尚未實作${NC}"
    echo "請手動從主專案複製更新的檔案"
}

# 查看狀態
cmd_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}   Fine-Tune AI Agent 狀態${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo

    # 版本資訊
    echo -e "${BLUE}版本:${NC} $FT_VERSION"
    echo

    # Atomic Agents
    local agents_count=$(find "$CLAUDE_DIR/agents/atomic" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${BLUE}Atomic Agents:${NC} $agents_count 個"

    # Skills
    local skills_count=$(find "$CLAUDE_DIR/skills" -maxdepth 1 -type d 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
    echo -e "${BLUE}Skills:${NC} $skills_count 個"

    # Git Hooks
    if [ -f "$PROJECT_ROOT/.git/hooks/commit-msg" ]; then
        echo -e "${BLUE}Git Hooks:${NC} ${GREEN}已安裝${NC}"
    else
        echo -e "${BLUE}Git Hooks:${NC} ${YELLOW}未安裝${NC} (執行 'ft hooks install' 安裝)"
    fi

    # CLAUDE.md
    if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
        echo -e "${BLUE}CLAUDE.md:${NC} ${GREEN}存在${NC}"
    else
        echo -e "${BLUE}CLAUDE.md:${NC} ${RED}不存在${NC}"
    fi

    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 更新
cmd_update() {
    echo -e "${BLUE}更新功能尚未實作${NC}"
    echo "請手動從主專案複製更新的檔案"
}

# 管理 Git Hooks
cmd_hooks() {
    case "${1:-help}" in
        install)
            bash "$CLAUDE_DIR/hooks/install.sh"
            ;;
        test)
            bash "$CLAUDE_DIR/hooks/test-hooks.sh"
            ;;
        uninstall)
            rm -f "$PROJECT_ROOT/.git/hooks/commit-msg"
            rm -f "$PROJECT_ROOT/.git/hooks/pre-push"
            rm -f "$PROJECT_ROOT/.git/hooks/pre-commit"
            echo -e "${GREEN}✓ Git Hooks 已移除${NC}"
            ;;
        *)
            echo "使用方式: ft hooks <command>"
            echo
            echo "命令:"
            echo "  install     安裝 Git Hooks"
            echo "  test        測試 Git Hooks"
            echo "  uninstall   移除 Git Hooks"
            ;;
    esac
}
