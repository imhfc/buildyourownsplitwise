#!/usr/bin/env python3
"""修復 .ai-docs 目錄中的死連結"""

import os
import re
from pathlib import Path

def fix_links(content, file_path):
    """修復連結"""
    modified = False

    # 修復規則
    fixes = [
        # 1. openspec-integration.md 移除（不存在）
        (r'\[openspec-integration\]\(\.\./\.claude/docs/openspec-integration\.md\)', '[OPENSPEC-INTEGRATION-STEPS](../.claude/docs/OPENSPEC-INTEGRATION-STEPS.md)'),

        # 2. 路徑層級錯誤：./../.ai-docs/ → ../../../
        (r'\]\(\.\/\.\./\.ai-docs/', r'](../../../'),

        # 3. memory-bank 路徑：memory-bank/ → .claude/memory-bank/
        (r'\]\(([./]*)memory-bank/', r'](\1.claude/memory-bank/'),
        (r'\]\(\.\.\/\.\.\/\.\.\/\.\.\/memory-bank/', r'](../../../../.claude/memory-bank/'),

        # 4. dev-plans 引用 dev-specs 路徑錯誤
        # 從 dev-plans/v1.0/order-mgmt/ 引用 dev-specs/v1.0/order-mgmt/
        (r'\]\(([./]*)dev-specs/', lambda m: fix_dev_specs_path(m, file_path)),

        # 5. knowledge 路徑層級錯誤
        (r'\]\(([./]*)knowledge/project-specific/', r'](\1../../../knowledge/project-specific/'),
        (r'\]\(([./]*)knowledge/universal/', r'](\1../../../knowledge/universal/'),
    ]

    for pattern, replacement in fixes:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                modified = True
                content = new_content

    return content, modified

def fix_dev_specs_path(match, file_path):
    """修復 dev-specs 路徑"""
    prefix = match.group(1) if match.group(1) else ''

    # 如果在 dev-plans 目錄中
    if '/dev-plans/' in file_path:
        # 從 dev-plans/v1.0/order-mgmt/ 到 dev-specs/v1.0/order-mgmt/
        # 需要 ../../dev-specs/
        return f']({prefix}../../dev-specs/'

    return match.group(0)

def process_file(file_path):
    """處理單個文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content, modified = fix_links(content, str(file_path))

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ 已修復: {file_path}")
            return 1

        return 0
    except Exception as e:
        print(f"✗ 錯誤: {file_path} - {e}")
        return 0

def main():
    """主函數"""
    print("修復 .ai-docs 目錄中的死連結...")
    print("=" * 60)

    ai_docs_dir = Path('.ai-docs')
    fixed_count = 0

    # 只處理 README.md 和 SEARCH-INDEX.md
    for md_file in ai_docs_dir.rglob('*.md'):
        if md_file.name in ['README.md', 'SEARCH-INDEX.md'] or 'INDEX' in md_file.name:
            fixed_count += process_file(md_file)

    print("=" * 60)
    print(f"總計修復 {fixed_count} 個文件")

if __name__ == '__main__':
    main()
