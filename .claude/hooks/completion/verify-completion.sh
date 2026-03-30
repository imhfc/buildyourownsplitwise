#!/bin/bash
# .claude/hooks/completion/verify-completion.sh
# Hook: Stop
# 用途：Claude 即將結束回應時，檢查工作是否真正完成
# 已適配：Python/FastAPI + React Native/Expo 專案
#
# 設計原則：
# - 無工作訊號時靜默通過
# - 有未完成項目時輸出結構化提醒
# - 分三級檢查：快速 → 品質 → 合規
# - 總執行時間 < 2 秒

set -u

# 讀取 stdin
input=$(cat 2>/dev/null || echo "{}")

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-.}"
cd "$PROJECT_ROOT" 2>/dev/null || exit 0

# ============================================
# 收集器：各級檢查結果
# ============================================
warnings=()
suggestions=()

# ============================================
# Level 1: 快速檢查（每次都執行，< 0.5 秒）
# ============================================

# --- Check 1-1: Git 未提交變更 ---
git_status=""
if git rev-parse --is-inside-work-tree &>/dev/null; then
    git_status=$(git status --porcelain 2>/dev/null || echo "")
fi

staged_count=0
unstaged_count=0

if [[ -n "$git_status" ]]; then
    staged_count=$(echo "$git_status" | grep '^[MADRC]' 2>/dev/null | wc -l | tr -d ' ')
    unstaged_count=$(echo "$git_status" | grep '^.[MADRC]' 2>/dev/null | wc -l | tr -d ' ')

    total_changes=$((staged_count + unstaged_count))
    if [[ "$total_changes" -gt 0 ]]; then
        warnings+=("[未提交] ${total_changes} 個檔案有變更（${staged_count} 已暫存 / ${unstaged_count} 未暫存）")
    fi
fi

# --- Check 1-2: 辨識變更類型 ---
py_files=""
tsx_files=""
has_backend_changes=false
has_mobile_changes=false

if [[ -n "$git_status" ]]; then
    py_files=$(echo "$git_status" | grep '\.py$' 2>/dev/null || echo "")
    tsx_files=$(echo "$git_status" | grep -E '\.(tsx?|jsx?)$' 2>/dev/null || echo "")

    if [[ -n "$py_files" ]]; then
        has_backend_changes=true
        py_count=$(echo "$py_files" | wc -l | tr -d ' ')
        suggestions+=("[Python] ${py_count} 個 Python 檔案有變更 — 建議執行 pytest tests/")
    fi

    if [[ -n "$tsx_files" ]]; then
        has_mobile_changes=true
        tsx_count=$(echo "$tsx_files" | wc -l | tr -d ' ')
        suggestions+=("[Mobile] ${tsx_count} 個 TypeScript/React 檔案有變更 — 建議執行 quality-gate.sh")
    fi
fi

# ============================================
# Level 2: 品質檢查（偵測到代碼變更時）
# ============================================

# --- Check 2-1: 後端 TODO/FIXME 殘留 ---
if [[ "$has_backend_changes" == "true" ]]; then
    todo_total=0
    todo_files=""
    while IFS= read -r line; do
        filepath=$(echo "$line" | awk '{print $NF}')
        if [[ -f "$filepath" ]]; then
            count=$(grep -E '(TODO|FIXME|HACK|XXX)' "$filepath" 2>/dev/null | wc -l | tr -d ' ')
            if [[ "$count" -gt 0 ]]; then
                todo_total=$((todo_total + count))
                basename_f=$(basename "$filepath")
                todo_files="${todo_files}${basename_f}(${count}) "
            fi
        fi
    done <<< "$py_files"

    if [[ "$todo_total" -gt 0 ]]; then
        warnings+=("[TODO] 變更的 Python 檔案中有 ${todo_total} 個 TODO/FIXME — ${todo_files}")
    fi

    # --- Check 2-2: 後端測試是否同步更新 ---
    src_changed=0
    test_changed=0
    while IFS= read -r line; do
        filepath=$(echo "$line" | awk '{print $NF}')
        if echo "$filepath" | grep -q 'tests/' 2>/dev/null; then
            test_changed=$((test_changed + 1))
        elif echo "$filepath" | grep -qE 'app/(api|services|models)/' 2>/dev/null; then
            src_changed=$((src_changed + 1))
        fi
    done <<< "$py_files"

    if [[ "$src_changed" -gt 0 && "$test_changed" -eq 0 ]]; then
        suggestions+=("[測試] ${src_changed} 個 app/ 檔案變更但無對應測試更新")
    fi
fi

# --- Check 2-3: Mobile TODO/FIXME 殘留 ---
if [[ "$has_mobile_changes" == "true" ]]; then
    tsx_todo_total=0
    while IFS= read -r line; do
        filepath=$(echo "$line" | awk '{print $NF}')
        if [[ -f "$filepath" ]]; then
            count=$(grep -E '(TODO|FIXME|HACK|XXX)' "$filepath" 2>/dev/null | wc -l | tr -d ' ')
            tsx_todo_total=$((tsx_todo_total + count))
        fi
    done <<< "$tsx_files"

    if [[ "$tsx_todo_total" -gt 0 ]]; then
        warnings+=("[TODO] 變更的 Mobile 檔案中有 ${tsx_todo_total} 個 TODO/FIXME")
    fi
fi

# ============================================
# Level 3: 合規檢查
# ============================================

# --- Check 3-1: QUALITY_SLA.md 報告 ---
for report in "$PROJECT_ROOT"/*SPEC-VERIFY*.md \
              "$PROJECT_ROOT"/*COMPLIANCE*.md \
              "$PROJECT_ROOT"/*REVIEW*.md; do
    if [[ -f "$report" ]]; then
        if [[ $(find "$report" -mmin -30 2>/dev/null | wc -l) -gt 0 ]]; then
            fail_count=$(grep -E '\[FAIL\]|\[ERROR\]|Critical' "$report" 2>/dev/null | wc -l | tr -d ' ')
            if [[ "$fail_count" -gt 0 ]]; then
                report_name=$(basename "$report")
                warnings+=("[報告] ${report_name} 有 ${fail_count} 個未解決問題")
            fi
        fi
    fi
done

# ============================================
# 輸出決策
# ============================================

# 無任何訊號 → 判斷是否有實質工作（有 code 變更才提示回顧）
if [[ ${#warnings[@]} -eq 0 && ${#suggestions[@]} -eq 0 ]]; then
    # 如果有程式碼變更，輕量提示回顧
    if [[ -n "$git_status" ]] && [[ -n "$py_files" || -n "$tsx_files" ]]; then
        echo "[TIP] 本次有程式碼變更，結束前可執行 /retro 沉澱學到的知識。"
    fi
    exit 0
fi

# 只有建議沒有警告 → 輕量提示
if [[ ${#warnings[@]} -eq 0 ]]; then
    echo "==== 完成度檢查（資訊）===="
    echo ""
    for s in "${suggestions[@]}"; do
        echo "  $s"
    done
    echo ""
    echo "===================="
    exit 0
fi

# 有警告 → 完整提醒
echo "==== 完成度檢查 ===="
echo ""

echo "待處理（${#warnings[@]} 項）:"
for w in "${warnings[@]}"; do
    echo "  - $w"
done
echo ""

if [[ ${#suggestions[@]} -gt 0 ]]; then
    echo "建議:"
    for s in "${suggestions[@]}"; do
        echo "  - $s"
    done
    echo ""
fi

echo "請確認以上項目已處理完畢，或向用戶說明原因後再結束工作。"
echo ""
echo "[TIP] 結束前可執行 /retro 回顧本次對話，將學到的知識沉澱到框架中。"
echo "===================="
exit 0
