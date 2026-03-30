# Atomic Agents 快速入門

> 5 分鐘上手 Atomic Agents

---

## 核心概念

**單一職責 + Haiku 模型 + 組合模式 = 高效開發**

- 49 個 Atomic Agents，每個只做一件事
- 全部使用 **haiku 模型**（快速 + 經濟）
- 透過組合完成複雜任務

---

## 立即開始

### 場景 1：修改單個文件

```bash
# 1. 找到文件
使用 file-finder 找出 UserService.java

# 2. 修改代碼
使用 code-editor 修改 UserService 的登入邏輯

# 3. 驗證修改
使用 test-runner 執行單元測試
```

**時間**：~20 秒（使用 haiku）
**成本**：極低

---

### 場景 2：開發新功能

```bash
# Phase 1: 設計
1. 使用 api-designer 設計 REST API
2. 使用 schema-designer 設計資料庫表

# Phase 2: 實作
3. 使用 code-generator 生成 Entity, Repository, Service
4. 使用 code-editor 實作業務邏輯
5. 使用 code-formatter 格式化代碼

# Phase 3: 測試
6. 使用 test-writer 生成單元測試
7. 使用 test-runner 執行測試
8. 使用 coverage-analyzer 檢查覆蓋率

# Phase 4: 審查
9. 使用 code-reviewer 審查代碼
10. 使用 security-scanner 掃描安全問題
```

**時間**：~2 分鐘（使用 haiku 組合）
**成本**：比單一 Sonnet 節省 80%

---

### 場景 3：批量重構

```bash
# 1. 搜索目標
使用 code-searcher 找出所有使用舊 API 的地方

# 2. 並行修改（10 個文件）
並行啟動 10 個 code-editor agents，同時修改

# 3. 驗證
使用 test-runner 執行所有相關測試

# 4. 清理
使用 code-formatter 統一格式
```

**時間**：~30 秒（並行執行）
**成本**：極低

---

## 可用的 Agents

### 搜索類 (SEARCH)

- **file-finder**: 根據條件查找文件
- **code-searcher**: 搜索代碼內容（使用 ast-grep）
- **symbol-locator**: 定位類、函數
- **dependency-tracer**: 追蹤依賴關係

### 代碼類 (CODE)

- **code-generator**: 生成新代碼
- **code-editor**: 編輯現有代碼
- **code-deleter**: 刪除代碼
- **code-formatter**: 格式化代碼

### 重構類 (REFACTOR)

- **code-simplifier**: 簡化複雜邏輯
- **duplicate-remover**: 移除重複代碼
- **naming-improver**: 改善命名
- **performance-tuner**: 優化性能

### 數據類 (DATA)

- **schema-designer**: 設計資料庫 schema
- **query-writer**: 撰寫 SQL 查詢
- **migration-generator**: 生成遷移腳本
- **data-validator**: 驗證數據正確性

### 測試類 (TEST)

- **test-writer**: 撰寫測試代碼
- **test-runner**: 執行測試
- **test-fixer**: 修復失敗測試
- **coverage-analyzer**: 分析覆蓋率

### 審查類 (REVIEW)

- **code-reviewer**: 審查代碼品質
- **security-scanner**: 掃描安全問題
- **pattern-checker**: 檢查設計模式
- **compliance-auditor**: 審計合規性

### 設計類 (DESIGN)

- **api-designer**: 設計 API
- **architecture-planner**: 規劃架構
- **interface-designer**: 設計介面
- **workflow-designer**: 設計業務流程

### 配置類 (CONFIG)

- **env-manager**: 管理環境變數
- **property-editor**: 編輯配置文件
- **docker-configurator**: 配置 Docker
- **ci-configurator**: 配置 CI/CD

---

## 常用組合模板

### 模板 1：快速修改

```
file-finder → code-editor → test-runner
```

**用途**：修改單個或少量文件
**時間**：~20 秒

---

### 模板 2：完整開發

```
api-designer → schema-designer →
code-generator → code-editor →
test-writer → test-runner →
code-reviewer
```

**用途**：開發新功能
**時間**：~2 分鐘

---

### 模板 3：品質保證

```
code-reviewer → security-scanner →
pattern-checker → compliance-auditor →
test-runner → coverage-analyzer
```

**用途**：上線前檢查
**時間**：~1 分鐘

---

### 模板 4：批量重構

```
file-finder →
duplicate-remover →
naming-improver →
code-simplifier →
code-formatter →
test-runner
```

**用途**：代碼優化
**時間**：~40 秒

---

## 效能對比

### 場景：修改 10 個 Controller 文件

| 方案 | 時間 | 成本 | 可並行 |
|------|------|------|--------|
| **單一 Sonnet Agent** | ~60 秒 | 高 |  |
| **Haiku Atomic Agents** | ~20 秒 | 極低 |  |
| **改善** | **3x 快** | **-80%** |  |

---

## 最佳實踐

###  推薦

1. **明確目標**：清楚知道要完成什麼
2. **拆分步驟**：將複雜任務拆分為單一職責
3. **選擇 Agent**：為每個步驟選擇最合適的 Agent
4. **及時驗證**：關鍵步驟後立即驗證
5. **並行執行**：獨立任務應並行處理

###  避免

1. **過度組合**：不要使用不必要的 Agents
2. **順序錯誤**：確保依賴順序正確
3. **缺乏驗證**：修改後必須測試
4. **串行執行**：不要串行處理可並行的任務

---

## 下一步

1. **閱讀完整文檔**：
   - [README](./README.md) - 完整的 Agents 列表

2. **使用 Skills**：
   - `/review-code` - 代碼審查（自動規劃）
   - `/write-tests` - 撰寫測試 + 執行 + 覆蓋率
   - `/parallel-develop` - 並行開發規劃

3. **實際使用**：
   - 從簡單場景開始（模板 1）
   - 使用 Skills 自動組合（推薦）
   - 根據需求自定義組合

4. **監控優化**：
   - 追蹤執行時間
   - 記錄常用組合
   - 持續改進流程

---

## 快速參考

### 我想...

- **找文件** → file-finder
- **搜代碼** → code-searcher
- **改代碼** → code-editor
- **生成代碼** → code-generator
- **寫測試** → test-writer
- **跑測試** → test-runner
- **審查代碼** → code-reviewer
- **掃安全** → security-scanner
- **設計 API** → api-designer
- **設計資料庫** → schema-designer

### 常見問題

**Q: 為什麼都用 Haiku？**
A: 單一職責不需要複雜推理，Haiku 快速且經濟

**Q: 何時用 Sonnet？**
A: 複雜架構設計、多步驟規劃、高層決策

**Q: 如何並行執行？**
A: 在單一消息中同時啟動多個獨立的 Agents

**Q: 如何選擇 Agent？**
A: 根據單一職責原則，選擇最匹配任務的 Agent

---

**版本**：1.0
**最後更新**：2026-01-25
