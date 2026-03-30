---
name: git-ops
description: 使用 Git Operations Framework 執行標準化 Git 操作（commit, status, push, branch, merge, conflict）。
allowed-tools: [Bash, Read]
---

# Git Operations Skill

> 透過 .claude/skills/git-ops/scripts/ 執行標準化 Git 操作，節省 75-86% token 消耗

---

## 觸發條件

**自動觸發**（僅限 Git 版本控制語境）：
- 提交: "提交", "commit", "送交"
- 狀態: "git 狀態", "git status"
- 推送: "推送", "push", "上傳到遠端"
- 分支: "建立分支", "切換分支", "branch"
- 合併: "合併", "merge"
- 歷史: "提交歷史", "git log", "git history"
- 衝突: "解決衝突", "conflict"

**支援命令**：
- `/git-ops commit` - 執行標準提交流程
- `/git-ops status` - 查看精簡狀態
- `/git-ops push` - 執行推送
- `/git-ops branch` - 分支管理
- `/git-ops merge` - 合併分支
- `/git-ops history` - 歷史分析
- `/git-ops conflict` - 衝突解決

---

## 核心原則

**所有 Git 操作都透過 .claude/skills/git-ops/scripts/ 執行**

```
傳統方式: AI 直接執行 git 命令 → 讀取完整輸出 → 高 token 消耗
新框架:   Script 收集壓縮資訊 → AI 只做決策 → 低 token 消耗
```

---

## 操作流程

### Commit（提交）

```
Step 1: 收集資訊
  .claude/skills/git-ops/scripts/git-collector.sh --for-commit
  輸出: 壓縮摘要（~250 tokens）

Step 2: AI 決策
  基於摘要生成 commit message
  規則: conventional commits + 繁體中文 + 無 AI 標記

Step 3: 執行
  .claude/skills/git-ops/scripts/git-executor.sh commit --message "..."
  輸出: 結構化結果
```

**效益**: 3300 → 450 tokens（-86%）

### Status（狀態）

```
Step 1: 收集資訊
  .claude/skills/git-ops/scripts/git-collector.sh --status
  輸出: 精簡狀態（~50 tokens）

Step 2: 報告
  AI 向用戶報告狀態
```

**效益**: 200 → 50 tokens（-75%）

### Push（推送）

```
Step 1: 收集資訊
  .claude/skills/git-ops/scripts/git-collector.sh --for-push
  輸出: 推送檢查 + 警告

Step 2: AI 決策
  確認警告、決定是否推送

Step 3: 執行
  .claude/skills/git-ops/scripts/git-executor.sh push
  輸出: 結構化結果
```

### Branch（分支管理）

```
收集資訊: git-collector.sh --for-branch
執行操作:
  git-executor.sh branch --create <name>   # 建立
  git-executor.sh branch --switch <name>   # 切換
  git-executor.sh branch --delete <name>   # 刪除
  git-executor.sh branch --list            # 列出
```

### Merge（合併）

```
Step 1: 收集資訊
  git-collector.sh --for-merge <target>
  輸出: 合併前檢查 + 潛在衝突

Step 2: AI 決策
  確認警告、決定是否合併

Step 3: 執行
  git-executor.sh merge <branch> [--no-ff]
```

### History（歷史分析）

```
git-collector.sh --history           # 全倉庫
git-collector.sh --history <file>    # 特定檔案
輸出: 最近提交 + 貢獻者 + 活動統計
```

### Conflict（衝突解決）

```
檢測: conflict-resolver.sh --detect
分析: conflict-resolver.sh --analyze <file>
解決:
  conflict-resolver.sh --resolve <file> ours    # 保留我們的
  conflict-resolver.sh --resolve <file> theirs  # 保留他們的
  conflict-resolver.sh --resolve <file> manual  # 手動解決
```

---

## 使用範例

### 提交

```
用戶: "提交"

執行:
1. git-collector.sh --for-commit → 摘要
2. AI 生成 message
3. git-executor.sh commit --message "feat: ..."

輸出:
result:
  status: success
  commit: abc1234
  message: "feat(xxx): ..."
```

### 查看狀態

```
用戶: "狀態"

執行:
git-collector.sh --status

輸出:
status:
  branch: master
  staged_files: 3
  unstaged_files: 0
  clean: false
```

### 推送

```
用戶: "推送"

執行:
1. git-collector.sh --for-push → 檢查
2. AI 確認警告
3. git-executor.sh push

輸出:
result:
  status: success
  commits_pushed: 2
```

---

## 錯誤處理

### Hook 失敗

```yaml
result:
  status: failed
  error_type: HOOK_FAILED
  suggestion: "修復問題後重新提交"
  recoverable: true
```

AI 會：解析錯誤 → 嘗試修復 → 重新執行

### 無變更

```yaml
result:
  status: failed
  error_type: NOTHING_TO_COMMIT
  suggestion: "請先 git add"
```

---

## Commit Message 生成規則

### 類型判斷

| 檔案類型 | Commit 類型 |
|---------|------------|
| config | feat/chore |
| doc | docs |
| code (新增) | feat |
| code (修復) | fix |
| test | test |
| script | chore |

### 範圍判斷

- 同一目錄 → 目錄名
- 共同前綴 → 前綴
- 否則 → 省略或 "multiple"

---

## 配置

`preferences.yaml` → `git_operations.ai_behavior`

---

## 相關文檔

- [scripts/README.md](scripts/README.md)
- [preferences.yaml](../../../.claude/memory-bank/project-context/preferences.yaml)
- [CLAUDE.md](../../../CLAUDE.md)
