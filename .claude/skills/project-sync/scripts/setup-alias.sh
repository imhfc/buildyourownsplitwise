#!/bin/bash

################################################################################
# Shell Alias 設定腳本
#
# 用途：為 fetch-profile.sh 設定便捷的 shell alias
#
# 使用方式：
#   source .claude/skills/project-sync/scripts/setup-alias.sh
#
# 之後就可以在任何微服務專案中使用：
#   fetch-profile                    # 自動偵測當前微服務
#   fetch-profile --milestone v0.9
#   fetch-profile --with-gradle
#
################################################################################

# 主專案腳本路徑
MAIN_SCRIPT="/Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/skills/project-sync/scripts/fetch-profile.sh"

# 自動偵測微服務並調用主專案腳本
fetch-profile() {
    local CURRENT_DIR="$(pwd)"
    local SERVICE_NAME=""

    # 偵測當前微服務
    case "$(basename "$CURRENT_DIR")" in
        *customer-agreement-mgmt*)
            SERVICE_NAME="CAM"
            ;;
        *customer-info-management*)
            SERVICE_NAME="CIM"
            ;;
        *custr-relationship-mgmt*)
            SERVICE_NAME="CRM"
            ;;
        *event-management*)
            SERVICE_NAME="EM"
            ;;
        *profile-management*)
            SERVICE_NAME="PM"
            ;;
        *sales-management*)
            SERVICE_NAME="SM"
            ;;
        *)
            echo "錯誤: 無法偵測微服務（當前目錄不是微服務專案）"
            echo "請在微服務專案根目錄執行"
            return 1
            ;;
    esac

    # 調用主專案腳本
    bash "$MAIN_SCRIPT" --service "$SERVICE_NAME" "$@"
}

echo "已設定 fetch-profile 函數"
echo ""
echo "使用方式："
echo "  fetch-profile                    # 複製配置檔案"
echo "  fetch-profile --milestone v0.9    # 指定里程碑"
echo "  fetch-profile --with-gradle      # 同時複製 gradle 設定"
echo "  fetch-profile --dry-run          # 預覽模式"
echo ""
echo "若要永久生效，請將以下命令加入 ~/.zshrc 或 ~/.bashrc："
echo "  source /Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/skills/project-sync/scripts/setup-alias.sh"
echo ""
