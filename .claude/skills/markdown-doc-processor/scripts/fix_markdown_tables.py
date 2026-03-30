#!/usr/bin/env python3
"""
fix_markdown_tables.py - 修復 pandoc 轉換的 Markdown 表格問題

功能：
1. 修復缺失的表格分隔線
2. 合併多行標題為單行
3. 修正欄位對齊
4. 清理多餘空白

使用方式：
    cat input.md | python3 fix_markdown_tables.py > output.md
    python3 fix_markdown_tables.py < input.md > output.md
    python3 fix_markdown_tables.py input.md output.md
"""
import re
import sys
from typing import List, Optional


def is_table_row(line: str) -> bool:
    """判斷是否為表格行"""
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 2


def is_separator_row(line: str) -> bool:
    """判斷是否為分隔線行"""
    stripped = line.strip()
    if not stripped.startswith('|'):
        return False
    # 分隔線只包含 |, -, :, 空格
    content = stripped[1:-1] if stripped.endswith('|') else stripped[1:]
    return bool(re.match(r'^[\s\-:|]+$', content)) and '-' in content


def count_columns(line: str) -> int:
    """計算表格欄位數"""
    stripped = line.strip()
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return len(stripped.split('|'))


def parse_row_cells(line: str) -> List[str]:
    """解析表格行的儲存格內容"""
    stripped = line.strip()
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split('|')]


def create_separator(num_cols: int) -> str:
    """建立標準分隔線"""
    return '|' + '---|' * num_cols


def merge_header_rows(header_rows: List[str]) -> str:
    """合併多行標題為單行"""
    if not header_rows:
        return ''
    if len(header_rows) == 1:
        return header_rows[0]

    # 解析所有行的儲存格
    all_cells = [parse_row_cells(row) for row in header_rows]

    # 找出最大欄位數
    max_cols = max(len(cells) for cells in all_cells)

    # 合併同一欄的文字
    merged = []
    for col_idx in range(max_cols):
        col_parts = []
        for row_cells in all_cells:
            if col_idx < len(row_cells) and row_cells[col_idx]:
                col_parts.append(row_cells[col_idx])
        merged.append(' '.join(col_parts))

    return '| ' + ' | '.join(merged) + ' |'


def process_table(table_lines: List[str]) -> List[str]:
    """處理單一表格，修復格式問題"""
    if not table_lines:
        return []

    # 找到分隔線位置
    sep_idx = -1
    for i, line in enumerate(table_lines):
        if is_separator_row(line):
            sep_idx = i
            break

    # 計算欄位數
    num_cols = max(count_columns(line) for line in table_lines if is_table_row(line) and not is_separator_row(line))

    if sep_idx == -1:
        # 無分隔線，在第一行後插入
        if len(table_lines) >= 1:
            return [table_lines[0], create_separator(num_cols)] + table_lines[1:]
        return table_lines

    if sep_idx == 0:
        # 分隔線在第一行（異常情況），移到第二行
        return [create_separator(num_cols)] + table_lines

    if sep_idx == 1:
        # 正常：標題 + 分隔線 + 資料
        return table_lines

    # sep_idx > 1：多行標題，需要合併
    header_rows = table_lines[:sep_idx]
    merged_header = merge_header_rows(header_rows)
    separator = table_lines[sep_idx]
    data_rows = table_lines[sep_idx + 1:]

    # 確保分隔線欄位數正確
    if count_columns(separator) != num_cols:
        separator = create_separator(num_cols)

    return [merged_header, separator] + data_rows


def fix_tables(content: str) -> str:
    """修復 Markdown 內容中的所有表格"""
    lines = content.split('\n')
    result = []
    table_buffer = []
    in_table = False

    for line in lines:
        is_table = is_table_row(line)

        if is_table:
            if not in_table:
                in_table = True
            table_buffer.append(line)
        else:
            if in_table:
                # 表格結束，處理並輸出
                processed = process_table(table_buffer)
                result.extend(processed)
                table_buffer = []
                in_table = False
            result.append(line)

    # 處理最後的表格（如果有）
    if table_buffer:
        processed = process_table(table_buffer)
        result.extend(processed)

    return '\n'.join(result)


def clean_fullwidth_spaces(content: str) -> str:
    """清理全形空格"""
    return content.replace('\u3000', ' ')


def fix_image_paths(content: str, old_ext: str = '.emf', new_ext: str = '.png') -> str:
    """修復圖片路徑副檔名"""
    return content.replace(old_ext, new_ext)


def main():
    """主程式"""
    # 讀取輸入
    if len(sys.argv) >= 2 and sys.argv[1] != '-':
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    # 處理內容
    content = clean_fullwidth_spaces(content)
    content = fix_tables(content)
    content = fix_image_paths(content)

    # 輸出結果
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(content)


if __name__ == '__main__':
    main()
