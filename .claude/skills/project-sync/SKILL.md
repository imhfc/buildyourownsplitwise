---
name: project-sync
description: 專案環境工具與跨專案同步。
model: claude-3-5-haiku-20241022
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Project Sync

> 專案環境工具 + 跨專案同步（統一入口）

---


## 觸發與路由


**Use this skill when user wants to:**
- Sync repos to IBM: "同步", "sync", "同步到 IBM", "sync to IBM"
- Fetch config files: "取得設定", "fetch profile", "取得 navi-profile"
- Setup environment: "初始化", "setup", "環境設定", "environment setup"
- Parallel development: "並行開發", "parallel", "Git Worktree"
- Cross-project sync: "同步特性到其他專案", "複製 hooks/agents/skills", "更新 Atomic Agents"

**Supports commands:**
- /project-sync sync [repo] [options]     - IBM 外網同步
- /project-sync fetch-profile [options]   - 取得 navi-profile 設定
- /project-sync setup [module]            - 環境初始化
- /project-sync parallel [modules...]     - 並行開發
- /project-sync cross [--target path]     - 跨專案同步
- /pt [subcommand]                        - 簡寫

**DO NOT trigger for:**
- Code sync questions: "如何同步代碼?" (questions)
- General discussions: "討論同步策略" (discussions)

**References: Atomic Agents 架構 (@.claude/agents/atomic/README.md), .claude/skills/shared/env.sh**

## 子命令總覽

| 子命令 | 用途 | Shell Script |
|--------|------|-------------|
| `sync` | IBM 外網同步（Azure DevOps → IBM GitHub） | `$PROJECT_SETUP/sync-repos.sh` |
| `fetch-profile` | 取得 navi-profile 設定檔 | `$PROJECT_SETUP/fetch-profile.sh` |
| `setup` | 環境初始化 | `$PROJECT_SETUP/install.sh` |
| `parallel` | Git Worktree 並行開發 | `$PROJECT_SETUP/parallel-dev.sh` |
| `cross` | 跨專案同步通用特性 | （見下方完整說明） |

環境變數 `$PROJECT_SETUP` 由 `.claude/skills/shared/env.sh` 自動設定。

---

## cross - 跨專案同步

> 從主專案同步通用框架元件到目標專案，智能排除專案特定內容

### 四階段工作流程

```
Phase 1: 同步通用元件（rsync --delete）
Phase 2: 刪除目標多餘檔案（source 沒有就刪）
Phase 3: 清除過時引用（.ai-docs、project、死連結）
Phase 4: 更新 README（反映目標實際結構）
```

---

## Phase 1: 同步通用元件

### Agents（通用）

```bash
# Atomic Agents（排除 project 專有）
rsync -av --delete \
  --exclude='review/project/' \
  --exclude='review/gbp-contract-comparator.md' \
  "$SRC/agents/atomic/" "$DST/agents/atomic/"

# Teams、Scripts、頂層 Agent 檔案
rsync -av "$SRC/agents/teams/" "$DST/agents/teams/"
rsync -av "$SRC/agents/scripts/" "$DST/agents/scripts/"
cp "$SRC/agents/general-assistant.md" "$DST/agents/"
cp "$SRC/agents/system-analyst.md" "$DST/agents/"
cp "$SRC/agents/README.md" "$DST/agents/"
```

**排除的 Project 專有 Agents**：
- `agents/atomic/review/project/`（4 個 project-*-compliance-auditor）
- `agents/atomic/review/gbp-contract-comparator.md`

### Skills（15 個通用）

逐一 rsync --delete：

| Skill | 類型 |
|-------|------|
| git-ops | 通用開發 |
| ast-grep | 通用開發 |
| review-code | 通用開發 |
| write-tests | 通用開發 |
| parallel-develop | 通用開發 |
| architecture-audit | 通用開發 |
| architecture-refactor | 通用開發 |
| agent-team | 專案管理 |
| skill-creator | 專案管理 |
| memory-bank | 專案管理 |
| project-sync | 專案管理 |
| docx | 文件處理 |
| xlsx | 文件處理 |
| markdown-doc-processor | 文件處理 |
| shared | 共用腳本 |

```bash
for skill in git-ops ast-grep review-code write-tests parallel-develop \
  agent-team skill-creator memory-bank markdown-doc-processor xlsx docx \
  project-sync shared architecture-audit architecture-refactor; do
  rsync -av --delete "$SRC/skills/$skill/" "$DST/skills/$skill/"
done
cp "$SRC/skills/README.md" "$DST/skills/README.md"
```

**排除的 Project 專有 Skills**：
- one-shot, one-shot-registry.yaml, one-shot-shared/
- reconcile-batch-* (spec-converter, spec-verifier, testdata, workflow)
- batch-dev-checklist, run-batch-pipeline, run-reconcile-batch
- batch-dataflow-report, data-flow-analysis
- accessor-generator, gbp-spec-verifier, gbp-api-decomposer
- spec-change-propagator, spec-drift-detector, reconcile-skill-updater
- analytics

### Hooks（整個替換）

```bash
rsync -av --delete --exclude='logs/' "$SRC/hooks/" "$DST/hooks/"
```

結構：`session/`、`validation/`、`tool/`、`subagent/`、`README.md`

### Settings

```
settings.json:     合併策略 — hooks + env 從 source，enabledPlugins 保留 target
settings.local.json: 加入 statusline + 通用 permissions，保留 target MCP 設定
statusline.sh:     直接覆蓋
mcp-tool-search.sh: 直接覆蓋
```

**settings.json 合併規則**：
- `env` 區塊 → 從 source 覆蓋
- `hooks` 區塊 → 從 source 覆蓋
- `enabledPlugins` 區塊 → 保留 target 原有設定

**settings.local.json 合併規則**：
- 加入 `statusLine` 設定（如 target 沒有）
- 加入通用 permissions（git add/commit, python3, Skill(git-ops)）
- 保留 target 的 MCP 設定和專案特定 permissions

### Memory Bank（結構同步，排除專案內容）

```bash
# 同步 README 和結構
cp "$SRC/memory-bank/README.md" "$DST/memory-bank/"
cp "$SRC/memory-bank/parallel-sessions/README.md" "$DST/memory-bank/parallel-sessions/"
```

**不同步的 Project 專有內容**：
- `microservices.yaml`
- `skill-triggers.yaml`

### CLAUDE.md

**不同步** — CLAUDE.md 是專案層級設定文件，包含專案特有描述（微服務列表、ADR 引用等），目標專案應自行維護。

---

## Phase 2: 刪除目標多餘檔案

**原則：source 沒有的就刪**

同步後，掃描目標專案中 source 不存在的檔案：

```bash
# 1. 舊 root agents（source 只保留 system-analyst.md + general-assistant.md）
# 常見殘留：architect.md, developer.md, qa.md, reviewer.md,
#           frontend-designer.md, system-designer.md,
#           orchestrator.md, module-developer.md

# 2. 舊 skills（source 沒有的 skill 目錄）
# 常見殘留：agents-sync, agent-router, general-assistant,
#           coding-standards, environment-setup, aidocs-navigator,
#           openspec, speckit-converter, governance-checker,
#           system-analyst, system-designer, docs,
#           analytics, audit-operations, bug, prove, techdebt,
#           frontend-designer, learn, plan-review

# 3. 舊 rules/（source 已不使用 rules 目錄）
# 4. 舊 docs/（source 已不使用 docs 目錄，內容移至 skills/agents）
# 5. 舊 scripts/（source 已不使用 scripts 目錄，移至 skills/shared）
# 6. 舊 hooks 扁平檔案（source 改用子目錄結構）
# 常見殘留：hooks 根目錄的 .sh 檔案、HOOKS-COMPARISON.md
# 7. 舊 hook/agent 附帶文件
# 常見殘留：DETECT-CORRECTION-GUIDE.md, ENFORCE-PLANNING.md 等
```

**檢查方法**：逐一比對 source 是否有對應檔案/目錄

---

## Phase 3: 清除過時引用

同步後的檔案仍可能包含 source 專案特有的引用，必須批量清除：

### 3.1 清除 .ai-docs context 引用（40+ agent 檔案）

Agent frontmatter 的 `context:` 區塊引用 `.ai-docs/` 路徑，目標專案不存在：

```bash
find "$DST/agents" -name "*.md" -exec sed -i '' '/\.ai-docs/d' {} +
```

### 3.2 清除 project 專有引用

批量替換所有 .md 和 .yaml 檔案：

```bash
find "$DST" \( -name "*.md" -o -name "*.yaml" \) -exec sed -i '' \
  -e 's/hexagonal-architecture-compliance-auditor/hexagonal-architecture-compliance-auditor/g' \
  -e 's/compliance-auditor/compliance-auditor/g' \
  -e 's/compliance-auditor/compliance-auditor/g' \
  -e 's/compliance-auditor/compliance-auditor/g' \
  -e 's|com/ibm/project/\*/|**/|g' \
  -e 's|/code-editor|/code-editor|g' \
  -e 's|/architecture-planner|/architecture-planner|g' \
  -e 's|/system-analyst|/system-analyst|g' \
  -e 's/PROJECT/PROJECT/g' \
  -e 's/Project/Project/g' \
  -e 's/source-ai-agent/source-ai-agent/g' \
  -e 's/project/project/g' \
  {} +
```

### 3.3 驗證零殘留

```bash
grep -ri "\.ai-docs\|project\|DOMAIN-BOUNDARY\|MCP-BEST-PRACTICES\|COMPOSITION-STRATEGY\|ARCHITECTURE-SRP" \
  --include="*.md" --include="*.yaml" "$DST/" | grep -v '.git/'
```

目標：**0 matches**

### 3.4 清除死連結

檢查 README 中引用的檔案是否存在：
- `COMPOSITION-STRATEGY.md`、`ARCHITECTURE-SRP.md` → 刪除引用
- `MCP-BEST-PRACTICES.md` → 刪除引用
- `module-developer`、`orchestrator` → 刪除引用
- `lib/logging.sh` → 刪除引用

---

## Phase 4: 更新 README

同步的 README 包含 source 專案特有內容，必須重寫以反映目標實際結構。

**重寫前先驗證實際計數**（勿依賴文檔中的舊數字）：

```bash
# Atomic Agents 實際數量（.md 檔案，排除 README/QUICK-START/STANDARDS-MAPPING，加計 task-router/README.md）
find "$DST/agents/atomic" -name "*.md" \
  ! -name "README.md" ! -name "QUICK-START.md" ! -name "STANDARDS-MAPPING.md" | wc -l
# 再加 1（task-router/README.md 是 agent 定義）→ 目前 source = 45 個

# Skills 實際數量（目錄數，不含 shared）
ls "$DST/skills" | grep -v -E '^(README\.md|shared)$' | wc -l
# 目前 source = 14 個

# Hooks 實際數量（各子目錄的 .sh 檔案數）
find "$DST/hooks" -name "*.sh" | wc -l
# 目前 source = 7 個（含 completion/verify-completion.sh）
```

**需重寫的 README**：
1. `.claude/README.md` — 反映目標的 skills/agents/hooks 數量和結構
2. `.claude/agents/README.md` — 移除已被 Atomic Agents 取代的舊 agents
3. `.claude/skills/README.md` — 只列出目標實際擁有的 skills
4. `.claude/hooks/README.md` — 移除 lib/logging.sh 引用、module-developer 引用
5. `.claude/memory-bank/README.md` — 移除 project 專有檔案描述
6. `.claude/agents/atomic/README.md` — 移除 project 專有 agents、Phase 6、.ai-docs context 範例

---

## 同步檢查清單

### 同步前

- [ ] 確認目標專案路徑存在且是 Git repository
- [ ] 確認 source 專案已 commit 最新變更

### Phase 1 後

- [ ] Atomic Agents 數量正確（排除 project 專有，source = 45 個）
- [ ] 14 個通用 Skills 全部同步（shared 是支援目錄，不計入）
- [ ] Hooks 為子目錄結構（session/validation/tool/subagent/completion，共 7 個）
- [ ] settings.json 合併正確（hooks+env 從 source，plugins 保留 target）

### Phase 2 後

- [ ] 無舊 root agents（architect, developer, qa 等）
- [ ] 無舊 skills（agents-sync, agent-router 等）
- [ ] 無 rules/、docs/、scripts/ 目錄
- [ ] 無扁平 hooks 檔案

### Phase 3 後

- [ ] `.ai-docs` 引用 = 0
- [ ] `project` 引用 = 0
- [ ] 死連結 = 0

### Phase 4 後

- [ ] 所有 README 反映目標實際結構
- [ ] 無引用不存在的檔案

### 最終

- [ ] `git add -A && git commit`
- [ ] 清除 .bak 暫存檔案（如有）

---

## 經驗教訓

### 2026-03-29 README 計數驗證實錄

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| README 寫 35 agents，實際 45 | 文檔從未更新，依賴舊數字 | Phase 4 前先 find/ls 驗證實際計數 |
| README 寫 22 skills，實際 14 | 混淆 shared 目錄 + 舊版遺留 | shared 是支援目錄，不計入 skill 數 |
| README 寫 6 hooks，實際 7 | 新增 completion/ 後文檔未同步 | 清點各子目錄的 .sh 檔案數 |
| task-router 未計入 agent 數 | find 排除 README.md 時漏計 | task-router/README.md 本身即 agent 定義，需 +1 |

### 2026-03-27 同步實錄

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| 首次同步遺漏大量舊檔案 | 只刪了已知的 2 個 agents，未全面比對 | Phase 2 必須全面掃描 |
| README 同步後含 project 內容 | rsync 直接覆蓋了 source 的 README | Phase 4 必須重寫 README |
| 40+ agent 含 .ai-docs 引用 | agent frontmatter 的 context 路徑 | Phase 3.1 批量 sed 清除 |
| 背景 agent 產生 .bak 檔案 | code-editor agent 的備份行為 | 最終清理步驟檢查 |
| settings.json 直接覆蓋破壞 plugins | source 和 target 的 plugins 不同 | 合併策略：分區塊處理 |
| CLAUDE.md 覆蓋使 target 變成 Project | CLAUDE.md 是專案層級設定 | 原則：CLAUDE.md 不同步 |
| cwd 被 hook 重設導致 grep 搜錯目錄 | validate-bash hook 重設 cwd | 使用絕對路徑 |

---

## 相關 Skills

- `memory-bank` - 記憶管理（同步後需調整 project-context）
- `skill-creator` - 建立專案特定 skills
