#!/bin/bash

# 審查所有 Atomic Agents 的配置問題

echo "========================================="
echo "Atomic Agents 配置審查"
echo "========================================="
echo ""

BASE_DIR="/Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/agents/atomic"

# 檢查重複的 context
echo "## 1. 檢查重複的 context 配置"
echo ""

for file in $(find "$BASE_DIR" -name "*.md" -type f ! -name "README.md" ! -name "STANDARDS-MAPPING.md" ! -name "COMPOSITION-STRATEGY.md" ! -name "QUICK-START.md"); do
    # 提取 frontmatter 中的 context 部分
    context_lines=$(sed -n '/^context:$/,/^---$/p' "$file" | grep -v "^---$" | grep -v "^context:$" | grep "^  -")

    # 檢查重複
    duplicates=$(echo "$context_lines" | sort | uniq -d)

    if [ -n "$duplicates" ]; then
        echo "❌ $(basename $file | sed 's/.md//')"
        echo "   重複的 context:"
        echo "$duplicates" | sed 's/^/   /'
        echo ""
    fi
done

echo ""
echo "## 2. 檢查缺少 CODE-SEARCH-BEST-PRACTICES.md 的 agents"
echo ""
echo "（代碼相關 agents 應該載入此文件）"
echo ""

# 代碼相關的 agents
CODE_RELATED_AGENTS=(
    "search/file-finder"
    "search/code-searcher"
    "search/symbol-locator"
    "search/dependency-tracer"
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
        if ! grep -q "CODE-SEARCH-BEST-PRACTICES.md" "$file"; then
            echo "⚠️  $(basename $agent)"
        fi
    fi
done

echo ""
echo "## 3. 檢查缺少 ADR-003 的代碼生成 agents"
echo ""
echo "（生成/編輯代碼的 agents 應該了解架構規範）"
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
        if ! grep -q "ADR-003" "$file"; then
            echo "⚠️  $(basename $agent)"
        fi
    fi
done

echo ""
echo "========================================="
echo "審查完成"
echo "========================================="
