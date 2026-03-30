# 開發工作流程

## 必遵守流程

1. **先讀再寫** — 修改檔案前必先讀取當前內容
2. **生成文件前先搜尋** — 任何「生成/撰寫文件」請求，先 Glob 搜尋 `docs/**/*` 確認是否已有同類檔案，避免重複生成
3. **開發完必測試** — 後端：`cd backend && pytest tests/`，前端：`bash mobile/scripts/quality-gate.sh`
4. **新功能 = 新測案** — 每個新端點或功能必須有對應測試
5. **Bug 修復後更新文件** — 更新 QUALITY_SLA.md 和 quality-gate.sh

## 後端驗證閘門

| 層級 | 指令 | 適用情境 |
|------|------|---------|
| Quick | `cd backend && python -m py_compile app/main.py` | 小幅修改 |
| Standard | `cd backend && pytest tests/` | Bug 修復 |
| Full | `cd backend && pytest tests/ -v` | 功能開發 |

前提：`docker compose -f docker-compose.test.yml up -d db-test`（測試 DB port 5433）

## 前端驗證閘門

| 層級 | 指令 | 適用情境 |
|------|------|---------|
| Quick | `cd mobile && npx tsc --noEmit` | TypeScript 類型檢查 |
| Standard | `bash mobile/scripts/quality-gate.sh` | 所有 mobile 改動 |
| Full | Standard + `npx expo-doctor` | 套件異動後 |

## 技術棧

- **後端**：FastAPI + SQLAlchemy (async) + PostgreSQL + Redis + Alembic
- **前端**：React Native + Expo + NativeWind + Zustand + i18next
- **測試**：pytest + pytest-asyncio（後端）、Jest（前端）
- **部署**：Docker Compose + GCP VM + GitHub Actions CI/CD
