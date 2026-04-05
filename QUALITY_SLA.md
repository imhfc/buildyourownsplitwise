# BYOSW 程式品質 SLA

> **這份文件是活文件。** 每次出現品質事件，必須在修復後更新 §4「已知違規模式」與 §5「版本歷史」。

---

## §1 SLA 指標（Service Level Agreement）

| ID | 指標 | 目標 | 違規定義 |
|----|------|------|----------|
| SLA-1 | Web bundle 必須零 SyntaxError 編譯成功 | 100%（零容忍） | bundle 出現任何 JS 語法錯誤 |
| SLA-2 | 首次載入不能空白頁 | 100%（零容忍） | `http://localhost:8081` 無法渲染任何內容 |
| SLA-3 | 預設語言顯示 zh-TW | 100%（零容忍） | 未設定偏好時顯示非 zh-TW |
| SLA-4 | Dark mode 切換無 Runtime Error | 100%（零容忍） | 切換主題時拋出 JS exception |
| SLA-5 | `pytest backend/tests/` 全數通過 | 100%（零容忍） | 任何測試 FAIL |
| SLA-6 | `npx expo-doctor` 無 major mismatch | 100%（零容忍） | 安裝新套件後出現版本衝突 |

**SLA 違規 = 不得合併 PR，不得部署。**

---

## §2 事件分級與修復時限（Incident Classification）

| 等級 | 定義 | 例子 | 修復時限 |
|------|------|------|----------|
| **P0** | App 無法啟動或一片空白 | bundle SyntaxError、空白頁 | **30 分鐘內** |
| **P1** | 核心功能損壞，但 App 仍開得起來 | 語言顯示錯誤、dark mode crash | **2 小時內** |
| **P2** | 功能正常但體驗受損 | 樣式跑版、動畫卡頓 | **下次開發 session** |

---

## §3 品質維護方法論（四層防禦）

```
Layer 1 — 組態不變式（自動驗證）
  ↓ 每次修改 config 相關檔案後執行
Layer 2 — 安裝後關卡（Post-Install Gate）
  ↓ 每次 npm install 後執行
Layer 3 — 提交前關卡（Pre-Commit Gate）
  ↓ 每次 git commit 前執行
Layer 4 — 事件學習迴圈（Post-Incident Loop）
  ↓ 每次 P0/P1 修復後更新本文件
```

### Layer 1：組態不變式自動驗證

執行：`bash mobile/scripts/quality-gate.sh`

腳本檢查所有已知高風險組態（見 §4）。**任一項 FAIL → 禁止繼續。**

### Layer 2：安裝後關卡

每次 `npm install` 或新增套件後必須通過：

```bash
cd mobile
npx expo-doctor                        # SLA-6：無 major mismatch
bash scripts/quality-gate.sh          # 組態不變式全部 PASS
npx expo start --web --clear &        # 等 10 秒後
sleep 10 && curl -s localhost:8081/status  # SLA-1/2：packager-status:running
```

### Layer 3：提交前關卡

每次 `git commit` 前的必做清單：

```bash
bash mobile/scripts/quality-gate.sh   # 組態不變式
pytest backend/tests/                  # SLA-5：後端測試
```

### Layer 4：事件學習迴圈

> ⚠️ **這一層是最重要的。前三層都是防止舊問題重演，這層是防止新問題被遺忘。跳過這層 = 浪費了整次修復的價值。**

**每次修復任何 bug（不限 P0/P1），Claude 必須主動、立即執行以下所有步驟，不需等使用者提醒：**

1. 確認根因（5-Why 分析，追到底層原因，不是表面症狀）
2. 在 §4 新增對應的「組態不變式」
3. 在 `mobile/scripts/quality-gate.sh` 新增對應的自動檢查腳本
4. 在 §5「版本歷史」補充完整紀錄（症狀、根因、解法）
5. 更新 `mobile/DEBUG_CHECKLIST.md` 的版本歷史表

**若 Claude 修復 bug 後沒有主動完成上述步驟，使用者應提醒，Claude 必須立即補做。**

---

## §4 組態不變式（Configuration Invariants）

> ⚠️ **強制規定：每次修復任何 bug，無論大小，都必須在這裡新增一條不變式，並同步更新 `quality-gate.sh`。**
> 修 bug 但不新增不變式 = 沒有真正修完。這份表格是「我們吃過的虧」的完整清單，每一行都代表一個真實踩過的坑。
>
> 以下規則由 `mobile/scripts/quality-gate.sh` 自動驗證。**不得手動跳過。**

| # | 檢查項目 | 對應 SLA | 根因事件 |
|---|----------|----------|----------|
| C-1 | `tailwind.config.js` 必須有 `darkMode: "class"` | SLA-4 | 2026-03-28 dark mode crash |
| C-2 | `babel.config.js` plugins 必須含 `babel-plugin-transform-import-meta` | SLA-1 | 2026-03-28 import.meta SyntaxError |
| C-3 | `metro.config.js` 必須有 `unstable_enablePackageExports = false` | SLA-1 | 2026-03-28 Zustand ESM 解析錯誤 |
| C-4 | `i18n/index.ts` 必須有 `detection: { caches: [] }` | SLA-3 | 2026-03-28 i18next localStorage 覆蓋 |
| C-5 | `package.json` 的 `react` 版本不能有 `^` | SLA-2 | 2026-03-28 react-dom 版本不符 |
| C-6 | `package.json` 的 `react-dom` 版本不能有 `^` | SLA-2 | 2026-03-28 react-dom 版本不符 |
| C-7 | `package.json` 的 `expo-crypto` 版本**禁止使用 canary**（不能含 `-canary-`） | SLA-2 | 2026-03-28 expo-crypto canary 造成 Metro InternalError |
| C-8 | `stores/auth.ts` 禁止在 `persist()` 選項內使用 `onRehydrateStorage`（Zustand 5 同步 toThenable 導致 callback 在 create() 完成前執行，此時 `useAuthStore` 為 undefined，setState 靜默失敗） | SLA-2 | 2026-03-28 hasHydrated 永遠為 false → App 轉圈圈 |
| C-9 | `app/_layout.tsx` redirect 邏輯必須涵蓋已登入用戶不在任何路由群組的情境（需包含 `inTabsGroup` 與 `inGroupPage` 判斷，避免從 root index 卡住，也避免在 `group/[id]` 時錯誤導回 tabs） | SLA-2 | 2026-03-28 isAuthenticated=true 在 root index 時兩個條件都不成立 → 永遠不跳轉 |
| C-10 | `app/group/[id].tsx` 的 Modal 表單 API 錯誤必須用 inline error state 顯示（必須有 `setAddError`），禁止用 `Alert.alert` 顯示 API 錯誤 | SLA-3 | 2026-03-30 新增消費失敗時錯誤訊息無聲消失 |
| C-11 | 所有使用 `router.back()` 的檔案必須同時使用 `canGoBack` 檢查，Expo Web 上直接開啟 URL 無導航歷史會拋出 GO_BACK not handled | SLA-2 | 2026-03-31 群組頁面無法返回 |
| C-12 | `docker-compose.yml` 中除 Caddy(80/443) 外，所有 `ports` 必須綁定 `127.0.0.1:`（如 `"127.0.0.1:5432:5432"`），禁止 `"5432:5432"` 或 `"0.0.0.0:5432:5432"` 對外開放 | SLA-5 | 2026-04-02 db/backend port 對所有網路介面開放 |
| C-13 | `mobile/services/api.ts` 中 `settlementsAPI` 定義的所有方法（含 `confirm`、`reject`、`pending`）必須至少有一處前端呼叫點，未使用的 API 方法代表功能未完成 | SLA-5 | 2026-04-02 結清功能只做了建立，缺少確認/拒絕 UI |
| C-14 | `group/[id].tsx` 結清按鈕（`settle_up`）只能顯示給付款方（`from_user_id === user?.id`），收款方只保留「發送提醒」按鈕。禁止用 `from_user_id \|\| to_user_id` 讓雙方都能發起結清 | SLA-5 | 2026-04-03 雙方都能按結清導致方向反轉 |
| C-15 | `settlement_service.py` 的 `create_settlement` 必須驗證 `from_user_id != data.to_user`，禁止自己對自己結清 | SLA-5 | 2026-04-03 自我結算垃圾資料影響餘額計算 |
| C-16 | `group_service.py` 的 `list_user_groups` 查詢必須包含 `expense_count` 子查詢，`is_settled` 判斷必須同時滿足 `debts == 0 AND expense_count > 0`，零費用群組不得被標記為已結清 | SLA-5 | 2026-04-03 新群組零狀態被誤判為已結清 |
| C-17 | `log_activity()` 的所有 `action` 值必須同時存在於：(1) `schemas/activity.py` 的 `ActivityType` Literal (2) 前端 `activities.tsx` 的 `ActivityType` union (3) 三語 i18n JSON (4) 前端 `getActivityStyle`/`ActivityIcon`/`buildDescription` 的 switch cases。任一處缺漏 = 活動列表整頁 500 | SLA-5 | 2026-04-03 email_invitation_cancelled 未加入 ActivityType 導致 Pydantic ValidationError |
| C-18 | `backend/app/services/` 中禁止使用 `db.expire_all()`，必須用 `db.expire(specific_obj)` 針對特定物件；且 expire 前必須先將後續需要的屬性存到區域變數 | SLA-5 | 2026-04-03 update_expense 的 expire_all 導致 MissingGreenlet |
| C-19 | `backend/.env` 的 `TEST_DATABASE_URL` 必須指向本機（包含 `127.0.0.1` 且包含 `ssl=disable`），禁止指向外部主機（Neon、RDS 等雲端 DB） | SLA-5 | 2026-04-03 TEST_DATABASE_URL 指向 Neon 美東，195 個測試要跑 10+ 分鐘（每次 TRUNCATE 3.5 秒 RTT），改本機後 8 秒 |
| C-20 | `mobile/components/ui/fab.tsx`、`mobile/components/ui/button.tsx`、`mobile/app/group/[id].tsx`、`mobile/app/(tabs)/friends.tsx` 中 `bg-primary` 上的圖示 color 不得為 `white`/`#fff`，必須使用 `hsl(var(--primary-foreground))` | SLA-4 | FAB/Button 在 byosp dark mode（primary 近白）上圖示不可見 |
| C-21 | `mobile/app/_layout.tsx` 包含 `viewport-fit=cover` 動態注入和 `100dvh` CSS 注入 | SLA-2 | Mobile web 上 safe area 自動偵測 + 排除瀏覽器工具列 |
| C-22 | `mobile/app/(tabs)/_layout.tsx` 的 tab bar 必須包含 `Platform.OS === "web"` 的 `Math.max` bottomInset fallback，且 `tabBarStyle` 必須同時設定 `height: 52 + bottomInset` 和 `paddingBottom: bottomInset`（配套公式） | SLA-2 | 2026-04-05 tab bar 文字被裁切（同一 bug 第 5 次） |
| C-23 | 所有頁面的 UI 設計 token 必須統一：Card `p-3.5 mb-2`、主文字 `text-sm font-medium`、次要文字 `text-xs text-muted-foreground`、金額 `text-sm font-semibold tabular-nums`、Bottom sheet `rounded-t-xl border-t`（禁止 `rounded-t-2xl`）、Dialog `rounded-xl border border-border p-6`（禁止裸 `rounded-xl` 無 border）、icon circle `h-9 w-9` + icon `18px`、modal title `text-base font-semibold`（禁止 `H3`/`text-xl`）、X close `size={20}`（禁止 `24`） | SLA-4 | 2026-04-06 四個 tab 頁面設計語言不一致（text size/padding/modal 樣式各自為政） |
| C-24 | EmptyState 元件傳入的 icon 必須與該頁面對應 tab bar 的圖標相同（好友=`Users`、群組=`SquaresFour`、活動=`ClockCounterClockwise`）；EmptyState 的 weight 固定為 `light` | SLA-4 | 2026-04-06 好友頁 EmptyState 用 UsersThree 但 tab bar 用 Users，視覺不一致 |
| C-25 | phosphor 圖標 weight 分級：tab bar 未選中/EmptyState 裝飾性用 `light`，tab bar 選中用 `fill`，頁面內互動圖標用 `regular`。禁止在 tab bar 未選中態使用 `regular`（線條太粗） | SLA-4 | 2026-04-06 tab bar 圖標線條太粗不夠精緻 |

---

## §5 版本歷史（每次事件後更新）

| 日期 | 等級 | 症狀 | 根因 | 新增不變式 |
|------|------|------|------|------------|
| 2026-03-28 | P0 | Expo web 空白頁 | `react-dom: ^19.2.4` 與 Expo SDK 55 不符 | C-5, C-6 |
| 2026-03-28 | P1 | Web 顯示日文 | i18next 25.x 讀 localStorage 蓋掉 config | C-4 |
| 2026-03-28 | P0 | `import.meta` SyntaxError | Expo 55 `unstable_enablePackageExports: true` 解析 Zustand ESM | C-2, C-3 |
| 2026-03-28 | P1 | Dark mode Runtime Error | `tailwind.config.js` 缺少 `darkMode: "class"` | C-1 |
| 2026-03-28 | P0 | App 一直轉圈圈（index.tsx ActivityIndicator 卡住） | `expo-crypto` canary 版本（`55.0.11-canary-...`）造成 npm 在 `expo-auth-session/node_modules/` 產生不完整的巢狀依賴，Metro resolver 嘗試開啟 `expo-auth-session/node_modules/expo-constants/package.json` 但找不到，拋出 InternalError → bundle 編譯失敗 → Zustand persist `onRehydrateStorage` 未執行 → `hasHydrated` 永遠為 `false` → redirect 永不觸發 | C-7 |
| 2026-03-28 | P0 | App 加入 Google 登入後一直轉圈圈（無 JS Error，spinner 在 index.tsx） | **雙重根因**：(1) Zustand 5 的 `toThenable` 對 localStorage 同步執行，`onRehydrateStorage` callback 在 `create()` 完成前就被呼叫，此時 `useAuthStore` 還是 `undefined`，`setState` 靜默失敗 → `hasHydrated` 永遠 `false`；(2) `_layout.tsx` redirect 邏輯僅處理兩種情境，未處理「已登入但在 root index（非 tabs 也非 auth）」→ 兩個 if 都不成立，永遠卡在 spinner | C-8, C-9 |
| 2026-03-30 | P1 | 無法新增消費（按「儲存」後無任何反應） | **雙重根因**：(1) 前端 `handleAddExpense` catch 區塊用 `Alert.alert` 顯示錯誤，Expo Web 上行為不穩定，錯誤訊息無聲消失；(2) 後端 `create_expense` 端點只捕捉 `ForbiddenError` 和 `ValidationError`，未捕捉 `NotFoundError`（匯率查詢失敗時），導致 500 Internal Server Error | C-10 |
| 2026-03-31 | P1 | 群組詳情頁無法返回上一頁 | **雙重根因**：(1) Expo Web 上 Stack navigator 的 native header（`headerShown: true`）不渲染返回按鈕；(2) 改用 `router.back()` 後，Web 直接開啟 URL 時無導航歷史，拋出 GO_BACK not handled 錯誤 | C-11 |
| 2026-04-01 | P1 | 遷移新 VM 後 HTTPS 無法連線（SSL handshake error） | Caddy 舊 volume 殘留 ACME **staging** 設定（`acme-staging-v02.api.letsencrypt.org`），staging 憑證不被瀏覽器信任；加上 DNS 傳播期間 Let's Encrypt 驗證伺服器快取舊 IP（35.206.96.99），challenge 全部失敗。解法：清除 `caddy_data`/`caddy_config` volume 後重啟，Caddy 自動用 production ACME 重新申請憑證 | — |
| 2026-04-02 | P1 | Docker Compose db/backend port 對外開放，任何人可直連資料庫 | `docker-compose.yml` ports 未綁定 `127.0.0.1`，預設 `0.0.0.0` 對所有網路介面開放。解法：所有內部服務 ports 加 `127.0.0.1:` 前綴，僅 Caddy(80/443) 對外；VM db-test 改用 `--network host` + `PGPORT=5433`；本機透過 autossh SSH tunnel 連線 | C-12 |
| 2026-04-02 | P1 | 結清後對方欠款未清除（活動紀錄有顯示但餘額不變） | Settlement 有 pending->confirmed 雙層確認，餘額計算只計 confirmed。前端只實作 `create`（status=pending），未實作 `confirm`/`reject` UI。`settlementsAPI.confirm()` 和 `.pending()` 在 api.ts 定義但從未被呼叫。解法：首頁新增待確認結清區塊（收款方可確認/拒絕）；建立結清後顯示「等待對方確認」提示；後端新增 reject 端點 | C-13 |
| 2026-04-03 | P1 | 雙方都能按結清，產生方向反轉和自我結算的垃圾資料 | **雙重根因**：(1) 前端結清按鈕條件用 `from_user_id \|\| to_user_id`，收款方也能點結清，但後端 `create_settlement` 把 `current_user` 設為 `from_user` → 方向反轉；(2) 後端未驗證 `from_user != to_user`，導致自己對自己結清的紀錄寫入 DB 影響餘額。解法：前端結清按鈕限定 `from_user_id === user?.id`，收款方只保留「發送提醒」；後端新增 `from_user == to_user` 驗證；群組 tab 加 badge 顯示 pending 數量 | C-14, C-15 |
| 2026-04-03 | P2 | 新建立的群組馬上被歸類到「已結清群組」 | `is_settled` 只檢查 `debts == 0`，新群組無任何費用所以債務為零，零狀態被誤判為已完成。解法：`list_user_groups` 加入 `expense_count` 子查詢，`is_settled` 改為 `debts == 0 AND expense_count > 0`，語意正確區分「從未有帳」與「帳已清完」 | C-16 |
| 2026-04-03 | P1 | 活動紀錄頁面載入失敗（500 Internal Server Error） | `email_invitation_service.py` 新增 `log_activity(action="email_invitation_cancelled")` 但未同步更新 `schemas/activity.py` 的 `ActivityType` Literal。`list_user_activities` 建構 `ActivityItem` 時 Pydantic 驗證失敗，整個列表 500。解法：`ActivityType` 加入 `email_invitation_cancelled`；前端型別、i18n、UI switch 同步補齊 | C-17 |
| 2026-04-03 | P1 | 更新消費後 MissingGreenlet 錯誤（500） | `update_expense` 中 `db.expire_all()` 把整個 session identity map 的物件全部 expire（含測試 fixture），後續存取 `expense.id` 觸發同步 lazy load，async session 下爆 `MissingGreenlet`。解法：改用 `db.expire(expense)` 只 expire 該物件，且在 expire 前先把 `expense.id` 存到區域變數 | C-18 |
| 2026-04-03 | P2 | 後端測試跑 10+ 分鐘（應 < 30 秒） | `backend/.env` 的 `TEST_DATABASE_URL` 仍指向 Neon 雲端 DB（美東），每次 TRUNCATE CASCADE 因跨洋 RTT 花 3.5 秒。testing-standards.md 寫了兩次要用本機但 .env 從未修正。解法：改為 `127.0.0.1:5432?ssl=disable`，新增 C-19 自動檢查 | C-19 |
| 2026-04-05 | P2 | byosp dark mode 下 FAB/Button 圖示不可見 | `bg-primary` 上的圖示 `color` 硬編碼為 `"white"`，而 byosp dark mode primary 為 HSL 0 0% 98%（近白），白色圖示在白底上不可見。解法：改為 `hsl(var(--primary-foreground))` 跟隨色系 | C-20 |
| 2026-04-05 | P2 | Mobile web tab bar 文字/內容被手機瀏覽器工具列裁切 | Expo 預設 viewport meta 無 `viewport-fit=cover`，且頁面高度使用 `100%` 而非 `100dvh`，無法自動排除瀏覽器工具列佔用空間。解法：`_layout.tsx` 動態注入 `viewport-fit=cover` 及 `height: 100dvh` CSS | C-21 |
| 2026-04-05 | P2 | Tab bar 文字在手機上被裁切（第 4 次復發） | **雙重根因**：(1) `tabBarStyle` 寫死 `height: 56 + insets.bottom`，不同裝置字體渲染不同導致文字被裁切；(2) 上個 commit 重構時移除了 web 端 `bottomInset = Math.max(rawInsets.bottom, 8)` fallback，web 上 `insets.bottom` 回傳 0 導致底部無間距。此 bug 已反覆出現 4 次，每次都是重構時把 web fallback 當冗餘刪除。解法：移除固定 height、恢復 web fallback、新增 C-22 自動檢查 | C-22 |
| 2026-04-05 | P2 | Tab bar 文字完全消失（第 5 次復發） | **根因**：ebe1e7d 依照「禁止固定 height」規則移除了 `height`，但只靠 `paddingBottom/paddingTop` 控制間距。React Navigation 內部 `getTabBarHeight()` 在沒有自訂 height 時回傳 `49 + insets.bottom`，而自訂 padding 會吃掉這 49px 的內容空間。web 上 insets.bottom=0 → height=49、paddingBottom=8、paddingTop=8 → 內容空間只剩 33px，icon 20px + label 14px = 34px → label 被擠出。**「禁止固定 height」規則本身就是錯的**，正確公式是 `height: 52 + bottomInset, paddingBottom: bottomInset` | C-22（更新） |
| 2026-04-06 | P3 | 群組詳情/朋友/帳號頁面的文字大小、Card 間距、Modal 樣式與群組列表不一致 | 各頁面獨立開發時沒有統一的 UI design token 規範，friends 用 `p-4 mb-3 text-base`，account 用 `text-xl` modal title，group detail 用 `text-lg font-bold` 金額。使用者反映「群組裡面的字跟外面不一樣大」。解法：建立統一 design token（Card p-3.5 mb-2、text-sm/text-xs 階梯、modal rounded-t-xl/rounded-xl），全量修正四個 tab + group detail | C-23 |
| 2026-04-06 | P3 | EmptyState 圖標與 tab bar 不一致（好友頁用三人圖、tab bar 用兩人圖） | 變更 tab bar 圖標（UserPlus→Users）時未同步更新 EmptyState 傳入的 icon，導致同一功能出現兩種圖標。解法：統一好友=Users、群組=SquaresFour；新增 C-24 不變式 | C-24 |
| 2026-04-06 | P3 | Tab bar 圖標線條太粗、SegmentedTabs 使用陰影不符設計語言 | Tab bar 未選中用 `regular` weight 線條偏粗；SegmentedTabs 用 pill 背景 + shadow 違反「不使用陰影」規範。解法：tab bar weight 改為 light→fill、SegmentedTabs 改為底線指示器、新增 C-25 不變式 | C-25 |
| 2026-04-06 | P3 | 主題色系 dark mode 看起來很奇怪，各色系背景色不一致 | 每個 scheme 各自定義完整 CSS 變數（390 行），dark mode 用帶色相的深色背景，不符合 shadcn 做法。解法：改為 shadcn 兩層系統（base Neutral 共用結構色 + color scheme 只覆蓋 primary/ring/card），CSS 降至 130 行；硬寫 hex 從 zinc 改為 neutral（去藍調）；卡片加主題色淡染（97% lightness） | — |
