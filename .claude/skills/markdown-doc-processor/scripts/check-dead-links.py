#!/usr/bin/env python3
"""檢查 Markdown 文件中的死連結"""

import os
import re
from pathlib import Path
from collections import defaultdict

# 顏色定義
class Color:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

def find_markdown_links(content):
    """提取 Markdown 連結 [text](path)"""
    # 匹配 [text](path) 格式，排除圖片 ![alt](path)
    pattern = r'(?<!!)\[([^\]]+)\]\(([^)]+)\)'
    return re.findall(pattern, content)

def is_external_link(link):
    """檢查是否為外部連結"""
    return link.startswith('http://') or link.startswith('https://') or link.startswith('#')

def resolve_path(file_path, link):
    """解析相對路徑為絕對路徑"""
    # 移除錨點
    clean_link = link.split('#')[0]
    if not clean_link:
        return None

    file_dir = os.path.dirname(file_path)

    if clean_link.startswith('/'):
        # 絕對路徑（從專案根目錄）
        target_path = os.path.join('.', clean_link.lstrip('/'))
    else:
        # 相對路徑
        target_path = os.path.join(file_dir, clean_link)

    # 標準化路徑
    return os.path.normpath(target_path)

def main():
    print("檢查 Markdown 文件中的死連結...")
    print("=" * 60)
    print()

    # 統計變數
    total_files = 0
    total_links = 0
    broken_links_list = []

    # 找出所有需要檢查的 Markdown 文件
    patterns = ['ai-docs', 'claude', 'gemini', 'github', 'agent']
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

    # 檢查每個文件
    for file_path in sorted(md_files):
        total_files += 1

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"{Color.YELLOW}{Color.NC} 無法讀取: {file_path}")
            print(f"  └─ 錯誤: {e}")
            continue

        # 提取所有連結
        links = find_markdown_links(content)

        for text, link in links:
            total_links += 1

            # 跳過外部連結和錨點
            if is_external_link(link):
                continue

            # 解析目標路徑
            target_path = resolve_path(file_path, link)
            if not target_path:
                continue

            # 檢查檔案或目錄是否存在
            if not os.path.exists(target_path):
                broken_links_list.append({
                    'file': file_path,
                    'text': text,
                    'link': link,
                    'target': target_path
                })

    # 輸出死連結
    if broken_links_list:
        print(f"{Color.RED}發現 {len(broken_links_list)} 個死連結:{Color.NC}")
        print()

        # 按文件分組
        by_file = defaultdict(list)
        for item in broken_links_list:
            by_file[item['file']].append(item)

        for file_path in sorted(by_file.keys()):
            print(f"{Color.RED}✗{Color.NC} {file_path}")
            for item in by_file[file_path]:
                print(f"  └─ [{item['text']}]({item['link']})")
                print(f"     目標不存在: {item['target']}")
            print()

    # 輸出統計
    print("=" * 60)
    print("統計結果:")
    print(f"  - 檢查文件數: {total_files}")
    print(f"  - 總連結數: {total_links}")
    print(f"  - 死連結數: {Color.RED}{len(broken_links_list)}{Color.NC}")
    print()

    if not broken_links_list:
        print(f"{Color.GREEN}✓ 沒有發現死連結！{Color.NC}")
    else:
        print(f"{Color.YELLOW}發現 {len(broken_links_list)} 個死連結{Color.NC}")

        # 儲存報告
        output_file = '.claude/scripts/dead-links-report.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("死連結報告\n")
            f.write("=" * 60 + "\n\n")

            for file_path in sorted(by_file.keys()):
                f.write(f"文件: {file_path}\n")
                for item in by_file[file_path]:
                    f.write(f"  連結: [{item['text']}]({item['link']})\n")
                    f.write(f"  目標: {item['target']}\n")
                f.write("\n")

        print(f"  詳細報告: {output_file}")

    return len(broken_links_list)

if __name__ == '__main__':
    exit(main())
