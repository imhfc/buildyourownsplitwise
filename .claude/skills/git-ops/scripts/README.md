# Git Operations Framework

> 版本：1.0 | 建立日期：2026-02-01

## 概述

Git Operations Framework 是一個用於優化 AI 與 Git 交互的框架，透過資訊壓縮和決策分離，大幅減少 token 消耗。

**核心理念**：
- 資訊收集層：Shell Script 收集並壓縮 Git 狀態資訊
- 決策層：AI 基於精簡摘要做決策
- 執行層：Shell Script 執行命令並返回結構化結果

**預期效益**：
- Commit 操作 Token 消耗：-86%（3300 → 450）
- Status 查詢 Token 消耗：-75%（200 → 50）

## 目錄結構

```
.claude/skills/git-ops/scripts/
├── README.md              # 本文件
├── git-collector.sh       # 資訊收集器
├── git-executor.sh        # 執行器
├── conflict-resolver.sh   # 衝突解決器
├── lib/
│   ├── file-type.sh       # 文件類型檢測
│   ├── change-extractor.sh # 關鍵變更提取
│   └── error-handler.sh   # 錯誤處理
└── templates/
    ├── commit-context.yaml # Commit 上下文模板
    └── result.yaml         # 執行結果模板
```

## 使用方式

### 資訊收集（git-collector.sh）

```bash
# 收集 commit 所需資訊
./git-collector.sh --for-commit

# 收集 status 資訊
./git-collector.sh --status

# 收集 push 所需資訊
./git-collector.sh --for-push
```

### 執行操作（git-executor.sh）

```bash
# 執行 commit
./git-executor.sh commit --message "feat: 新增功能"

# 執行 push
./git-executor.sh push

# 執行 push 到指定分支
./git-executor.sh push --branch feature/xxx
```

## 輸出格式

### 資訊收集輸出（YAML）

```yaml
commit_context:
  branch: master
  status: 3 files changed, 62 insertions(+), 8 deletions(-)
  files:
    - file: preferences.yaml
      status: M
      type: config
      key_changes: "+force_agent_mode: true; ..."
  commit_style:
    recent_patterns:
      - "feat(xxx): ..."
  hooks:
    pre_commit: enabled
```

### 執行結果輸出（YAML）

```yaml
result:
  status: success
  commit: abc1234
  message: "feat: 新增功能"
  summary: "3 files changed, 10 insertions(+)"
```

## 配置

配置位於 `preferences.yaml` 的 `git_operations` 區塊。

---

## AI 整合

### Skill 觸發

使用 `/git-ops` skill 自動執行標準化流程：

```
/git-ops commit  → 收集 + 決策 + 執行
/git-ops status  → 收集 + 報告
/git-ops push    → 收集 + 確認 + 執行
```

### AI 行為規則

定義於 `preferences.yaml` → `git_operations.ai_behavior`：

```yaml
workflows:
  commit:
    steps: [collect, decide, execute]
  status:
    steps: [collect, report]
  push:
    steps: [collect, decide, execute]

forbidden_direct_commands:
  - "git commit"
  - "git push"

allowed_direct_commands:
  - "git add"
  - "git diff"
```

### 工作流程

```
用戶: "提交"
     ↓
AI 識別: commit 操作
     ↓
Step 1: Bash(git-collector.sh --for-commit)
     ↓
Step 2: AI 基於摘要生成 commit message
     ↓
Step 3: Bash(git-executor.sh commit --message "...")
     ↓
返回結構化結果
```

---

## 進階功能

Git Operations Framework 提供進階的分支、合併、歷史和衝突解決功能，支援複雜的 Git 工作流程。

### 分支管理（Branch Operations）

```bash
# 收集分支資訊
./git-collector.sh --for-branch

# 執行分支操作
./git-executor.sh branch --action create --name feature/new-feature
./git-executor.sh branch --action delete --name feature/old-feature
./git-executor.sh branch --action switch --name develop
```

**使用場景**：
- 建立功能分支：`建立分支 feature/xxx`
- 切換分支：`切換分支 develop`
- 刪除分支：`刪除分支 feature/old`

**AI 行為**：
- 自動驗證分支命名符合 `branch_prefix` 規則
- 檢查目標分支是否已存在
- 提醒未提交的變更

### 合併操作（Merge Operations）

```bash
# 收集合併前檢查
./git-collector.sh --for-merge

# 執行合併
./git-executor.sh merge --branch feature/new-feature
./git-executor.sh merge --branch develop --strategy recursive
```

**使用場景**：
- 合併功能分支：`合併 feature/new-feature`
- 合併開發分支：`merge develop`
- 使用特定策略合併：`merge main --strategy=squash`

**AI 行為**：
- 偵測是否有未提交的變更
- 預警可能的合併衝突
- 確認目標分支正確性
- 自動檢查 hooks 狀態

### 歷史查詢（History Operations）

```bash
# 收集提交歷史
./git-collector.sh --history
./git-collector.sh --history --file path/to/file
./git-collector.sh --history --author "name" --since "2 weeks ago"

# 執行歷史查詢
./git-executor.sh log --oneline
./git-executor.sh blame --file path/to/file
```

**使用場景**：
- 查看最近提交：`查看歷史`
- 查看文件變更：`查看 UserService.java 的歷史`
- 查看特定作者：`誰改了這個功能`
- 查看時間範圍：`最近一個月的提交`

**AI 行為**：
- 提供清晰的提交時間線
- 解釋關鍵變更原因
- 指出提交作者和時間
- 自動偵測重要的架構變更

### 衝突解決（Conflict Resolution）

```bash
# 偵測衝突
./.claude/skills/git-ops/scripts/conflict-resolver.sh --detect

# 分析衝突
./.claude/skills/git-ops/scripts/conflict-resolver.sh --analyze

# 執行衝突解決
./.claude/skills/git-ops/scripts/conflict-resolver.sh --resolve
./.claude/skills/git-ops/scripts/conflict-resolver.sh --resolve --strategy ours
./.claude/skills/git-ops/scripts/conflict-resolver.sh --resolve --strategy theirs
```

**衝突類型偵測**：
- **代碼衝突**：邏輯衝突、方法重名、導入語句衝突
- **配置衝突**：YAML 配置、properties 檔案、XML 組態
- **文檔衝突**：Markdown、README 等文檔文件
- **構建文件衝突**：pom.xml、build.gradle 等

**使用場景**：
- 偵測現有衝突：`檢查衝突`
- 分析衝突原因：`分析衝突`
- 解決衝突：`解決衝突`
- 使用特定策略：`使用 ours 策略解決衝突`

**解決策略**：
- `ours`：保留當前分支的變更
- `theirs`：採用合併分支的變更
- `manual`：引導用戶手動解決
- `auto`：嘗試自動解決（僅適用於簡單衝突）

**AI 行為**：
- 自動識別衝突類型和位置
- 分析每個衝突的上下文
- 提供衝突解決建議
- 指導用戶手動或自動解決
- 確認所有衝突已解決後才允許提交

### 綜合工作流程示例

**場景：修復功能並合併回主分支**

```
1. 用戶：建立分支 feature/user-auth
   → git-collector.sh --for-branch
   → AI 驗證分支命名
   → git-executor.sh branch --action create

2. 用戶：（開發並提交變更）
   → git-collector.sh --for-commit
   → AI 生成 commit message
   → git-executor.sh commit

3. 用戶：合併回 develop
   → git-collector.sh --for-merge
   → 衝突偵測：conflict-resolver.sh --detect
   → AI 分析衝突並提供建議
   → 用戶解決衝突或選擇策略
   → git-executor.sh merge

4. 用戶：推送到遠端
   → git-collector.sh --for-push
   → AI 確認可以推送
   → git-executor.sh push

5. 用戶：查看合併歷史
   → git-collector.sh --history
   → AI 報告變更摘要
```

---

## 與現有系統整合

- **Hooks**: 與 pre-commit/commit-msg hooks 協同工作
- **強制 Agent 模式**: 遵循 context 節省原則
- **配置**: 整合於 preferences.yaml
- **Skill**: `/git-ops` skill 封装完整流程

---

**參考文檔**：
- [CLAUDE.md](../../CLAUDE.md) - Git 操作標準流程
- [preferences.yaml](../../.claude/memory-bank/project-context/preferences.yaml) - 詳細配置
- [git-ops SKILL](../../.claude/skills/git-ops/SKILL.md) - Skill 說明
