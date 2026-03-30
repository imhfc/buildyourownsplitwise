#!/usr/bin/env python3
"""
使用 markitdown 從 Excel 提取欄位比對表並計算 selectIndex

用途：
- 從 Excel 提取欄位比對表
- 自動計算 selectIndex (Key 欄位 + Y 欄位)
- 輸出符合 FCS BPMN 規格的 Markdown

特點：
- 自動識別「是否比對」欄位
- 排除 REDEFINE 欄位
- 從 0 開始編號非 REDEFINE 欄位
- 計算並輸出 selectIndex

安裝：
pip install 'markitdown[xlsx]'

使用：
python3 extract_excel_markitdown.py <excel_file> [--output output.md]
"""

from markitdown import MarkItDown
from pathlib import Path
import sys
import argparse
import re

def extract_field_mapping(excel_file, output_file=None):
    """
    從 Excel 提取欄位比對表並計算 selectIndex

    Args:
        excel_file: Excel 檔案路徑
        output_file: 輸出 Markdown 檔案（可選）

    Returns:
        selectIndex 字串
    """
    excel_path = Path(excel_file)
    if not excel_path.exists():
        raise FileNotFoundError(f"找不到檔案: {excel_file}")

    print(f"📄 讀取: {excel_path.name}")

    # 初始化轉換器
    md = MarkItDown()

    try:
        # 轉換 Excel
        result = md.convert(excel_path)
        lines = result.markdown.split('\n')

        # 解析欄位比對表
        in_table = False
        header_found = False
        header_cols = []
        index = 0
        key_indices = []
        y_indices = []
        field_rows = []

        for i, line in enumerate(lines):
            # 跳過空行
            if not line.strip():
                continue

            # 尋找欄位比對表
            if '|' in line:
                cols = [c.strip() for c in line.split('|')[1:-1]]

                # 識別表頭
                if not header_found and any('欄位' in c or 'Field' in c for c in cols):
                    header_found = True
                    header_cols = cols
                    print(f"\n找到欄位比對表 (行 {i+1})")
                    print(f"   欄位數: {len(cols)}")
                    continue

                # 跳過分隔線
                if '---' in line or '===' in line:
                    continue

                # 解析資料行
                if header_found and len(cols) >= 3:
                    # 假設格式: | 序號 | 欄位名稱 | ... | 是否比對 | ... |
                    field_name = cols[1] if len(cols) > 1 else ""
                    is_compare = ""

                    # 尋找「是否比對」欄位
                    for col in cols:
                        if col.upper() in ['Y', 'N', 'YES', 'NO']:
                            is_compare = col.upper()
                            break

                    # 跳過空行或標題行
                    if not field_name or '序號' in field_name or 'No.' in field_name:
                        continue

                    # 跳過 REDEFINE 欄位
                    remark = cols[-1] if cols else ""
                    if "REDEFINE" in field_name.upper() or "REDEFINE" in remark.upper():
                        print(f"   跳過 REDEFINE: {field_name}")
                        continue

                    # 記錄欄位
                    field_rows.append({
                        'index': index,
                        'name': field_name,
                        'is_compare': is_compare
                    })

                    # 識別 Key 欄位
                    is_key = False
                    for keyword in ["CUST-NO", "CUSTNO", "TYPE", "KEY"]:
                        if keyword in field_name.upper():
                            key_indices.append(str(index))
                            is_key = True
                            break

                    # 識別 Y 欄位
                    is_y = is_compare in ['Y', 'YES']
                    if is_y:
                        y_indices.append(str(index))

                    # 輸出進度
                    markers = []
                    if is_key:
                        markers.append("Key")
                    if is_y:
                        markers.append("Y")
                    marker_str = f" ({', '.join(markers)})" if markers else ""
                    print(f"   [{index:3d}] {field_name}{marker_str}")

                    index += 1

        if index == 0:
            print("未找到有效欄位")
            return None

        # 計算 selectIndex
        all_indices = sorted(set(key_indices + y_indices), key=int)
        select_index = ",".join(all_indices)

        # 輸出統計
        print(f"\n## 欄位比對表分析")
        print(f"- 總欄位數: {index}")
        print(f"- Key 欄位索引: {', '.join(key_indices) if key_indices else '(無)'}")
        print(f"- Y 欄位索引: {', '.join(y_indices) if y_indices else '(無)'}")
        print(f"\n**selectIndex**: `{select_index}`")

        # 輸出到檔案
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                # 寫入標題
                f.write(f"# 欄位比對表\n\n")
                f.write(f"**來源**: `{excel_path.name}`\n\n")

                # 寫入 selectIndex
                f.write(f"## FCS selectIndex\n\n")
                f.write(f"```\n")
                f.write(f"selectIndex=\"{select_index}\"\n")
                f.write(f"```\n\n")

                # 寫入表格
                f.write(f"## 欄位列表\n\n")
                f.write(f"| index | 欄位名稱 | 是否比對 | 備註 |\n")
                f.write(f"|-------|---------|---------|------|\n")

                for row in field_rows:
                    markers = []
                    if str(row['index']) in key_indices:
                        markers.append("Key")
                    if row['is_compare'] in ['Y', 'YES']:
                        markers.append("Y")

                    marker_str = ', '.join(markers) if markers else ""
                    f.write(f"| {row['index']} | {row['name']} | {row['is_compare']} | {marker_str} |\n")

                f.write(f"\n---\n\n")
                f.write(f"**統計**:\n")
                f.write(f"- 總欄位: {index}\n")
                f.write(f"- Key 欄位: {len(key_indices)}\n")
                f.write(f"- Y 欄位: {len(y_indices)}\n")

            print(f"\n已儲存: {output_path}")

        return select_index

    except Exception as e:
        print(f"處理失敗: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='從 Excel 提取欄位比對表並計算 selectIndex',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 提取並輸出到終端
  python3 extract_excel_markitdown.py 欄位比對表.xlsx

  # 提取並儲存為 Markdown
  python3 extract_excel_markitdown.py 欄位比對表.xlsx --output 09-欄位比對表.md

selectIndex 計算規則:
  1. 排除 REDEFINE 欄位
  2. 從 0 開始編號剩餘欄位
  3. 找出 Key 欄位 (CUST-NO, TYPE) 的索引
  4. 找出「是否比對 = Y」欄位的索引
  5. 合併並排序
        """
    )

    parser.add_argument('excel_file', help='Excel 檔案路徑')
    parser.add_argument('--output', '-o', help='輸出 Markdown 檔案')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    try:
        # 檢查 markitdown 是否已安裝
        try:
            import markitdown
        except ImportError:
            print("markitdown 未安裝")
            print("\n安裝指令:")
            print("pip install 'markitdown[xlsx]'")
            sys.exit(1)

        # 提取欄位比對表
        select_index = extract_field_mapping(args.excel_file, args.output)

        if select_index:
            print(f"\n提取完成")
            sys.exit(0)
        else:
            print(f"\n提取失敗")
            sys.exit(1)

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
