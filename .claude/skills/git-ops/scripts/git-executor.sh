#!/bin/bash
# Git Operations Framework - 執行器
# 用途：執行 Git 操作並返回結構化結果
# 版本：1.0

set -e

# 取得腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 解析目錄參數
TARGET_DIR="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--directory)
            TARGET_DIR="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

# 切換到目標目錄
if [ -n "$TARGET_DIR" ] && [ "$TARGET_DIR" != "." ]; then
    cd "$TARGET_DIR" || {
        echo "錯誤：無法切換到目錄 $TARGET_DIR" >&2
        exit 1
    }
fi

# 取得 Git 根目錄
GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# 載入輔助函數
source "$SCRIPT_DIR/lib/error-handler.sh"

# 使用追蹤
track_usage() {
    local action="$1"
    local status="${2:-success}"
    local tracker="$SCRIPT_DIR/../telemetry/usage-tracker.sh"
    if [[ -x "$tracker" ]]; then
        "$tracker" "git-executor" "$action" "$status" &>/dev/null &
    fi
}

# 顯示幫助
show_help() {
    cat << EOF
Git Command Executor
用法: git-executor.sh <command> [options]

命令:
  commit --message "msg"       執行 git commit
  push [--branch name]         執行 git push
  add [files...]               執行 git add
  branch --create <name>       建立新分支
  branch --switch <name>       切換分支
  branch --delete <name>       刪除分支
  branch --list                列出所有分支
  merge <branch> [--no-ff]     合併分支
  checkout <branch|file>       檢出分支或文件
  checkout -- <file>           放棄檔案變更

選項:
  --message, -m    Commit 訊息
  --branch, -b     目標分支
  --force, -f      強制推送（使用 --force-with-lease）
  --no-ff          建立 merge commit（用於 merge）
  --help           顯示此幫助資訊

輸出格式: YAML
EOF
}

# 執行 commit
execute_commit() {
    local message=""

    # 解析參數
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --message|-m)
                message="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    if [ -z "$message" ]; then
        cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "缺少 commit message"
  suggestion: "使用 --message 或 -m 參數提供 commit message"
  recoverable: true
EOF
        return 1
    fi

    # 檢查是否有暫存的變更
    if git diff --cached --quiet 2>/dev/null; then
        cat << EOF
result:
  status: failed
  error_type: NOTHING_TO_COMMIT
  error_message: "沒有暫存的變更"
  suggestion: "請先使用 git add 暫存要提交的檔案"
  recoverable: true
EOF
        return 1
    fi

    # 執行 commit
    if output=$(git commit -m "$message" 2>&1); then
        local commit_hash=$(git rev-parse --short HEAD)
        local stat=$(git diff --stat HEAD~1 2>/dev/null | tail -1 || echo "")

        cat << EOF
result:
  status: success
  commit: $commit_hash
  message: "$message"
  summary: "$stat"
EOF
    else
        local error_type=$(detect_error_type "$output")
        local suggestion=$(suggest_fix "$error_type")
        local recoverable=$(is_recoverable "$error_type")

        cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $recoverable
EOF
        return 1
    fi
}

# 執行 push
execute_push() {
    local branch=""
    local force=false

    # 解析參數
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --branch|-b)
                branch="$2"
                shift 2
                ;;
            --force|-f)
                force=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # 預設推送當前分支
    if [ -z "$branch" ]; then
        branch=$(git branch --show-current 2>/dev/null)
    fi

    # 檢查是否有需要推送的 commit
    local ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    if [ "$ahead" = "0" ]; then
        cat << EOF
result:
  status: skipped
  reason: "沒有需要推送的 commit"
  branch: $branch
EOF
        return 0
    fi

    # 執行 push
    local push_cmd="git push"
    if [ "$force" = true ]; then
        push_cmd="git push --force-with-lease"
    fi

    if output=$($push_cmd origin "$branch" 2>&1); then
        cat << EOF
result:
  status: success
  branch: $branch
  commits_pushed: $ahead
  message: "成功推送到 origin/$branch"
EOF
    else
        local error_type=$(detect_error_type "$output")
        local suggestion=$(suggest_fix "$error_type")

        cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $(is_recoverable "$error_type")
EOF
        return 1
    fi
}

# 執行 add
execute_add() {
    local files=("$@")

    if [ ${#files[@]} -eq 0 ]; then
        cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "沒有指定要添加的檔案"
  suggestion: "請指定檔案路徑，或使用 '.' 添加所有變更"
  recoverable: true
EOF
        return 1
    fi

    if output=$(git add "${files[@]}" 2>&1); then
        local staged=$(git diff --cached --name-only | wc -l | tr -d ' ')

        cat << EOF
result:
  status: success
  files_staged: $staged
  files:
$(git diff --cached --name-only | sed 's/^/    - /')
EOF
    else
        cat << EOF
result:
  status: failed
  error_type: ADD_FAILED
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "檢查檔案路徑是否正確"
  recoverable: true
EOF
        return 1
    fi
}

# 執行分支操作
execute_branch() {
    local action=""
    local branch_name=""

    # 解析參數
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --create)
                action="create"
                branch_name="$2"
                shift 2
                ;;
            --switch)
                action="switch"
                branch_name="$2"
                shift 2
                ;;
            --delete)
                action="delete"
                branch_name="$2"
                shift 2
                ;;
            --list)
                action="list"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    case "$action" in
        create)
            # 建立新分支
            if [ -z "$branch_name" ]; then
                cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "缺少分支名稱"
  suggestion: "使用 --create <branch-name> 建立分支"
  recoverable: true
EOF
                return 1
            fi

            # 檢查分支是否已存在
            if git rev-parse --verify "$branch_name" 2>/dev/null; then
                cat << EOF
result:
  status: failed
  error_type: BRANCH_EXISTS
  error_message: "分支 '$branch_name' 已存在"
  suggestion: "使用其他分支名稱或刪除現有分支"
  recoverable: true
EOF
                return 1
            fi

            if output=$(git branch "$branch_name" 2>&1); then
                cat << EOF
result:
  status: success
  action: created
  branch: $branch_name
  message: "已建立分支 $branch_name"
EOF
            else
                local error_type=$(detect_error_type "$output")
                local suggestion=$(suggest_fix "$error_type")

                cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $(is_recoverable "$error_type")
EOF
                return 1
            fi
            ;;

        switch)
            # 切換分支
            if [ -z "$branch_name" ]; then
                cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "缺少分支名稱"
  suggestion: "使用 --switch <branch-name> 切換分支"
  recoverable: true
EOF
                return 1
            fi

            # 檢查是否有未提交的變更
            if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
                cat << EOF
result:
  status: failed
  error_type: UNCOMMITTED_CHANGES
  error_message: "工作目錄中有未提交的變更"
  suggestion: "提交或暫存變更後再切換分支，或使用 git stash 暫時保存"
  recoverable: true
EOF
                return 1
            fi

            if output=$(git checkout "$branch_name" 2>&1); then
                cat << EOF
result:
  status: success
  action: switched
  branch: $branch_name
  message: "已切換至分支 $branch_name"
EOF
            else
                local error_type=$(detect_error_type "$output")
                local suggestion=$(suggest_fix "$error_type")

                cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $(is_recoverable "$error_type")
EOF
                return 1
            fi
            ;;

        delete)
            # 刪除分支
            if [ -z "$branch_name" ]; then
                cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "缺少分支名稱"
  suggestion: "使用 --delete <branch-name> 刪除分支"
  recoverable: true
EOF
                return 1
            fi

            # 檢查分支是否存在
            if ! git rev-parse --verify "$branch_name" 2>/dev/null; then
                cat << EOF
result:
  status: failed
  error_type: BRANCH_NOT_FOUND
  error_message: "分支 '$branch_name' 不存在"
  suggestion: "檢查分支名稱是否正確"
  recoverable: false
EOF
                return 1
            fi

            # 檢查是否為當前分支
            local current_branch=$(git branch --show-current 2>/dev/null)
            if [ "$current_branch" = "$branch_name" ]; then
                cat << EOF
result:
  status: failed
  error_type: CANNOT_DELETE_CURRENT
  error_message: "無法刪除當前分支 '$branch_name'"
  suggestion: "先切換至其他分支"
  recoverable: true
EOF
                return 1
            fi

            if output=$(git branch -d "$branch_name" 2>&1); then
                cat << EOF
result:
  status: success
  action: deleted
  branch: $branch_name
  message: "已刪除分支 $branch_name"
EOF
            else
                local error_type=$(detect_error_type "$output")
                local suggestion=$(suggest_fix "$error_type")

                cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $(is_recoverable "$error_type")
EOF
                return 1
            fi
            ;;

        list)
            # 列出所有分支
            if output=$(git branch -a 2>&1); then
                local branches=$(git branch -a | sed 's/\*/ /')
                local count=$(echo "$branches" | wc -l | tr -d ' ')

                cat << EOF
result:
  status: success
  action: listed
  total_branches: $count
  branches:
$(echo "$branches" | sed 's/^/    - /' | sed 's/  *//g')
EOF
            else
                local error_type=$(detect_error_type "$output")

                cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  recoverable: false
EOF
                return 1
            fi
            ;;

        *)
            cat << EOF
result:
  status: failed
  error_type: INVALID_ACTION
  error_message: "無效的分支操作"
  suggestion: "使用 --create, --switch, --delete 或 --list"
  recoverable: true
EOF
            return 1
            ;;
    esac
}

# 執行合併操作
execute_merge() {
    local branch_to_merge=""
    local no_ff=false

    # 解析參數
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-ff)
                no_ff=true
                shift
                ;;
            *)
                if [ -z "$branch_to_merge" ]; then
                    branch_to_merge="$1"
                fi
                shift
                ;;
        esac
    done

    if [ -z "$branch_to_merge" ]; then
        cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "缺少要合併的分支名稱"
  suggestion: "使用 merge <branch-name> 指定要合併的分支"
  recoverable: true
EOF
        return 1
    fi

    # 檢查分支是否存在
    if ! git rev-parse --verify "$branch_to_merge" 2>/dev/null; then
        cat << EOF
result:
  status: failed
  error_type: BRANCH_NOT_FOUND
  error_message: "分支 '$branch_to_merge' 不存在"
  suggestion: "檢查分支名稱是否正確"
  recoverable: false
EOF
        return 1
    fi

    # 檢查是否有未提交的變更
    if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
        cat << EOF
result:
  status: failed
  error_type: UNCOMMITTED_CHANGES
  error_message: "工作目錄中有未提交的變更"
  suggestion: "提交或暫存變更後再進行合併"
  recoverable: true
EOF
        return 1
    fi

    # 執行合併
    local merge_cmd="git merge"
    if [ "$no_ff" = true ]; then
        merge_cmd="$merge_cmd --no-ff"
    fi

    if output=$($merge_cmd "$branch_to_merge" 2>&1); then
        # 計算合併的 commits
        local current_branch=$(git branch --show-current 2>/dev/null)
        local commits_merged=$(git rev-list --count "$branch_to_merge"..@{u} 2>/dev/null || echo "0")

        cat << EOF
result:
  status: success
  merged_branch: $branch_to_merge
  commits_merged: $commits_merged
  message: "已成功合併分支 $branch_to_merge 到 $current_branch"
  conflicts: []
EOF
    else
        # 檢測是否發生衝突
        if git status 2>/dev/null | grep -q "both modified"; then
            local conflicted_files=$(git diff --name-only --diff-filter=U | sed 's/^/    - /')
            cat << EOF
result:
  status: conflict
  merged_branch: $branch_to_merge
  error_type: MERGE_CONFLICT
  error_message: "合併發生衝突，請手動解決"
  suggestion: "解決衝突後執行 git add . && git commit"
  recoverable: true
  conflicts:
$conflicted_files
EOF
            return 1
        else
            local error_type=$(detect_error_type "$output")
            local suggestion=$(suggest_fix "$error_type")

            cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $(is_recoverable "$error_type")
EOF
            return 1
        fi
    fi
}

# 執行檢出操作
execute_checkout() {
    local target=""
    local reset_file=false

    # 解析參數
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --)
                reset_file=true
                shift
                ;;
            *)
                target="$1"
                shift
                ;;
        esac
    done

    if [ -z "$target" ]; then
        cat << EOF
result:
  status: failed
  error_type: MISSING_ARGUMENT
  error_message: "缺少檢出目標（分支或檔案）"
  suggestion: "使用 checkout <branch> 或 checkout -- <file>"
  recoverable: true
EOF
        return 1
    fi

    if [ "$reset_file" = true ]; then
        # 放棄檔案變更
        if [ ! -f "$target" ]; then
            cat << EOF
result:
  status: failed
  error_type: FILE_NOT_FOUND
  error_message: "檔案 '$target' 不存在"
  suggestion: "檢查檔案路徑是否正確"
  recoverable: false
EOF
            return 1
        fi

        if output=$(git checkout -- "$target" 2>&1); then
            cat << EOF
result:
  status: success
  action: file_reset
  file: $target
  message: "已放棄檔案 $target 的變更"
EOF
        else
            local error_type=$(detect_error_type "$output")

            cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  recoverable: false
EOF
            return 1
        fi
    else
        # 檢出分支
        # 檢查分支是否存在
        if ! git rev-parse --verify "$target" 2>/dev/null; then
            cat << EOF
result:
  status: failed
  error_type: BRANCH_NOT_FOUND
  error_message: "分支 '$target' 不存在"
  suggestion: "檢查分支名稱是否正確"
  recoverable: false
EOF
            return 1
        fi

        # 檢查是否有未提交的變更
        if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
            cat << EOF
result:
  status: failed
  error_type: UNCOMMITTED_CHANGES
  error_message: "工作目錄中有未提交的變更"
  suggestion: "提交或暫存變更後再檢出分支"
  recoverable: true
EOF
            return 1
        fi

        if output=$(git checkout "$target" 2>&1); then
            cat << EOF
result:
  status: success
  action: branch_checkout
  branch: $target
  message: "已檢出分支 $target"
EOF
        else
            local error_type=$(detect_error_type "$output")
            local suggestion=$(suggest_fix "$error_type")

            cat << EOF
result:
  status: failed
  error_type: $error_type
  error_message: |
$(echo "$output" | sed 's/^/    /')
  suggestion: "$suggestion"
  recoverable: $(is_recoverable "$error_type")
EOF
            return 1
        fi
    fi
}

# 主函數
main() {
    local command="${1:-}"
    shift || true

    case "$command" in
        commit)
            track_usage "commit"
            execute_commit "$@"
            ;;
        push)
            track_usage "push"
            execute_push "$@"
            ;;
        add)
            track_usage "add"
            execute_add "$@"
            ;;
        branch)
            track_usage "branch"
            execute_branch "$@"
            ;;
        merge)
            track_usage "merge"
            execute_merge "$@"
            ;;
        checkout)
            track_usage "checkout"
            execute_checkout "$@"
            ;;
        --help|-h|"")
            show_help
            ;;
        *)
            echo "錯誤：未知命令 '$command'"
            echo "使用 --help 查看幫助"
            exit 1
            ;;
    esac
}

main "$@"
