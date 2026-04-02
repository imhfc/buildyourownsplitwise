# 開發工作流程

## 必遵守流程

1. **先讀再寫** — 修改檔案前必先讀取當前內容
2. **生成文件前先搜尋** — 任何「生成/撰寫文件」請求，先 Glob 搜尋 `docs/**/*` 確認是否已有同類檔案，避免重複生成
3. **開發完必審查** — 功能開發完成後，必須觸發 `/review-code` 進行代碼審查，確認無安全漏洞、架構違規、效能問題
4. **新功能必寫新測試** — 新端點或功能必須觸發 `/write-tests` 撰寫對應測試案例並執行，未附測試的功能不算完成
5. **既有功能必跑回歸測試** — 任何改動（含 bug 修復、重構）完成後，必須執行完整測試套件確認既有功能未被破壞（後端：`pytest tests/`，前端：`bash mobile/scripts/quality-gate.sh`）
6. **Bug 修復後更新文件** — 更新 QUALITY_SLA.md 和 quality-gate.sh
7. **新功能完成後更新 README** — 同步更新 `README.md` 功能列表 + `docs/CHANGELOG.md`（2026-04-02 回顧）

## 後端驗證閘門

| 層級 | 指令 | 適用情境 |
|------|------|---------|
| Quick | `cd backend && .venv/bin/python -m py_compile app/main.py` | 小幅修改 |
| Standard | `cd backend && .venv/bin/python -m pytest tests/` | Bug 修復 |
| Full | `cd backend && .venv/bin/python -m pytest tests/ -v` | 功能開發 |

測試 DB 使用 Neon serverless（`TEST_DATABASE_URL` 定義在 `backend/.env`），不需要本機 Docker。
完整測試規範參見 `.claude/rules/testing-standards.md`。

## 前端驗證閘門

| 層級 | 指令 | 適用情境 |
|------|------|---------|
| Quick | `cd mobile && npx tsc --noEmit` | TypeScript 類型檢查 |
| Standard | `bash mobile/scripts/quality-gate.sh` | 所有 mobile 改動 |
| Full | Standard + `npx expo-doctor` | 套件異動後 |

## Skill 觸發規則

| 使用者關鍵字 | 必須觸發的 Skill | 禁止行為 |
|-------------|-----------------|---------|
| commit / 提交 / push / 推送 / branch / merge / conflict / git status | `/git-ops` | 禁止直接用 Bash 執行 git 指令 |
| 審查 / review / 檢查 / 掃描 | `/review-code` | — |
| 寫測試 / 測試 / 覆蓋率 | `/write-tests` | — |
| 回顧 / retro / 沉澱 | `/retro` | — |

**注意**：
- 對話開始時的 git status snapshot 可能已過時，commit 前必須重新執行 `git status` 確認當前狀態
- Skill 已內建標準化檢查流程，手動執行等於繞過保護

## 狀態工作流完整性規則（2026-04-02 回顧）

- 任何涉及 status 欄位（狀態機）的功能，**必須在設計階段列出所有狀態轉換**，並確認每個轉換都有對應的前端 UI 觸發點
- `api.ts` 中定義的 API 方法必須有至少一處前端呼叫，否則代表功能未完成
- 建立帶有 pending 狀態的資料時，前端必須明確告知使用者「等待確認」，不能讓使用者誤以為已生效
- 有方向性的操作（A->B 結清/轉帳），UI 按鈕只能顯示給發起方，對方只能回應（確認/拒絕/提醒），禁止用 OR 條件讓雙方都能發起同一個 action（2026-04-03 回顧）
- 需要使用者回應的 pending 項目，必須有 tab badge 或首頁 banner 等被動通知機制，不能只在特定深層頁面顯示（2026-04-03 回顧）

## 技術棧

- **後端**：FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic
- **前端**：React Native + Expo + NativeWind + Zustand + i18next
- **測試**：pytest + pytest-asyncio（後端）、Jest（前端）
- **部署**：Docker Compose + GCP VM + GitHub Actions CI/CD

## UI 設計規則（2026-04-03 回顧）

- 配色/排版/動畫等視覺設計，先搜尋 MD3 / Apple HIG best practice 取得具體數值，禁止憑直覺
- Dark mode 設計規則詳見 `project-standards.md`
