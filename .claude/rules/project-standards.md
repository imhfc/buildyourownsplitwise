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

## Mobile 規範

- 所有使用者可見文字必須透過 i18n 的 `t()` 函式
- 按鈕使用 `<Button>` 的 variant，跟隨 bg-primary 色系
- 數字輸入必須搭配 onChangeText 正規表達式過濾
- 所有 API 呼叫需 try/catch 並顯示錯誤訊息
- Modal 表單的 API 錯誤必須用 inline error state 顯示，禁止用 Alert.alert（Expo Web 上行為不穩定）
