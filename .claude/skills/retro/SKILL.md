---
name: retro
description: 對話回顧與知識沉澱。在每次對話結束前，萃取本次學到的知識，分類為固化/泛化，分析影響範圍，自動修正受影響的 skills/rules/memory。Use this skill when 使用者說「回顧」「retro」「沉澱」「學到什麼」或對話即將結束時。
user-invocable: true
---

# Retrospective Skill — 對話回顧與知識沉澱

> 每次對話都是一次學習。這個 Skill 把學習成果固化到框架中，讓同樣的錯不犯第二次，讓好的做法成為預設。

---

## 執行模型

**所有 Phase 的 Agent 呼叫必須使用 `model: "sonnet"`**，以降低成本並加快執行速度。retro 的工作以文字萃取、分類和檔案編輯為主，不需要最高階推理能力。

---

## 觸發條件

- 使用者說「回顧」「retrospective」「沉澱」「總結這次學到什麼」
- 對話結束前主動提議（由 Stop hook 提示）
- 完成重大任務後（bug 修復、新功能、架構變更）

---

## 核心流程（5 個 Phase）

```
Phase 1: 萃取 ──→ Phase 2: 分類 ──→ Phase 3: 影響分析 ──→ Phase 4: 修正 ──→ Phase 5: 驗證
 (Extract)         (Classify)        (Impact)             (Correct)         (Verify)
```

---

## Phase 1: 知識萃取 (Extract)

回顧本次對話，逐一列出所有**值得記住的事件**：

### 萃取清單

| 類型 | 觸發訊號 | 範例 |
|------|---------|------|
| Bug 修復 | 找到並修正了錯誤 | 「hydration callback 用錯了 API」 |
| 踩坑經驗 | 嘗試失敗後換方法 | 「react-dom 版本不能用 ^，要 pin」 |
| 新發現 | 學到未預期的行為 | 「expo-doctor 會檢查 peer deps」 |
| 技術決策 | 做了選擇並有理由 | 「選 Zustand 因為比 Redux 簡潔」 |
| 流程改善 | 發現更好的做事方式 | 「先跑 quality-gate 再跑 pytest 更快」 |
| 配置發現 | 發現必須維持的設定 | 「metro.config 的 unstable_enablePackageExports 必須 false」 |

### 輸出格式

```yaml
extracted_knowledge:
  - id: K-001
    type: bug_fix          # bug_fix | pitfall | discovery | decision | process | config
    summary: "簡短描述"
    detail: "完整脈絡：問題 → 原因 → 解法"
    confidence: high       # high | medium | low（對這條知識的確信程度）
```

**規則**：
- 只萃取**非顯而易見**的知識（顯而易見的 = 讀代碼就能看出來的）
- 每條知識必須有**因果關係**（不只是「做了什麼」，要有「為什麼」）
- 數量不限，但寧缺毋濫

---

## Phase 2: 知識分類 (Classify)

將每條知識分為兩類：

### 固化知識（Solidified）

**定義**：具體的、可直接編碼為規則或檢查的、專案特定的。

**特徵**：
- 可以寫成 if-then 規則
- 違反時會直接導致錯誤
- 有明確的檢查方式

**範例**：
- 「react-dom 版本不能有 ^，否則 hydration 會壞」→ quality-gate.sh 檢查
- 「金額必須用 Decimal，float 會有精度問題」→ architecture-audit 檢查項
- 「i18n caches 必須設 []，否則 localStorage 會覆蓋語言設定」→ 設定不變式

**去向**：
- `QUALITY_SLA.md` → 新增不變式
- `quality-gate.sh` → 新增自動檢查
- `.claude/rules/` → 新增或更新規則
- `.claude/skills/*/SKILL.md` → 更新檢查清單
- `CLAUDE.md` → 更新常見錯誤清單

---

### 泛化知識（Generalized）

**定義**：通用的、屬於最佳實踐的、跨情境適用的。

**特徵**：
- 是一種思維方式或策略
- 不能簡化為單一規則
- 需要根據情境判斷

**範例**：
- 「debug 空白頁時，先檢查 console error 再檢查 bundler」→ 除錯策略
- 「改 config 後一定要清快取再測」→ 開發習慣
- 「API 設計先寫 schema，再寫 route，最後寫 service」→ 開發順序

**去向**：
- `.claude/memory-bank/project-context/decisions.yaml` → 技術決策
- `.claude/skills/*/SKILL.md` → 更新流程建議
- `.claude/rules/development-workflow.md` → 更新工作流程
- `.claude/agents/atomic/*/` → 更新 agent 行為準則

---

### 分類輸出格式

```yaml
classified_knowledge:
  solidified:
    - id: K-001
      summary: "..."
      rule: "IF <條件> THEN <必須/禁止>"
      check_method: "如何自動檢查"
      target_files:
        - path: "目標檔案"
          action: "新增/更新/刪除"
          section: "哪個段落"

  generalized:
    - id: K-003
      summary: "..."
      principle: "核心原則（一句話）"
      when_to_apply: "什麼情境下適用"
      target_files:
        - path: "目標檔案"
          action: "新增/更新"
          section: "哪個段落"
```

---

## Phase 3: 影響分析 (Impact Analysis)

對每條知識，判斷它影響哪些檔案：

### 影響矩陣

| 知識類型 | 可能影響的檔案 |
|---------|--------------|
| Bug 修復 | `QUALITY_SLA.md` §4 §5, `quality-gate.sh`, `.claude/rules/` |
| 配置發現 | `QUALITY_SLA.md` §4, `quality-gate.sh` |
| 技術決策 | `memory-bank/decisions.yaml`, `.claude/rules/` |
| 流程改善 | `.claude/rules/development-workflow.md`, `.claude/skills/*/SKILL.md` |
| 踩坑經驗 | `CLAUDE.md` 常見錯誤清單, `.claude/skills/*/SKILL.md` |
| 新發現 | `.claude/agents/atomic/*/`, `.claude/rules/` |

### 衝突檢測

修正前必須檢查：
1. **讀取目標檔案** — 確認修正不會與現有內容矛盾
2. **向量衝突** — 新規則是否與既有規則衝突
3. **範圍確認** — 修正是否超出了這條知識的適用範圍

### 輸出格式

```yaml
impact_analysis:
  - knowledge_id: K-001
    affected_files:
      - path: "QUALITY_SLA.md"
        current_content: "（讀取後摘要）"
        proposed_change: "在 §4 新增 C-XX 不變式"
        conflict: none
      - path: "mobile/scripts/quality-gate.sh"
        current_content: "（讀取後摘要）"
        proposed_change: "新增檢查腳本"
        conflict: none
    risk: low    # low | medium | high
```

---

## Phase 4: 自動修正 (Correct)

### 修正原則

1. **最小改動** — 只改需要改的，不做額外「改善」
2. **先讀後寫** — 每個檔案修改前必須先讀取當前內容
3. **保持格式** — 沿用目標檔案的現有格式和風格
4. **加註來源** — 在修正處標註來自哪次回顧（日期）

### 修正順序

```
1. QUALITY_SLA.md      ← 固化知識（不變式 + 事件歷史）
2. quality-gate.sh     ← 固化知識（自動檢查）
3. .claude/rules/      ← 兩種知識都可能
4. .claude/skills/     ← 泛化知識（流程改善）
5. memory-bank/        ← 泛化知識（決策/進度）
6. CLAUDE.md           ← 固化知識（常見錯誤清單）
7. agents/atomic/      ← 泛化知識（agent 行為）
```

### 每個修正必須包含

```markdown
### [修正 ID] — 簡短描述
- **來源**：K-XXX（本次回顧萃取）
- **類型**：固化 / 泛化
- **修改檔案**：path/to/file
- **修改內容**：具體的 diff 描述
- **理由**：為什麼要改
```

---

## Phase 5: 驗證 (Verify)

### 驗證清單

- [ ] 所有修正的檔案都能正常讀取（無語法錯誤）
- [ ] `quality-gate.sh` 新增的檢查可以執行
- [ ] 新增的規則不與既有規則矛盾
- [ ] `memory-bank` 的 YAML 格式正確
- [ ] 修正報告完整（每條知識都有去向）

### 最終報告

```markdown
# 對話回顧報告 — YYYY-MM-DD

## 知識萃取
- 萃取：X 條知識
- 固化：Y 條 → Z 個檔案修正
- 泛化：W 條 → V 個檔案修正
- 跳過：N 條（理由：已存在 / 確信度低 / 不適用）

## 固化知識（已編碼為規則）
| ID | 摘要 | 修正檔案 | 狀態 |
|----|------|---------|------|
| K-001 | ... | quality-gate.sh | Done |

## 泛化知識（已沉澱為指引）
| ID | 摘要 | 修正檔案 | 狀態 |
|----|------|---------|------|
| K-003 | ... | decisions.yaml | Done |

## 未處理
| ID | 摘要 | 原因 |
|----|------|------|
| K-005 | ... | 確信度低，需更多驗證 |
```

---

## 使用方式

```bash
# 手動觸發（對話結束前）
/retro

# 自然語言
回顧一下這次對話學到什麼
沉澱這次的經驗
總結並更新框架
```

---

## 設計哲學

### 為什麼要分固化和泛化？

- **固化知識**可以變成**自動檢查**，讓機器替你守護 → 永遠不犯第二次
- **泛化知識**只能變成**指引**，提醒 AI 下次注意 → 提高判斷品質

如果所有知識都當泛化處理，就只是「記住了但沒防線」。
如果所有知識都當固化處理，就會產生過多僵化規則。

### 知識沉澱的目標

```
第 1 次犯錯：修復 bug
第 2 次犯錯：不應該發生（因為已經有自動檢查）

第 1 次做對：完成任務
第 2 次做對：更快完成（因為流程已經優化）
```
