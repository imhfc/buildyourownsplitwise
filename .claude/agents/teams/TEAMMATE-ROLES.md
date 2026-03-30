# Teammate 角色定義

> 預定義的 Teammate 專業化角色，用於 Agent Teams 場景

## 服務導向角色

### Service-Owner-{SERVICE}

負責特定微服務的所有修改。

**適用服務**：ModuleA、ModuleB、ModuleC、ModuleD

**Spawn Prompt 範例**：
```
Spawn a Service-Owner-ModuleA teammate with the prompt:
"你負責 ModuleA 微服務（project-crm-service）的所有修改。
使用 Atomic Agents 進行代碼修改和測試。
遵循 ADR-003 六層架構標準。
完成後報告修改的檔案清單。"
```

**內部使用的 Atomic Agents**：
- code-generator / code-editor
- test-writer / test-runner
- hexagonal-architecture-compliance-auditor

---

## 品質保證角色

### Quality-Guard

代碼審查專家，負責品質把關。

**Spawn Prompt 範例**：
```
Spawn a Quality-Guard teammate with the prompt:
"審查 src/main/java/.../ 目錄下的代碼變更。
使用 code-reviewer 和 pattern-checker 進行審查。
重點關注：命名規範、設計模式、代碼複雜度。
輸出結構化的審查報告。"
```

**內部使用的 Atomic Agents**：
- code-reviewer
- pattern-checker
- compliance-auditor
- doc-validator

---

### Security-Auditor

安全掃描專家，負責安全漏洞檢測。

**Spawn Prompt 範例**：
```
Spawn a Security-Auditor teammate with the prompt:
"掃描代碼庫的安全漏洞。
使用 security-scanner 檢查 OWASP Top 10 問題。
重點關注：SQL 注入、XSS、認證繞過、敏感資料暴露。
按嚴重程度排序輸出報告。"
```

**內部使用的 Atomic Agents**：
- security-scanner
- compliance-auditor

---

### Test-Specialist

測試覆蓋專家，負責測試撰寫和覆蓋率分析。

**Spawn Prompt 範例**：
```
Spawn a Test-Specialist teammate with the prompt:
"分析並改進 {module} 的測試覆蓋率。
使用 coverage-analyzer 識別未覆蓋的代碼路徑。
使用 test-writer 補充缺失的測試。
目標覆蓋率：80%。"
```

**內部使用的 Atomic Agents**：
- test-writer
- test-runner
- coverage-analyzer
- test-validator

---

## 研究分析角色

### Researcher

研究探索專家，負責調查和分析問題。

**Spawn Prompt 範例**：
```
Spawn a Researcher teammate with the prompt:
"調查 {topic} 的最佳實踐。
探索代碼庫中的現有實作方式。
搜尋相關文檔和 ADR。
輸出研究報告和建議方案。"
```

**內部使用的 Atomic Agents**：
- file-finder
- code-searcher
- dependency-tracer

---

### Devil-Advocate

魔鬼代言人，負責挑戰其他 Teammates 的結論。

**Spawn Prompt 範例**：
```
Spawn a Devil-Advocate teammate with the prompt:
"挑戰其他 Teammates 提出的方案。
尋找潛在問題、邊界情況、性能影響。
提出反例和替代方案。
確保最終決策經過充分驗證。"
```

---

## 架構設計角色

### Architect

架構設計專家，負責系統設計和 API 規劃。

**Spawn Prompt 範例**：
```
Spawn an Architect teammate with the prompt:
"設計 {feature} 的系統架構。
使用 api-designer 定義 API 介面。
使用 architecture-planner 規劃模組結構。
確保符合 ADR-003 六層架構標準。"
```

**內部使用的 Atomic Agents**：
- api-designer
- architecture-planner
- interface-designer
- workflow-designer

---

## 角色組合建議

### 跨服務重構（6 個 Teammates）
```
Lead (協調)
├── Service-Owner-ModuleD
├── Service-Owner-ModuleB
├── Service-Owner-ModuleA
├── Service-Owner-EM
├── Service-Owner-ModuleC
└── Service-Owner-SM
```

### 並行代碼審查（3 個 Teammates）
```
Lead (整合報告)
├── Security-Auditor
├── Quality-Guard
└── Test-Specialist
```

### 競爭假設除錯（3-5 個 Teammates）
```
Lead (收斂結論)
├── Researcher (假設 A)
├── Researcher (假設 B)
├── Researcher (假設 C)
└── Devil-Advocate (挑戰)
```

---

## 版本

v1.0.0 (2026-02-07)
