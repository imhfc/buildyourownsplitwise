# Build Your Own Splitewise - 開發規範

## 必遵守工作流程（每次都要做）

1. **先讀再寫** — 修改任何檔案之前，務必先讀取該檔案的當前內容，禁止盲目覆蓋。
2. **開發完必審查** — 功能開發完成後，必須觸發 `/review-code` 進行代碼審查，確認無安全漏洞、架構違規、效能問題。
3. **新功能必寫新測試** — 新端點或功能必須觸發 `/write-tests` 撰寫對應測試案例並執行，未附測試的功能不算完成。
4. **既有功能必跑回歸測試** — 任何改動（含 bug 修復、重構）完成後，必須執行完整測試套件確認既有功能未被破壞：
   ```bash
   # 後端回歸測試（打本機 PostgreSQL，port 5432）
   cd backend && pytest tests/
   ```
   若需自訂 DB 位址：`TEST_DATABASE_URL=postgresql+asyncpg://... pytest tests/`
5. **每次對話都要讀這份文件** — 此 CLAUDE.md 是專案開發標準的唯一真相來源。
6. **Mobile 提交前必跑品質關卡** — 任何 mobile 相關改動提交前執行 `bash mobile/scripts/quality-gate.sh`，任一 FAIL 禁止提交。
7. **Mobile 套件異動後必跑安裝後關卡** — 任何 `npm install` 後執行 `npx expo-doctor` + `quality-gate.sh`。
8. **任何 bug 修復後，必須立即更新兩份文件，無例外** — 這是強制義務，不是選項。修 bug 但沒有更新文件 = 任務未完成。
   - `QUALITY_SLA.md` §4 新增組態不變式、§5 新增版本歷史（**事件歷史的唯一真相來源**）
   - `mobile/scripts/quality-gate.sh` 新增對應的自動檢查腳本
   - **目的：讓同樣的 bug 永遠不會發生第二次。** 每一個 bug 都是一條新的防線。跳過這步就是在讓未來的自己重踩同一個坑。
9. **新功能完成後必須更新 README.md** — 功能列表必須反映實際狀態。同步更新 `README.md`「主要功能」區塊 + `docs/CHANGELOG.md`。

---

## 專案概覽

類似 Splitwise 的分帳應用程式，採用 **Vibe Coding**（AI 輔助開發）方式建構。

### 技術棧

| 層級       | 技術                                |
| ---------- | ----------------------------------- |
| 後端       | FastAPI (Python 3.x)                |
| 資料庫     | PostgreSQL 16 + SQLAlchemy (async)  |
| 認證       | JWT (python-jose + passlib/bcrypt)  |
| 資料遷移   | Alembic                             |
| 測試       | pytest + pytest-asyncio             |
| 容器化     | Docker Compose                      |

---

## 1. 架構原則

### 1.1 分層架構（Clean Architecture）

```
app/
├── api/          # 展示層 — 路由處理，僅負責請求/回應
├── schemas/      # 資料傳輸物件 — Pydantic 模型，負責驗證
├── services/     # 業務邏輯層 — 核心領域邏輯
├── models/       # 資料層 — SQLAlchemy ORM 模型
└── core/         # 基礎設施 — 設定、資料庫、安全性、依賴注入
```

**規則：**
- API 層禁止包含業務邏輯，必須委派給 services
- Services 禁止從 `api/` 匯入
- Models 禁止從 `services/` 或 `api/` 匯入
- 每一層只能依賴其下方的層
- `get_db()` 依賴會在請求結束後自動 `commit()`，Services 層禁止手動呼叫 `db.commit()`（僅用 `db.flush()` 取得生成的 ID）

### 1.2 非同步優先

- 所有資料庫操作使用 `async/await` 搭配 `asyncpg`
- 所有 API 端點應使用 `async def`
- 外部 HTTP 請求使用 `httpx.AsyncClient`

### 1.3 外部資料預取模式

- Service 層禁止在 API 請求路徑中同步呼叫外部 API（匯率、第三方服務等）
- 外部資料必須透過背景排程定期寫入 DB，Service 層只從 DB 讀取
- 理由：外部 API 延遲不可控，同步呼叫會累積延遲導致前端 timeout

---

## 2. 程式碼規範

### 2.1 Python 風格

- 嚴格遵守 **PEP 8**
- 最大行寬：**120 字元**
- 所有函式簽名必須使用 **type hints**
- 變數/函式使用 `snake_case`，類別使用 `PascalCase`
- 匯入順序：標準庫 → 第三方套件 → 本地模組（使用 `isort`）

### 2.2 命名慣例

| 項目         | 慣例              | 範例                        |
| ------------ | ----------------- | --------------------------- |
| 檔案         | snake_case        | `exchange_rate.py`          |
| 類別         | PascalCase        | `ExpenseSplit`              |
| 函式         | snake_case        | `calculate_balances()`      |
| 常數         | UPPER_SNAKE_CASE  | `MAX_GROUP_SIZE`            |
| 資料表       | 複數 snake_case   | `expenses`, `group_members` |
| API 端點     | 複數 kebab-case   | `/api/v1/expenses`          |

### 2.3 檔案組織

- `models/` 中每個模型一個檔案
- `api/` 中每個資源一個路由檔案
- `schemas/` 中每個資源一個 schema 模組
- `services/` 中將相關的服務函式分組

---

## 3. API 設計

### 3.1 RESTful 慣例

- 正確使用 HTTP 方法：`GET`（讀取）、`POST`（建立）、`PUT`（完整更新）、`PATCH`（部分更新）、`DELETE`
- 所有端點加上版本前綴：`/api/v1/...`
- 回傳適當的狀態碼：`200`、`201`、`204`、`400`、`401`、`403`、`404`、`422`
- 錯誤回應使用一致的格式：

```json
{
  "detail": "錯誤描述"
}
```

### 3.2 分頁

- 列表端點必須支援分頁：`?skip=0&limit=20`
- 預設 limit：20，最大 limit：100

### 3.3 認證

- 除了 `/auth/register` 和 `/auth/login` 以外，所有端點都需要 JWT Bearer token
- Token 應設定合理的過期時間（例如：access token 30 分鐘，refresh token 7 天）

---

## 4. 資料庫與資料模型

### 4.1 核心實體

```
User → Group（多對多，透過 group_members）
Group → Expense（一對多）
Expense → ExpenseSplit（一對多，追蹤誰欠多少）
User → Settlement（付款人/收款人）
ExchangeRate（多幣別支援）
```

### 4.2 遷移規則

- 禁止修改已存在的 migration 檔案
- Schema 變更時建立新的 Alembic revision：`alembic revision --autogenerate -m "描述"`
- Migration 訊息應具描述性：`"add_currency_field_to_expenses"`
- 提交前必須測試 upgrade 和 downgrade 都能正常運作

### 4.3 資料完整性

- 使用資料庫層級的約束（NOT NULL、UNIQUE、FOREIGN KEY、CHECK）
- 金額使用 `Numeric(12, 2)` — 禁止使用浮點數
- 時間戳記一律存 UTC，使用 `server_default=func.now()`
- 適當場景使用軟刪除（加入 `deleted_at` 欄位）

---

## 5. 安全性

### 5.1 強制規範

- 禁止寫死密鑰 — 使用環境變數（`.env` 檔案，透過 `python-dotenv` 載入）
- `.env` 檔案必須加入 `.gitignore`
- 密碼使用 bcrypt 雜湊（透過 `passlib`）
- 所有使用者輸入必須透過 Pydantic schemas 驗證與清理
- 只使用參數化查詢（SQLAlchemy 已處理）

### 5.2 授權

- 每次寫入/刪除操作都要驗證資源擁有權
- 使用者只能檢視/修改所屬群組的費用
- 群組管理操作需要管理員角色檢查

---

## 6. 測試策略

### 6.1 測試金字塔

| 層級         | 工具              | 範圍                           |
| ------------ | ----------------- | ------------------------------ |
| 單元測試     | pytest            | Service 層邏輯、工具函式       |
| 整合測試     | pytest + httpx    | API 端點搭配真實資料庫         |
| 端對端（未來）| 待定             | 完整使用者流程                 |

### 6.2 測試規則

- 測試檔案放在 `backend/tests/`，結構鏡射 `app/`
- 檔名格式：`test_<模組>.py`
- 使用 fixtures 建立資料庫 session 和已認證的客戶端
- 每個端點至少測試 **正常路徑** 和一個 **錯誤案例**
- 分帳計算邏輯必須有完整的單元測試（均分、指定金額、百分比）
- 每次提交前執行測試：`pytest backend/tests/`

---

## 7. Vibe Coding 工作流程

> 本專案採用 AI 輔助開發，請遵循以下指引以維護品質。

### 7.1 提示前準備

- 清楚描述要建構「什麼」以及「為什麼」
- 參照本專案現有的程式碼模式
- 將複雜功能拆分為小型、漸進的步驟

### 7.2 AI 產生程式碼期間

- 接受前必須審查每一段生成的程式碼
- 檢查重點：安全性問題、邊界處的錯誤處理、與現有模式的一致性
- 驗證生成的 SQL/查詢不會造成 N+1 問題

### 7.3 生成後

- 執行測試套件
- 手動測試正常路徑（使用 FastAPI `/docs` Swagger UI）
- 提交前用 `git diff` 檢視所有變更

### 7.4 提示詞紀錄

- 非瑣碎功能的提示詞和關鍵決策應記錄在 commit message 中
- 若 AI 建議架構變更，先討論再實作

---

## 8. Git 版本控制

### 8.1 分支策略

- `main` — 穩定、可部署
- `feature/<名稱>` — 新功能
- `fix/<名稱>` — 修復 bug
- `refactor/<名稱>` — 重構

### 8.2 Commit 訊息格式

格式：`<類型>: <簡短描述>`

類型：`feat`、`fix`、`refactor`、`test`、`docs`、`chore`

範例：
```
feat: 新增百分比分帳功能
fix: 修正多幣別群組的餘額計算
test: 新增結算 API 的整合測試
```

### 8.3 PR 指引

- PR 保持聚焦 — 每個 PR 只處理一個功能或修復
- 包含變更摘要和測試計畫
- 合併前所有測試必須通過

---

## 9. 開發環境

### 9.1 快速啟動

#### 前端開發（Hot Reload，最常用）⚠️ 預設打本機後端

**DB 在 Neon（雲端），不需要本機 DB 或 Docker。**
`mobile/.env` 預設指向本機 backend（`http://localhost:8000/api/v1`）。
啟動前必須先把本機後端跑起來，否則 API 會 connection refused：

```bash
# 步驟 1：啟動本機 FastAPI（直接連 Neon DB）
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 步驟 2：啟動前端 dev server（另開一個 terminal）
cd mobile
npx expo start --web
```

開啟 http://localhost:8081，改任何 `.tsx` 檔案 → 瀏覽器立即更新。

> ✅ Neon DB 是共用的，但不經過 VM，VM 死掉也沒關係。

#### 需要打 Prod API（緊急驗證 prod 行為）

```bash
cd mobile
EXPO_PUBLIC_API_URL=https://byosw.duckdns.org/api/v1 npx expo start --web
```

> ⚠️ 注意：API 打的是 prod VM，VM 如果掛掉就無法使用。不要常用。

#### 跑測試（使用獨立 PostgreSQL，不影響 dev DB）

```bash
cd backend && pytest tests/
```

### 9.2 環境變數

參考 `backend/.env.example` 了解必要的環境變數。複製為 `backend/.env` 後自行設定。

---

## 10. 分帳領域規則

以下為核心業務規則，任何變更都需要額外的審查和測試覆蓋。

- **均分**：總金額平均分攤給所有參與者
- **指定金額**：各參與者的分攤金額個別指定，總和必須等於總金額
- **百分比分帳**：各參與者指定百分比，總和必須等於 100%
- **結算演算法**：使用淨餘額圖搭配貪婪匹配（max-heap）以最小化交易次數
- 所有金額計算必須使用 `Decimal`，禁止使用 `float`
- 四捨五入的差異歸付款人承擔

---

## 11. Mobile 開發規範（React Native / Expo）

> **UI 設計規範完整版**：`docs/UI_DESIGN_SPEC.md` -- 色彩系統、排版、圓角、間距、元件設計的唯一真相來源。

### 11.0 UI 設計核心原則（byosw 品牌）

- **設計哲學**：Minimalist, organic-tech, fluid, connected（極簡、有機科技、流動、高連結性）
- **色彩**：深炭灰（`HSL 222 47% 11%`，shadcn zinc）+ 純白高對比，accent 用 muted teal（`HSL 174`）極度克制
- **圓角**：Card `rounded-xl`、Button/Input `rounded-lg`、FAB/Badge/Avatar `rounded-full`
- **尺寸**：Button `h-10`(40px) / Input `h-10`(40px) / 文字統一 `text-sm`（shadcn 標準）
- **無陰影**：卡片用 `border border-border` 取代 shadow，保持平面極簡
- **圖示**：phosphor-react-native，`regular` weight（line art），與 logo 風格一致
- **留白**：寧多不少，用空間分組取代分隔線
- **品牌格式**：app name / tab label 使用小寫，呼應 logo "byosw" 的小寫風格
- **詳細規範**：所有色值、間距、元件尺寸請查閱 `docs/UI_DESIGN_SPEC.md`

### 11.1 表單輸入驗證

- **數字欄位必須限制輸入**：金額等數字輸入不能只靠 `keyboardType`，必須在 `onChangeText` 中用正規表達式過濾非法字元（例如 `/^\d*\.?\d{0,2}$/`），因為使用者可以透過貼上或第三方鍵盤輸入任意文字
- **金額欄位使用 `decimal-pad`**：不要用 `numeric`，改用 `decimal-pad` 以支援小數點輸入
- **送出前二次驗證**：按鈕的 `disabled` 條件和提交函式中都要檢查數值有效性（非空、大於零）
- **空字串特殊處理**：驗證正規表達式時要允許空字串，否則使用者無法清空輸入欄位

### 11.2 狀態管理

- 表單狀態使用 `useState`，全域狀態使用 Zustand store
- 避免在 `useEffect` 中直接呼叫 API，改用 `useCallback` + `useFocusEffect` 確保畫面聚焦時才刷新資料
- 非同步操作（API 呼叫）需要有 loading 狀態，防止重複送出

### 11.3 主題配色規範

- **所有互動按鈕必須使用 `bg-primary` 色系**：儲存、確認、送出等 CTA 按鈕，一律使用 `variant="default"`（即 `bg-primary text-primary-foreground`），禁止寫死顏色（例如 `bg-blue-500`），才能在使用者切換色系時自動更新。
- **`<Button>` 元件預設即為 `variant="default"`**：新增消費、建立群組、登入等按鈕只需 `<Button>` 不帶 `variant` 即可正確跟隨色系。
- **危險操作使用 `variant="destructive"`**：刪除、退出等操作使用 destructive variant，此 variant 固定為紅色（語義色），不隨色系改變。
- **色系變數定義在 `global.css`，新色系必須同步更新 5 個地方**：
  1. `mobile/lib/theme.tsx` — `ColorScheme` 型別 + `COLOR_SCHEMES` 陣列
  2. `mobile/global.css` — light/dark CSS 變數
  3. `mobile/app/_layout.tsx` — `SCHEME_CLASS` 映射
  4. `mobile/i18n/*.json`（zh-TW、en、ja）— 顯示名稱翻譯
- **Dark mode 設計規則（參照 Material Design 3 / Apple HIG）**（2026-04-03 回顧）：
  - 背景/卡片/邊框必須帶該 scheme 的 hue（saturation 8-12%），禁止共用中性黑底（`0 0% X%`）
  - Lightness 階梯：bg 5% → card 10% → secondary 13% → accent 15% → border 16%
  - Primary 色：飽和度降 20-30%（保留 50-65%），亮度升 5-10%（55-65%）
  - Foreground 亮度：86%
  - 任何涉及視覺配色的設計，先搜尋業界 best practice（MD3/Apple HIG），禁止憑直覺調參數
- **Preview 色必須與實際 primary 一致** — `COLOR_SCHEMES` 的 `preview.light` / `preview.dark` 必須是該 scheme light/dark mode `--primary` 的近似 hex 值（2026-04-03 回顧）
- **色系間色相差距 >= 30 度** — 任意兩個 scheme 的主色 hue 差距不得小於 30 度，避免視覺無法區分（2026-04-03 回顧）

### 11.4 常見錯誤清單（禁止再犯）

| 錯誤 | 正確做法 |
| --- | --- |
| 只用 `keyboardType` 限制輸入 | 必須搭配 `onChangeText` 正規表達式過濾 |
| 金額用 `parseFloat` 但未檢查 `NaN` | 送出前用 `Number(value) > 0` 驗證 |
| 未處理 API 錯誤 | 所有 API 呼叫需 `try/catch`，並顯示錯誤訊息給使用者 |
| 列表未加 `keyExtractor` | FlatList 必須指定唯一的 `keyExtractor` |
| 硬編碼文字 | 所有使用者可見文字必須透過 `i18n` 的 `t()` 函式 |
| 密碼欄位未設 `secureTextEntry` | 密碼輸入必須加上 `secureTextEntry` |
| Modal/BottomSheet 未處理鍵盤遮擋 | 使用 `KeyboardAvoidingView` 包裹表單內容 |
| 直接在 JSX 中寫複雜邏輯 | 抽成獨立函式或自訂 hook |
| 按鈕寫死顏色（如 `bg-blue-500`） | 一律使用 `<Button>` 的 `variant`，跟隨 `bg-primary` 色系 |
| 用 `Alert.alert` 帶 buttons 做確認 | Expo Web 上 `Alert.alert` 的 buttons/onPress 不作用，必須用自定義 Modal 做確認對話框 |
| `catch` 區塊用 `Alert.alert` 顯示 API 錯誤 | Expo Web 上 Alert 行為不穩定，錯誤訊息可能無聲消失；必須用 inline error state（`useState<string \| null>`）搭配 Modal 內 `<Text className="text-destructive">` 顯示，操作成功後清除 |
| `useState("equal")` 期望聯合型別 | TypeScript 會將字串字面值推斷為 `string`，必須明確標注：`useState<'equal' \| 'exact' \| 'ratio' \| 'shares'>('equal')` 或用 `(typeof SPLIT_METHODS)[number]` 從常數陣列衍生型別 |
| handler 函式在前置條件不滿足時 silent return | 若 user 為 null 或 hydration 未完成而直接 return，使用者看到的是「什麼都沒發生」；必須在 return 前 `setFormError(t("unknown_error"))` 或用 UI `disabled` 阻擋操作 |
| `useNativeDriver: true` 硬編碼 | 使用 `Platform.OS !== "web"` 條件判斷，否則 web 環境會產生警告並 fallback 到 JS 動畫 |
| 直接呼叫 `router.back()` 不檢查歷史 | Expo Web 上直接開啟 URL 時無導航歷史，`router.back()` 會拋出 GO_BACK not handled 錯誤；必須用 `router.canGoBack() ? router.back() : router.replace("/(tabs)")` |
| 依賴 Stack `headerShown: true` 顯示返回按鈕 | Expo Web 上 Stack native header 渲染不可靠，需要跨平台返回按鈕的頁面必須用自訂 header 元件（`headerShown: false` + 頁面內 ChevronLeft + router.back fallback） |
| 後端有 status 欄位但前端只實作部分狀態轉換 | 若 model 有 status 工作流（如 pending->confirmed），前端必須實作所有狀態轉換的 UI；api.ts 中定義但未被呼叫的方法 = 功能缺口，必須補齊或移除 |
| 有方向性的操作（A->B）讓雙方都能發起 | 結清、轉帳等有方向性的操作，按鈕只能顯示給發起方；對方只能回應（確認/拒絕/提醒），禁止用 `\|\|` 條件讓雙方都能觸發同一個 action |
| 後端未驗證有方向性關係的兩端不是同一人 | 建立 settlement/transfer 等有方向性的資料時，後端 service 層必須驗證 `from != to`，防止前端 bug 產生自我操作的垃圾資料 |
| 待處理項目只在深層頁面顯示，無被動通知 | 需要使用者回應的 pending 項目（結清確認、邀請等），必須有 tab badge 或首頁 banner 等被動通知機制，不能只在特定子頁面才看得到 |
| Dark mode 配色全部共用中性黑底 `0 0% X%` | 每個 theme 的 dark mode 背景/卡片/邊框必須帶自身色相（saturation 8-12%），參照 MD3 lightness 階梯（bg 5% → card 10% → secondary 13% → accent 15% → border 16%） |
| 憑直覺設計 dark mode 飽和度/亮度 | 先搜尋 Material Design 3 / Apple HIG best practice 取得具體數值，再依規則設計；primary 飽和度降 20-30%（保留 50-65%），亮度升 5-10% |
| `COLOR_SCHEMES` preview 色與實際 primary 不符 | preview hex 必須是 `global.css` 中對應 scheme light/dark `--primary` 的近似值，名稱也必須反映實際色調 |
| 兩個 scheme 色相差距 < 30 度 | 新增 scheme 前檢查所有現有 hue，任意兩者差距 >= 30 度，否則視覺無法區分 |
| 布林旗標只檢查「結果為零」就判定為「已完成」 | `is_settled` 等代表「完成」語意的旗標，必須同時檢查「曾經開始過」（如 `expense_count > 0`），零狀態實體（如新群組無費用）不等於已完成 |
| 新增 `log_activity(action="xxx")` 但未同步更新 `ActivityType` | 新增任何 activity action 值時，必須同步更新 4 處：(1) `schemas/activity.py` ActivityType Literal (2) 前端 `activities.tsx` ActivityType union + switch cases (3) 三語 i18n JSON (4) 前端 icon/style/description。缺任一處 = 活動列表整頁 500 |
| async session 中使用 `db.expire_all()` | `expire_all()` 會 expire 整個 identity map（含測試 fixture），觸發同步 lazy load → `MissingGreenlet`；改用 `db.expire(specific_obj)` 只 expire 需要重載的物件，且呼叫前先將後續需要的屬性存到區域變數 |
| `backend/.env` 的 `TEST_DATABASE_URL` 指向雲端 DB | 必須指向本機 `127.0.0.1` 且含 `ssl=disable`；指向雲端（Neon/RDS）會因跨洋 RTT 導致測試慢 100 倍以上（每次 TRUNCATE 3.5 秒 vs 本機 0.01 秒），規範文件寫了兩次沒用，必須靠 quality-gate.sh C-19 自動檢查 |
| Service 層寫入操作沒有發推播通知 | 每個 service 層的寫入操作（CREATE/UPDATE/DELETE）必須呼叫 `push_service` 對應的通知函式，通知受影響的群組成員；否則其他使用者畫面不會即時更新（2026-04-05 回顧） |
| 新增 tab 頁面但沒有推播回調 | 所有顯示資料的 tab 頁面，除了 `useFocusEffect` 拉資料外，必須同時加上 `useEffect` + `addNotificationReceivedCallback` 刷新同一組資料；否則收到推播時該頁面不會即時更新（2026-04-05 回顧） |
| `<Badge>` 內包裹 `<Text>` 等 JSX 元素 | Badge 元件的 children 型別為 `string`，直接傳 `{t("key")}` 字串即可，包 `<Text>` 會觸發 TS2745 錯誤（2026-04-05 回顧） |
| 已結清消費用 in-place update 直接修改 | 已結清消費必須用沖銷+重建（soft-delete 原始消費 + 建立新消費帶 `adjusted_from_id`），禁止原地修改；已確認結算仍在 DB 貢獻餘額，原地修改會導致結算對應的抵消效果失真、餘額計算不一致（2026-04-05 回顧） |
| 直接用 `icon.png` 作為頁面內 logo | `icon.png` 自帶白底，放在非白底頁面會出現白色方塊；頁面內 logo 必須用 `logo-transparent.png`（透明底），dark mode 用 `tintColor` 染色 |
| UI 元件尺寸憑直覺設定（如 Button `h-12`、Input `h-12`） | 先查 shadcn/ui 標準值再設定：Button `h-10`(default)/`h-9`(sm)/`h-11`(lg)、Input `h-10`、文字統一 `text-sm`；詳見 `docs/UI_DESIGN_SPEC.md` |
| `tabBarStyle` 只設 padding 不設 height，或設了任意 height 不配套 padding | 框架內部固定 height=49+insets.bottom，自訂 padding 會吃掉內容空間；正確公式：`height: 49 + bottomInset, paddingBottom: bottomInset`，確保內容空間永遠 49px（UIKit 標準） |
| Tab bar 移除 web 端 `bottomInset` fallback（`Math.max(rawInsets.bottom, 8)`） | Web 上 `useSafeAreaInsets().bottom` 經常回傳 0，必須保留 `Platform.OS === "web" ? Math.max(rawInsets.bottom, 8) : rawInsets.bottom`；此防護已被誤刪至少 3 次，每次都導致 tab bar 文字被裁切 |
| `bg-primary` 上圖示用 `color="white"` 或 `color="#fff"` | byosp dark mode primary 近白（HSL 0 0% 98%），白色圖示不可見；必須用 `hsl(var(--primary-foreground))` 跟隨主題（2026-04-05 回顧） |
| 裝置 safe area / 工具列高度用 hardcode 常數（如 `8`、`44`） | 每台手機 safe area 不同，hardcode 無法適配；必須用瀏覽器 API 自動偵測（`viewport-fit=cover` + `env(safe-area-inset-*)` + `useSafeAreaInsets()`）（2026-04-05 回顧） |
