#!/bin/bash
# OpenSpec 安裝與設定腳本
# 用途：自動安裝與初始化 OpenSpec 規格驅動開發工具
# 版本：1.1

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢測是否為互動式終端
IS_INTERACTIVE=true
if [ ! -t 0 ] || [ ! -t 1 ]; then
    IS_INTERACTIVE=false
fi

# 全局參數
AUTO_YES=false

echo -e "${BLUE}=== OpenSpec 安裝與設定 ===${NC}"
echo ""

# 檢查 Node.js 和 npm
check_nodejs() {
    if ! command -v node &> /dev/null; then
        echo -e "${RED}錯誤：未安裝 Node.js${NC}"
        echo "請先安裝 Node.js: https://nodejs.org/"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        echo -e "${RED}錯誤：未安裝 npm${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Node.js 版本: $(node --version)${NC}"
    echo -e "${GREEN}✓ npm 版本: $(npm --version)${NC}"
    echo ""
}

# 安裝 OpenSpec
install_openspec() {
    echo -e "${BLUE}正在安裝 @fission-ai/openspec...${NC}"

    if npm install -g @fission-ai/openspec@latest; then
        echo -e "${GREEN}✓ OpenSpec 安裝成功${NC}"
    else
        echo -e "${RED}✗ OpenSpec 安裝失敗${NC}"
        exit 1
    fi
    echo ""
}

# 檢查是否已安裝
check_installed() {
    if command -v openspec &> /dev/null; then
        echo -e "${GREEN}✓ OpenSpec 已安裝: $(openspec --version 2>/dev/null || echo 'latest')${NC}"
        return 0
    else
        return 1
    fi
}

# 初始化 OpenSpec
init_openspec() {
    echo -e "${BLUE}初始化 OpenSpec...${NC}"

    if [ -d "openspec" ]; then
        echo -e "${YELLOW}openspec 目錄已存在${NC}"

        if [ "$IS_INTERACTIVE" = true ] && [ "$AUTO_YES" = false ]; then
            read -p "$(echo -e ${BLUE}是否重新初始化？[y/N]:${NC} )" confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}跳過初始化${NC}"
                return
            fi
        elif [ "$AUTO_YES" = false ]; then
            echo -e "${YELLOW}跳過初始化（非互動模式）${NC}"
            return
        fi
    fi

    openspec init

    echo -e "${GREEN}✓ OpenSpec 初始化完成${NC}"
    echo ""
}

# 建立整合文檔
create_integration_guide() {
    echo -e "${BLUE}建立整合指南...${NC}"

    mkdir -p .ai-docs/knowledge/universal/claude-doc
    cat > .ai-docs/knowledge/universal/claude-doc/openspec-integration.md << 'EOF'
# OpenSpec 整合指南

> Spec-driven development (SDD) for AI coding assistants
> 版本：1.0 (2026-01-24)

---

## 什麼是 OpenSpec？

OpenSpec 是一個規格驅動開發工具，讓開發者在寫程式碼之前先定義規格，確保人類與 AI 對於要建立的內容達成共識。

## 核心概念

### 目錄結構

```
openspec/
├── specs/              # 當前系統規格（真實來源）
│   └── [domain]/
│       └── spec.md
├── changes/            # 活躍的功能提案
│   └── [feature-name]/
│       ├── proposal.md  # 提案說明
│       ├── tasks.md     # 實作任務清單
│       ├── design.md    # 設計文檔（選填）
│       └── specs/       # 規格變更（delta）
└── archive/            # 已完成的變更
```

### 工作流程

```
Draft → Review → Implement → Archive
(起草) (審查)   (實作)      (歸檔)
```

**1. Draft（起草）**: 建立變更提案，捕捉預期的規格更新
**2. Review（審查）**: 與 AI 迭代，直到規格符合需求
**3. Implement（實作）**: 執行參考已同意規格的任務
**4. Archive（歸檔）**: 將已批准的更新合併到真實來源規格

---

## 命令使用

### 基本命令

```bash
# 初始化專案
openspec init

# 查看活躍的變更
openspec list

# 互動式儀表板
openspec view

# 顯示特定變更的詳細資訊
openspec show <change-name>

# 驗證變更格式
openspec validate <change-name>

# 歸檔已完成的變更
openspec archive <change-name>
```

### 與 Claude Code 整合

OpenSpec 提供原生 slash commands：

```bash
/openspec:proposal   # 建立新提案
/openspec:apply      # 應用變更
/openspec:archive    # 歸檔變更
```

---

## 規格文件格式

### proposal.md

```markdown
# Proposal: [功能名稱]

## 背景
[說明為何需要此變更]

## 目標
[列出此變更要達成的目標]

## 範圍
[定義變更的範圍]

## 影響
[說明可能的影響範圍]
```

### tasks.md

```markdown
# Tasks: [功能名稱]

## 實作任務

- [ ] 任務 1: 描述
- [ ] 任務 2: 描述
- [ ] 任務 3: 描述

## 驗證

- [ ] 單元測試通過
- [ ] 整合測試通過
- [ ] 文檔更新
```

### spec.md (delta format)

```markdown
# Spec Delta: [功能名稱]

## ADDED Requirements

### Requirement: [需求名稱]

描述新增的需求

#### Scenario: [場景名稱]

GIVEN [前提條件]
WHEN [觸發條件]
THEN [預期結果]

## MODIFIED Requirements

### Requirement: [需求名稱]

描述修改的需求

## REMOVED Requirements

### Requirement: [需求名稱]

說明移除的原因
```

---

## 與現有 .ai-docs 整合

OpenSpec 與專案現有的 `.ai-docs` 結構互補：

| 用途 | .ai-docs | OpenSpec |
|------|----------|----------|
| **靜態知識庫** | ADR, Patterns, Guides | - |
| **規格管理** | specs-index.yaml | specs/ |
| **變更提案** | - | changes/ |
| **實作追蹤** | progress.yaml | tasks.md |
| **歷史記錄** | - | archive/ |

**建議工作流程**：
1. 使用 OpenSpec 管理功能變更提案
2. 完成後，將重要決策升級為 ADR（.ai-docs）
3. 將規格同步到 specs-index.yaml

---

## 最佳實踐

### 1. 規格優先

在寫程式碼前，先建立 OpenSpec 提案：
```bash
openspec view  # 建立新提案
```

### 2. 使用 Delta 格式

明確標記 ADDED/MODIFIED/REMOVED：
- 清楚的變更追蹤
- 易於審查
- 降低誤解

### 3. 場景驅動

每個 Requirement 至少包含一個 Scenario：
```markdown
### Requirement: 用戶登入驗證

#### Scenario: 成功登入
GIVEN 用戶輸入正確的帳號密碼
WHEN 點擊登入按鈕
THEN 系統應導向首頁
```

### 4. 迭代審查

與 AI 多次迭代，確保規格清晰：
- 第一版：粗略草稿
- 第二版：補充場景
- 第三版：精煉用語
- 最終版：確認後實作

### 5. 及時歸檔

完成實作後，立即歸檔：
```bash
openspec archive <change-name>
```

---

## 範例工作流程

### 新增功能：用戶認證

```bash
# 1. 建立提案
openspec view
# 選擇 "Create new change" → 輸入 "user-authentication"

# 2. 編輯 proposal.md
# 說明為何需要用戶認證功能

# 3. 編輯 tasks.md
# - [ ] 實作 AuthService
# - [ ] 建立登入 API
# - [ ] 撰寫單元測試

# 4. 編輯 specs/auth/spec.md
# 定義認證規格與場景

# 5. 與 AI 審查
# 使用 Claude Code 檢視並完善規格

# 6. 實作
# 開始執行 tasks.md 中的任務

# 7. 驗證
openspec validate user-authentication

# 8. 歸檔
openspec archive user-authentication
```

---

## 常見問題

### Q: OpenSpec 與 ADR 有何不同？

**OpenSpec**: 管理功能變更的提案與實作追蹤
**ADR**: 記錄架構決策的理由與權衡

兩者互補，OpenSpec 處理動態變更，ADR 記錄靜態決策。

### Q: 何時使用 OpenSpec？

- 新增功能
- 修改現有行為
- 跨多個規格的變更
- 需要與 AI 明確對齊的任務

### Q: 如何處理小變更？

小變更（如修復 typo）不需要 OpenSpec，直接修改即可。

---

## 參考資源

- [OpenSpec GitHub](https://github.com/Fission-AI/OpenSpec)
- [OpenSpec npm](https://www.npmjs.com/package/@fission-ai/openspec)
- [使用指南](https://github.com/Fission-AI/OpenSpec/blob/main/README.md)

EOF

    if [ -f ".ai-docs/knowledge/universal/claude-doc/openspec-integration.md" ]; then
        echo -e "${GREEN}✓ 整合指南建立完成: .ai-docs/knowledge/universal/claude-doc/openspec-integration.md${NC}"
    else
        echo -e "${YELLOW}無法建立整合指南${NC}"
    fi
    echo ""
}

# 顯示後續步驟
show_next_steps() {
    echo -e "${BLUE}=== 安裝完成 ===${NC}"
    echo ""
    echo -e "${GREEN}後續步驟：${NC}"
    echo ""
    echo "1. 查看整合指南："
    echo -e "   ${BLUE}cat .ai-docs/knowledge/universal/claude-doc/openspec-integration.md${NC}"
    echo ""
    echo "2. 查看活躍的變更："
    echo -e "   ${BLUE}openspec list${NC}"
    echo ""
    echo "3. 開啟互動式儀表板："
    echo -e "   ${BLUE}openspec view${NC}"
    echo ""
    echo "4. 建立第一個提案："
    echo -e "   ${BLUE}openspec view${NC} → Create new change"
    echo ""
    echo "5. 閱讀完整文檔："
    echo -e "   ${BLUE}https://github.com/Fission-AI/OpenSpec${NC}"
    echo ""
}

# 顯示使用說明
show_usage() {
    cat << EOF
${BLUE}OpenSpec 安裝與設定腳本${NC}

使用方式:
  $0 [options]

參數:
  -y, --yes        - 自動確認所有提示（非互動模式）
  -h, --help       - 顯示此說明

範例:
  $0               # 互動式安裝
  $0 -y            # 非互動模式安裝

EOF
}

# 主程式
main() {
    # 解析參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes)
                AUTO_YES=true
                IS_INTERACTIVE=false
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}未知參數: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done

    echo -e "${BLUE}OpenSpec 安裝程序${NC}"
    echo ""

    # 1. 檢查 Node.js
    check_nodejs

    # 2. 檢查是否已安裝
    if check_installed; then
        echo -e "${YELLOW}OpenSpec 已安裝，跳過安裝步驟${NC}"
        echo ""
    else
        # 3. 安裝 OpenSpec
        install_openspec
    fi

    # 4. 初始化 OpenSpec
    if [ "$IS_INTERACTIVE" = true ] && [ "$AUTO_YES" = false ]; then
        read -p "$(echo -e ${BLUE}是否初始化 OpenSpec？[Y/n]:${NC} )" init_confirm
        if [[ ! "$init_confirm" =~ ^[Nn]$ ]]; then
            init_openspec
        fi
    elif [ "$AUTO_YES" = true ]; then
        init_openspec
    else
        echo -e "${YELLOW}跳過初始化（非互動模式，使用 -y 強制初始化）${NC}"
    fi

    # 5. 建立整合文檔
    create_integration_guide

    # 6. 顯示後續步驟
    show_next_steps
}

main "$@"
