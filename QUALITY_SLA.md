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

**每次 P0/P1 事件修復後，Claude 必須主動執行：**

1. 確認根因（5-Why 分析）
2. 在 §4 新增對應的「組態不變式」
3. 在 `mobile/scripts/quality-gate.sh` 新增對應的自動檢查
4. 在 §5「版本歷史」補充紀錄
5. 更新 `mobile/DEBUG_CHECKLIST.md` 的已知根因表

---

## §4 組態不變式（Configuration Invariants）

> 以下規則由 `mobile/scripts/quality-gate.sh` 自動驗證。**不得手動跳過。**

| # | 檢查項目 | 對應 SLA | 根因事件 |
|---|----------|----------|----------|
| C-1 | `tailwind.config.js` 必須有 `darkMode: "class"` | SLA-4 | 2026-03-28 dark mode crash |
| C-2 | `babel.config.js` plugins 必須含 `babel-plugin-transform-import-meta` | SLA-1 | 2026-03-28 import.meta SyntaxError |
| C-3 | `metro.config.js` 必須有 `unstable_enablePackageExports = false` | SLA-1 | 2026-03-28 Zustand ESM 解析錯誤 |
| C-4 | `i18n/index.ts` 必須有 `detection: { caches: [] }` | SLA-3 | 2026-03-28 i18next localStorage 覆蓋 |
| C-5 | `package.json` 的 `react` 版本不能有 `^` | SLA-2 | 2026-03-28 react-dom 版本不符 |
| C-6 | `package.json` 的 `react-dom` 版本不能有 `^` | SLA-2 | 2026-03-28 react-dom 版本不符 |

---

## §5 版本歷史（每次事件後更新）

| 日期 | 等級 | 症狀 | 根因 | 新增不變式 |
|------|------|------|------|------------|
| 2026-03-28 | P0 | Expo web 空白頁 | `react-dom: ^19.2.4` 與 Expo SDK 55 不符 | C-5, C-6 |
| 2026-03-28 | P1 | Web 顯示日文 | i18next 25.x 讀 localStorage 蓋掉 config | C-4 |
| 2026-03-28 | P0 | `import.meta` SyntaxError | Expo 55 `unstable_enablePackageExports: true` 解析 Zustand ESM | C-2, C-3 |
| 2026-03-28 | P1 | Dark mode Runtime Error | `tailwind.config.js` 缺少 `darkMode: "class"` | C-1 |
