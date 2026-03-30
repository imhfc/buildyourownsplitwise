#!/bin/bash
# Worktree 管理工具
# 用途：建立、清理、狀態檢查

set -e

PROJECT_ROOT="/Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt"
WORKTREE_ROOT="/Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt-worktrees"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# 函數：建立 Worktree
# ============================================
create_worktree() {
    local module=$1
    local branch="feature/refactor-${module}"
    local worktree_path="${WORKTREE_ROOT}/refactor-${module}"

    echo -e "${BLUE}📁 建立 Worktree: ${module}${NC}"

    # 檢查 worktree 是否已存在
    if [ -d "$worktree_path" ]; then
        echo -e "${RED}❌ Worktree 已存在: ${worktree_path}${NC}"
        return 1
    fi

    # 切換到主專案目錄
    cd "$PROJECT_ROOT"

    # 建立 worktree
    echo -e "${YELLOW}⚙️  建立分支: ${branch}${NC}"
    git worktree add -b "$branch" "$worktree_path"

    echo -e "${GREEN}✅ Worktree 建立完成${NC}"
    echo -e "   路徑: ${worktree_path}"
    echo -e "   分支: ${branch}"
    echo ""
}

# ============================================
# 函數：列出所有 Worktree
# ============================================
list_worktrees() {
    echo -e "${BLUE}📋 Worktree 清單${NC}"
    cd "$PROJECT_ROOT"
    git worktree list
    echo ""
}

# ============================================
# 函數：清理 Worktree
# ============================================
remove_worktree() {
    local module=$1
    local worktree_path="${WORKTREE_ROOT}/refactor-${module}"

    echo -e "${YELLOW}🗑️  清理 Worktree: ${module}${NC}"

    if [ ! -d "$worktree_path" ]; then
        echo -e "${RED}❌ Worktree 不存在: ${worktree_path}${NC}"
        return 1
    fi

    cd "$PROJECT_ROOT"

    # 移除 worktree
    git worktree remove "$worktree_path" --force

    echo -e "${GREEN}✅ Worktree 已清理${NC}"
    echo ""
}

# ============================================
# 函數：清理所有 Worktree
# ============================================
remove_all_worktrees() {
    echo -e "${YELLOW}🗑️  清理所有 Worktree${NC}"

    cd "$PROJECT_ROOT"

    # 列出所有 worktree（排除主 worktree）
    git worktree list --porcelain | grep "worktree " | awk '{print $2}' | while read -r worktree_path; do
        if [ "$worktree_path" != "$PROJECT_ROOT" ]; then
            echo -e "   清理: ${worktree_path}"
            git worktree remove "$worktree_path" --force 2>/dev/null || true
        fi
    done

    echo -e "${GREEN}✅ 所有 Worktree 已清理${NC}"
    echo ""
}

# ============================================
# 函數：驗證 Worktree 狀態
# ============================================
verify_worktree() {
    local module=$1
    local worktree_path="${WORKTREE_ROOT}/refactor-${module}"

    echo -e "${BLUE}🔍 驗證 Worktree: ${module}${NC}"

    if [ ! -d "$worktree_path" ]; then
        echo -e "${RED}❌ Worktree 不存在${NC}"
        return 1
    fi

    cd "$worktree_path"

    # 檢查分支
    local current_branch=$(git branch --show-current)
    echo -e "   分支: ${current_branch}"

    # 檢查狀態
    local status=$(git status --porcelain)
    if [ -z "$status" ]; then
        echo -e "${GREEN}   狀態: 乾淨${NC}"
    else
        echo -e "${YELLOW}   狀態: 有變更${NC}"
        git status --short
    fi

    echo ""
}

# ============================================
# 函數：批次建立 Worktree
# ============================================
batch_create() {
    local batch_num=$1

    case $batch_num in
        1)
            create_worktree "cusf"
            create_worktree "cigk"
            ;;
        2)
            create_worktree "cusvaa"
            create_worktree "cust"
            ;;
        3)
            create_worktree "cusva3"
            create_worktree "cusvd1"
            ;;
        4)
            create_worktree "lnam"
            create_worktree "rstm"
            ;;
        5)
            create_worktree "rstv"
            create_worktree "reom1"
            ;;
        6)
            create_worktree "reom2"
            create_worktree "reom3"
            ;;
        *)
            echo -e "${RED}❌ 無效的批次編號: ${batch_num}${NC}"
            echo "   可用批次: 1-6"
            return 1
            ;;
    esac

    echo -e "${GREEN}✅ Batch ${batch_num} Worktree 建立完成${NC}"
}

# ============================================
# 主程式
# ============================================
case "${1:-}" in
    create)
        create_worktree "$2"
        ;;
    remove)
        remove_worktree "$2"
        ;;
    remove-all)
        remove_all_worktrees
        ;;
    list)
        list_worktrees
        ;;
    verify)
        verify_worktree "$2"
        ;;
    batch-create)
        batch_create "$2"
        ;;
    *)
        echo "用法: $0 {create|remove|remove-all|list|verify|batch-create} [module|batch-num]"
        echo ""
        echo "指令："
        echo "  create <module>        建立單一 Worktree"
        echo "  remove <module>        移除單一 Worktree"
        echo "  remove-all             移除所有 Worktree"
        echo "  list                   列出所有 Worktree"
        echo "  verify <module>        驗證 Worktree 狀態"
        echo "  batch-create <num>     批次建立 Worktree (1-6)"
        echo ""
        echo "範例："
        echo "  $0 batch-create 1      建立 Batch 1 (CUSF + CIGK)"
        echo "  $0 list                列出所有 Worktree"
        echo "  $0 verify cusf         驗證 CUSF Worktree"
        echo "  $0 remove-all          清理所有 Worktree"
        exit 1
        ;;
esac
