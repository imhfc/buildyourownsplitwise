# Agent Teams 場景模板

> 預定義的 Agent Teams 使用場景，可直接使用或作為參考

## 場景 1：跨服務 API 重構

**觸發條件**：需要同時修改多個微服務的 API

**Team 結構**：
```
建立 Agent Team 重構所有微服務的 {API_NAME} API。

Spawn 以下 Teammates：
1. Service-Owner-ModuleA：負責 ModuleA 服務的 API 修改
2. Service-Owner-ModuleD：負責 ModuleB 服務的 API 修改
3. Service-Owner-ModuleC：負責 PM 服務的 API 修改

每個 Teammate 使用 Atomic Agents 進行代碼修改：
- api-designer 設計新 API
- code-editor 修改實作
- test-writer 更新測試

完成後，Lead 整合所有變更並驗證 API 一致性。
```

**注意事項**：
- 確保 API 規格在開始前已統一
- 每個 Teammate 只修改自己負責的服務
- Lead 負責跨服務的整合測試

---

## 場景 2：並行代碼審查

**觸發條件**：需要多維度審查 PR 或代碼變更

**Team 結構**：
```
建立 Agent Team 審查 PR #{PR_NUMBER}。

Spawn 三個 Reviewers：
1. Security-Auditor：安全審查
   - 使用 security-scanner 掃描漏洞
   - 重點：OWASP Top 10、認證授權、敏感資料

2. Quality-Guard：品質審查
   - 使用 code-reviewer 和 pattern-checker
   - 重點：命名規範、設計模式、複雜度

3. Test-Specialist：測試審查
   - 使用 coverage-analyzer 和 test-validator
   - 重點：測試覆蓋率、斷言品質、邊界情況

每個 Reviewer 獨立審查後，Lead 整合成統一報告。
```

**輸出格式**：
```markdown
# PR #{PR_NUMBER} 審查報告

## 安全審查
- [ ] 問題 1：...
- [ ] 問題 2：...

## 品質審查
- [ ] 問題 1：...
- [ ] 問題 2：...

## 測試審查
- [ ] 問題 1：...
- [ ] 問題 2：...

## 總結
嚴重問題：X 個
建議改進：Y 個
通過：是/否
```

---

## 場景 3：競爭假設除錯

**觸發條件**：難以定位的 Bug，需要多角度調查

**Team 結構**：
```
建立 Agent Team 調查 {BUG_DESCRIPTION}。

Spawn 以下 Investigators：
1. Researcher-A：假設是資料庫問題
   - 檢查 SQL 查詢、連線池、Transaction

2. Researcher-B：假設是快取問題
   - 檢查 Redis、本地快取、過期策略

3. Researcher-C：假設是並發問題
   - 檢查鎖、競態條件、執行緒安全

4. Devil-Advocate：挑戰所有假設
   - 找反例、邊界情況、遺漏的可能性

Teammates 互相討論和挑戰，直到收斂到真正的根因。
```

**關鍵機制**：
- 啟用 Teammate 間訊息傳遞
- Devil-Advocate 主動挑戰其他人的結論
- Lead 記錄辯論過程並決定最終結論

---

## 場景 4：全系統研究

**觸發條件**：需要理解大型系統的運作方式

**Team 結構**：
```
建立 Agent Team 研究 {SYSTEM_TOPIC}。

Spawn 以下 Researchers：
1. Researcher-Architecture：研究系統架構
   - 使用 dependency-tracer 分析模組關係
   - 繪製架構圖

2. Researcher-DataFlow：研究資料流
   - 追蹤資料從輸入到輸出的路徑
   - 識別關鍵轉換點

3. Researcher-Integration：研究外部整合
   - 檢查 API 呼叫、訊息佇列、資料庫連線
   - 列出所有外部依賴

Lead 整合三個研究報告成完整的系統文檔。
```

---

## 場景 5：批次開發（Project 專用）

**觸發條件**：需要同時開發多個 Reconcile 批次

**Team 結構**：
```
建立 Agent Team 開發 v1.0 Reconcile 批次。

Spawn 以下 Developers：
1. Batch-Dev-T1：負責 T1 類型批次（來源比對）
   - 使用 compliance-auditor 驗證

2. Batch-Dev-T2：負責 T2 類型批次（目的比對）
   - 使用 compliance-auditor 驗證

3. Batch-Dev-T3：負責 T3 類型批次（雙向比對）
   - 使用 compliance-auditor 驗證

每個 Developer 遵循 ADR-006 批次框架標準。
完成後，Lead 執行整合測試驗證所有批次。
```

---

## 快速啟動命令

### 使用 /agent-team Skill

```bash
# 跨服務重構
/agent-team create cross-service-refactor --services ModuleA,ModuleB,ModuleC

# 並行審查
/agent-team create parallel-review --pr 142

# 競爭假設除錯
/agent-team create competing-hypothesis --bug "連線超時問題"

# 全系統研究
/agent-team create full-system-research --topic "認證系統"
```

### 直接自然語言

```
建立 Agent Team 進行跨服務 API 重構，
修改 ModuleA、ModuleB、ModuleC 三個服務的 Customer API。
```

---

## Token 使用估算

| 場景 | Teammates | 預估 Token 消耗 |
|------|-----------|----------------|
| 跨服務重構 | 3-6 | 高 |
| 並行審查 | 3 | 中 |
| 競爭假設 | 3-5 | 中-高 |
| 全系統研究 | 3 | 中 |

**建議**：對於簡單任務，使用單一會話 + Atomic Agents 更經濟。

---

## 版本

v1.0.0 (2026-02-07)
