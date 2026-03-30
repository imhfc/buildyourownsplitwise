---
name: parallel-develop
description: 規劃並行開發任務，自動分析依賴、檢測衝突、生成執行計劃。
allowed-tools: Task, Read, Glob, Bash
---

# Parallel Develop Skill

> 組合 Parallel Coordinator + 開發 Agents 完成並行開發

## 執行流程

```
Step 1: 調用 parallel-coordinator 規劃
  ↓
Step 2: 收到執行計劃（YAML）
  ↓
Step 3: 根據計劃並行執行開發 Agents
  ↓
Step 4: 整合代碼並測試
```

**重要**：此 Skill 在主會話執行，不在 forked context。

## 使用場景

使用此 Skill 來：

### 1. 並行開發多個模組
- 微服務模組並行開發
- API 端點並行實作
- 多個功能並行開發
- 批次任務並行建立

### 2. 依賴分析
- 自動分析模組間依賴關係
- 識別共用組件需求
- 建議最優開發順序

### 3. 衝突檢測
- 檢測文件級別衝突
- 識別實體級別衝突
- 提供衝突解決方案

### 4. 執行計劃生成
- Phase 劃分（階段規劃）
- 並行分組（Group 策略）
- 時間估算和風險評估

## 使用方式

```bash
# 方式 1: 使用斜線命令
/parallel-develop 並行開發 user-mgmt、order-mgmt、profile-mgmt 三個模組

# 方式 2: 自然語言（自動觸發）
並行開發 User、Order、Product 模組
同時開發 5 個 API 端點
```

## 範例

### 範例 1: 並行開發微服務模組
```bash
/parallel-develop 並行開發 user-mgmt、order-mgmt、profile-mgmt
```

**輸出**：
- 依賴關係分析
- 共用組件識別
- 3 階段執行計劃（共用組件 → 並行開發 → 集成測試）
- 時間估算：3-4 小時

---

### 範例 2: 並行開發 API 端點
```bash
/parallel-develop 並行開發 User API 的 5 個端點
```

**輸出**：
- 衝突檢測（UserController.java、UserService.java）
- 完全並行策略
- 2 階段執行計劃（並行開發 → 合併代碼）
- 時間估算：1.5 小時

---

### 範例 3: 批次任務並行開發
```bash
/parallel-develop 並行開發 v1.0 order-mgmt Reconcile 批次任務
```

**輸出**：
- 流水線依賴分析（Reader → Processor → Writer）
- 順序執行策略
- 3 階段執行計劃（配置 → 順序開發 → 測試）
- 時間估算：2.5-3 小時

## Worktree 自動建議

### 觸發條件

當偵測到以下情況時，AI 會自動建議使用 Git Worktree：

#### 關鍵字偵測
- **並行開發相關**：「並行」、「同時開發」、「多模組」、「平行」
- **Worktree 相關**：「worktree」、「隔離」、「實驗」、「獨立分支」
- **英文關鍵字**：「parallel」、「concurrent」、「multiple features」

#### 上下文判斷
- 涉及 **3+ 個文件**或 **2+ 個模組**的開發
- 需要**獨立分支**進行功能開發
- 存在**文件衝突風險**的並行任務
- **長時間任務**需要工作區隔離

### 建議訊息格式

當觸發 Worktree 建議時，會輸出以下訊息：

```
────────────────────────────────────────────────────────────────────────────
建議：使用 Git Worktree 進行並行開發
────────────────────────────────────────────────────────────────────────────

檢測到並行開發場景，建議使用 Git Worktree 隔離工作區：

【Worktree 優勢】
  ✓ 完全隔離的工作目錄 - 避免文件層級衝突
  ✓ 獨立的分支狀態 - 每個 worktree 可在不同分支
  ✓ 真正的並行開發 - 無需切換分支
  ✓ 快速整合測試 - worktree 完成後自動合併

【快速開始】
  1. git worktree add -b <feature-branch> ../<feature-name>
  2. cd ../<feature-name> && 進行開發...
  3. cd .. && git worktree remove <feature-name>

【自動管理】
  使用 /parallel-develop skill 自動管理 worktree
```

### Worktree 並行開發流程

```
主工作區（main/master）
  ├── worktree-1: feature/user-management
  ├── worktree-2: feature/payment-integration
  ├── worktree-3: feature/notification-service
  └── worktree-4: feature/analytics-dashboard

優勢：
  ✓ 所有 worktree 同時開發，無切換延遲
  ✓ 每個 worktree 獨立的 git 狀態和依賴
  ✓ 完成後簡單 merge 即可集成
  ✓ 支持自動化測試和 CI/CD
```

### Worktree 最佳實踐

#### 命名規範
```bash
# 良好做法
git worktree add -b feature/user-auth ../worktree-user-auth
git worktree add -b bugfix/payment-issue ../worktree-payment-fix

# 避免
git worktree add -b temp ../tmp  # 名稱不清楚
```

#### 生命週期管理
```bash
# 1. 建立 worktree
git worktree add -b feature/xxx ../feature-xxx
cd ../feature-xxx

# 2. 開發、測試、提交
# ... 進行並行開發 ...
git add . && git commit -m "feat: xxx"

# 3. 返回主工作區並清理
cd ..
git worktree remove feature-xxx
git branch -D feature/xxx  # 如果需要刪除分支
```

#### 與 /parallel-develop 集成
```bash
# 自動建立和管理 worktree
/parallel-develop 並行開發 user-mgmt、order-mgmt、profile-mgmt

# AI 會：
# 1. 分析依賴並生成執行計劃
# 2. 為每個模組自動建立 worktree
# 3. 並行執行開發任務
# 4. 完成後自動合併並清理 worktree
```

### 注意事項

1. **磁盤空間**：每個 worktree 會複製 git metadata，但共享對象庫
2. **性能**：Worktree 比分支切換更輕量，適合長時間並行開發
3. **主工作區保護**：建議主工作區保持乾淨，所有開發在 worktree 中
4. **合併策略**：Worktree 合併前務必進行充分測試

## 自動觸發關鍵字

當主會話偵測到以下關鍵字時會自動使用此 Skill：
- **並行**、**同時開發**、**多模組**
- **平行開發**、**並發開發**
- **一起開發**、**batch development**

## Coordinator 特性

- **模型**: Haiku（規則型決策，極快且省成本）
- **規劃速度**: ~1-3 秒
- **成本**: 極低
- **職責**: 只規劃，不執行（執行由主會話完成）

## 輸出格式

Parallel Coordinator 會返回結構化的執行計劃（YAML）：

```yaml
parallel_development_plan:
  scope: "開發範圍描述"
  strategy: "策略名稱（full_parallel/sequential_layers/shared_components_first/time_sliced）"

  phases:
    - phase: 1
      name: "階段名稱"
      parallel: true/false
      components: [...]

  estimates:
    total_time: "時間估算"
    risk_level: "風險等級"
    modules_count: 數量

  recommendations:
    - "建議 1"
    - "建議 2"
```

## 並行開發策略

Parallel Coordinator 會根據情況選擇最佳策略：

| 策略 | 適用場景 | 特點 |
|------|---------|------|
| **full_parallel** | 無依賴、無衝突 | 所有模組同時開發，最快 |
| **sequential_layers** | 有依賴、無衝突 | 按依賴層級順序並行 |
| **shared_components_first** | 有共用組件 | 先建立共用，再並行開發 |
| **time_sliced** | 有文件衝突 | 時間分片，避免衝突 |

## 與其他 Agents 配合

```
parallel-coordinator (規劃)
  ↓
主會話執行計劃
  ├─ Phase 1: code-generator (建立共用組件)
  ├─ Phase 2: module-developer (並行開發模組) × 3
  └─ Phase 3: test-runner (集成測試)
```

## 不適用場景

以下任務不應該使用此 Skill：

| 任務類型 | 使用 Skill |
|---------|-----------|
| 單一模組開發 | `/code-editor` |
| 代碼審查 | `/review-code` |
| 測試撰寫 | `/write-tests` |
| 架構設計 | `/architecture-planner` |
| 需求分析 | `/system-analyst` |

## 最佳實踐

1. **提供明確範圍**：「開發 user-mgmt、order-mgmt 模組」比「開發幾個模組」更好
2. **說明開發類型**：「API 端點」、「批次任務」、「微服務模組」
3. **提及已知依賴**：「order-mgmt 依賴 user-mgmt 的 Customer 實體」
4. **指出特殊需求**：「需要共用配置」、「避免文件衝突」
5. **考慮 Worktree**：對於需要長時間並行開發的任務，優先使用 worktree

## 常見問題

**Q: Parallel Coordinator 會執行開發嗎？**
A: 不會。它只負責「規劃」，生成執行計劃後由主會話執行。

**Q: 為何使用 Haiku 而非 Sonnet？**
A: 並行規劃是規則型決策（依賴分析、衝突檢測），不需要深度推理。Haiku 速度快 3 倍且成本低 80%。

**Q: 計劃準確嗎？**
A: Parallel Coordinator 基於規則和模式匹配，準確率 > 90%。如有疑問會提出建議供用戶確認。

**Q: 可以手動調整計劃嗎？**
A: 可以。收到計劃後，用戶可以要求主會話調整執行順序或策略。

**Q: Worktree 對性能有影響嗎？**
A: 不會。Worktree 與分支共享對象庫，占用磁盤空間少。性能反而更好（避免頻繁分支切換）。

**Q: 如何在 Worktree 中運行構建？**
A: 與普通工作區相同。Gradle/Maven 會自動檢測當前路徑並進行構建。

## 相關文檔

- [LL-002: 多模組重構經驗](.claude/memory-bank/project-context/lessons-learned.yaml) - 實戰經驗與最佳實踐

---

**版本**: 1.1
**最後更新**: 2026-02-01
**適用專案**: Project + 所有 Spring Boot 專案
