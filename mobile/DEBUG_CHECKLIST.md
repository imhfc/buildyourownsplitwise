# Mobile Web Debug Checklist & KPI

> 遇到 bug 時先跑完這份 checklist，再開始改 code。每次找到新問題、新解法就更新這份文件。

---

## Expo Web 空白頁（Blank Page）

### 診斷順序
- [ ] 1. Metro server 有沒有跑？
  ```bash
  curl localhost:8081/status   # 預期：packager-status:running
  ```
- [ ] 2. HTML 有沒有正確回傳？
  ```bash
  curl localhost:8081/ | grep "root"  # 預期看到 <div id="root">
  ```
- [ ] 3. Bundle 能不能 compile？
  ```bash
  curl "http://localhost:8081/node_modules/expo-router/entry.bundle?platform=web&dev=true&hot=false&lazy=true&transform.engine=hermes&transform.routerRoot=app&unstable_transformProfile=hermes-stable" | tail -5
  # 預期：__r(0); 結尾，沒有 SyntaxError
  ```
- [ ] 4. 套件版本有沒有衝突？
  ```bash
  npx expo-doctor
  # 所有 major version 必須符合；精確版本用 npx expo install --check 修正
  ```
- [ ] 5. 清 Metro cache 重啟
  ```bash
  npx expo start --web --clear
  ```
- [ ] 6. **開 Chrome DevTools → Console → 看 JS Error**（最直接，應優先做）

### 已知根因 & 解法

| 症狀 | 根因 | 解法 |
|------|------|------|
| 空白頁，bundle OK | `react-dom` 版本不符 Expo SDK | `package.json` 改精確版本，`npm install` + `--clear` |
| 空白頁，套件剛更新 | Metro cache 沒清 | `npx expo start --web --clear` |
| 空白頁，JS crash | React render error，無 ErrorBoundary | DevTools console 看 error，或加 ErrorBoundary |
| `Cannot use 'import.meta' outside a module` | Expo 55 預設 `unstable_enablePackageExports: true`，導致 Metro 解析 Zustand ESM（.mjs）版本，其中包含 `import.meta.env` | `metro.config.js` 加 `config.resolver.unstable_enablePackageExports = false`，`--clear` 重啟 |

---

## i18n 語言顯示錯誤

### 診斷順序
- [ ] 1. 重新整理頁面（排除記憶體狀態）
- [ ] 2. 確認 `localStorage.i18nextLng`
  - DevTools → Application → Local Storage → 找 `i18nextLng` key → 刪除後重新整理
- [ ] 3. 確認 i18n init 有 `detection: { caches: [] }`（禁止 i18next 讀/寫 localStorage）

### 已知根因 & 解法

| 症狀 | 根因 | 解法 |
|------|------|------|
| 即使 `lng:"zh-TW"` 仍顯示其他語言 | i18next 25.x 讀 localStorage 蓋掉 config | init 加 `detection: { caches: [] }` |
| 設定頁切換語言後 reload 沒復原 | 同上 | 同上 |

---

## API / 後端連線問題

### 診斷順序
- [ ] 1. 後端有沒有跑？`curl http://localhost:8000/health`
- [ ] 2. CORS 設定有沒有允許 web origin？（`http://localhost:8081`）
- [ ] 3. JWT token 有沒有過期？DevTools → Network → 看 401 response
- [ ] 4. `services/api.ts` 的 `baseURL` 有沒有設正確？

---

## 套件相關 KPI

> 每次 `npm install` 新套件後必須通過：

- [ ] `npx expo-doctor` 無 major version mismatch
- [ ] `npx expo start --web --clear` 成功啟動，不出現空白頁
- [ ] `pytest backend/tests/` 全部通過（若有動到後端）

---

## 版本歷史（每次發現新問題請補充）

| 日期 | 問題 | 根因 | 解法 |
|------|------|------|------|
| 2026-03-28 | Expo web 空白頁 | `react-dom: ^19.2.4` 與 Expo SDK 55 不符 | 改 `19.2.0`，`npm install`，`--clear` |
| 2026-03-28 | Web 顯示日文 | i18next 25.x 讀 `localStorage.i18nextLng` | i18n init 加 `detection: { caches: [] }` |
| 2026-03-28 | `Cannot use 'import.meta' outside a module` | Expo 55 `getDefaultConfig` 預設 `unstable_enablePackageExports: true`，Metro 解析 Zustand 5.x 的 ESM `.mjs` 版（含 `import.meta.env`）而非 CJS | `metro.config.js` 明確加 `config.resolver.unstable_enablePackageExports = false`，`--clear` 重啟 |
