# 測試規範

> 此檔案為所有測試操作的唯一真相來源。`/write-tests` skill、回歸測試、CI 皆參照此規範。

## 後端測試 (pytest)

### 環境

- 測試 DB：Neon serverless PostgreSQL（`TEST_DATABASE_URL` 環境變數，定義在 `backend/.env`）
- 不需要本機 Docker db-test
- conftest.py 透過 `dotenv.load_dotenv` 自動載入 `backend/.env`，不需手動 export 環境變數
- conftest.py 使用 `NullPool` + `statement_cache_size=0`（Neon 和本機 Docker 皆適用）
- `setup_database` fixture 只做 `create_all`（不 drop），schema 由 Alembic 管理

### 執行步驟

```bash
# 執行所有後端測試（一行搞定）
cd backend && .venv/bin/python -m pytest tests/

# 執行特定測試模組
cd backend && .venv/bin/python -m pytest tests/test_expenses.py -v

# 查看覆蓋率
cd backend && .venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing
```

### 規則

- 測試檔案放在 `backend/tests/`，命名 `test_<模組>.py`
- 使用 `conftest.py` 中的 fixtures（`db`, `client`, `user_a`, `user_b`, `group_with_members` 等）
- 每個端點至少測試正常路徑和一個錯誤案例
- 分帳計算（均分、指定金額、百分比）必須有完整單元測試
- 金額用 `Decimal`，禁止 `float`
- 認證 header 使用 `conftest.auth_header(user)` 取得

## 前端測試

### 品質關卡（必跑）

```bash
bash mobile/scripts/quality-gate.sh
```

任一 FAIL 禁止提交。

### Jest 單元測試

```bash
cd mobile && npx jest
cd mobile && npx jest --coverage
```

- 測試檔案放在 `mobile/__tests__/`
- 使用 @testing-library/react-native
- 工具函式和常數必須有單元測試

## 測試金字塔

| 層級 | 工具 | 範圍 |
|------|------|------|
| 單元測試 | pytest / Jest | Service 層邏輯、工具函式 |
| 整合測試 | pytest + httpx | API 端點 + 真實 PostgreSQL (Neon) |
| 品質關卡 | quality-gate.sh | 設定不變式檢查 |
