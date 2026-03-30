# Agents 架構

> Atomic Agents + Skills 組合

---

## 高層 Agents

| Agent | 模型 | 用途 |
|-------|------|------|
| [system-analyst](./system-analyst.md) | opus | 需求分析 |
| [general-assistant](./general-assistant.md) | sonnet | 通用助手 |

## 協調者（Coordinators）

| Coordinator | 模型 | Skill |
|------------|------|-------|
| [review-coordinator](./atomic/coordinator/review-coordinator.md) | haiku | /review-code |
| [parallel-coordinator](./atomic/coordinator/parallel-coordinator.md) | haiku | /parallel-develop |
| [plan-reviewer](./atomic/coordinator/plan-reviewer.md) | haiku | - |

## Atomic Agents

45 個 haiku 模型 agents，按職責分類：

| 類別 | Agents |
|------|--------|
| COORDINATOR | task-router, parallel-coordinator, review-coordinator, plan-reviewer |
| SEARCH | file-finder, code-searcher, symbol-locator, dependency-tracer |
| CODE | code-generator, code-editor, code-deleter, code-formatter |
| REFACTOR | code-simplifier, duplicate-remover, performance-tuner, naming-improver |
| DATA | schema-designer, query-writer, migration-generator, data-validator |
| TEST | test-writer, test-runner, coverage-analyzer, test-fixer |
| REVIEW | code-reviewer, security-scanner, pattern-checker, compliance-auditor, doc-validator, test-validator, spec-validator, hexagonal-architecture-compliance-auditor |
| DESIGN | api-designer, architecture-planner, interface-designer, workflow-designer |
| CONFIG | env-manager, property-editor, docker-configurator, ci-configurator |
| LOG-ANALYSIS | log-analysis-coordinator, error-pattern-analyzer, exception-tracer, markdown-report-generator, report-consolidator |

**詳細說明**：[Atomic Agents](./atomic/README.md) | [Agent Teams](./teams/README.md)
