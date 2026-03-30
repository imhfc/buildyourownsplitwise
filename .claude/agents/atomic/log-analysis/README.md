# Log Analysis Atomic Agents

> LOG 分析框架 Atomic Agents 說明文檔

**版本**: 1.0.0
**最後更新**: 2026-01-29

---

## 概述

此目錄包含 LOG 分析框架的所有 Atomic Agents，這些 Agents 採用模組化設計，可單獨使用或組合使用。

## Agents 清單

### Coordinator

| Agent | 用途 | 模型 | 預估時間 |
|-------|------|------|---------|
| [log-analysis-coordinator](./log-analysis-coordinator.md) | 規劃執行策略並協調 Agents | Haiku | 10-20 秒 |

### 分析 Agents

| Agent | 用途 | 模型 | 預估時間 |
|-------|------|------|---------|
| [error-pattern-analyzer](./error-pattern-analyzer.md) | 錯誤模式分析和統計 | Haiku | 5-15 秒 |
| [exception-tracer](./exception-tracer.md) | 異常堆疊追蹤和根本原因分析 | Haiku | 10-20 秒 |
| performance-analyzer | 性能指標分析（待實作） | Haiku | 10-15 秒 |
| workflow-tracer | 業務流程追蹤（待實作） | Haiku | 10-15 秒 |

### 報告 Agents

| Agent | 用途 | 模型 | 預估時間 |
|-------|------|------|---------|
| [report-consolidator](./report-consolidator.md) | 整合多維度分析結果 | Haiku | 20-30 秒 |
| [markdown-report-generator](./markdown-report-generator.md) | 生成 Markdown 報告 | Haiku | 15-20 秒 |

## 執行流程

```
log-analysis-coordinator (規劃)
  ↓
並行執行:
  ├─ error-pattern-analyzer (錯誤分析)
  └─ exception-tracer (異常追蹤)
  ↓
report-consolidator (整合)
  ↓
markdown-report-generator (報告)
```

## 工具使用矩陣

| Agent | Glob | Grep | Read | Write | Bash | Task | Edit |
|-------|------|------|------|-------|------|------|------|
| log-analysis-coordinator | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| error-pattern-analyzer | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| exception-tracer | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| report-consolidator | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| markdown-report-generator | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |

**說明**:
- ✅ 允許使用
- ❌ 禁止使用

## 數據流

### 輸入

```
用戶輸入:
  - log_dir: LOG 目錄路徑
  - analysis_types: 分析類型列表
  - parallel_mode: 並行處理開關
```

### 中間產物

```
/tmp/log-analysis-{timestamp}/
  ├── error-pattern-{file_hash}.json
  ├── exception-trace-{file_hash}.json
  ├── performance-{file_hash}.json (可選)
  ├── workflow-{file_hash}.json (可選)
  └── consolidated-report.json
```

### 最終輸出

```
{output_path}/log-analysis-report.md
```

## 使用示例

### 單獨使用 Agent

```bash
# 只分析錯誤模式
Task(error-pattern-analyzer, "分析 /path/to/file.log 的錯誤模式")

# 只追蹤異常
Task(exception-tracer, "追蹤 /path/to/file.log 的異常堆疊")
```

### 組合使用

```bash
# 完整分析流程
1. Task(log-analysis-coordinator, "規劃 /path/to/logs 的分析策略")
2. Task(error-pattern-analyzer, "分析錯誤") x 並行
3. Task(exception-tracer, "追蹤異常") x 並行
4. Task(report-consolidator, "整合結果")
5. Task(markdown-report-generator, "生成報告")
```

### 使用 Skill（推薦）

```bash
/log-analysis --dir /path/to/logs
```

## 擴展指南

### 添加新的分析 Agent

1. 建立新的 Agent 定義文件：
```
.claude/agents/atomic/log-analysis/new-analyzer.md
```

2. 定義角色、工具限制、執行流程

3. 更新 Coordinator 以包含新 Agent：
```yaml
# log-analysis-coordinator.md
agents:
  - new-analyzer
```

4. 更新 Skill 文檔：
```yaml
# SKILL.md
支援的分析類型:
  - new_analysis: 新分析類型描述
```

### 添加新的報告格式

1. 建立新的報告生成 Agent：
```
.claude/agents/atomic/log-analysis/html-report-generator.md
```

2. 實作報告生成邏輯

3. 更新 Skill 參數：
```bash
--format html  # 支援新格式
```

## 性能優化建議

### Context 優化
- ✅ 所有 Agent 使用 Haiku 模型（極速且省成本）
- ✅ 中間結果存儲在文件而非傳遞 Context
- ✅ 主對話只接收最終報告路徑

### 並行優化
- ✅ 文件級並行：多個文件同時分析
- ✅ 維度級並行：同一文件多維度同時分析
- ✅ 批次處理：大量文件分批執行

### 速度優化
- ✅ 使用 Grep/Bash 管道避免多次掃描
- ✅ 限制分析深度（Top N）
- ✅ 大文件自動抽樣

## 測試

### 單元測試

每個 Agent 包含測試案例章節，測試方法：

```bash
# 手動測試
Task(error-pattern-analyzer, "測試案例 1: JSON 格式 LOG")

# 檢查輸出
Read: /tmp/log-analysis-*/error-pattern-*.json
```

### 整合測試

```bash
# 使用實際 LOG 目錄測試
/log-analysis --dir /path/to/test/logs

# 驗證報告內容
Read: ./log-analysis-report.md
```

## 故障排查

### 常見問題

**Q: Agent 執行超時**
A: 檢查 LOG 文件大小，大文件會自動抽樣

**Q: JSON 格式錯誤**
A: 檢查中間產物文件，確認格式正確

**Q: 報告生成失敗**
A: 檢查 consolidated-report.json 是否存在

### 調試模式

```bash
# 保留中間產物
export LOG_ANALYSIS_DEBUG=1

# 查看詳細日誌
ls -la /tmp/log-analysis-*/
cat /tmp/log-analysis-*/error-pattern-*.json
```

## 版本歷史

- **v1.0.0** (2026-01-29): 初始版本
  - 實作 5 個核心 Agents
  - 支援錯誤、異常分析
  - Markdown 報告生成

## 相關資源

- [Skill 文檔](.claude/skills/log-analysis/SKILL.md)
- [報告模板](.claude/skills/log-analysis/templates/)
- [Atomic Agents 架構](.claude/agents/atomic/README.md)

---

**維護者**: Claude Code Team
**聯繫**: 參考 CLAUDE.md
