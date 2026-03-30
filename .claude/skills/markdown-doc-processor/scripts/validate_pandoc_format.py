#!/usr/bin/env python3
"""
Pandoc 格式轉換驗證腳本

在轉換前執行此腳本分析所有格式問題，一次性產出問題報告。
避免增量式發現問題、增量式修復的情況。

使用方式:
    python3 validate_pandoc_format.py <directory>
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class FormatIssue:
    """格式問題"""
    issue_type: str
    count: int
    sample_files: List[str] = field(default_factory=list)
    fix_tool: str = ""


def analyze_file(file_path: Path) -> Dict[str, int]:
    """分析單一檔案的格式問題"""
    issues = {
        "grid_table": 0,        # +---+ 框線
        "pandoc_span": 0,       # {.mark}, {.underline}
        "invalid_link": 0,      # [text](.)
        "escape_char": 0,       # \_
        "empty_row": 0,         # | | | |
        "compressed_list": 0,   # 1. xxx 2. xxx
        "missing_spacing": 0,   # 表格前後無空行
        "broken_table": 0,      # 斷頭表格 (separator 無 header)
    }

    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Grid Table
            if re.match(r'^\+[-:+=]+\+', line):
                issues["grid_table"] += 1

            # Pandoc span
            if '{.mark}' in line or '{.underline}' in line:
                issues["pandoc_span"] += 1

            # Invalid link
            if re.search(r'\[.*?\]\(\.\)', line):
                issues["invalid_link"] += 1

            # Escape char
            issues["escape_char"] += line.count('\\_')

            # Empty row (只計算表格行，排除簽章表格 placeholder)
            # 簽章表格特徵: 2-3 欄，下一行是分隔線，且有「簽章」「日期」等關鍵字
            if re.match(r'^\|(\s*\|)+\s*$', line):
                # 檢查是否為簽章表格 (下一行有分隔線且後面有簽章相關文字)
                is_signature_table = False
                if i + 2 < len(lines):
                    next_line = lines[i + 1]
                    content_line = lines[i + 2] if i + 2 < len(lines) else ""
                    if re.match(r'^\|[-|]+\|$', next_line) and ('簽章' in content_line or '日期' in content_line):
                        is_signature_table = True
                if not is_signature_table:
                    issues["empty_row"] += 1

            # Compressed list in table
            if line.startswith('|') and ' 2. ' in line and '<br>' not in line:
                issues["compressed_list"] += 1

            # Missing spacing (表格前一行不是空行，排除分隔線)
            # 排除分隔線 (|---|---| 格式) 作為表格起始
            if line.startswith('|') and i > 0 and lines[i-1].strip() and not lines[i-1].startswith('|'):
                # 排除分隔線 (|---| 格式)
                if not re.match(r'^\|[-:| ]+\|$', line):
                    issues["missing_spacing"] += 1

            # Broken table (separator 行前面不是表格 header)
            # 模式: |---|---|---| 前面是空行或非表格行
            if re.match(r'^\|[-]+(\|[-]+)+\|?\s*$', line):
                if i > 0:
                    prev_line = lines[i-1].strip()
                    # 前一行應該是表格 header (以 | 開頭但不是 separator)
                    if not prev_line.startswith('|') or re.match(r'^\|[-]+', prev_line):
                        # 檢查是否在簽章區域（前面 2-5 行有「單位」）
                        context_start = max(0, i - 5)
                        context = '\n'.join(lines[context_start:i])
                        if '單位:' in context or '單位：' in context:
                            issues["broken_table"] += 1

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return issues


def analyze_directory(directory: Path) -> Dict[str, FormatIssue]:
    """分析目錄中所有 Markdown 檔案"""
    all_issues: Dict[str, FormatIssue] = {
        "grid_table": FormatIssue("Grid Table (+---+)", 0, [], "fix_pandoc_format.py"),
        "pandoc_span": FormatIssue("Pandoc Span ({.mark})", 0, [], "fix_pandoc_spans.py"),
        "invalid_link": FormatIssue("Invalid Link [text](.)", 0, [], "fix_invalid_links.py"),
        "escape_char": FormatIssue("Escape Char (\\_)", 0, [], "fix_escape_chars.py"),
        "empty_row": FormatIssue("Empty Table Row", 0, [], "fix_empty_rows.py"),
        "compressed_list": FormatIssue("Compressed List (1. 2. 3.)", 0, [], "fix_table_cell_linebreaks.py"),
        "missing_spacing": FormatIssue("Missing Table Spacing", 0, [], "fix_table_spacing.py"),
        "broken_table": FormatIssue("Broken Signature Table", 0, [], "fix_signature_tables.py"),
    }

    md_files = list(directory.rglob("*.md"))

    for md_file in md_files:
        file_issues = analyze_file(md_file)
        rel_path = str(md_file.relative_to(directory))

        for issue_type, count in file_issues.items():
            if count > 0:
                all_issues[issue_type].count += count
                if len(all_issues[issue_type].sample_files) < 3:
                    all_issues[issue_type].sample_files.append(f"{rel_path} ({count})")

    return all_issues


def print_report(issues: Dict[str, FormatIssue], total_files: int):
    """輸出問題報告"""
    print("=" * 70)
    print("Pandoc 格式問題分析報告")
    print("=" * 70)
    print(f"\n分析檔案數: {total_files}")
    print()

    has_issues = False
    tools_needed = []

    print("| 問題類型 | 數量 | 修復工具 |")
    print("|----------|------|----------|")

    for issue_type, issue in issues.items():
        if issue.count > 0:
            has_issues = True
            print(f"| {issue.issue_type} | {issue.count} | `{issue.fix_tool}` |")
            if issue.fix_tool not in tools_needed:
                tools_needed.append(issue.fix_tool)

    if not has_issues:
        print("| (無問題) | 0 | - |")

    print()

    if has_issues:
        print("### 範例檔案")
        print()
        for issue_type, issue in issues.items():
            if issue.count > 0 and issue.sample_files:
                print(f"**{issue.issue_type}**:")
                for f in issue.sample_files[:3]:
                    print(f"  - {f}")
                print()

        print("### 建議修復順序")
        print()
        print("```bash")
        for tool in tools_needed:
            print(f"python3 .ai-docs/tools/{tool} /path/to/specs")
        print("```")
        print()
        print("或使用 Ralph Loop 自動修復:")
        print("```bash")
        print("/ralph-wiggum:ralph-loop 修復所有格式問題 --max-iterations 5")
        print("```")
    else:
        print("所有格式檢查通過！")

    print()
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("使用方式: python3 validate_pandoc_format.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"錯誤: {directory} 不是目錄")
        sys.exit(1)

    md_files = list(directory.rglob("*.md"))
    issues = analyze_directory(directory)
    print_report(issues, len(md_files))


if __name__ == "__main__":
    main()
