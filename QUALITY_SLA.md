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
