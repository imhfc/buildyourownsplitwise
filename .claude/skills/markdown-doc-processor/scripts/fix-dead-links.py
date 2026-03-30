#!/usr/bin/env python3
"""修復 Markdown 文件中的死連結"""

import os
import re
from pathlib import Path

# 修復規則
FIXES = [
    # memory-bank 路徑修復（.ai-docs/memory-bank → .claude/memory-bank）
    (r'\]\(([./]*)(\.ai-docs/memory-bank/[^)]+)\)', r'](\1.claude/memory-bank/\3)'),
    (r'\]\(([\./]*)memory-bank/([^)]+)\)', r'](\1.claude/memory-bank/\2)'),

    # .claude 路徑修復（從 .ai-docs 引用時）
    # 從 .ai-docs/behavior/universal/standards/ 引用 .claude/
    (r'\]\(\.\./\.\./\.\./\.claude/', r'](../../../.claude/'),

    # 從 .ai-docs/information/project-specific/example/ 引用 .claude/
    (r'\]\(\.\./\.\./\.\./\.\./\.claude/', r'](../../../../.claude/'),

    # dev-specs 路徑修復（從 dev-plans 引用 dev-specs）
    # 移除多餘的 dev-plans 層級
    (r'\]\(([./]*)dev-specs/([^)]+)\)', lambda m: f']({m.group(1)}../../dev-specs/{m.group(2)})' if '/dev-plans/' in current_file else m.group(0)),
]

def fix_markdown_links(content, file_path):
    """修復 Markdown 連結"""
    global current_file
    current_file = file_path

    modified = False
    original = content

    for pattern, replacement in FIXES:
        if callable(replacement):
            # 跳過 lambda 函數修復（太複雜）
            continue

        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content

    return content, modified

def main():
    print("修復 Markdown 文件中的死連結...")
    print("=" * 60)
    print()

    # 統計變數
    total_files = 0
    modified_files = 0

    # 找出所有需要修復的 Markdown 文件
    patterns = ['ai-docs', 'claude']
    md_files = []

    for root, dirs, files in os.walk('.'):
        # 排除 node_modules 和 .git
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]

        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                # 檢查路徑是否包含任一關鍵字
                if any(pattern in file_path for pattern in patterns):
                    md_files.append(file_path)

    # 修復每個文件
    for file_path in sorted(md_files):
        total_files += 1

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"無法讀取: {file_path}")
            print(f"  └─ 錯誤: {e}")
            continue

        # 修復連結
        new_content, modified = fix_markdown_links(content, file_path)

        if modified:
            modified_files += 1
            print(f"✓ 修復: {file_path}")

            # 寫入修復後的內容
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                print(f"  └─ ✗ 無法寫入: {e}")

    # 輸出統計
    print()
    print("=" * 60)
    print("修復統計:")
    print(f"  - 檢查文件數: {total_files}")
    print(f"  - 修復文件數: {modified_files}")
    print()

    if modified_files > 0:
        print(f"✓ 成功修復 {modified_files} 個文件")
    else:
        print("✓ 沒有需要修復的文件")

    return 0

if __name__ == '__main__':
    exit(main())
