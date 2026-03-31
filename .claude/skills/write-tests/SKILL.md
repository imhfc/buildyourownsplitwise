---
name: write-tests
description: 撰寫單元測試、執行測試、分析覆蓋率。Use this skill when 使用者要求「寫測試」「測試」「覆蓋率」「單元測試」「補充測試」。
---

# Write Tests Skill

使用 Atomic Agents: test-writer → test-runner → coverage-analyzer 完成測試任務。

## 使用場景

### 1. 後端測試 (pytest + FastAPI)
- API 端點整合測試（httpx AsyncClient）
- Service 層單元測試
- 分帳邏輯測試（均分、指定金額、百分比、比例）
- 結算演算法測試

### 2. 前端測試 (Jest + React Native)
- 元件渲染測試
- 工具函式單元測試
- Store 狀態測試

### 3. 執行與覆蓋率
- 運行測試並驗證通過
- 修復失敗的測試
- 識別未覆蓋的代碼

## 使用方式

```bash
# 斜線命令
/write-tests 為 expense_service 撰寫單元測試

# 自然語言（自動觸發）
為 settlement_service 寫測試
測試新增的 API 端點
補充 exchange_rate 的測試
```

## 執行流程

```
Step 0: 讀取 .claude/rules/testing-standards.md（取得最新環境、指令、規則）
Step 1: test-writer (Haiku) — 分析目標代碼，撰寫測試
Step 2: test-runner (Haiku) — 執行測試，收集結果
Step 3: test-fixer (Haiku) — 如有失敗，自動修復
Step 4: coverage-analyzer (Haiku) — 分析覆蓋率，建議補充
```

> **重要**：`.claude/rules/testing-standards.md` 為測試操作的唯一真相來源，每次觸發此 skill 必須先讀取。

## 後端測試規範

### 測試結構
```python
# backend/tests/test_<模組>.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_<功能>_success(client: AsyncClient, auth_headers: dict):
    """正常路徑測試"""
    response = await client.post("/api/v1/...", headers=auth_headers, json={...})
    assert response.status_code == 201
    data = response.json()
    assert data["field"] == expected_value

@pytest.mark.asyncio
async def test_<功能>_error(client: AsyncClient, auth_headers: dict):
    """錯誤路徑測試"""
    response = await client.post("/api/v1/...", headers=auth_headers, json={...})
    assert response.status_code == 400
```

### 必遵守規則
- 使用 `conftest.py` 中的 fixtures（`db`, `client`, `user_a`, `user_b`, `group_with_members`, `auth_header()`）
- 每個端點至少正常路徑 + 一個錯誤案例
- 金額計算用 `Decimal`，禁止 `float`
- 測試 DB 使用 Neon serverless（`TEST_DATABASE_URL` 定義在 `backend/.env`），不需要本機 Docker

### 執行測試
```bash
# 執行所有測試
cd backend && .venv/bin/python -m pytest tests/

# 執行特定測試
cd backend && .venv/bin/python -m pytest tests/test_expenses.py -v

# 查看覆蓋率
cd backend && .venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing
```

## 前端測試規範

### 測試結構
```typescript
// mobile/__tests__/lib/utils.test.ts
import { formatAmount } from '../../lib/utils';

describe('formatAmount', () => {
  it('should format currency correctly', () => {
    expect(formatAmount(1234.5)).toBe('1,234.50');
  });
});
```

### 執行測試
```bash
cd mobile && npx jest
cd mobile && npx jest --coverage
```

## 驗證清單

- [ ] 測試檔案放在正確目錄（backend/tests/ 或 mobile/__tests__/）
- [ ] 正常路徑和錯誤路徑都有測試
- [ ] 所有測試通過（pytest / jest）
- [ ] 無 TODO/FIXME 殘留在測試中
