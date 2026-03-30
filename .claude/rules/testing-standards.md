# 測試規範

## 後端測試 (pytest)

- 測試檔案放在 `backend/tests/`，命名 `test_<模組>.py`
- 使用 fixtures 建立 async DB session 和已認證的 httpx client
- 每個端點至少測試正常路徑和一個錯誤案例
- 分帳計算（均分、指定金額、百分比）必須有完整單元測試
- 測試 DB 使用 docker-compose.test.yml（port 5433）
- 執行：`cd backend && pytest tests/`

## 前端測試 (Jest)

- 測試檔案放在 `mobile/__tests__/`
- 使用 @testing-library/react-native
- 工具函式和常數必須有單元測試
- 執行：`cd mobile && npx jest`

## 測試金字塔

| 層級 | 工具 | 範圍 |
|------|------|------|
| 單元測試 | pytest / Jest | Service 層邏輯、工具函式 |
| 整合測試 | pytest + httpx | API 端點 + 真實 PostgreSQL |
| 品質關卡 | quality-gate.sh | 設定不變式檢查 |
