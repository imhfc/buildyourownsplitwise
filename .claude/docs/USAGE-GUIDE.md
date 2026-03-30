# Fine-Tune AI Agent 使用指南

> 為 Build Your Own Splitewise 專案量身打造的 AI 開發助手框架

---

## 零、你不需要做任何事

框架大部分功能是**自動運作**的。只要你在專案目錄中啟動 Claude Code，以下事情會自動發生：

| 時機 | 自動行為 |
|------|---------|
| 開始對話 | 載入專案記憶（技術棧、偏好、進度） |
| 你輸入 Bash 指令 | 攔截危險命令、自動放行安全命令 |
| Bash 執行失敗 | 自動分析 pytest / npm 錯誤原因並建議修正 |
| 對話結束 | 提醒未完成任務、檢查未提交變更 |

你只需要知道：**有幾個 Skill 可以幫你做事更快。**

---

## 一、最常用的 4 個 Skills

### 1. `/write-tests` — 寫測試

直接告訴 AI 你要測什麼：

```
/write-tests 為 settlement_service 撰寫單元測試
```

或用自然語言（AI 會自動判斷）：

```
幫我補充 exchange_rate 的測試
為新增的 API 端點寫測試
測試分帳邏輯的邊界條件
```

**它會做什麼**：
1. 讀取你的產品代碼
2. 撰寫 pytest 測試（後端）或 Jest 測試（前端）
3. 執行測試確認通過
4. 分析覆蓋率，建議補充

**測試放哪裡**：
- 後端：`backend/tests/test_<模組>.py`
- 前端：`mobile/__tests__/<模組>.test.ts`

---

### 2. `/review-code` — 代碼審查

```
/review-code 審查 expense_service.py
```

或自然語言：

```
審查最近的變更
檢查 auth.py 的安全性
Review group_service 的程式碼品質
掃描 API 層有沒有安全漏洞
```

**它會做什麼**：
1. 根據檔案數量自動選擇審查策略（快速/標準/深度）
2. 多維度並行審查：安全性、架構合規、資料完整性、程式碼品質
3. 輸出結構化報告（Critical / High / Medium / Low）

**什麼時候用**：
- PR 前自我審查
- 改完重要邏輯後
- 想確認安全性時

---

### 3. `/git-ops` — Git 操作

```
/git-ops commit    # 自動收集變更、生成 commit message
/git-ops status    # 壓縮版 git status
/git-ops push      # 推送前檢查
```

**好處**：自動遵循 commit 格式（`feat: 描述`），省掉手動寫 message 的時間。

---

### 4. `/memory-bank` — 記憶管理

```
記錄決策：我們決定用 Redis 快取匯率，TTL 設 1 小時
更新進度：expense API 的多幣別支援已完成
搜索教訓：之前 hydration 的 bug 是怎麼解決的？
```

**什麼時候用**：
- 做了重要技術決策 → 記下來，下次對話能回憶
- 完成里程碑 → 更新進度
- 遇到類似問題 → 搜索過去的經驗

---

## 二、最重要的 Skill：`/retro`

### `/retro` — 對話回顧與知識沉澱

**每次對話結束前執行。** 這是讓框架越用越聰明的核心機制。

```
/retro
回顧一下這次學到什麼
沉澱這次的經驗
```

**它會做什麼**（5 個 Phase）：

```
萃取 → 分類 → 影響分析 → 修正 → 驗證
```

1. **萃取**：掃描對話，找出 bug 修復、踩坑經驗、技術決策、新發現
2. **分類**：
   - **固化知識** — 可以變成自動檢查（加進 quality-gate.sh、QUALITY_SLA.md）
   - **泛化知識** — 只能變成指引（更新 skills、rules、memory-bank）
3. **影響分析**：判斷每條知識影響哪些檔案
4. **自動修正**：更新受影響的檔案
5. **驗證**：確認修正不破壞現有功能

**為什麼重要**：
- 固化知識 = 自動防線 → 同一個 bug 永遠不會發生第二次
- 泛化知識 = AI 變聰明 → 下次對話做得更快更好

**什麼時候用**：
- 每次對話結束前（hook 會自動提醒你）
- 修完一個難纏的 bug 之後
- 做了重要的架構決策之後

---

## 三、其他 Skills

### `/architecture-audit` — 架構合規審查

```
架構審查
Clean Architecture 合規檢查
```

自動檢查 17 項規範：
- API 層有沒有混入業務邏輯
- 有沒有反向依賴（services import api）
- 金額是不是用 Decimal
- 認證有沒有硬編碼密鑰

---

### `/parallel-develop` — 並行開發

```
並行開發：同時實作 settlement API 和 notification 功能
```

AI 會分析依賴關係，規劃哪些任務可以並行，哪些要順序執行。

---

### `/agent-team` — Agent 團隊

```
建立 Agent Team 對 expense 模組做跨維度審查
```

啟動多個獨立 AI Agent 同時工作（需要 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）。

---

## 四、自動安全防護（Hooks）

你不需要設定，以下行為已自動生效：

### 危險命令攔截

| 命令 | 行為 |
|------|------|
| `rm -rf /` | 直接阻止，無法執行 |
| `git push --force` | 警告，需手動確認 |
| `git reset --hard` | 警告，需手動確認 |
| `git --no-verify` | 自動拒絕（繞過 hooks 需人工同意） |

### 安全命令自動放行

以下命令不會跳出權限確認框：

| 命令 | 原因 |
|------|------|
| `git status/diff/log` | 只讀 Git 操作 |
| `pytest tests/` | 後端測試 |
| `npx expo/jest/tsc` | 前端工具 |
| `quality-gate.sh` | 品質關卡 |
| `docker compose ... ps/logs` | Docker 檢視 |

### 失敗自動分析

當 pytest 或 npm 失敗時，AI 會自動辨識錯誤類型：
- **ImportError** → 建議 `pip install -r requirements.txt`
- **ConnectionRefusedError** → 建議啟動測試 DB
- **TypeScript 類型錯誤** → 建議 `npx tsc --noEmit`
- **Metro SyntaxError** → 建議檢查 babel/metro config

---

## 五、記憶系統

### 自動記憶（跨對話保存）

框架有兩套記憶：

| 系統 | 位置 | 用途 |
|------|------|------|
| Claude Auto Memory | `~/.claude/projects/.../memory/` | 使用者偏好、回饋、專案資訊 |
| Memory Bank | `.claude/memory-bank/` | 技術決策、開發進度、偏好設定 |

### 記憶檔案

```
.claude/memory-bank/project-context/
├── decisions.yaml      # 技術決策（為什麼選 FastAPI、為什麼用 Decimal）
├── preferences.yaml    # 專案偏好（Git 操作規則、並行開發觸發條件）
├── progress.yaml       # 開發進度（當前衝刺、已完成功能）
└── microservices.yaml  # 專案元件配置（backend/mobile/db/cache）
```

### 怎麼用

不需要手動編輯這些檔案。對 AI 說就好：

```
記住：我們決定匯率快取改為每 30 分鐘更新一次
更新進度：Google OAuth 已完成
```

---

## 六、日常開發工作流

### 場景 A：開發新功能

```
1. 告訴 AI 你要做什麼
   → AI 讀取相關代碼，實作功能

2. "為新功能寫測試" 或 /write-tests
   → AI 自動撰寫 + 執行測試

3. "審查一下剛才的改動" 或 /review-code
   → AI 多維度審查，回報問題

4. /git-ops commit
   → 自動生成 commit message 並提交
```

### 場景 B：修 Bug

```
1. 描述 bug 現象
   → AI 定位問題、修復

2. AI 自動跑測試（CLAUDE.md 規定的）

3. "記錄這個 bug"
   → AI 更新 QUALITY_SLA.md + quality-gate.sh（CLAUDE.md 規定的）
```

### 場景 C：代碼審查

```
1. /review-code 審查 backend/app/services/
   → 深度審查所有 service 檔案

2. 根據報告修正問題

3. /architecture-audit
   → 確認架構沒有被破壞
```

---

## 七、`ft` 命令行工具

```bash
# 先加入 PATH（一次性設定）
export PATH="$PWD/.claude/bin:$PATH"

# 查看狀態
ft status

# 查看幫助
ft help

# 查看版本
ft version
```

---

## 八、檔案結構速查

```
.claude/
├── settings.json          # Hooks 註冊（自動觸發）
├── settings.local.json    # 權限設定（WebSearch 等）
├── rules/                 # 行為規則（自動載入，影響 AI 行為）
│   ├── language-standards.md
│   ├── git-standards.md
│   ├── development-workflow.md
│   ├── project-standards.md
│   ├── testing-standards.md
│   ├── context-management.md
│   └── memory-bank.md
├── hooks/                 # 自動化腳本（事件觸發）
│   ├── session/           # 會話開始/結束
│   ├── validation/        # 命令安全檢查
│   ├── tool/              # 權限自動判斷 + 失敗分析
│   ├── completion/        # 完成度檢查
│   └── subagent/          # 子代理驗證
├── skills/                # 可用 Skills（斜線命令觸發）
│   ├── write-tests/       # /write-tests
│   ├── review-code/       # /review-code
│   ├── git-ops/           # /git-ops
│   ├── memory-bank/       # /memory-bank
│   ├── architecture-audit/
│   ├── parallel-develop/
│   └── ...
├── agents/atomic/         # 49 個原子 Agent（由 Skills 組合調用）
│   ├── test/              # test-writer, test-runner, test-fixer, coverage-analyzer
│   ├── review/            # code-reviewer, security-scanner, compliance-auditor
│   ├── code/              # code-editor, code-generator, code-formatter
│   ├── search/            # file-finder, code-searcher
│   └── ...
├── memory-bank/           # 跨對話記憶
│   └── project-context/   # decisions, preferences, progress
├── bin/                   # ft 命令行工具
└── docs/                  # 文件（本指南）
```

---

## 九、常見問題

### Q: Skills 沒有觸發？

確認 `.claude/settings.json` 存在且有 hooks 設定。可以用 `ft status` 檢查。

### Q: Hook 誤攔了我的命令？

hooks 的安全建議（INFO 等級）可以忽略。只有 BLOCK 等級會阻止執行。如果被誤攔，直接重新執行即可。

### Q: 怎麼新增自己的 Skill？

```
/skill-creator 建立一個新的 Skill
```

或手動在 `.claude/skills/<name>/SKILL.md` 建立，遵循現有格式。

### Q: 記憶過時了怎麼辦？

```
更新 decisions.yaml：匯率快取策略已改為 XXX
清除 progress.yaml 的舊任務
```

AI 會幫你更新對應的 YAML 檔案。

---

## 十、一句話總結

> **你只需要用自然語言跟 AI 說話。框架在背後自動處理安全、記憶、品質檢查。
> 想加速就用 `/write-tests`、`/review-code`、`/git-ops`。**
