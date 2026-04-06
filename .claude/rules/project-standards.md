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
- async session 中禁止 `db.expire_all()`，改用 `db.expire(specific_obj)` 只 expire 需要重載的物件；expire 前必須先將後續需要的屬性存到區域變數，否則存取 expired 屬性觸發同步 lazy load → `MissingGreenlet`（2026-04-03 回顧）
- 已結清消費的修改必須用沖銷+重建模式（soft-delete 原始 + create new with `adjusted_from_id`），禁止 in-place update；已確認結算不動，差額自然進入當前未結清餘額。被已確認記錄引用的金融資料，一律用 append-only 模式修改（2026-04-05 回顧）

## Docker / 部署規則

- `docker-compose.yml` 中除 Caddy(80/443) 外，所有 `ports` 必須綁定 `127.0.0.1:`，禁止對外開放內部服務（2026-04-02 回顧）
- VM 上有 UFW 防火牆時，Docker port mapping 可能與 iptables 衝突，優先使用 `--network host` + 自訂 `PGPORT`（2026-04-02 回顧）
- 測試 DB 使用本機 PostgreSQL（`brew install postgresql@16`，port 5432），不需 SSH tunnel（2026-04-03 更新）

## Mobile 規範

- 所有使用者可見文字必須透過 i18n 的 `t()` 函式
- 按鈕使用 `<Button>` 的 variant，跟隨 bg-primary 色系
- 數字輸入必須搭配 onChangeText 正規表達式過濾
- 所有 API 呼叫需 try/catch 並顯示錯誤訊息
- Modal 表單的 API 錯誤必須用 inline error state 顯示，禁止用 Alert.alert（Expo Web 上行為不穩定）
- UI 元件尺寸/圓角/間距必須對齊 shadcn/ui 標準值（Button h-10、Input h-10、rounded-lg），禁止憑直覺自訂（2026-04-05 回顧）
- 頁面內 logo 使用 `logo-transparent.png`（透明底），禁止直接引用 `icon.png`（有白底）；dark mode 用 `tintColor` 染色（2026-04-05 回顧）
- `bg-primary` 上的圖示/spinner color 禁止 `white`/`#fff`，必須用 `hsl(var(--primary-foreground))`；dark mode primary 可能近白色（2026-04-05 回顧）
- Mobile web 必須動態注入 `viewport-fit=cover`（啟用 safe-area-inset）+ `100dvh` CSS（排除瀏覽器工具列），裝置差異尺寸禁止 hardcode 常數（2026-04-05 回顧）
- phosphor 圖標 weight 分級：tab bar 未選中/EmptyState 裝飾性用 `light`，tab bar 選中用 `fill`，頁面內互動用 `regular`；SegmentedTabs 使用底線指示器（`border-b border-primary`），禁止 pill 背景和 shadow（2026-04-06 回顧）
- EmptyState 圖標必須與對應 tab bar 圖標一致（好友=Users、群組=SquaresFour、活動=ClockCounterClockwise）；變更 tab bar icon 後必須全域搜尋同步（2026-04-06 回顧）

## UI Design Token（2026-04-06 回顧）

所有頁面（四個 tab + group detail + 所有 modal）必須使用以下統一 token，禁止各頁面自行定義不同值：

| 元素 | Token | 禁止 |
|------|-------|------|
| Card 間距 | `mb-2` | `mb-3` |
| Card 內距 | `p-3.5` | `p-4` |
| 主文字 | `text-sm font-medium text-foreground` | `text-base font-medium`、裸 `font-medium` |
| 次要文字 | `text-xs text-muted-foreground` | `<Muted>` 無 `text-xs`、裸 `<Muted>` |
| 金額 | `text-sm font-semibold tabular-nums` | `text-lg font-bold`、`text-base font-bold`、缺 `tabular-nums` |
| Section header | `text-xs font-medium text-muted-foreground uppercase tracking-wider` | `font-semibold` 無 size/uppercase |
| Icon circle | `h-9 w-9` + icon `size={18}` | `h-10 w-10` + `size={20}`（列表卡片中） |
| Bottom sheet | `rounded-t-xl border-t border-border`、`h-1 w-8 bg-muted-foreground/20`、title `text-base font-semibold`、X `size={20} hitSlop={8}`、`mb-5` | `rounded-t-2xl`、`h-1 w-10`、`<H3>`、`text-xl`、X `size={24}`、`mb-6` |
| Dialog | `rounded-xl border border-border p-6`、title `text-base font-semibold text-foreground`、body `text-sm text-muted-foreground` | 無 border、`<H3>`、body `text-base` |

- 任何 UI 變更必須跨所有 tab 頁面檢查一致性，不能只改觸發問題的那一個（2026-04-06 回顧）

## 推播通知規則（2026-04-05 回顧）

- 即時同步策略：推播通知 + REST re-fetch（Splitwise 模式），不使用 WebSocket
- Service 層每個寫入操作（CREATE/UPDATE/DELETE）必須呼叫 `push_service` 對應通知函式
- 通知對象：群組成員廣播用 `notify_group_members()`，特定對象用 `send_push()`
- 操作者自己不收推播（`exclude_user_id` 參數排除）
- 前端每個 tab 頁面必須同時有 `useFocusEffect`（進入時拉資料）+ `addNotificationReceivedCallback`（推播時刷新）

## 主題色系統（shadcn 兩層架構）（2026-04-06 回顧）

參照 shadcn/ui 官方色票，採用兩層系統：

### Base 層（所有主題共用）
- `global.css` `:root` / `.dark` 定義結構色（background/card/foreground/border/secondary/muted/accent/destructive）
- 基底為 shadcn Neutral（hue 0，純黑白灰，零飽和度）
- Light: background `0 0% 98%`（淡灰）、card `0 0% 100%`（純白）
- Dark: background `0 0% 3.9%`（近黑）、card `0 0% 7%`（微亮）

### Color 層（反轉設計：底色染色、卡片留白）
- `--primary`、`--primary-foreground`、`--ring`：取自 shadcn 官方色票（Blue/Green/Violet/Orange/Rose）
- `--background`：底色染色，讓整體畫面帶主題色調
  - Light: 取主題 hue，saturation 35-40%，lightness 97%
  - Dark: 取主題 hue，saturation 12%，lightness 8%
- `--card`（+ `--popover`）：回歸 base 中性色（light 純白 `0 0% 100%`，dark `0 0% 7%`）
- 禁止在 scheme 中重新定義 foreground/border/secondary/muted 等其他結構色

### 硬寫 hex 色碼規則
- 品牌預設黑白灰，硬寫 hex 必須用 Tailwind **neutral** 色階（hue 0 純灰）
- 禁止用 **zinc** 色階（hue 240 帶藍紫調）：`#18181B` `#52525B` `#71717A` `#A1A1AA` `#0A0C0F`
- 正確對應：`#171717` `#525252` `#737373` `#A3A3A3` `#0A0A0A`

### 新增/修改色系的同步清單
- `global.css`：新增 `.scheme-xxx` + `.dark.scheme-xxx`（各 ~6 行）
- `theme.tsx`：`ColorScheme` 型別 + `COLOR_SCHEMES` 陣列（preview hex 與實際 primary 一致）
- `_layout.tsx`：`SCHEME_CLASS` 映射
- 三語 i18n（zh-TW/en/ja）：顯示名稱必須反映實際顏色
