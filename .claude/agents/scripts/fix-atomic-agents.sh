#!/bin/bash

# 修復所有 Atomic Agents 的配置問題

set -e

BASE_DIR="/Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/agents/atomic"

echo "========================================="
echo "開始修復 Atomic Agents 配置"
echo "========================================="
echo ""

# 函數：移除重複的 context 行
remove_duplicate_context() {
    local file="$1"
    local pattern="$2"

    # 使用 awk 只保留第一次出現的行
    awk '
        /^context:$/ { in_context=1; print; next }
        /^---$/ && in_context { in_context=0 }
        in_context {
            if (substr($0, 1, 4) == "  - ") {
                if (!seen[$0]++) print
            } else {
                print
            }
            next
        }
        { print }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"

    echo "✓ 已修復重複 context: $(basename $file)"
}

# 函數：在 context 中新增一行
add_context_line() {
    local file="$1"
    local new_line="$2"

    # 檢查是否已存在
    if grep -q "$new_line" "$file"; then
        return 0
    fi

    # 在 context: 後面插入新行
    awk -v line="  - $new_line" '
        /^context:$/ { print; getline; print line; print; next }
        { print }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"

    echo "✓ 已新增 context: $new_line → $(basename $file)"
}

# 函數：更新 description 加入 AST-GREP 說明
add_ast_grep_to_description() {
    local file="$1"

    # 檢查是否已經包含 ast-grep 說明
    if grep -q "ast-grep" "$file" || grep -q "AST-GREP" "$file"; then
        return 0
    fi

    # 在 description 最後一行前加入說明
    sed -i.bak '/^description: |$/,/^context:$/{
        /^context:$/i\
  優先使用 ast-grep 進行代碼結構搜索（LL-001）
    }' "$file" && rm "$file.bak"

    echo "✓ 已更新 description: $(basename $file)"
}

echo "## 1. 移除重複的 context"
echo ""

# 移除重複的 ROLE-03
for agent in code-generator code-editor code-formatter data-validator query-writer performance-tuner code-simplifier naming-improver duplicate-remover; do
    file="$BASE_DIR"/*/"$agent.md"
    if [ -f "$file" ]; then
        remove_duplicate_context "$file" "ROLE-03"
    fi
done

# 移除重複的 ARCH-01
for agent in file-finder dependency-tracer; do
    file="$BASE_DIR"/*/"$agent.md"
    if [ -f "$file" ]; then
        remove_duplicate_context "$file" "ARCH-01"
    fi
done

echo ""
echo "## 2. 新增 CODE-SEARCH-BEST-PRACTICES.md"
echo ""

CODE_RELATED_AGENTS=(
    "search/file-finder"
    "code/code-generator"
    "code/code-editor"
    "code/code-deleter"
    "code/code-formatter"
    "refactor/code-simplifier"
    "refactor/duplicate-remover"
    "refactor/naming-improver"
    "refactor/performance-tuner"
    "test/test-writer"
    "test/test-fixer"
    "design/api-designer"
    "design/interface-designer"
)

for agent in "${CODE_RELATED_AGENTS[@]}"; do
    file="$BASE_DIR/$agent.md"
    if [ -f "$file" ]; then
        add_context_line "$file" ".ai-docs/knowledge/universal/claude-doc/CODE-SEARCH-BEST-PRACTICES.md"
        add_ast_grep_to_description "$file"
    fi
done

echo ""
echo "## 3. 新增 ADR-003 架構規範"
echo ""

NEEDS_ADR003=(
    "code/code-generator"
    "code/code-editor"
    "refactor/code-simplifier"
    "test/test-writer"
)

for agent in "${NEEDS_ADR003[@]}"; do
    file="$BASE_DIR/$agent.md"
    if [ -f "$file" ]; then
        add_context_line "$file" ".ai-docs/knowledge/universal/adr/ADR-003-layered-architecture-standards/README.md"
    fi
done

echo ""
echo "========================================="
echo "修復完成！"
echo "========================================="
