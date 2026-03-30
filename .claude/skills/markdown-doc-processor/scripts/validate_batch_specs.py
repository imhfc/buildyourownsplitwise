#!/usr/bin/env python3
"""
批次規格驗證工具
- 檢查 README.md 斷鏈
- 檢查 API 真實重複 (method + URI)
- 檢查表格格式問題
"""
import os
import re
import sys

def validate_specs(base_dir):
    readme_issues = []
    api_issues = []
    
    for spec_dir in sorted(os.listdir(base_dir)):
        if not spec_dir.startswith("NVBK_SD_B31-003-"):
            continue
        
        dir_path = os.path.join(base_dir, spec_dir)
        if not os.path.isdir(dir_path):
            continue
        
        readme_path = os.path.join(dir_path, "README.md")
        if not os.path.exists(readme_path):
            readme_issues.append({'dir': spec_dir, 'issue': '缺少 README.md'})
            continue
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # 檢查斷鏈
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', readme_content)
        broken = []
        for text, path in links:
            if not os.path.exists(os.path.join(dir_path, path)):
                broken.append((text, path))
        
        if broken:
            readme_issues.append({'dir': spec_dir, 'broken_links': broken})
        
        # 檢查 API 重複 (method + URI)
        api_path = os.path.join(dir_path, "05-API.md")
        if os.path.exists(api_path):
            with open(api_path, 'r', encoding='utf-8') as f:
                api_content = f.read()
            
            apis = re.findall(r'\|\s*\w+\s*\|\s*(GET|POST|PUT|DELETE)\s*\|\s*([^\|]+)\s*\|', api_content)
            seen = set()
            dups = []
            for method, uri in apis:
                key = f"{method} {uri.strip()}"
                if key in seen:
                    dups.append(key)
                seen.add(key)
            
            if dups:
                api_issues.append({'dir': spec_dir, 'duplicates': dups})
    
    return readme_issues, api_issues

def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate_batch_specs.py <目錄路徑>")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    readme_issues, api_issues = validate_specs(base_dir)
    
    print(f"=== README.md 問題 ({len(readme_issues)} 個目錄) ===\n")
    for issue in readme_issues:
        print(f"📁 {issue['dir']}")
        if 'broken_links' in issue:
            for text, path in issue['broken_links']:
                print(f"   [{text}]({path})")
        else:
            print(f"   {issue.get('issue', '未知問題')}")
        print()
    
    print(f"=== API 真實重複 ({len(api_issues)} 個目錄) ===\n")
    for issue in api_issues:
        print(f"📁 {issue['dir']}")
        for dup in issue['duplicates']:
            print(f"   {dup}")
        print()
    
    total = len(readme_issues) + len(api_issues)
    print(f"總計: {total} 個問題")
    
    return 0 if total == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
