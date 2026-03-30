#!/usr/bin/env python3
"""
批次規格 README.md 修正工具
- 檢測並修正斷鏈
- 不存在的章節標記為 N/A
- 自動偵測 09-* 各種命名
"""
import os
import re
import sys

# 章節順序定義
SECTIONS = [
    ("00-00-文件資訊", "0. 文件資訊"),
    ("01-規格資訊", "1. 規格資訊"),
    ("02-回應代碼列表", "2. 回應代碼列表"),
    ("03-檔案處理流程", "3. 檔案處理流程"),
    ("04-DB", "4. DB"),
    ("05-API", "5. API"),
    ("06-FSD", "6. FSD"),
    ("07-測試", "7. 測試檔案"),
    ("08-附件", "8. 附件"),
    ("09-", "9. 附錄-欄位對照表"),
]

def fix_readme(dir_path, dry_run=False):
    """修正單一目錄的 README.md"""
    spec_dir = os.path.basename(dir_path)
    readme_path = os.path.join(dir_path, "README.md")
    
    # 取得目錄中所有 .md 文件
    md_files = set()
    for f in os.listdir(dir_path):
        if f.endswith('.md') and not f.startswith('_'):
            md_files.add(f)
    
    # 生成新的 README 內容
    lines = [f"# {spec_dir}", "", "## 章節列表", ""]
    
    for prefix, label in SECTIONS:
        matching_file = None
        for f in md_files:
            if f.startswith(prefix):
                matching_file = f
                break
        
        if matching_file and matching_file != "README.md":
            display_label = label
            if prefix.startswith("09-"):
                display_label = matching_file.replace(".md", "").replace("09-", "9. ")
            lines.append(f"- [{display_label}]({matching_file})")
        elif prefix in ["04-DB", "06-FSD", "07-測試"]:
            lines.append(f"- {label} - N/A")
    
    # 添加原始文件引用
    for f in md_files:
        if f.startswith('_原始文件_'):
            lines.append(f"- [原始文件]({f})")
    
    lines.append("")
    new_content = "\n".join(lines)
    
    if dry_run:
        print(f"[DRY-RUN] {spec_dir}")
        return False
    
    old_content = ""
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            old_content = f.read()
    
    if old_content.strip() != new_content.strip():
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("用法: python3 fix_readme_links.py <目錄路徑> [--dry-run]")
        print("範例: python3 fix_readme_links.py ./reconcile-batch-specs")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    fixed_count = 0
    for spec_dir in sorted(os.listdir(base_dir)):
        if not spec_dir.startswith("NVBK_SD_B31-003-"):
            continue
        
        dir_path = os.path.join(base_dir, spec_dir)
        if not os.path.isdir(dir_path):
            continue
        
        if fix_readme(dir_path, dry_run):
            fixed_count += 1
            print(f"已修正: {spec_dir}/README.md")
    
    print(f"\n總計修正 {fixed_count} 個檔案")

if __name__ == "__main__":
    main()
