# Build Your Own Splitewise - 後端安全掃描報告

**掃描日期**: 2026-04-02  
**掃描範圍**: 新增 P0 功能（消費分類、軟刪除、活動紀錄）  
**掃描工具**: 靜態代碼分析 + 手動授權邏輯檢查

---

## 執行摘要

發現 **7 個安全問題**，其中：
- **Critical (關鍵)**: 3 個
- **High (高)**: 3 個
- **Medium (中)**: 1 個

**建議行動**: 立即修復 Critical 和 High 級別問題。

---

## 詳細漏洞清單

### 1. 軟刪除不一致導致資料洩露 (Critical)

**檔案**: `backend/app/services/group_service.py`  
**行號**: 162, 176, 241-243  
**嚴重程度**: Critical

**問題**:
- `update_group()` (第 162 行) 未檢查 `deleted_at`，允許更新已刪除群組
- `delete_group()` (第 176 行) 未檢查 `deleted_at`，允許重複刪除或刪除已刪除群組
- `get_group_detail()` (第 241-243 行) 未過濾 `deleted_at`，允許直接存取已刪除群組資訊

**現象**:
```python
# update_group - 缺少 deleted_at.is_(None)
result = await db.execute(select(Group).where(Group.id == group_id))  # 應加上 deleted_at.is_(None)
group = result.scalar_one()

# get_group_detail - 缺少 deleted_at 過濾
result = await db.execute(
    select(Group)
    .where(Group.id == group_id)  # 應加上 deleted_at.is_(None)
    .options(...)
)
```

**攻擊場景**:
1. 使用者 A 刪除群組 X（設定 `deleted_at = now()`）
2. 使用者 A 繼續呼叫 `PATCH /groups/{group_id}` → 成功修改已刪除群組
3. 使用者 B 呼叫 `GET /groups/{group_id}` → 看到已刪除群組詳情

**修復**:
```python
# update_group - 第 162 行
result = await db.execute(
    select(Group).where(
        Group.id == group_id,
        Group.deleted_at.is_(None)  # 添加此行
    )
)

# get_group_detail - 第 242 行
result = await db.execute(
    select(Group)
    .where(Group.id == group_id, Group.deleted_at.is_(None))  # 添加 deleted_at 檢查
    .options(...)
)
```

---

### 2. Categories API 缺少群組成員驗證 (Critical)

**檔案**: `backend/app/api/categories.py`  
**行號**: 32-49 (POST), 52-69 (DELETE)  
**嚴重程度**: Critical

**問題**:
POST `/categories` 端點允許使用者為 **任意群組** 建立分類，無需驗證該使用者是否為群組成員。

**現象**:
```python
@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,  # data.group_id 未驗證
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = ExpenseCategory(
        name=data.name,
        icon=data.icon,
        color=data.color,
        group_id=data.group_id,  # 未檢查 user 是否屬於此 group
        is_default=False,
        created_by=current_user.id,
    )
```

**攻擊場景**:
1. 使用者 A 得知群組 X 的 ID（透過任何管道）
2. 使用者 A 呼叫 `POST /categories`，指定 `group_id=X`
3. 使用者 A 成功為 X 群組建立分類，即使不是 X 的成員

**修復**:
```python
@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 驗證使用者是否為群組成員
    if data.group_id:
        await check_membership(db, data.group_id, current_user.id)  # 添加此行
    
    category = ExpenseCategory(...)
```

**補充**:
DELETE `/categories/{category_id}` 端點雖檢查 `created_by`，但未驗證使用者是否為該分類所屬群組的成員，可能允許非成員的建立者刪除分類。

---

### 3. Categories DELETE 缺少群組成員驗證 (High)

**檔案**: `backend/app/api/categories.py`  
**行號**: 52-69  
**嚴重程度**: High

**問題**:
DELETE 端點驗證 `created_by == current_user.id` 但未驗證使用者是否為該分類所屬群組的成員。

**現象**:
```python
@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ...檢查 created_by...
    if category.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete category")
    
    # 但未驗證：current_user 是否為 category.group_id 的成員
    await db.delete(category)
```

**修復**:
```python
@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default category")
    if category.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete category")
    
    # 添加群組成員驗證
    if category.group_id:
        await check_membership(db, category.group_id, current_user.id)  # 添加此行
    
    await db.delete(category)
```

---

### 4. DEBUG 模式在生產環境中啟用 (Critical)

**檔案**: `backend/app/core/config.py`  
**行號**: 7  
**嚴重程度**: Critical

**問題**:
`DEBUG: bool = True` 在生產環境會洩露敏感資訊（完整 stack traces、環境變數等）。

**現象**:
```python
class Settings(BaseSettings):
    APP_NAME: str = "BYOSW"
    APP_SUBTITLE: str = "絕對免費，全部AI開發的分帳系統"
    DEBUG: bool = True  # ✗ 應為 False
```

**影響**:
- 未捕獲的例外返回完整 stack trace，洩露代碼路徑、資料庫結構、第三方服務端點
- 可能洩露環境變數或機密資訊

**修復**:
```python
class Settings(BaseSettings):
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"  # 由環境變數控制
```

在生產環境，應設置 `DEBUG=false`。

---

### 5. 硬編碼的 SECRET_KEY (Critical)

**檔案**: `backend/app/core/config.py`  
**行號**: 13  
**嚴重程度**: Critical

**問題**:
SECRET_KEY 寫死為預設值，所有部署實例使用相同密鑰，允許攻擊者偽造 JWT tokens。

**現象**:
```python
SECRET_KEY: str = "change-me-in-production-use-a-real-secret-key"
```

**攻擊場景**:
1. 攻擊者知道預設 SECRET_KEY
2. 攻擊者自簽署 JWT token，聲稱為任意使用者
3. FastAPI 驗證失敗，攻擊者獲得任意使用者存取權限

**修復**:
```python
class Settings(BaseSettings):
    SECRET_KEY: str = Field(
        ..., 
        description="Must be set in environment or .env file"
    )
    # 在 .env 中設置：
    # SECRET_KEY=your-random-secret-key-at-least-32-chars
```

---

### 6. CORS 配置過於寬鬆 (High)

**檔案**: `backend/app/core/config.py`  
**行號**: 28  
**嚴重程度**: High

**問題**:
`ALLOWED_ORIGINS: str = "*"` 允許任何域名發起跨域請求，可能導致 CSRF 攻擊。

**現象**:
```python
ALLOWED_ORIGINS: str = "*"
```

**攻擊場景**:
1. 使用者訪問惡意網站 `evil.com`
2. 該網站的 JavaScript 在使用者瀏覽器中發起 API 請求
3. 由於 CORS 允許所有來源，請求成功，攻擊者可造成使用者帳戶損害

**修復**:
```python
# 在 .env 中設置：
ALLOWED_ORIGINS=https://app.example.com,https://staging.example.com

# 禁止使用 "*"，改用具體域名列表
```

---

### 7. 活動紀錄可能記錄敏感資訊 (Medium)

**檔案**: `backend/app/services/activity_log_service.py`  
**行號**: 12-37  
**嚴重程度**: Medium

**問題**:
`log_activity()` 函式記錄 `description` 和 `extra_name` 欄位，可能洩露敏感資訊。

**現象**:
```python
async def log_activity(
    db: AsyncSession,
    group_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    description: str | None = None,  # 可能包含敏感資訊
    amount: Decimal | None = None,
    extra_name: str | None = None,  # 可能包含個人資訊
) -> None:
    log = ActivityLog(
        description=description,  # 例如：銀行帳號、信用卡號
        extra_name=extra_name,    # 例如：真實名稱
        amount=amount,
        # ...
    )
```

**風險**:
- 如果 `description` 來自使用者輸入未清理，可能記錄個人身份資訊（如銀行帳號）
- `extra_name` 洩露使用者真實名稱
- 活動紀錄被意外曝露時，歷史記錄中的敏感資訊無法恢復

**修復**:
```python
# 1. 驗證 description 不包含敏感資訊
# 2. 對敏感欄位進行脫敏（如 extra_name 只記錄首字母）
# 3. 不記錄完整金額，改用模糊化描述（如 "expense_added" 而非金額）

async def log_activity(...):
    # 清理 description，移除個人資訊
    sanitized_description = sanitize_description(description)
    
    log = ActivityLog(
        description=sanitized_description,
        extra_name=f"{extra_name[0]}..." if extra_name else None,
        amount=amount,  # 或設為 None 以防洩露
    )
```

---

## 額外發現

### A. 軟刪除檢查不一致

除了上述 3 個 Critical 問題外，以下函式也缺少 `deleted_at` 檢查：

| 函式 | 檔案 | 行號 | 風險 |
|------|------|------|------|
| `get_group_member_ids()` | group_service.py | 266 | 無法驗證群組是否被刪除 |
| `create_invite_token()` | group_service.py | 280 | 允許為已刪除群組產生邀請連結 |
| `revoke_invite_token()` | group_service.py | 297 | 允許撤銷已刪除群組的邀請 |
| `regenerate_invite_token()` | group_service.py | 308 | 允許為已刪除群組產生新邀請 |

**建議**: 統一在所有 `select(Group)` 查詢中加上 `Group.deleted_at.is_(None)` 條件。

### B. 資料庫連線字符串

`DEFAULT DATABASE_URL` 包含硬編碼的認證資訊（使用者 `splitewise`），應從環境變數載入。

---

## 修復優先順序

### P0 (立即修復 - 安全阻擋)

1. **SECRET_KEY 硬編碼** → 使用隨機生成的密鑰
2. **DEBUG=True** → 改為 False
3. **Categories API 缺少群組驗證** → 添加 `check_membership()`
4. **軟刪除檢查不一致** → 統一在所有 Group 查詢中添加 `deleted_at` 過濾

### P1 (高優先 - 本周修復)

5. **CORS 過於寬鬆** → 設置具體域名白名單
6. **Categories DELETE 缺少群組驗證** → 添加成員檢查
7. **活動紀錄敏感資訊** → 實施脫敏政策

---

## 測試建議

修復後應執行以下測試：

```bash
# 1. 軟刪除一致性測試
pytest tests/test_soft_delete.py -v

# 2. 授權測試
pytest tests/test_authorization.py -v

# 3. 完整回歸測試
pytest tests/ -v

# 4. 手動測試已刪除群組存取
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/v1/groups/{deleted_group_id}
# 應返回 404，不是 200 或 403
```

---

## 結論

新增的 P0 功能（消費分類、軟刪除、活動紀錄）存在 **3 個 Critical 安全漏洞**，需立即修復：

1. ✗ 軟刪除邏輯不一致，允許存取已刪除資源
2. ✗ Categories API 缺少群組成員驗證
3. ✗ 硬編碼密鑰和 DEBUG 模式洩露敏感資訊

**建議**: 暫停部署，修復上述問題後重新提交代碼審查。

