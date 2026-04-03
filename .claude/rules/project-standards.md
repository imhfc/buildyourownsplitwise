# 專案架構規範

## Clean Architecture 分層

```
backend/app/
├── api/          # 展示層 — 路由，僅負責請求/回應
├── schemas/      # Pydantic 驗證 — DTO
├── services/     # 業務邏輯 — 核心領域
├── models/       # SQLAlchemy ORM — 資料層
└── core/         # 基礎設施 — 設定、DB、安全、DI
```

**分層規則**：
- API 層禁止包含業務邏輯，必須委派給 services
- Services 禁止從 api/ 匯入
- Models 禁止從 services/ 或 api/ 匯入
- 每一層只能依賴其下方的層

## 命名慣例

| 項目 | 慣例 | 範例 |
|------|------|------|
| Python 檔案/函式 | snake_case | `exchange_rate.py`, `calculate_balances()` |
| Python 類別 | PascalCase | `ExpenseSplit` |
| 常數 | UPPER_SNAKE_CASE | `MAX_GROUP_SIZE` |
| 資料表 | 複數 snake_case | `expenses`, `group_members` |
| API 端點 | 複數 kebab-case | `/api/v1/expenses` |
| React 元件 | PascalCase | `CurrencyPicker` |
| React 檔案 | kebab-case | `currency-picker.tsx` |

## 資料庫規則

- 金額使用 `Numeric(12, 2)` — 禁止浮點數
- 時間戳記一律 UTC，使用 `server_default=func.now()`
- 所有操作使用 async/await + asyncpg
- Schema 變更建立新 Alembic revision，禁止修改已存在的 migration
- Service 層禁止在請求路徑中同步呼叫外部 API，外部資料（匯率等）必須透過背景排程預取存入 DB
- 軟刪除過濾：任何涉及 `group_members` 或 `activity_logs` 的查詢，必須 join `groups` 並加 `Group.deleted_at.is_(None)`，避免回傳已刪除群組的資料（2026-04-02 回顧）
- 有方向性的關係（settlement, transfer）建立時，service 層必須驗證兩端不是同一人（`from != to`），防止前端 bug 產生自我操作的垃圾資料（2026-04-03 回顧）
- 代表「完成」語意的布林旗標（如 `is_settled`），必須同時檢查「曾經有過活動」（如 `expense_count > 0`），零狀態實體不等於已完成（2026-04-03 回顧）
- `log_activity(action=...)` 的 action 值必須同步存在於 `ActivityType` Literal（後端 schema）+ 前端 ActivityType union + i18n + UI switch，缺任一處 = 活動列表整頁 500（2026-04-03 回顧）

## Docker / 部署規則

- `docker-compose.yml` 中除 Caddy(80/443) 外，所有 `ports` 必須綁定 `127.0.0.1:`，禁止對外開放內部服務（2026-04-02 回顧）
- VM 上有 UFW 防火牆時，Docker port mapping 可能與 iptables 衝突，優先使用 `--network host` + 自訂 `PGPORT`（2026-04-02 回顧）
- 本機連 VM 內部服務一律透過 SSH tunnel（autossh + launchd），禁止對外開放 port（2026-04-02 回顧）

## Mobile 規範

- 所有使用者可見文字必須透過 i18n 的 `t()` 函式
- 按鈕使用 `<Button>` 的 variant，跟隨 bg-primary 色系
- 數字輸入必須搭配 onChangeText 正規表達式過濾
- 所有 API 呼叫需 try/catch 並顯示錯誤訊息
- Modal 表單的 API 錯誤必須用 inline error state 顯示，禁止用 Alert.alert（Expo Web 上行為不穩定）

## Dark Mode 設計規則（2026-04-03 回顧）

參照 Material Design 3 / Apple HIG best practice：

- 背景帶品牌色相染色（saturation 8-12%），禁止共用中性黑底 `0 0% X%`
- Lightness 階梯：bg 5% → card 10% → secondary 13% → accent 15% → border 16%
- Primary 色：飽和度降 20-30%（保留 50-65%），亮度升 5-10%（55-65%）
- Foreground 亮度：86%
- Preview hex 必須與實際 primary 一致
- 任意兩個 scheme 色相差距 >= 30 度
- 設計配色前先搜尋業界 best practice，禁止憑直覺
