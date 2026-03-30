#!/bin/bash
# Git Operations Framework - 資訊收集器
# 用途：收集 Git 狀態資訊並壓縮為 AI 決策所需的精簡格式
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
GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

# 載入輔助函數
source "$SCRIPT_DIR/lib/file-type.sh"
source "$SCRIPT_DIR/lib/change-extractor.sh"
source "$SCRIPT_DIR/lib/error-handler.sh"

# 使用追蹤
track_usage() {
    local action="$1"
    local status="${2:-success}"
    local tracker="$SCRIPT_DIR/../telemetry/usage-tracker.sh"
    if [[ -x "$tracker" ]]; then
        "$tracker" "git-collector" "$action" "$status" &>/dev/null &
    fi
}

# 配置
MAX_KEY_CHANGES=5
MAX_RECENT_COMMITS=5
MAX_COMMITS_TO_PUSH=10
MAX_RECENT_BRANCHES=10
MAX_HISTORY_COMMITS=10
MAX_CONTRIBUTORS=10

# 顯示幫助
show_help() {
    cat << EOF
Git Information Collector

用法: git-collector.sh [選項]

選項:
  --for-commit    收集 commit 所需的上下文資訊
  --status        收集精簡的狀態資訊
  --for-push      收集 push 所需的上下文資訊
  --for-branch    收集分支管理資訊
  --for-merge     收集合併前檢查資訊 (需提供目標分支)
  --history       收集歷史分析資訊 (可選檔案路徑)
  --help          顯示此幫助資訊

輸出格式: YAML

範例:
  git-collector.sh --for-commit      # 準備提交前的資訊
  git-collector.sh --status          # 快速查看狀態
  git-collector.sh --for-push        # 推送前的檢查
  git-collector.sh --for-branch      # 分支管理資訊
  git-collector.sh --for-merge develop  # 合併到 develop 的檢查
  git-collector.sh --history         # 完整歷史分析
  git-collector.sh --history src/main/java/UserService.java  # 特定檔案歷史
EOF
}

# 取得目前分支名稱
get_current_branch() {
    git branch --show-current 2>/dev/null || echo "detached"
}

# 取得已暫存檔案統計
get_staged_stats() {
    git diff --cached --stat 2>/dev/null | tail -1 || echo "no changes"
}

# 取得已暫存檔案清單
get_staged_files() {
    git diff --cached --name-status 2>/dev/null || true
}

# 取得未暫存變更檔案數
get_unstaged_count() {
    git diff --name-only 2>/dev/null | wc -l | tr -d ' '
}

# 取得未追蹤檔案數
get_untracked_count() {
    git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' '
}

# 取得領先遠端的 commit 數
get_ahead_count() {
    git rev-list --count @{u}..HEAD 2>/dev/null || echo "0"
}

# 取得落後遠端的 commit 數
get_behind_count() {
    git rev-list --count HEAD..@{u} 2>/dev/null || echo "0"
}

# 取得遠端名稱
get_remote_name() {
    local branch=$(get_current_branch)
    git config --get "branch.$branch.remote" 2>/dev/null || echo "origin"
}

# 取得上游追蹤分支
get_upstream_branch() {
    git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "none"
}

# 檢查是否有本地變更
is_clean() {
    local staged=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
    local unstaged=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
    local untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

    if [ "$staged" = "0" ] && [ "$unstaged" = "0" ] && [ "$untracked" = "0" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# 獲取本地分支列表及其資訊
get_local_branches_info() {
    git branch -v --format="%(refname:short)|%(objectname:short)|%(upstream:short)|%(committerdate:unix)" 2>/dev/null | head -n "$MAX_RECENT_BRANCHES" || true
}

# 獲取遠端分支列表
get_remote_branches() {
    git branch -r 2>/dev/null | head -n "$MAX_RECENT_BRANCHES" || true
}

# 計算分支領先/落後提交數
get_branch_sync_info() {
    local branch=$1
    local tracking=$(git for-each-ref --format='%(upstream:short)' "refs/heads/$branch" 2>/dev/null)

    if [ -z "$tracking" ]; then
        echo "no_tracking"
        return
    fi

    local ahead=$(git rev-list --count "$tracking..$branch" 2>/dev/null || echo "0")
    local behind=$(git rev-list --count "$branch..$tracking" 2>/dev/null || echo "0")

    echo "${ahead}|${behind}"
}

# 檢查合併狀態
can_fast_forward() {
    local from=$1
    local to=$2

    # 檢查是否可快進合併
    if git merge-base --is-ancestor "$from" "$to" 2>/dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

# 獲取要合併的提交數量
get_commits_to_merge() {
    local from=$1
    local to=$2

    git rev-list --count "$to..$from" 2>/dev/null || echo "0"
}

# 檢測潛在衝突
detect_merge_conflicts() {
    local from=$1
    local to=$2
    local merge_base=$(git merge-base "$from" "$to" 2>/dev/null)

    if [ -z "$merge_base" ]; then
        return
    fi

    # 檢查衝突風險的檔案
    git diff --name-only "$merge_base...$from" 2>/dev/null | \
    while read -r from_file; do
        if git diff --name-only "$merge_base...$to" 2>/dev/null | grep -q "^$from_file$"; then
            # 檢查衝突風險程度
            local from_changes=$(git show "$from:$from_file" 2>/dev/null | wc -l || echo "0")
            local to_changes=$(git show "$to:$from_file" 2>/dev/null | wc -l || echo "0")

            if [ "$from_changes" -gt 50 ] && [ "$to_changes" -gt 50 ]; then
                echo "    - file: \"$from_file\""
                echo "      risk: \"high\""
            elif [ "$from_changes" -gt 10 ] || [ "$to_changes" -gt 10 ]; then
                echo "    - file: \"$from_file\""
                echo "      risk: \"medium\""
            else
                echo "    - file: \"$from_file\""
                echo "      risk: \"low\""
            fi
        fi
    done
}

# 獲取最近修改的分支
get_recent_branches_activity() {
    git for-each-ref --sort=-committerdate --format='%(refname:short) (%(committerdate:relative))' refs/heads/ 2>/dev/null | head -n "$MAX_RECENT_BRANCHES" || true
}

# 獲取提交歷史
get_commit_history() {
    local file=$1
    local format='%h|%an|%cd|%s'

    if [ -n "$file" ] && [ -f "$file" ]; then
        git log --pretty=format:"$format" --date=short "$file" 2>/dev/null | head -n "$MAX_HISTORY_COMMITS" || true
    else
        git log --pretty=format:"$format" --date=short 2>/dev/null | head -n "$MAX_HISTORY_COMMITS" || true
    fi
}

# 獲取貢獻者統計
get_contributors_stats() {
    local file=$1

    if [ -n "$file" ] && [ -f "$file" ]; then
        git shortlog -sne "$file" 2>/dev/null | head -n "$MAX_CONTRIBUTORS" || true
    else
        git shortlog -sne 2>/dev/null | head -n "$MAX_CONTRIBUTORS" || true
    fi
}

# 獲取活動統計
get_activity_stats() {
    # 上週提交數
    local last_week=$(git log --since="7 days ago" --oneline 2>/dev/null | wc -l | tr -d ' ')

    # 上月提交數
    local last_month=$(git log --since="30 days ago" --oneline 2>/dev/null | wc -l | tr -d ' ')

    echo "${last_week}|${last_month}"
}

# 收集 commit 上下文
collect_for_commit() {
    local branch=$(get_current_branch)
    local stat=$(get_staged_stats)
    local staged_count=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')

    cat << EOF
commit_context:
  branch: "$branch"
  status: "$stat"
  staged_files_count: $staged_count

  files:
EOF

    # 遍歷已暫存的檔案
    if [ "$staged_count" -gt 0 ]; then
        get_staged_files | while read -r status file; do
            local file_type=$(detect_file_type "$file")
            local key_changes=$(extract_key_changes "$file" "$MAX_KEY_CHANGES" 2>/dev/null || echo "無法提取")

            cat << EOF
    - file: "$file"
      status: "$status"
      type: "$file_type"
      key_changes: "$key_changes"
EOF
        done
    else
        cat << EOF
    # 無已暫存檔案
EOF
    fi

    cat << EOF

  recent_commits:
    count: $MAX_RECENT_COMMITS
    patterns:
EOF

    # 取得最近的 commit 風格
    if git log --oneline -1 >/dev/null 2>&1; then
        git log --oneline -"$MAX_RECENT_COMMITS" 2>/dev/null | while read -r line; do
            echo "      - \"$line\""
        done
    else
        echo "      # 尚無 commit"
    fi

    cat << EOF

  hooks_status:
    pre_commit: $(test -x "$GIT_ROOT/.git/hooks/pre-commit" 2>/dev/null && echo "enabled" || echo "disabled")
    commit_msg: $(test -x "$GIT_ROOT/.git/hooks/commit-msg" 2>/dev/null && echo "enabled" || echo "disabled")
    prepare_commit_msg: $(test -x "$GIT_ROOT/.git/hooks/prepare-commit-msg" 2>/dev/null && echo "enabled" || echo "disabled")
EOF
}

# 收集精簡狀態
collect_status() {
    local branch=$(get_current_branch)
    local staged=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
    local unstaged=$(get_unstaged_count)
    local untracked=$(get_untracked_count)
    local ahead=$(get_ahead_count)
    local behind=$(get_behind_count)
    local clean=$(is_clean)

    cat << EOF
status:
  branch: "$branch"
  staged_files: $staged
  unstaged_files: $unstaged
  untracked_files: $untracked
  ahead_of_remote: $ahead
  behind_remote: $behind
  working_tree_clean: $clean

  summary:
    total_changes: $((staged + unstaged + untracked))
    has_uncommitted: $([ "$((staged + unstaged))" -gt 0 ] && echo "true" || echo "false")
    has_untracked: $([ "$untracked" -gt 0 ] && echo "true" || echo "false")
EOF
}

# 收集 push 上下文
collect_for_push() {
    local branch=$(get_current_branch)
    local remote=$(get_remote_name)
    local upstream=$(get_upstream_branch)
    local ahead=$(get_ahead_count)
    local behind=$(get_behind_count)

    cat << EOF
push_context:
  branch: "$branch"
  remote: "$remote"
  upstream_branch: "$upstream"
  ahead_of_remote: $ahead
  behind_remote: $behind

  commits_to_push:
EOF

    if [ "$ahead" -gt 0 ]; then
        local limit=$((ahead < MAX_COMMITS_TO_PUSH ? ahead : MAX_COMMITS_TO_PUSH))

        # 取得待推送的 commit hash 列表
        git log @{u}..HEAD --format=%H -n "$limit" 2>/dev/null | while read -r commit_hash; do
            # 取得 commit 基本資訊
            local commit_info=$(git log --format="%h|%s" -n 1 "$commit_hash" 2>/dev/null)
            local short_hash=$(echo "$commit_info" | cut -d'|' -f1)
            local message=$(echo "$commit_info" | cut -d'|' -f2-)

            cat << EOF
    - commit: "$short_hash"
      message: "$message"
      files:
EOF

            # 列出此 commit 的變更檔案
            git diff-tree --no-commit-id --name-status -r "$commit_hash" 2>/dev/null | head -n 10 | while read -r status file; do
                local file_type=$(detect_file_type "$file")

                # 嘗試提取關鍵變更（僅針對 Modified 的檔案）
                local key_changes="N/A"
                if [ "$status" = "M" ] && [ -f "$file" ]; then
                    # 取得此 commit 中該檔案的變更摘要
                    key_changes=$(git show "$commit_hash" -- "$file" | grep -E "^[\+\-]" | grep -v "^[\+\-][\+\-][\+\-]" | head -n 3 | sed 's/^/        /' || echo "        無法提取")
                fi

                cat << EOF
        - file: "$file"
          status: "$status"
          type: "$file_type"
EOF

                if [ "$status" = "M" ]; then
                    echo "          key_changes: |"
                    echo "$key_changes"
                fi
            done

            # 如果檔案數超過 10 個，顯示提示
            local total_files=$(git diff-tree --no-commit-id --name-only -r "$commit_hash" 2>/dev/null | wc -l | tr -d ' ')
            if [ "$total_files" -gt 10 ]; then
                echo "        - \"... 還有 $((total_files - 10)) 個檔案\""
            fi
        done

        if [ "$ahead" -gt "$MAX_COMMITS_TO_PUSH" ]; then
            local remaining=$((ahead - MAX_COMMITS_TO_PUSH))
            echo "    - \"... 還有 $remaining 個 commit\""
        fi
    else
        echo "    # 無新 commit 待推送"
    fi

    cat << EOF

  warnings:
EOF

    local has_warning=false

    if [ "$behind" != "0" ]; then
        echo "    - \"遠端有 $behind 個新 commit，建議先執行 pull\""
        has_warning=true
    fi

    if [ "$branch" = "master" ] || [ "$branch" = "main" ]; then
        echo "    - \"正在推送到主分支，請確認無誤\""
        has_warning=true
    fi

    if [ "$ahead" = "0" ]; then
        echo "    - \"無 commit 需要推送\""
        has_warning=true
    fi

    # 檢查是否有未暫存的變更
    if [ "$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "    - \"工作目錄有未暫存的變更，建議先提交\""
        has_warning=true
    fi

    if [ "$has_warning" = "false" ]; then
        echo "    # 無警告"
    fi

    cat << EOF

  hooks_status:
    pre_push: $(test -x "$GIT_ROOT/.git/hooks/pre-push" 2>/dev/null && echo "enabled" || echo "disabled")
    post_push: $(test -x "$GIT_ROOT/.git/hooks/post-push" 2>/dev/null && echo "enabled" || echo "disabled")

  sync_status:
    in_sync: $([ "$ahead" = "0" ] && [ "$behind" = "0" ] && echo "true" || echo "false")
    ready_to_push: $([ "$ahead" -gt 0 ] && [ "$behind" = "0" ] && echo "true" || echo "false")
EOF
}

# 收集分支管理資訊
collect_for_branch() {
    local current_branch=$(get_current_branch)

    cat << EOF
branch_context:
  current: "$current_branch"

  local_branches:
EOF

    # 顯示本地分支及其詳細資訊
    get_local_branches_info | while IFS='|' read -r branch commit tracking timestamp; do
        branch=$(echo "$branch" | xargs)
        commit=$(echo "$commit" | xargs)

        # 獲取該分支的領先/落後資訊
        local sync_info=$(get_branch_sync_info "$branch")
        if [ "$sync_info" != "no_tracking" ]; then
            local ahead=$(echo "$sync_info" | cut -d'|' -f1)
            local behind=$(echo "$sync_info" | cut -d'|' -f2)
        else
            local ahead=0
            local behind=0
        fi

        cat << EOF
    - name: "$branch"
      last_commit: "$commit"
      ahead: $ahead
      behind: $behind
EOF
    done

    cat << EOF

  remote_branches:
EOF

    # 顯示遠端分支
    get_remote_branches | while read -r branch; do
        branch=$(echo "$branch" | xargs | sed 's/^ *//')
        echo "    - \"$branch\""
    done

    cat << EOF

  recent_branches:
EOF

    # 顯示最近活動的分支
    get_recent_branches_activity | while read -r line; do
        echo "    - \"$line\""
    done
}

# 收集合併前檢查資訊
collect_for_merge() {
    local target=$1
    local current=$(get_current_branch)

    if [ -z "$target" ]; then
        echo "錯誤：必須指定目標分支"
        echo "用法：git-collector.sh --for-merge <target-branch>"
        exit 1
    fi

    # 驗證目標分支是否存在
    if ! git rev-parse --verify "$target" >/dev/null 2>&1; then
        echo "錯誤：目標分支 '$target' 不存在"
        exit 1
    fi

    local can_ff=$(can_fast_forward "$current" "$target")
    local commits_count=$(get_commits_to_merge "$current" "$target")
    local has_local_changes=$([ "$(is_clean)" = "true" ] && echo "false" || echo "true")

    cat << EOF
merge_context:
  current: "$current"
  target: "$target"
  can_fast_forward: $can_ff
  commits_to_merge: $commits_count

  potential_conflicts:
EOF

    # 檢測潛在衝突
    conflicts=$(detect_merge_conflicts "$current" "$target")
    if [ -z "$conflicts" ]; then
        echo "    # 無潛在衝突"
    else
        echo "$conflicts"
    fi

    cat << EOF

  warnings:
EOF

    local has_warning=false

    # 檢查是否有本地未提交的變更
    if [ "$has_local_changes" = "true" ]; then
        echo "    - \"目標分支有未提交的變更，建議先提交或暫存\""
        has_warning=true
    fi

    # 檢查是否有落後遠端
    local behind=$(git rev-list --count "$target..@{u}" 2>/dev/null || echo "0")
    if [ "$behind" != "0" ] && [ "$behind" != "" ]; then
        echo "    - \"目標分支落後遠端 $behind 個提交，建議先拉取\""
        has_warning=true
    fi

    # 檢查是否在主分支上
    if [ "$target" = "master" ] || [ "$target" = "main" ] || [ "$target" = "develop" ]; then
        echo "    - \"正在合併到 $target 分支，請確認無誤\""
        has_warning=true
    fi

    # 檢查提交數量
    if [ "$commits_count" -gt 20 ]; then
        echo "    - \"待合併提交數較多 ($commits_count 個)，建議分步驟合併\""
        has_warning=true
    fi

    if [ "$has_warning" = "false" ]; then
        echo "    # 無警告"
    fi

    cat << EOF

  readiness:
    has_local_changes: $has_local_changes
    ready_to_merge: $([ "$commits_count" -gt 0 ] && [ "$has_local_changes" = "false" ] && echo "true" || echo "false")
EOF
}

# 收集歷史分析資訊
collect_history() {
    local file=$1

    cat << EOF
history_context:
EOF

    if [ -n "$file" ] && [ -f "$file" ]; then
        echo "  file: \"$file\""
    else
        echo "  file: null"
    fi

    cat << EOF

  recent_commits:
EOF

    # 顯示最近的提交
    get_commit_history "$file" | while IFS='|' read -r hash author date message; do
        cat << EOF
    - hash: "$hash"
      author: "$author"
      date: "$date"
      message: "$message"
EOF
    done

    cat << EOF

  contributors:
EOF

    # 顯示貢獻者統計
    get_contributors_stats "$file" | while read -r line; do
        commits=$(echo "$line" | awk '{print $1}')
        author=$(echo "$line" | cut -d' ' -f2-)

        cat << EOF
    - name: "$author"
      commits: $commits
EOF
    done

    cat << EOF

  activity:
EOF

    # 顯示活動統計
    local stats=$(get_activity_stats)
    local last_week=$(echo "$stats" | cut -d'|' -f1)
    local last_month=$(echo "$stats" | cut -d'|' -f2)

    cat << EOF
    last_week: $last_week
    last_month: $last_month
EOF
}

# 主函數
main() {
    case "${1:-}" in
        --for-commit)
            track_usage "for-commit"
            collect_for_commit
            ;;
        --status)
            track_usage "status"
            collect_status
            ;;
        --for-push)
            track_usage "for-push"
            collect_for_push
            ;;
        --for-branch)
            track_usage "for-branch"
            collect_for_branch
            ;;
        --for-merge)
            track_usage "for-merge"
            collect_for_merge "$2"
            ;;
        --history)
            track_usage "history"
            collect_history "$2"
            ;;
        --help|-h)
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                echo "錯誤：未指定選項"
                echo
                show_help
                exit 1
            else
                echo "錯誤：未知選項 '$1'"
                echo "使用 --help 查看幫助"
                exit 1
            fi
            ;;
    esac
}

main "$@"
