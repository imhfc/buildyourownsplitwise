#!/usr/bin/env python3
"""
使用 Microsoft markitdown 轉換 DOCX/Excel 為 Markdown

用途：
- 轉換 DOCX 批次規格書為 Markdown
- 轉換 Excel 欄位比對表為 Markdown
- 自動處理圖片提取
- 直接輸出 Pipe Table 格式

特點：
- Python 原生，無需系統依賴
- 開箱即用，設定簡單
- 表格格式更乾淨（直接 Pipe Table）

安裝：
pip install 'markitdown[docx, xlsx]'

使用：
python3 convert_docx_markitdown.py <input_file> <output_dir> [--org-mode]
"""

from markitdown import MarkItDown
from pathlib import Path
import sys
import argparse
import shutil
from datetime import datetime

def convert_file(input_file, output_dir, org_mode=False):
    """
    使用 markitdown 轉換檔案

    Args:
        input_file: 輸入檔案（DOCX 或 Excel）
        output_dir: 輸出目錄
        org_mode: 是否使用 org 目錄結構

    Returns:
        輸出檔案路徑
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"找不到檔案: {input_file}")

    # 確定輸出目錄
    if org_mode:
        # org 模式: 輸出到 spec_dir/org/
        spec_dir = Path(output_dir)
        output_path = spec_dir / "org"
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    # 初始化轉換器
    print(f"📄 轉換: {input_path.name}")
    md = MarkItDown()

    try:
        # 轉換檔案
        result = md.convert(input_path)

        # 儲存 Markdown
        if input_path.suffix.lower() == '.xlsx':
            # Excel 檔案
            output_file = output_path / f"{input_path.stem}.md"
        else:
            # DOCX 檔案 - 使用 _原始文件_ 前綴
            output_file = output_path / f"_原始文件_{input_path.stem}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.markdown)

        # 輸出統計
        line_count = len(result.markdown.splitlines())
        print(f"輸出: {output_file}")
        print(f"   行數: {line_count}")

        if result.title:
            print(f"   標題: {result.title}")

        # 檢查轉換品質
        if line_count < 50 and input_path.suffix.lower() == '.docx':
            print(f"警告: 行數過少 ({line_count} < 50)，請檢查轉換品質")

        return output_file

    except Exception as e:
        print(f"轉換失敗: {e}")
        raise

def batch_convert(input_dir, output_dir, org_mode=False):
    """
    批次轉換目錄中的所有 DOCX/Excel 檔案

    Args:
        input_dir: 輸入目錄
        output_dir: 輸出目錄
        org_mode: 是否使用 org 目錄結構
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"找不到目錄: {input_dir}")

    # 找出所有支援的檔案
    supported_files = []
    for ext in ['.docx', '.xlsx', '.xlsm']:
        supported_files.extend(input_path.glob(f"*{ext}"))

    if not supported_files:
        print(f"未找到支援的檔案 (.docx, .xlsx)")
        return

    print(f"\n找到 {len(supported_files)} 個檔案")

    # 逐一轉換
    success_count = 0
    for file in supported_files:
        try:
            convert_file(file, output_dir, org_mode)
            success_count += 1
            print()
        except Exception as e:
            print(f"跳過: {file.name} - {e}")
            print()

    print(f"\n轉換完成: {success_count}/{len(supported_files)} 成功")

def main():
    parser = argparse.ArgumentParser(
        description='使用 markitdown 轉換 DOCX/Excel 為 Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 單一檔案轉換
  python3 convert_docx_markitdown.py spec.docx ./output

  # 批次轉換 (org 模式)
  python3 convert_docx_markitdown.py /path/to/docx_folder /path/to/specs --org-mode

  # 轉換 Excel 欄位比對表
  python3 convert_docx_markitdown.py 欄位比對表.xlsx ./output
        """
    )

    parser.add_argument('input', help='輸入檔案或目錄')
    parser.add_argument('output', help='輸出目錄')
    parser.add_argument('--org-mode', action='store_true',
                        help='使用 org 目錄結構 (輸出到 spec_dir/org/)')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    try:
        input_path = Path(args.input)

        # 檢查 markitdown 是否已安裝
        try:
            import markitdown
        except ImportError:
            print("markitdown 未安裝")
            print("\n安裝指令:")
            print("pip install 'markitdown[docx, xlsx]'")
            sys.exit(1)

        # 判斷是檔案還是目錄
        if input_path.is_file():
            convert_file(args.input, args.output, args.org_mode)
        elif input_path.is_dir():
            batch_convert(args.input, args.output, args.org_mode)
        else:
            print(f"無效的輸入: {args.input}")
            sys.exit(1)

    except Exception as e:
        print(f"\n錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
