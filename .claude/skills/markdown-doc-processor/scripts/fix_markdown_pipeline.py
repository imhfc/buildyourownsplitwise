#!/usr/bin/env python3
"""
fix_markdown_pipeline.py - Markdown 格式修復 Pipeline (SOLID 重構版)

整合 9 個格式修復工具為統一 Pipeline：
1. Grid Table → Pipe Table (fix_pandoc_format)
2. 清理嵌入式 Grid 標記 (fix_embedded_tables)
3. 移除 Pandoc span 標記 (fix_pandoc_spans)
4. 移除空表格行 (fix_empty_rows)
5. 修復無效連結 (fix_invalid_links)
6. 表格前後空行 (fix_table_spacing)
7. 清理跳脫字元 (fix_escape_chars)
8. 儲存格換行 (fix_table_cell_linebreaks)
9. 還原簽章表格 (fix_signature_tables)

使用方式：
    python3 fix_markdown_pipeline.py /path/to/specs
    python3 fix_markdown_pipeline.py /path/to/specs --dry-run
    python3 fix_markdown_pipeline.py /path/to/specs --steps 1,2,3
"""
import argparse
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# ============================================================
# SOLID: Single Responsibility - 每個 Fixer 只做一件事
# ============================================================

@dataclass
class FixResult:
    """修復結果"""
    fixer_name: str
    changes_made: int
    details: List[str]


class MarkdownFixer(ABC):
    """抽象基類 - 開放封閉原則"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def fix(self, content: str) -> Tuple[str, int]:
        """修復內容，返回 (修復後內容, 修改次數)"""
        pass


class GridTableFixer(MarkdownFixer):
    """Step 1: Grid Table → Pipe Table"""

    @property
    def name(self) -> str:
        return "grid_table"

    @property
    def description(self) -> str:
        return "Grid Table → Pipe Table"

    def fix(self, content: str) -> Tuple[str, int]:
        changes = 0
        lines = content.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]
            # 檢測 Grid Table 開始 (+---+---+)
            if re.match(r'^\+[-=]+(\+[-=]+)+\+$', line.strip()):
                table_lines = [line]
                i += 1
                while i < len(lines) and (lines[i].strip().startswith('|') or
                                          re.match(r'^\+[-=]+', lines[i].strip())):
                    table_lines.append(lines[i])
                    i += 1
                # 轉換為 Pipe Table
                converted = self._convert_grid_to_pipe(table_lines)
                result.extend(converted)
                changes += 1
            else:
                result.append(line)
                i += 1

        return '\n'.join(result), changes

    def _convert_grid_to_pipe(self, lines: List[str]) -> List[str]:
        """轉換 Grid Table 為 Pipe Table"""
        result = []
        header_done = False

        for line in lines:
            stripped = line.strip()
            # 跳過框線
            if re.match(r'^\+[-=]+', stripped):
                if not header_done and result:
                    # 插入分隔線
                    cols = result[-1].count('|') - 1
                    result.append('|' + '|'.join(['---'] * cols) + '|')
                    header_done = True
                continue
            # 資料行
            if stripped.startswith('|'):
                result.append(stripped)

        return result


class EmbeddedTableFixer(MarkdownFixer):
    """Step 2: 清理儲存格內嵌 Grid 標記"""

    @property
    def name(self) -> str:
        return "embedded_table"

    @property
    def description(self) -> str:
        return "清理嵌入式 Grid 標記"

    def fix(self, content: str) -> Tuple[str, int]:
        # 移除儲存格內的 +---+ 殘留
        pattern = r'\|\s*\+[-=]+\+\s*\|'
        matches = len(re.findall(pattern, content))
        content = re.sub(pattern, '| |', content)
        return content, matches


class PandocSpanFixer(MarkdownFixer):
    """Step 3: 移除 Pandoc span 標記"""

    @property
    def name(self) -> str:
        return "pandoc_span"

    @property
    def description(self) -> str:
        return "移除 {.mark}, {.underline} 等標記"

    def fix(self, content: str) -> Tuple[str, int]:
        patterns = [
            r'\{\.mark\}',
            r'\{\.underline\}',
            r'\{\.strikethrough\}',
            r'\[\]{[^}]+}',
        ]
        total = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, content))
            content = re.sub(pattern, '', content)
            total += matches
        return content, total


class EmptyRowFixer(MarkdownFixer):
    """Step 4: 移除空表格行"""

    @property
    def name(self) -> str:
        return "empty_row"

    @property
    def description(self) -> str:
        return "移除空表格行 (保護簽章表格)"

    def fix(self, content: str) -> Tuple[str, int]:
        lines = content.split('\n')
        result = []
        changes = 0
        in_signature_table = False

        for i, line in enumerate(lines):
            # 偵測簽章表格
            if '製表' in line or '審核' in line or '核准' in line:
                in_signature_table = True
            if in_signature_table and line.strip() == '':
                in_signature_table = False

            # 空表格行: | | | |
            if re.match(r'^\|\s*\|\s*\|\s*\|?\s*$', line.strip()):
                if not in_signature_table:
                    changes += 1
                    continue
            result.append(line)

        return '\n'.join(result), changes


class InvalidLinkFixer(MarkdownFixer):
    """Step 5: 修復無效連結"""

    @property
    def name(self) -> str:
        return "invalid_link"

    @property
    def description(self) -> str:
        return "修復 [text](.) 等無效連結"

    def fix(self, content: str) -> Tuple[str, int]:
        # [text](.) -> text
        pattern = r'\[([^\]]+)\]\(\.\)'
        matches = len(re.findall(pattern, content))
        content = re.sub(pattern, r'\1', content)
        return content, matches


class TableSpacingFixer(MarkdownFixer):
    """Step 6: 表格前後空行"""

    @property
    def name(self) -> str:
        return "table_spacing"

    @property
    def description(self) -> str:
        return "確保表格前後有空行"

    def fix(self, content: str) -> Tuple[str, int]:
        lines = content.split('\n')
        result = []
        changes = 0

        for i, line in enumerate(lines):
            is_table = line.strip().startswith('|')
            prev_table = i > 0 and lines[i-1].strip().startswith('|')
            prev_empty = i > 0 and lines[i-1].strip() == ''

            # 表格開始前需要空行
            if is_table and not prev_table and not prev_empty and i > 0:
                result.append('')
                changes += 1

            result.append(line)

            # 表格結束後需要空行
            next_exists = i + 1 < len(lines)
            next_not_table = next_exists and not lines[i+1].strip().startswith('|')
            next_not_empty = next_exists and lines[i+1].strip() != ''
            if is_table and next_not_table and next_not_empty:
                result.append('')
                changes += 1

        return '\n'.join(result), changes


class EscapeCharFixer(MarkdownFixer):
    """Step 7: 清理跳脫字元"""

    @property
    def name(self) -> str:
        return "escape_char"

    @property
    def description(self) -> str:
        return "清理 \\_ → _"

    def fix(self, content: str) -> Tuple[str, int]:
        patterns = [
            (r'\\_', '_'),
            (r'\\-', '-'),
            (r'\\\.', '.'),
        ]
        total = 0
        for pattern, replacement in patterns:
            matches = len(re.findall(pattern, content))
            content = re.sub(pattern, replacement, content)
            total += matches
        return content, total


class CellLinebreakFixer(MarkdownFixer):
    """Step 8: 儲存格換行"""

    @property
    def name(self) -> str:
        return "cell_linebreak"

    @property
    def description(self) -> str:
        return "恢復儲存格內換行 <br>"

    def fix(self, content: str) -> Tuple[str, int]:
        # 1. xxx 2. xxx → 1. xxx<br>2. xxx
        pattern = r'(\d+\.\s+[^|]+?)(\s+)(\d+\.\s+)'

        def replacer(m):
            return m.group(1) + '<br>' + m.group(3)

        matches = len(re.findall(pattern, content))
        content = re.sub(pattern, replacer, content)
        return content, matches


class SignatureTableFixer(MarkdownFixer):
    """Step 9: 還原簽章表格"""

    @property
    def name(self) -> str:
        return "signature_table"

    @property
    def description(self) -> str:
        return "還原簽章表格 header"

    def fix(self, content: str) -> Tuple[str, int]:
        lines = content.split('\n')
        result = []
        changes = 0

        for i, line in enumerate(lines):
            # 偵測斷頭簽章表格 (分隔線後直接是資料)
            if re.match(r'^\|[-:]+\|', line.strip()):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if '製表' in next_line or '審核' in next_line:
                        # 插入 header
                        cols = line.count('|') - 1
                        header = '| ' + ' | '.join([''] * cols) + ' |'
                        result.append(header)
                        changes += 1
            result.append(line)

        return '\n'.join(result), changes


# ============================================================
# SOLID: 依賴反轉 - Pipeline 依賴抽象介面
# ============================================================

class MarkdownPipeline:
    """Markdown 修復 Pipeline"""

    def __init__(self, fixers: Optional[List[MarkdownFixer]] = None):
        self.fixers = fixers or self._default_fixers()

    def _default_fixers(self) -> List[MarkdownFixer]:
        """預設 9 步驟"""
        return [
            GridTableFixer(),
            EmbeddedTableFixer(),
            PandocSpanFixer(),
            EmptyRowFixer(),
            InvalidLinkFixer(),
            TableSpacingFixer(),
            EscapeCharFixer(),
            CellLinebreakFixer(),
            SignatureTableFixer(),
        ]

    def process(self, content: str) -> Tuple[str, List[FixResult]]:
        """執行所有 Fixer"""
        results = []
        for fixer in self.fixers:
            content, changes = fixer.fix(content)
            results.append(FixResult(
                fixer_name=fixer.name,
                changes_made=changes,
                details=[fixer.description]
            ))
        return content, results

    def process_file(self, file_path: Path, dry_run: bool = False) -> List[FixResult]:
        """處理單一檔案"""
        content = file_path.read_text(encoding='utf-8')
        new_content, results = self.process(content)

        if not dry_run and new_content != content:
            file_path.write_text(new_content, encoding='utf-8')

        return results


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Markdown 格式修復 Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例:
  python3 fix_markdown_pipeline.py ./specs
  python3 fix_markdown_pipeline.py ./specs --dry-run
  python3 fix_markdown_pipeline.py ./specs --steps 1,2,3
        '''
    )
    parser.add_argument('path', help='規格目錄或檔案路徑')
    parser.add_argument('--dry-run', action='store_true', help='預覽模式，不寫入檔案')
    parser.add_argument('--steps', help='指定執行步驟 (例: 1,2,3)')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')

    args = parser.parse_args()
    path = Path(args.path)

    # 建立 Pipeline
    pipeline = MarkdownPipeline()

    if args.steps:
        step_nums = [int(s) - 1 for s in args.steps.split(',')]
        all_fixers = pipeline._default_fixers()
        pipeline.fixers = [all_fixers[i] for i in step_nums if i < len(all_fixers)]

    # 收集檔案
    if path.is_file():
        files = [path]
    else:
        files = list(path.glob('**/_原始文件_*.md'))
        if not files:
            files = list(path.glob('**/*.md'))

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}處理 {len(files)} 個檔案")
    print("=" * 60)

    total_changes = 0
    for file in files:
        results = pipeline.process_file(file, dry_run=args.dry_run)
        file_changes = sum(r.changes_made for r in results)
        total_changes += file_changes

        if file_changes > 0 or args.verbose:
            print(f"\n📄 {file.name}")
            for r in results:
                if r.changes_made > 0:
                    print(f"   {r.fixer_name}: {r.changes_made} 處修改")

    print("\n" + "=" * 60)
    print(f"總計: {total_changes} 處修改")
    if args.dry_run:
        print("(預覽模式，未實際寫入)")


if __name__ == '__main__':
    main()
