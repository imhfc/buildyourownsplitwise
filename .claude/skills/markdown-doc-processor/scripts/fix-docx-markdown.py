#!/usr/bin/env python3
"""
DOCX 轉換後 Markdown 修復工具
用途: 修復 docling 轉換 DOCX 後產生的常見格式問題

使用方式:
    python fix-docx-markdown.py input.md [--extract-images]

修復項目:
    1. 轉義字元: \_ → _
    2. HTML entities: &lt; &gt; &amp;
    3. 表格分隔線: 過長的 ------ 標準化為 6 個
    4. 表格內空行: 移除破壞表格渲染的空行
    5. Base64 圖片: 提取為獨立檔案 (需 --extract-images)

版本: 1.0
日期: 2026-01-08
來源: LL-016 DOCX Markdown 轉換經驗
"""
import re
import sys
import os
import base64
import argparse


def fix_escaped_underscores(content: str) -> str:
    """修復轉義的底線 \_ → _"""
    return content.replace(r'\_', '_')


def fix_html_entities(content: str) -> str:
    """修復 HTML entities"""
    replacements = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&nbsp;': ' ',
        '&quot;': '"',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    return content


def fix_table_separators(content: str) -> str:
    """標準化表格分隔線 (超過 6 個 dash 改為 6 個)"""
    return re.sub(r'-{7,}', '------', content)


def fix_table_blank_lines(content: str) -> str:
    """移除表格內的空行 (會破壞 Markdown 表格渲染)"""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if line.strip().startswith('|') and '|' in line[1:]:
            # 收集表格行
            table_lines = [line]
            j = i + 1

            while j < len(lines):
                next_line = lines[j].rstrip()
                stripped = next_line.strip()

                if not stripped:
                    # 空行 - 檢查後面是否還有表格內容
                    k = j + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1

                    if k < len(lines) and lines[k].strip().startswith('|'):
                        j = k
                        continue
                    else:
                        break
                elif stripped.startswith('|'):
                    table_lines.append(next_line)
                    j += 1
                else:
                    break

            result.extend(table_lines)
            result.append('')
            i = j
        else:
            result.append(line)
            i += 1

    # 清理多餘空行
    content = '\n'.join(result)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content


def fix_standalone_pipes(content: str) -> str:
    """移除獨立的 | 或 | | 行"""
    lines = content.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped in ['|', '| |', '||', '|  |']:
            continue
        result.append(line)
    return '\n'.join(result)


def extract_base64_images(content: str, output_dir: str) -> str:
    """提取 base64 圖片為獨立檔案"""
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    pattern = r'!\[([^\]]*)\]\(data:image/([^;]+);base64,([^)]+)\)'

    def replace_image(match):
        alt_text = match.group(1)
        img_type = match.group(2)
        base64_data = match.group(3)

        img_count = len([f for f in os.listdir(images_dir) if f.startswith('extracted_')])
        filename = f'extracted_image_{img_count + 1}.{img_type}'
        filepath = os.path.join(images_dir, filename)

        try:
            img_data = base64.b64decode(base64_data)
            with open(filepath, 'wb') as f:
                f.write(img_data)
            print(f"  提取圖片: {filename} ({len(img_data):,} bytes)")
        except Exception as e:
            print(f"  警告: 圖片提取失敗 - {e}")
            return match.group(0)

        return f'![{alt_text or "圖片"}](images/{filename})'

    return re.sub(pattern, replace_image, content)


def check_issues(content: str) -> dict:
    """檢查檔案中的問題"""
    issues = {
        'escaped_underscores': len(re.findall(r'\\_', content)),
        'html_entities': len(re.findall(r'&lt;|&gt;|&amp;', content)),
        'long_separators': len(re.findall(r'-{50,}', content)),
        'base64_images': len(re.findall(r'data:image', content)),
        'standalone_pipes': len(re.findall(r'^\s*\|\s*\|?\s*$', content, re.MULTILINE)),
        'max_line_length': max(len(line) for line in content.split('\n')),
    }
    return issues


def main():
    parser = argparse.ArgumentParser(
        description='DOCX 轉換後 Markdown 修復工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
    python fix-docx-markdown.py document.md
    python fix-docx-markdown.py document.md --extract-images
    python fix-docx-markdown.py document.md --check-only
        """
    )
    parser.add_argument('input_file', help='要修復的 Markdown 檔案')
    parser.add_argument('--extract-images', action='store_true',
                        help='提取 base64 圖片為獨立檔案')
    parser.add_argument('--check-only', action='store_true',
                        help='僅檢查問題，不修復')
    parser.add_argument('--output', '-o', help='輸出檔案 (預設覆蓋原檔)')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"錯誤: 找不到檔案 {args.input_file}")
        sys.exit(1)

    with open(args.input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"檔案: {args.input_file}")
    print(f"大小: {len(content):,} 字元, {len(content.split(chr(10))):,} 行")
    print()

    # 檢查問題
    issues = check_issues(content)
    print("問題檢查:")
    print(f"  轉義底線 (\\_): {issues['escaped_underscores']}")
    print(f"  HTML entities: {issues['html_entities']}")
    print(f"  過長分隔線: {issues['long_separators']}")
    print(f"  Base64 圖片: {issues['base64_images']}")
    print(f"  獨立 pipe 行: {issues['standalone_pipes']}")
    print(f"  最長行: {issues['max_line_length']:,} 字元")

    if args.check_only:
        if issues['max_line_length'] > 500:
            print("\n警告: 有超長行，可能包含嵌入表格")
        sys.exit(0)

    print("\n修復中...")

    # 執行修復
    content = fix_escaped_underscores(content)
    print("  ✓ 修復轉義底線")

    content = fix_html_entities(content)
    print("  ✓ 修復 HTML entities")

    content = fix_table_separators(content)
    print("  ✓ 標準化表格分隔線")

    content = fix_standalone_pipes(content)
    print("  ✓ 移除獨立 pipe 行")

    content = fix_table_blank_lines(content)
    print("  ✓ 修復表格內空行")

    if args.extract_images:
        output_dir = os.path.dirname(args.input_file) or '.'
        content = extract_base64_images(content, output_dir)
        print("  ✓ 提取 base64 圖片")

    # 寫入檔案
    output_file = args.output or args.input_file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n完成: {output_file}")

    # 再次檢查
    final_issues = check_issues(content)
    if final_issues['max_line_length'] > 500:
        print(f"\n仍有超長行 ({final_issues['max_line_length']:,} 字元)")
        print("   可能需要手動處理嵌入表格")


if __name__ == '__main__':
    main()
