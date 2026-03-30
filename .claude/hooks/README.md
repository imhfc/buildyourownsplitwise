# Claude Code Hooks

> 精簡後的 Hook 配置（7 個）

---

## 目錄結構

```
.claude/hooks/
├── completion/
│   └── verify-completion.sh      # Stop: 三級完成度檢查
├── session/
│   ├── load-memory.sh            # SessionStart: 載入記憶庫
│   └── save-session.sh           # SessionEnd: 檢查未完成任務
├── subagent/
│   └── verify-subagent.sh        # SubagentStop: 驗證測試結果
├── tool/
│   ├── analyze-tool-failure.sh   # PostToolUseFailure: Gradle 失敗分析
│   └── auto-approve-permission.sh # PermissionRequest: 自動批准安全命令
├── validation/
│   └── validate-bash.sh          # PreToolUse(Bash): 阻擋危險命令
├── logs/
└── README.md
```

---

## Hook 配置總覽

| 事件 | 腳本 | 用途 |
|------|------|------|
| SessionStart | `session/load-memory.sh` | 載入專案記憶庫（偏好、進度、經驗教訓） |
| PreToolUse(Bash) | `validation/validate-bash.sh` | 阻擋危險命令（`rm -rf /`）、警告風險命令、建議專用工具 |
| PermissionRequest(Bash) | `tool/auto-approve-permission.sh` | 自動批准安全命令（git 只讀、ls、gradlew test）、拒絕 `--no-verify` |
| PostToolUseFailure(Bash) | `tool/analyze-tool-failure.sh` | 分析 Gradle 測試失敗（編譯錯誤、斷言失敗、NPE） |
| Stop | `completion/verify-completion.sh` | 三級完成度檢查（Git 未提交、TODO 殘留、規格合規） |
| SubagentStop | `subagent/verify-subagent.sh` | 驗證 test-writer/test-runner 測試是否通過 |
| SessionEnd | `session/save-session.sh` | 檢查未完成任務、提示下次會話建議 |

---

## 各 Hook 說明

### 1. load-memory.sh (SessionStart)

載入 `.claude/memory-bank/project-context/` 中的偏好、進度、經驗教訓，在會話開始時提供上下文。

### 2. validate-bash.sh (PreToolUse)

三層防護：
- **阻止**：`rm -rf /`、fork 炸彈、`mkfs`、`dd if=/dev/zero`
- **警告**：`rm -rf`、`git push --force`、`git reset --hard`、`sudo`
- **建議**：偵測到 `find`/`grep`/`cat` 時建議使用專用工具

### 3. auto-approve-permission.sh (PermissionRequest)

自動批准：
- Git 只讀：`git status/diff/log/show/branch/remote/fetch`
- 系統只讀：`ls/pwd/which/whoami/date/hostname`
- Gradle：`./gradlew test/build/clean`
- 搜尋：`grep/find/rg/ag`

自動拒絕：
- `--no-verify` 繞過 Git Hooks

注意：極度危險命令已由 PreToolUse (`validate-bash.sh`) 攔截，此處不重複檢查。

### 4. analyze-tool-failure.sh (PostToolUseFailure)

僅分析 `./gradlew test` 的 BUILD FAILED：
- 編譯錯誤（cannot find symbol）
- 斷言失敗（AssertionError）
- 空指針（NullPointerException）
- 方法/類別找不到（NoSuchMethodError）

### 5. verify-subagent.sh (SubagentStop)

驗證 `test-writer`、`test-runner`、`module-developer` 的 transcript：
- `BUILD SUCCESSFUL` → 通過
- `BUILD FAILED` → 阻止並提示修正
- 無測試結果 → 阻止並提示執行測試

### 6. verify-completion.sh (Stop)

三級檢查：
- **Level 1（快速）**：Git 未提交變更
- **Level 2（品質）**：Java 檔案 TODO/FIXME 殘留、測試同步
- **Level 3（合規）**：規格驗證報告 FAIL、審查報告 Critical

### 7. save-session.sh (SessionEnd)

檢查 transcript 中是否有未完成的 pending/in_progress 任務，提示下次會話繼續。

---

## 共用工具

### lib/logging.sh（已移除）

原提供統一日誌功能，已在 v6.0.0 清理中移除。各 hook 腳本中仍有條件引用（`|| true` 保護），不會影響執行。

---

## 版本歷史

- v7.0.0（2026-03-27）：新增 Stop hook、移除 emoji、Hook 安全檢查去重
- v6.0.0（2026-03-13）：精簡至 6 個 hook，刪除 14 個低價值/無效 hook
- v5.1.0（2026-02-01）：整合學習管理、規劃檢查（12+ 個）
- v5.0.0（2026-01-26）：目錄重組、簡化 4 個 hook（-60% 代碼量）
