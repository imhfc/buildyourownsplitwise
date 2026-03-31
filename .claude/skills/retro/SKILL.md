---
name: retro
description: 對話回顧與知識沉澱。萃取本次學到的知識，分類為固化/泛化，修正受影響的檔案。Use this skill when 使用者說「回顧」「retro」「沉澱」「學到什麼」或對話即將結束時。
user-invocable: true
---

# Retrospective Skill — 對話回顧與知識沉澱

> 把學習成果固化到框架中，讓同樣的錯不犯第二次，讓好的做法成為預設。

## 執行模型

**所有 Agent 呼叫使用 `model: "sonnet"`**。retro 以文字萃取和檔案編輯為主，不需要最高階推理。

---

## 核心流程（3 步）

```
Step 1: 萃取與分類 ──→ Step 2: 修正 ──→ Step 3: 驗證與報告
```

---

## Step 1: 萃取與分類

回顧對話，列出**非顯而易見**的知識（讀代碼就能看出來的不算），每條必須有因果關係。

同時將每條知識分類：

| 分類 | 定義 | 特徵 | 去向 |
|------|------|------|------|
| **固化** | 可編碼為規則或自動檢查 | if-then 規則、違反會出錯、可自動檢查 | `QUALITY_SLA.md`, `quality-gate.sh`, `.claude/rules/`, `CLAUDE.md` 常見錯誤清單 |
| **泛化** | 最佳實踐、策略、跨情境適用 | 思維方式、需情境判斷、不能簡化為單一規則 | `decisions.yaml`, `.claude/rules/`, `.claude/skills/` |

### 輸出格式

```yaml
knowledge:
  solidified:
    - id: K-001
      summary: "簡短描述"
      detail: "問題 → 原因 → 解法"
      rule: "IF <條件> THEN <必須/禁止>"
      targets:
        - path: "目標檔案"
          action: "新增/更新"

  generalized:
    - id: K-002
      summary: "簡短描述"
      detail: "問題 → 原因 → 解法"
      principle: "核心原則（一句話）"
      targets:
        - path: "目標檔案"
          action: "新增/更新"

  skipped:
    - id: K-003
      summary: "..."
      reason: "已存在 / 確信度低 / 不適用"
```

寧缺毋濫。確信度低的放 skipped，不強行修正。

---

## Step 2: 修正

### 原則

1. **先讀後寫** — 修改前必先讀取當前內容，確認不衝突
2. **最小改動** — 只改需要改的，保持目標檔案的現有格式
3. **加註來源** — 標註回顧日期

### 修正順序

```
1. QUALITY_SLA.md      ← 固化（不變式 + 事件歷史）
2. quality-gate.sh     ← 固化（自動檢查）
3. .claude/rules/      ← 固化 + 泛化
4. .claude/skills/     ← 泛化（流程改善）
5. memory-bank/        ← 泛化（決策/進度）
6. CLAUDE.md           ← 固化（常見錯誤清單）
```

---

## Step 3: 驗證

- 修正的檔案可正常讀取（無語法錯誤）
- `quality-gate.sh` 新增的檢查可執行
- `memory-bank` YAML 格式正確

驗證通過即完成，不需要輸出摘要報告。

---

## 設計哲學

- **固化知識** → 自動檢查，機器守護 → 永遠不犯第二次
- **泛化知識** → 指引，提醒 AI 下次注意 → 提高判斷品質

```
第 1 次犯錯：修復 bug
第 2 次犯錯：不應該發生（已有自動檢查）
```
