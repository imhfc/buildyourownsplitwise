#!/bin/bash

################################################################################
# 遠端配置拉取腳本 (主專案版)
#
# 用途：從主專案為所有微服務拉取本地開發配置
# 來源：git@github.ibm.com:ctbc-navi/navi-profile.git
#
# 配置來源優先順序：
#   1. 命令行參數（最高優先級）
#   2. setup/install.conf（自動讀取）
#   3. 內建預設值（向後兼容）
#
# 使用方式：
#   bash setup/fetch-profile.sh [選項]
#
# 選項：
#   --milestone <DXX> 指定開發里程碑 (v0.9|v1.0|v2.0|v3.0...，預設: 從分支名稱自動偵測或 install.conf)
#   --with-gradle     同時複製 gradle 設定 (預設不複製)
#   --update          強制更新快取
#   --dry-run         只顯示會複製的檔案，不實際執行
#   --service <名稱>  只處理指定微服務 (不指定則處理全部)
#   --help            顯示說明
#
################################################################################

set -e

# 取得腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# project/scripts → fine-tune-ai-agent → fine-tune-ai-agent
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# ============================================================================
# 讀取 install.conf 配置
# ============================================================================
load_config() {
    local config_file="$SCRIPT_DIR/install.conf"

    # 預設值（向後兼容）
    PROFILE_REPO="git@github.ibm.com:ctbc-navi/navi-profile.git"
    PROFILE_BRANCH="main"
    CACHE_DIR="$HOME/.cache/navi-profile"
    DEFAULT_MILESTONE="v1.0"
    BASE_DIR="/Users/Shared/Work/Projects"

    # 如果配置文件存在，讀取配置
    if [ -f "$config_file" ]; then
        while IFS='=' read -r key value; do
            # 跳過註解和空行
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue
            # 跳過模組對應行
            [[ "$key" == *:* ]] && continue

            # 去除空白
            key=$(echo "$key" | tr -d '[:space:]')
            value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            # 展開變數
            value=$(eval echo "$value")

            case "$key" in
                PROFILE_REPO)     PROFILE_REPO="$value" ;;
                PROFILE_BRANCH)   PROFILE_BRANCH="$value" ;;
                PROFILE_CACHE_DIR) CACHE_DIR="$value" ;;
                DEFAULT_VERSION)  DEFAULT_MILESTONE="$value" ;;  # 向後兼容
                DEFAULT_MILESTONE) DEFAULT_MILESTONE="$value" ;;
                BASE_DIR)         BASE_DIR="$value" ;;
            esac
        done < "$config_file"
    fi
}

# 載入配置
load_config

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ${NC}  $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC}  $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

show_help() {
    echo "用法: $0 [選項]"
    echo ""
    echo "配置來源優先順序:"
    echo "  1. 命令行參數（最高優先級）"
    echo "  2. setup/install.conf（自動讀取）"
    echo "  3. 內建預設值（向後兼容）"
    echo ""
    echo "選項:"
    echo "  --milestone <DXX> 指定開發里程碑 (v0.9|v1.0|v2.0|v3.0...，預設: 從分支名稱自動偵測或 install.conf)"
    echo "  --with-gradle     同時複製 gradle 設定 (預設只複製 resources)"
    echo "  --update          強制更新快取 repo"
    echo "  --dry-run         只顯示會複製的檔案，不實際執行"
    echo "  --service <名稱>  只處理指定微服務 (CRM|CIM|CAM|EM|PM|SM，不指定則全部)"
    echo "  --branch <分支>   指定 profile repo 分支 (預設: 從 install.conf 或 main)"
    echo "  --help            顯示此說明"
    echo ""
    echo "範例:"
    echo "  $0                        # 為所有微服務複製 resources (使用預設里程碑)"
    echo "  $0 --with-gradle          # 同時複製 gradle 設定"
    echo "  $0 --milestone v0.9        # 使用 v0.9 里程碑（覆蓋 install.conf）"
    echo "  $0 --service CRM          # 只處理 CRM 微服務"
    echo "  $0 --milestone v1.0 --service CRM  # v1.0 里程碑的 CRM 配置"
    echo "  $0 --update               # 強制更新快取後再複製"
    echo ""
}

# 預設值
MILESTONE=""  # 空值表示尚未指定，稍後從分支偵測
WITH_GRADLE=false
FORCE_UPDATE=false
DRY_RUN=false
TARGET_SERVICE=""
MILESTONE_FROM_ARG=false

# 解析參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --milestone)
            MILESTONE="$2"
            MILESTONE_FROM_ARG=true
            shift 2
            ;;
        --version)
            # 向後兼容：--version 仍然可用
            MILESTONE="$2"
            MILESTONE_FROM_ARG=true
            shift 2
            ;;
        --with-gradle)
            WITH_GRADLE=true
            shift
            ;;
        --update)
            FORCE_UPDATE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --service)
            TARGET_SERVICE="$2"
            shift 2
            ;;
        --branch)
            PROFILE_BRANCH="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
done

# ============================================================================
# 自動偵測 Milestone（從 git 分支名稱）
# 優先順序：命令行參數 > 分支名稱 > install.conf 預設值
# 支援格式：v0.9, v1.0, v2.0, v3.0, D60... (大小寫均可)
# 範例：feature/v2.0_DEV_REVIEW → v2.0, release/v3.0 → v3.0
# ============================================================================
detect_milestone_from_branch() {
    local branch
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    if [ -n "$branch" ]; then
        # 從分支名稱擷取 D 後接數字的里程碑（忽略大小寫，取第一個匹配）
        local detected
        detected=$(echo "$branch" | grep -oiE 'D[0-9]+' | head -1 | tr '[:lower:]' '[:upper:]')
        echo "$detected"
    fi
}

if [ "$MILESTONE_FROM_ARG" = false ]; then
    BRANCH_MILESTONE=$(detect_milestone_from_branch)
    if [ -n "$BRANCH_MILESTONE" ]; then
        MILESTONE="$BRANCH_MILESTONE"
        MILESTONE_SOURCE="分支自動偵測 ($(git rev-parse --abbrev-ref HEAD 2>/dev/null))"
    else
        MILESTONE="$DEFAULT_MILESTONE"
        MILESTONE_SOURCE="install.conf 預設值"
    fi
else
    MILESTONE_SOURCE="命令行參數"
fi

print_header "Navi Profile 本地開發設定"

echo "配置來源: $SCRIPT_DIR/install.conf"
echo "快取目錄: $CACHE_DIR"
echo "開發里程碑: $MILESTONE  [$MILESTONE_SOURCE]"
echo ""

# ============================================================================
# 步驟 1: 智能同步 profile repo
# ============================================================================
NEED_FETCH=false
FETCH_REASON=""
REMOTE_AVAILABLE=true

if [ ! -d "$CACHE_DIR/.git" ]; then
    NEED_FETCH=true
    FETCH_REASON="首次克隆"
else
    cd "$CACHE_DIR"
    if git fetch origin --quiet 2>/dev/null; then
        REMOTE_AVAILABLE=true
        LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null)
        REMOTE_HEAD=$(git rev-parse "origin/$PROFILE_BRANCH" 2>/dev/null)

        if [ "$FORCE_UPDATE" = true ]; then
            NEED_FETCH=true
            FETCH_REASON="強制更新"
        elif [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
            NEED_FETCH=true
            FETCH_REASON="遠端有更新"
        fi
    else
        REMOTE_AVAILABLE=false
        print_warning "無法連線遠端，使用本地快取"
    fi
    cd "$PROJECT_ROOT"
fi

if [ "$NEED_FETCH" = true ]; then
    print_info "同步 profile repo ($FETCH_REASON)..."

    if [ ! -d "$CACHE_DIR/.git" ]; then
        mkdir -p "$(dirname "$CACHE_DIR")"
        if git clone --branch "$PROFILE_BRANCH" --single-branch "$PROFILE_REPO" "$CACHE_DIR" 2>/dev/null; then
            print_success "已從遠端克隆"
        else
            print_error "無法克隆遠端 repo，請檢查網路連線"
            exit 1
        fi
    else
        cd "$CACHE_DIR"
        git reset --hard "origin/$PROFILE_BRANCH" --quiet
        cd "$PROJECT_ROOT"
        print_success "已從遠端同步"
    fi
elif [ "$REMOTE_AVAILABLE" = false ]; then
    print_info "使用本地快取 (離線模式)"
else
    print_info "使用本地快取 (無更新)"
fi

# ============================================================================
# 步驟 2: 偵測微服務
# ============================================================================
# 微服務對應表: 代號|目錄名稱|navi-profile專案名稱
SERVICE_DEFINITIONS="
CRM|Service_order-management|Service_order-management
CIM|Service_user-management|Service_user-management
CAM|Service_agreement-management|Service_agreement-management
EM|Service_event-management|Service_event-management
PM|Service_profile-management|Service_profile-management
SM|Service_sales-management|Service_sales-management
"
DETECTED_SERVICES=()

get_service_info() {
    local target="$1"
    echo "$SERVICE_DEFINITIONS" | grep "^$target|" | head -1
}

if [ -n "$TARGET_SERVICE" ]; then
    # 指定單一服務
    service_info=$(get_service_info "$TARGET_SERVICE")
    if [ -n "$service_info" ]; then
        IFS='|' read -r code dir_name profile_name <<< "$service_info"
        SERVICE_PATH="$BASE_DIR/$dir_name"
        if [ -d "$SERVICE_PATH/.git" ]; then
            DETECTED_SERVICES+=("$TARGET_SERVICE:$SERVICE_PATH:$profile_name")
        else
            print_error "找不到微服務: $TARGET_SERVICE ($SERVICE_PATH)"
            exit 1
        fi
    else
        print_error "未知的微服務代號: $TARGET_SERVICE (可用: CRM, CIM, CAM, EM, PM, SM)"
        exit 1
    fi
else
    # 自動偵測所有微服務
    while IFS='|' read -r code dir_name profile_name; do
        [ -z "$code" ] && continue
        SERVICE_PATH="$BASE_DIR/$dir_name"
        if [ -d "$SERVICE_PATH/.git" ]; then
            DETECTED_SERVICES+=("$code:$SERVICE_PATH:$profile_name")
        fi
    done <<< "$SERVICE_DEFINITIONS"
fi

if [ ${#DETECTED_SERVICES[@]} -eq 0 ]; then
    print_warning "未偵測到任何微服務"
    echo ""
    echo "請確認微服務位於: $BASE_DIR/services/"
    exit 0
fi

echo ""
print_info "偵測到 ${#DETECTED_SERVICES[@]} 個微服務"
for entry in "${DETECTED_SERVICES[@]}"; do
    IFS=':' read -r service_name service_path profile_name <<< "$entry"
    echo "  - $service_name → $(basename "$service_path")"
done
echo ""

# ============================================================================
# 步驟 3: 為每個微服務複製配置
# ============================================================================
SUCCESS_COUNT=0
FAILED_COUNT=0

for entry in "${DETECTED_SERVICES[@]}"; do
    IFS=':' read -r SERVICE_NAME SERVICE_PATH PROFILE_NAME <<< "$entry"

    echo ""
    echo -e "${CYAN}━━━ $SERVICE_NAME ━━━${NC}"

    # 定位配置來源 (使用 navi-profile 專案名稱)
    PROFILE_SERVICE_DIR="$CACHE_DIR/$PROFILE_NAME/$MILESTONE"

    if [ ! -d "$PROFILE_SERVICE_DIR" ]; then
        print_error "找不到配置目錄: $PROFILE_SERVICE_DIR"
        ((FAILED_COUNT++))
        continue
    fi

    # 定義要複製的檔案
    declare -a FILES_TO_COPY=()

    # Gradle 設定 (僅在 --with-gradle 時複製)
    if [ "$WITH_GRADLE" = true ]; then
        FILES_TO_COPY+=(
            "gradle/wrapper/gradle-wrapper.properties"
            "platform.gradle"
            "settings.gradle"
        )
    fi

    # Resources 檔案 (預設複製)
    SERVICES_SUBDIR=$(find "$PROFILE_SERVICE_DIR/services" -maxdepth 1 -type d ! -name "services" | head -1)
    if [ -n "$SERVICES_SUBDIR" ]; then
        SERVICE_SUBNAME=$(basename "$SERVICES_SUBDIR")
        FILES_TO_COPY+=(
            "services/$SERVICE_SUBNAME/src/main/resources/application-ibm.yaml"
            "services/$SERVICE_SUBNAME/src/main/resources/application-local.yaml"
            "services/$SERVICE_SUBNAME/src/main/resources/clientTruststore.p12"
        )
    fi

    # 複製檔案
    COPIED_COUNT=0
    for file in "${FILES_TO_COPY[@]}"; do
        SRC="$PROFILE_SERVICE_DIR/$file"
        DST="$SERVICE_PATH/$file"

        if [ -f "$SRC" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo "   [預覽] $file"
            else
                mkdir -p "$(dirname "$DST")"
                cp "$SRC" "$DST"
                echo "   ✓ $file"
            fi
            COPIED_COUNT=$((COPIED_COUNT + 1))
        fi
    done

    if [ $COPIED_COUNT -gt 0 ]; then
        print_success "已覆蓋 $COPIED_COUNT 個檔案"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        print_warning "無檔案可複製"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done

# ============================================================================
# 完成報告
# ============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
if [ "$DRY_RUN" = true ]; then
    print_info "預覽完成"
    echo "移除 --dry-run 以實際執行"
else
    print_success "處理完成"
    echo "成功: $SUCCESS_COUNT 個微服務"
    [ $FAILED_COUNT -gt 0 ] && echo "失敗: $FAILED_COUNT 個微服務"
fi
echo ""
print_warning "提醒: 這些檔案不應提交到 git (已被 pre-commit hook 保護)"
echo ""
