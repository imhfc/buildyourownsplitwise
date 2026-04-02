# Product Requirement Document (PRD)

## Build Your Own Splitewise -- 分帳應用程式

| 項目     | 內容                                      |
| -------- | ----------------------------------------- |
| 文件版本 | v1.0                                      |
| 建立日期 | 2026-03-30                                |
| 產品名稱 | Build Your Own Splitewise (BYOSW)         |
| 目標平台 | iOS / Android (React Native) + Web + API  |
| 技術棧   | Expo + React Native + FastAPI + PostgreSQL |

---

## 1. 產品願景與目標

### 1.1 產品願景

打造一款功能完整的分帳應用程式，讓使用者能夠輕鬆記錄、分攤、結算與朋友或群組間的共同消費，消除人際間因金錢產生的尷尬與摩擦。

### 1.2 核心目標

1. **簡化分帳流程** -- 使用者能在 10 秒內完成一筆消費的記錄與分攤
2. **最小化交易次數** -- 透過債務簡化演算法，將群組內的多筆債務整合為最少的轉帳次數
3. **多幣別支援** -- 支援跨國旅遊場景下的多幣別消費與自動匯率換算
4. **即時同步** -- 所有參與者能即時看到消費與餘額的變動
5. **跨平台一致體驗** -- Mobile App 與 Web 介面提供一致的使用者體驗

### 1.3 目標使用者

| 使用者類型 | 描述                                     | 核心需求                     |
| ---------- | ---------------------------------------- | ---------------------------- |
| 室友       | 共同居住、分攤房租與生活開支             | 定期帳單分攤、自動提醒       |
| 旅伴       | 出國旅遊時的共同消費                     | 多幣別支援、離線記帳         |
| 情侶       | 日常約會消費分攤                         | 簡單快速記帳、隱私性         |
| 聚餐群組   | 朋友間的餐廳消費分帳                     | 收據掃描、逐項分攤           |
| 專案團隊   | 工作相關的共同開支（差旅費、物資採購）   | 分類報表、CSV 匯出           |

---

## 2. 功能需求總覽

### 2.1 功能優先級定義

| 優先級 | 標籤   | 說明                                   |
| ------ | ------ | -------------------------------------- |
| P0     | 必備   | 產品上線的最低可行功能（MVP）          |
| P1     | 重要   | 上線後首次重大更新                     |
| P2     | 期望   | 提升使用者體驗與黏著度                 |
| P3     | 進階   | Premium 功能或未來規劃                 |

### 2.2 功能矩陣

| 模組               | 功能                     | 優先級 | 備註                         |
| ------------------ | ------------------------ | ------ | ---------------------------- |
| 使用者與認證       | 註冊 / 登入              | P0     | 已完成                       |
| 使用者與認證       | Google OAuth 登入         | P0     | 已完成                       |
| 使用者與認證       | JWT Token 管理            | P0     | 已完成                       |
| 使用者與認證       | 個人檔案管理              | P1     |                              |
| 使用者與認證       | 頭像上傳                  | P1     | 由 P2 提升                   |
| 好友系統           | 新增 / 移除好友           | P0     | 已完成                       |
| 好友系統           | 好友搜尋（Email / 暱稱） | P0     | 已完成                       |
| 好友系統           | 好友邀請與通知            | P1     |                              |
| 好友系統           | 非註冊好友（Email 邀請）  | P1     | 由 P2 提升                   |
| 群組管理           | 建立 / 編輯 / 刪除群組   | P0     | 已完成                       |
| 群組管理           | 邀請成員加入群組          | P0     | 已完成                       |
| 群組管理           | 群組類型分類              | P2     | 由 P1 降低                   |
| 群組管理           | 群組封面照片              | P1     | 由 P2 提升                   |
| 群組管理           | 群組簡化債務開關          | P1     |                              |
| 消費記錄           | 新增 / 編輯 / 刪除消費   | P0     | 已完成                       |
| 消費記錄           | 多種分帳方式              | P0     | 已完成                       |
| 消費記錄           | 消費分類                  | P0     | 已完成                       |
| 消費記錄           | 多人付款                  | P1     |                              |
| 消費記錄           | 附加備註與照片            | P1     |                              |
| 消費記錄           | 週期性消費                | P2     | 由 P1 降低                   |
| 消費記錄           | 收據掃描（OCR）           | P3     |                              |
| 消費記錄           | 逐項分攤（Itemization）  | P3     |                              |
| 分帳計算           | 均分                      | P0     | 已完成                       |
| 分帳計算           | 指定金額                  | P0     | 已完成                       |
| 分帳計算           | 百分比分帳                | P0     | 已完成                       |
| 分帳計算           | 份數分帳                  | P1     |                              |
| 分帳計算           | 調整分帳                  | P3     | 由 P2 降低，暫不規劃         |
| 餘額與結算         | 即時餘額計算              | P0     | 已完成                       |
| 餘額與結算         | 債務簡化演算法            | P0     | 已完成                       |
| 餘額與結算         | 記錄結算                  | P0     | 已完成                       |
| 餘額與結算         | 整合支付平台              | P3     |                              |
| 多幣別             | 消費幣別選擇              | P0     | 已完成                       |
| 多幣別             | 自動匯率換算              | P1     |                              |
| 多幣別             | 群組預設幣別              | P1     |                              |
| 通知系統           | Push 推播通知             | P1     |                              |
| 通知系統           | Email 通知                | P2     |                              |
| 通知系統           | 付款提醒                  | P1     |                              |
| 活動紀錄           | 消費異動歷程              | P0     | 已完成                       |
| 活動紀錄           | 評論功能                  | P3     | 由 P2 降低，暫不規劃         |
| 活動紀錄           | 編輯歷史追蹤              | P2     |                              |
| 報表與分析         | 消費分類統計              | P3     | 由 P2 降低，暫不規劃         |
| 報表與分析         | 月度趨勢圖表              | P3     | 由 P2 降低，暫不規劃         |
| 報表與分析         | CSV / JSON 匯出           | P3     | 由 P2 降低，暫不規劃         |
| 系統               | 多語系（i18n）            | P0     | 已完成                       |
| 系統               | 深色模式（視覺重設計）    | P1     | 已有基礎，需重新設計為高級質感 |
| 系統               | 離線模式                  | P3     |                              |

---

## 3. 詳細功能規格

### 3.1 使用者與認證模組

#### 3.1.1 註冊 (P0)

**描述**：使用者可透過 Email + 密碼或 Google OAuth 建立帳號。

**功能需求**：

- 支援 Email + 密碼註冊
  - Email 格式驗證
  - 密碼強度要求：至少 8 字元，包含大小寫字母與數字
  - Email 唯一性檢查
- 支援 Google OAuth 2.0 登入/註冊
  - 首次 OAuth 登入自動建立帳號
  - 綁定 Google 帳號的 Email 作為主要 Email
- 註冊欄位：
  - Email（必填）
  - 密碼（必填，OAuth 除外）
  - 顯示名稱（必填）
  - 預設幣別（選填，預設 TWD）

**驗收條件**：

- [ ] 使用者可透過 Email + 密碼成功註冊
- [ ] 重複 Email 註冊回傳 409 Conflict
- [ ] 密碼以 bcrypt 雜湊儲存，原文不落地
- [ ] Google OAuth 首次登入自動建立帳號
- [ ] 註冊成功後自動發放 JWT Token

#### 3.1.2 登入 (P0)

**描述**：使用者可透過 Email + 密碼或 Google OAuth 登入。

**功能需求**：

- Email + 密碼登入
  - 登入失敗回傳通用錯誤訊息（防止帳號枚舉）
  - 登入成功發放 access token（30 分鐘）+ refresh token（7 天）
- Google OAuth 登入
  - 已綁定帳號直接登入
  - 未綁定帳號跳轉註冊流程
- Token 刷新機制
  - 使用 refresh token 取得新的 access token
  - Refresh token rotation（每次刷新同時更換 refresh token）

**驗收條件**：

- [ ] 正確帳密可成功登入並取得 JWT
- [ ] 錯誤帳密回傳 401 Unauthorized
- [ ] Access token 過期後可用 refresh token 換發新 token
- [ ] Refresh token 過期後需重新登入

#### 3.1.3 個人檔案管理 (P1)

**描述**：使用者可檢視與編輯個人資料。

**功能需求**：

- 可編輯欄位：
  - 顯示名稱
  - 預設幣別
  - 語言偏好（zh-TW / en / ja）
  - 色系偏好
- 頭像上傳（P2）
  - 支援 JPG / PNG，最大 5MB
  - 自動裁切為正方形、壓縮至 256x256

**API 端點**：

```
GET    /api/v1/users/me
PATCH  /api/v1/users/me
POST   /api/v1/users/me/avatar    (P2)
```

---

### 3.2 好友系統模組

#### 3.2.1 好友管理 (P0)

**描述**：使用者可以新增好友，在好友之間記錄非群組的消費。

**功能需求**：

- 透過 Email 搜尋已註冊使用者
- 發送好友請求
- 接受 / 拒絕好友請求
- 移除好友（需雙方餘額為 0）
- 好友列表顯示各好友的淨餘額摘要
- 非註冊使用者的 Email 邀請（P2）
  - 發送邀請 Email
  - 受邀者註冊後自動建立好友關係
  - 邀請狀態追蹤（待回應 / 已接受 / 已過期）

**資料模型**：

```
friendships
├── id (PK)
├── user_id (FK → users)
├── friend_id (FK → users)
├── status (pending / accepted / rejected)
├── created_at
└── updated_at
```

**API 端點**：

```
GET    /api/v1/friends                    # 好友列表（含餘額摘要）
POST   /api/v1/friends/requests           # 發送好友請求
GET    /api/v1/friends/requests           # 待處理的好友請求
PATCH  /api/v1/friends/requests/{id}      # 接受 / 拒絕
DELETE /api/v1/friends/{friend_id}        # 移除好友
GET    /api/v1/friends/search?q={email}   # 搜尋使用者
```

**驗收條件**：

- [ ] 可透過 Email 搜尋並發送好友請求
- [ ] 對方可接受或拒絕請求
- [ ] 好友列表正確顯示淨餘額
- [ ] 有未結清餘額時無法移除好友

---

### 3.3 群組管理模組

#### 3.3.1 群組 CRUD (P0)

**描述**：使用者可建立群組，邀請成員共同記帳。

**功能需求**：

- 建立群組
  - 群組名稱（必填，最長 100 字元）
  - 群組類型（P1）：旅行、室友、情侶、聚餐、工作、其他
  - 群組預設幣別
  - 簡化債務開關（預設開啟）
- 編輯群組設定
  - 修改名稱、類型、幣別
  - 上傳封面照片（P2）
- 刪除群組
  - 僅建立者可刪除
  - 所有餘額必須為 0 才能刪除
  - 軟刪除（設定 deleted_at）
- 成員管理
  - 邀請成員（透過 Email 或好友列表）
  - 移除成員（該成員餘額需為 0）
  - 成員退出群組（自身餘額需為 0）
  - 任何成員皆可新增/移除成員（wiki 模式，無管理員角色）

**資料模型**：

```
groups
├── id (PK)
├── name (VARCHAR 100, NOT NULL)
├── group_type (ENUM: trip/roommates/couple/dining/work/other)
├── default_currency (VARCHAR 3, DEFAULT 'TWD')
├── simplify_debts (BOOLEAN, DEFAULT true)
├── cover_image_url (VARCHAR, NULLABLE)
├── created_by (FK → users)
├── created_at
├── updated_at
└── deleted_at (NULLABLE, 軟刪除)

group_members
├── id (PK)
├── group_id (FK → groups)
├── user_id (FK → users)
├── joined_at
└── left_at (NULLABLE)
```

**API 端點**：

```
POST   /api/v1/groups                          # 建立群組
GET    /api/v1/groups                          # 使用者的群組列表
GET    /api/v1/groups/{group_id}               # 群組詳情（含成員與餘額）
PATCH  /api/v1/groups/{group_id}               # 編輯群組
DELETE /api/v1/groups/{group_id}               # 刪除群組
POST   /api/v1/groups/{group_id}/members       # 邀請成員
DELETE /api/v1/groups/{group_id}/members/{uid}  # 移除成員
POST   /api/v1/groups/{group_id}/leave         # 退出群組
```

**驗收條件**：

- [ ] 可建立群組並邀請成員
- [ ] 群組列表正確顯示各群組的淨餘額摘要
- [ ] 有未結清餘額的成員無法被移除或自行退出
- [ ] 所有餘額為 0 時才可刪除群組
- [ ] 任何成員均可編輯群組設定（wiki 模式）

---

### 3.4 消費記錄模組

#### 3.4.1 新增消費 (P0)

**描述**：使用者可記錄一筆消費並指定分攤方式。

**功能需求**：

- 消費基本資訊
  - 描述（必填，最長 255 字元）
  - 金額（必填，Decimal(12,2)，必須大於 0）
  - 幣別（必填，預設為群組幣別或使用者預設幣別）
  - 日期（必填，預設為今天）
  - 分類（必填，預設「一般」）
  - 備註（選填，最長 500 字元）
  - 照片/收據附件（P1，最多 5 張）
- 付款人
  - 單一付款人（P0）：從群組成員中選擇
  - 多人付款（P1）：多人各付不同金額，總和必須等於消費金額
- 分攤對象
  - 預設為群組全部成員
  - 可選擇子集成員參與分攤
- 分攤方式（詳見 3.5 節）

**資料模型**：

```
expenses
├── id (PK)
├── group_id (FK → groups, NULLABLE -- 非群組消費)
├── description (VARCHAR 255, NOT NULL)
├── amount (NUMERIC 12,2, NOT NULL)
├── currency (VARCHAR 3, NOT NULL)
├── expense_date (DATE, NOT NULL)
├── category_id (FK → expense_categories)
├── split_type (ENUM: equal/exact/percentage/shares/adjustment)
├── note (TEXT, NULLABLE)
├── created_by (FK → users)
├── created_at
├── updated_at
└── deleted_at (NULLABLE)

expense_payers
├── id (PK)
├── expense_id (FK → expenses)
├── user_id (FK → users)
└── amount (NUMERIC 12,2, NOT NULL)

expense_splits
├── id (PK)
├── expense_id (FK → expenses)
├── user_id (FK → users)
├── amount (NUMERIC 12,2, NOT NULL)        # 最終應付金額
├── percentage (NUMERIC 5,2, NULLABLE)     # 百分比（若適用）
└── shares (INTEGER, NULLABLE)             # 份數（若適用）

expense_attachments  (P1)
├── id (PK)
├── expense_id (FK → expenses)
├── file_url (VARCHAR, NOT NULL)
├── file_type (VARCHAR 10)
├── uploaded_by (FK → users)
└── created_at
```

**消費分類清單**：

| 分類       | 圖示 | 子分類                             |
| ---------- | ---- | ---------------------------------- |
| 餐飲       | --   | 早餐、午餐、晚餐、飲料、外送       |
| 交通       | --   | 計程車、大眾運輸、油資、停車費      |
| 住宿       | --   | 飯店、民宿、房租                   |
| 生活       | --   | 水電瓦斯、網路、日用品、家具        |
| 娛樂       | --   | 電影、KTV、遊樂園、演唱會          |
| 購物       | --   | 服飾、3C、超市、雜貨               |
| 旅遊       | --   | 門票、紀念品、導遊                 |
| 醫療       | --   | 掛號費、藥品                       |
| 教育       | --   | 書籍、課程、學費                   |
| 其他       | --   | 未分類                             |

**API 端點**：

```
POST   /api/v1/groups/{group_id}/expenses          # 建立群組消費
GET    /api/v1/groups/{group_id}/expenses          # 群組消費列表（分頁）
GET    /api/v1/expenses/{expense_id}               # 消費詳情
PATCH  /api/v1/expenses/{expense_id}               # 編輯消費
DELETE /api/v1/expenses/{expense_id}               # 刪除消費（軟刪除）
POST   /api/v1/expenses/{expense_id}/attachments   # 上傳附件 (P1)
POST   /api/v1/friends/{friend_id}/expenses        # 建立非群組消費
GET    /api/v1/expenses/categories                 # 分類列表
```

**驗收條件**：

- [ ] 可建立消費並選擇分攤方式
- [ ] 所有分攤金額總和必須等於消費金額
- [ ] 多人付款的付款金額總和必須等於消費金額
- [ ] 僅群組成員可對該群組新增消費
- [ ] 消費建立後即時更新所有相關使用者的餘額
- [ ] 編輯/刪除消費後正確重算餘額

#### 3.4.2 週期性消費 (P1)

**描述**：使用者可建立自動重複的消費（如月租金、訂閱費用）。

**功能需求**：

- 支援的重複頻率：
  - 每週
  - 每兩週
  - 每月
  - 每年
- 可設定起始日期與結束日期（選填）
- 系統在指定日期自動建立消費記錄
- 可隨時暫停或終止週期性消費
- 編輯範圍選擇：僅修改此次 / 修改此次及未來所有

**資料模型**：

```
recurring_expenses
├── id (PK)
├── expense_template (JSONB -- 消費模板，含所有消費欄位)
├── frequency (ENUM: weekly/biweekly/monthly/yearly)
├── start_date (DATE, NOT NULL)
├── end_date (DATE, NULLABLE)
├── next_occurrence (DATE, NOT NULL)
├── is_active (BOOLEAN, DEFAULT true)
├── created_by (FK → users)
├── created_at
└── updated_at
```

---

### 3.5 分帳計算模組

#### 3.5.1 均分 (Equal Split) -- P0

**描述**：消費金額平均分攤給所有參與者。

**計算邏輯**：

```
每人應付 = 總金額 / 參與人數
餘數（四捨五入差異）= 總金額 - (每人應付 * 參與人數)
→ 差額歸付款人承擔
```

**範例**：
- 總金額 NT$100，3 人均分
- 每人 NT$33.33，剩餘 NT$0.01 由付款人承擔
- 結果：付款人負擔 NT$33.34，其餘每人 NT$33.33

#### 3.5.2 指定金額 (Exact Amount) -- P0

**描述**：手動指定每位參與者應付的精確金額。

**驗證規則**：

- 所有參與者的指定金額總和必須**精確等於**消費總金額
- 每位參與者的金額必須 >= 0
- 至少一位參與者的金額 > 0

#### 3.5.3 百分比分帳 (Percentage Split) -- P0

**描述**：以百分比分配消費金額。

**驗證規則**：

- 所有參與者的百分比總和必須**精確等於 100%**
- 每位參與者的百分比必須 >= 0
- 實際金額 = 總金額 * 百分比 / 100，四捨五入至小數第二位
- 四捨五入產生的差額歸付款人承擔

#### 3.5.4 份數分帳 (Shares Split) -- P1

**描述**：以份數比例分配消費金額，適用於依使用量分攤的場景。

**計算邏輯**：

```
每份金額 = 總金額 / 總份數
某人應付 = 每份金額 * 該人份數
```

**範例**：
- 住宿 NT$3,000，A 住 2 晚、B 住 1 晚、C 住 3 晚
- 總份數 = 6，每份 = NT$500
- A: NT$1,000、B: NT$500、C: NT$1,500

#### 3.5.5 調整分帳 (Adjustment Split) -- P2

**描述**：以均分為基準，對個別參與者做金額增減。

**計算邏輯**：

```
基準金額 = (總金額 - 調整金額總和) / 參與人數
某人應付 = 基準金額 + 該人調整金額
```

**範例**：
- 晚餐 NT$1,000，3 人，A 多點了 NT$200 的菜
- 調整後：A 多 +NT$200
- 基準 = (1000 - 200) / 3 = NT$266.67
- A: NT$466.67、B: NT$266.67、C: NT$266.66

---

### 3.6 餘額與結算模組

#### 3.6.1 餘額計算 (P0)

**描述**：即時計算使用者在各群組和好友間的淨餘額。

**計算邏輯**：

```
使用者 X 在群組 G 中的淨餘額 =
  X 在 G 中所有消費的付款總額 - X 在 G 中所有消費的應付總額
  + X 在 G 中收到的結算總額 - X 在 G 中支出的結算總額

正數 = 其他人欠 X
負數 = X 欠其他人
```

**顯示層級**：

| 層級       | 說明                                       |
| ---------- | ------------------------------------------ |
| 總覽       | 使用者在所有群組/好友的淨餘額加總          |
| 群組層     | 使用者在特定群組中對各成員的淨餘額         |
| 好友層     | 使用者與特定好友在所有群組 + 非群組的淨餘額 |
| 明細       | 特定兩人之間每一筆消費的分攤明細           |

**API 端點**：

```
GET /api/v1/balances                               # 總餘額摘要
GET /api/v1/groups/{group_id}/balances             # 群組內餘額
GET /api/v1/friends/{friend_id}/balances           # 與好友的餘額
GET /api/v1/balances/detail?user_id={id}           # 與特定人的明細
```

#### 3.6.2 債務簡化演算法 (P0)

**描述**：將群組內的多筆複雜債務關係簡化為最少的轉帳次數。

**演算法概述**：

1. **計算淨餘額**：算出每位成員的淨現金流（所有收入 - 所有支出）
2. **分類**：將成員分為債權人（淨正值）與債務人（淨負值）
3. **貪婪匹配**：使用 max-heap 將最大債務人與最大債權人配對
4. **生成轉帳清單**：輸出最小化的轉帳指令

**範例**：

原始債務：
```
A 欠 B: NT$100
B 欠 C: NT$80
A 欠 C: NT$50
```

簡化後：
```
A 付 B: NT$20
A 付 C: NT$130
```
（從 3 筆交易簡化為 2 筆）

**注意事項**：

- 此問題為 NP-Complete（等價於子集合加總問題）
- 使用貪婪啟發式演算法取得近似最佳解
- 群組設定中可開關「簡化債務」功能
- 關閉時，顯示原始的一對一債務關係

#### 3.6.3 結算（Settle Up）(P0)

**描述**：記錄成員間的實際付款，清除債務。

**功能需求**：

- 選擇付款對象
- 輸入結算金額
- 選擇結算方式（現金、轉帳、第三方支付）
- 結算後即時更新雙方餘額
- 支援部分結算（不必一次還清）
- 結算紀錄可被刪除（例如對方實際未收到款項）

**資料模型**：

```
settlements
├── id (PK)
├── group_id (FK → groups, NULLABLE)
├── payer_id (FK → users, NOT NULL)        # 付款人
├── payee_id (FK → users, NOT NULL)        # 收款人
├── amount (NUMERIC 12,2, NOT NULL)
├── currency (VARCHAR 3, NOT NULL)
├── settlement_method (ENUM: cash/transfer/third_party)
├── note (TEXT, NULLABLE)
├── settled_at (TIMESTAMP, NOT NULL)
├── created_by (FK → users)
├── created_at
└── deleted_at (NULLABLE)
```

**API 端點**：

```
POST   /api/v1/groups/{group_id}/settlements       # 群組內結算
POST   /api/v1/friends/{friend_id}/settlements     # 好友間結算
GET    /api/v1/settlements                         # 結算紀錄列表
DELETE /api/v1/settlements/{settlement_id}         # 刪除結算
```

**驗收條件**：

- [ ] 可記錄結算並即時更新餘額
- [ ] 支援部分結算
- [ ] 結算金額必須 > 0
- [ ] 付款人與收款人不可為同一人
- [ ] 刪除結算後正確回滾餘額

---

### 3.7 多幣別模組

#### 3.7.1 幣別支援 (P0)

**描述**：支援多種幣別的消費記錄。

**功能需求**：

- 支援至少以下常用幣別：

| 幣別代碼 | 名稱       |
| -------- | ---------- |
| TWD      | 新台幣     |
| USD      | 美元       |
| EUR      | 歐元       |
| JPY      | 日圓       |
| KRW      | 韓元       |
| CNY      | 人民幣     |
| GBP      | 英鎊       |
| THB      | 泰銖       |
| HKD      | 港幣       |
| SGD      | 新加坡幣   |
| AUD      | 澳幣       |
| CAD      | 加幣       |

- 每筆消費可獨立指定幣別
- 群組可設定預設幣別
- 使用者個人可設定預設幣別

#### 3.7.2 匯率換算 (P1)

**描述**：自動取得即時匯率，將不同幣別的消費統一換算為使用者偏好幣別顯示餘額。

**功能需求**：

- 匯率來源：台灣銀行牌告匯率（主要）/ Open Exchange Rates（備援）
- 匯率快取：Redis 快取，每小時更新一次
- 餘額顯示時自動換算為使用者偏好幣別
- 消費記錄保留原始幣別與金額（不做永久轉換）
- 匯率換算僅用於「顯示」用途，實際結算以原始幣別為準

**資料模型**：

```
exchange_rates
├── id (PK)
├── base_currency (VARCHAR 3, NOT NULL)
├── target_currency (VARCHAR 3, NOT NULL)
├── rate (NUMERIC 12,6, NOT NULL)
├── source (VARCHAR 50)                    # 'tbank' / 'openexchangerates'
├── fetched_at (TIMESTAMP, NOT NULL)
└── UNIQUE(base_currency, target_currency, fetched_at)
```

---

### 3.8 通知系統模組

#### 3.8.1 應用內通知 (P1)

**描述**：在 App 內顯示即時通知。

**觸發事件**：

| 事件                     | 通知內容範例                            |
| ------------------------ | --------------------------------------- |
| 被加入群組               | 「{user} 邀請你加入 {group}」           |
| 群組新增消費             | 「{user} 在 {group} 新增了 NT$500」     |
| 消費被編輯               | 「{user} 編輯了 {expense}」             |
| 消費被刪除               | 「{user} 刪除了 {expense}」             |
| 收到結算                 | 「{user} 向你付了 NT$300」              |
| 好友請求                 | 「{user} 想加你為好友」                 |
| 付款提醒                 | 「{user} 提醒你結清 NT$500」            |
| 週期性消費建立           | 「自動建立了 {expense}」                |

#### 3.8.2 Push 推播 (P1)

**功能需求**：

- 使用 Expo Push Notifications
- 使用者可自訂通知偏好（開/關各類通知）
- 靜音時段設定

#### 3.8.3 付款提醒 (P1)

**描述**：使用者可向欠款者發送提醒。

**功能需求**：

- 一鍵發送提醒（限制頻率：同一對象每 24 小時最多 1 次）
- 提醒包含欠款金額與明細連結
- 提醒紀錄留存

---

### 3.9 活動紀錄模組

#### 3.9.1 活動動態牆 (P0)

**描述**：以時間軸顯示群組內的所有活動。

**功能需求**：

- 顯示以下活動類型：
  - 消費新增 / 編輯 / 刪除
  - 結算紀錄
  - 成員加入 / 離開
  - 群組設定變更
- 按時間倒序排列
- 支援分頁載入（infinite scroll）
- 每筆活動顯示操作者、時間、變更摘要

**資料模型**：

```
activity_logs
├── id (PK)
├── group_id (FK → groups, NULLABLE)
├── user_id (FK → users)
├── action_type (ENUM: expense_created/expense_updated/expense_deleted/
│                      settlement_created/settlement_deleted/
│                      member_joined/member_left/group_updated)
├── target_type (VARCHAR 50)        # 'expense' / 'settlement' / 'group'
├── target_id (INTEGER)
├── metadata (JSONB)                # 變更前後的差異
├── created_at
└── INDEX(group_id, created_at DESC)
```

**API 端點**：

```
GET /api/v1/activity                               # 使用者的所有活動
GET /api/v1/groups/{group_id}/activity             # 群組活動
```

#### 3.9.2 評論功能 (P2)

**描述**：使用者可在消費下方留言討論。

**功能需求**：

- 文字評論（最長 500 字元）
- 評論通知（通知消費相關人員）
- 刪除自己的評論

**資料模型**：

```
comments
├── id (PK)
├── expense_id (FK → expenses)
├── user_id (FK → users)
├── content (TEXT, NOT NULL, MAX 500)
├── created_at
└── deleted_at (NULLABLE)
```

#### 3.9.3 編輯歷史追蹤 (P2)

**描述**：記錄消費的每次修改，方便群組成員查證。

**功能需求**：

- 記錄修改前後的差異（金額、分攤方式、描述等）
- 顯示修改者與修改時間
- 支援還原至特定版本

---

### 3.10 報表與分析模組 (P2)

#### 3.10.1 消費統計

**功能需求**：

- 依分類的消費佔比圓餅圖
- 月度消費趨勢折線圖
- 可篩選時間範圍（本月、上月、自訂）
- 可篩選群組
- 顯示總支出、總收入、淨餘額

#### 3.10.2 資料匯出

**功能需求**：

- CSV 匯出
  - 群組層級匯出
  - 包含欄位：日期、描述、金額、幣別、付款人、分攤明細、分類
- JSON 完整備份（P3）
  - 匯出使用者所有資料
  - 包含消費、結算、群組、好友等

**API 端點**：

```
GET /api/v1/groups/{group_id}/export?format=csv    # CSV 匯出
GET /api/v1/reports/summary?period=monthly         # 月度摘要
GET /api/v1/reports/by-category?from=&to=          # 分類統計
GET /api/v1/users/me/export                        # 完整備份 (P3)
```

---

### 3.11 多語系模組 (P0)

#### 3.11.1 語系支援

**支援語系**：

| 語系代碼 | 語言     |
| -------- | -------- |
| zh-TW    | 繁體中文 |
| en       | English  |
| ja       | 日本語   |

**功能需求**：

- 所有使用者可見文字透過 i18next 的 `t()` 函式取得
- 語系切換即時生效，無需重啟
- 後端錯誤訊息根據使用者語系偏好回傳
- 日期、數字、幣別格式依語系自動調整

---

## 4. 非功能需求

### 4.1 效能

| 指標                 | 目標值                        |
| -------------------- | ----------------------------- |
| API 回應時間（P95）  | < 200ms                       |
| 頁面載入時間         | < 3 秒（首次）、< 1 秒（後續）|
| 餘額計算延遲         | < 100ms                       |
| 並發使用者數         | 支援 100 同時在線使用者       |
| 資料庫查詢           | 禁止 N+1 查詢                 |

### 4.2 安全性

| 項目                 | 規範                                          |
| -------------------- | --------------------------------------------- |
| 認證                 | JWT Bearer Token（access 30m + refresh 7d）   |
| 密碼儲存             | bcrypt 雜湊，禁止明文                         |
| 輸入驗證             | Pydantic schema 驗證所有輸入                  |
| SQL 注入防護         | SQLAlchemy 參數化查詢                         |
| XSS 防護             | React 自動跳脫 + CSP Header                   |
| CORS                 | 僅允許前端域名                                |
| 資源授權             | 每次操作驗證使用者對資源的存取權限            |
| 敏感資料             | .env 不入版控、JWT Secret 不寫死              |
| HTTPS                | 生產環境強制 HTTPS                            |

### 4.3 可靠性

| 項目                 | 目標                            |
| -------------------- | ------------------------------- |
| 可用性               | 99.5% uptime                    |
| 資料一致性           | 金額計算使用 Decimal，禁止 float |
| 資料備份             | 每日自動備份 PostgreSQL          |
| 錯誤處理             | 統一錯誤回應格式、前端顯示錯誤訊息 |
| 軟刪除               | 消費、群組、結算支援軟刪除與恢復  |

### 4.4 可擴展性

| 項目                 | 規範                                  |
| -------------------- | ------------------------------------- |
| API 版本化           | 路徑前綴 `/api/v1/`                   |
| 資料庫遷移           | Alembic 管理，禁止修改已有 migration  |
| 模組化架構           | Clean Architecture 分層               |
| 快取策略             | Redis 快取匯率、session 等高頻存取資料 |

### 4.5 可測試性

| 項目                 | 規範                                       |
| -------------------- | ------------------------------------------ |
| 後端測試覆蓋率       | 核心業務邏輯 > 80%                         |
| 整合測試             | 每個 API 端點至少 1 正常路徑 + 1 錯誤案例  |
| 測試資料庫           | 獨立 PostgreSQL（port 5433）               |
| CI 自動化            | GitHub Actions 自動執行測試                |

---

## 5. 使用者流程

### 5.1 首次使用流程

```
開啟 App
  → 註冊頁面（Email + 密碼 或 Google OAuth）
  → 設定顯示名稱與預設幣別
  → 首頁（空白狀態，引導建立群組或新增好友）
  → 建立第一個群組
  → 邀請成員
  → 新增第一筆消費
  → 查看餘額
```

### 5.2 日常記帳流程

```
首頁
  → 選擇群組
  → 點擊「新增消費」
  → 輸入描述、金額
  → 選擇付款人
  → 選擇分攤方式與對象
  → 儲存
  → 自動更新餘額並通知群組成員
```

### 5.3 結算流程

```
群組頁面
  → 查看餘額
  → 點擊「結算」
  → 系統建議最佳結算方案（簡化債務）
  → 選擇結算對象
  → 輸入/確認金額
  → 選擇付款方式
  → 儲存結算紀錄
  → 自動更新餘額
```

### 5.4 查看報表流程

```
「我的」頁面
  → 點擊「消費統計」
  → 選擇時間範圍
  → 查看分類佔比圓餅圖
  → 查看月度趨勢
  → 匯出 CSV
```

---

## 6. 技術架構

### 6.1 系統架構圖

```
                    ┌─────────────┐
                    │   Mobile    │
                    │  (Expo/RN)  │
                    └──────┬──────┘
                           │ HTTPS
                    ┌──────▼──────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   FastAPI   │
                    │  (Backend)  │
                    └──┬──────┬───┘
                       │      │
              ┌────────▼┐  ┌──▼────────┐
              │PostgreSQL│  │   Redis   │
              │  (Data)  │  │  (Cache)  │
              └──────────┘  └───────────┘
```

### 6.2 技術棧詳細

| 層級       | 技術                                        | 用途              |
| ---------- | ------------------------------------------- | ----------------- |
| 前端框架   | React Native + Expo                          | 跨平台 Mobile App |
| 樣式       | NativeWind (TailwindCSS)                     | UI 樣式           |
| 狀態管理   | Zustand                                      | 全域狀態          |
| 國際化     | i18next + react-i18next                      | 多語系            |
| 後端框架   | FastAPI                                      | REST API          |
| ORM        | SQLAlchemy (async)                           | 資料庫操作        |
| 資料庫     | PostgreSQL 16                                | 主要資料儲存      |
| 快取       | Redis 7                                      | 匯率快取、session |
| 認證       | python-jose (JWT) + passlib (bcrypt)         | 使用者認證        |
| 資料遷移   | Alembic                                      | Schema 版控       |
| 容器化     | Docker Compose                               | 部署環境          |
| CI/CD      | GitHub Actions                               | 自動測試與部署    |
| 雲端資料庫 | Neon (PostgreSQL)                            | 生產環境 DB       |
| 雲端主機   | GCP VM                                       | 應用程式伺服器    |

---

## 7. 里程碑規劃

### Phase 1 -- MVP（P0 功能）

**目標**：可用的最小可行產品

| 功能                              | 狀態 |
| --------------------------------- | ---- |
| 使用者註冊 / 登入（含 Google）    | --   |
| 群組 CRUD + 成員管理              | --   |
| 消費 CRUD                         | --   |
| 均分 / 指定金額 / 百分比分帳      | --   |
| 餘額計算與顯示                    | --   |
| 債務簡化演算法                    | --   |
| 結算功能                          | --   |
| 多幣別消費記錄                    | --   |
| 活動動態牆                        | --   |
| 多語系（zh-TW / en / ja）         | --   |

### Phase 2 -- 完善體驗（P1 功能）

**目標**：提升使用者體驗與功能完整度

| 功能                   | 狀態 |
| ---------------------- | ---- |
| 好友系統               | --   |
| 個人檔案管理           | --   |
| 多人付款               | --   |
| 份數分帳               | --   |
| 自動匯率換算           | --   |
| 週期性消費             | --   |
| Push 推播通知          | --   |
| 付款提醒               | --   |
| 消費附件（照片/收據）  | --   |
| 深色模式               | --   |
| 群組類型分類           | --   |
| 群組簡化債務開關       | --   |

### Phase 3 -- 進階功能（P2 功能）

**目標**：資料洞察與社交互動

| 功能               | 狀態 |
| ------------------ | ---- |
| 消費分類統計圖表   | --   |
| 月度趨勢報表       | --   |
| CSV 匯出           | --   |
| 評論功能           | --   |
| 編輯歷史追蹤       | --   |
| Email 通知         | --   |
| 調整分帳           | --   |
| 頭像上傳           | --   |
| 群組封面照片       | --   |
| 非註冊好友邀請     | --   |

### Phase 4 -- 進階版（P3 功能）

**目標**：Premium 功能與生態整合

| 功能                 | 狀態 |
| -------------------- | ---- |
| 收據 OCR 掃描        | --   |
| 逐項分攤             | --   |
| JSON 完整備份匯出    | --   |
| 第三方支付整合       | --   |
| 離線模式             | --   |

---

## 8. 附錄

### 8.1 名詞定義

| 術語           | 定義                                                     |
| -------------- | -------------------------------------------------------- |
| 消費 (Expense) | 一筆由一或多人付款、由一或多人分攤的支出紀錄             |
| 分攤 (Split)   | 消費金額在參與者之間的分配方式與結果                     |
| 餘額 (Balance) | 兩位使用者之間所有消費與結算後的淨欠款金額               |
| 結算 (Settlement) | 實際的轉帳或付款行為，用於清除債務                    |
| 債務簡化 (Simplify Debts) | 將多筆複雜債務重組為最少交易次數的演算法       |
| 群組 (Group)   | 一組使用者的集合，在同一群組內共同記帳                   |
| 週期性消費 (Recurring Expense) | 按固定頻率自動建立的消費紀錄               |

### 8.2 參考資料

- [Splitwise 官方網站](https://www.splitwise.com/)
- [Splitwise Pro 功能](https://www.splitwise.com/pro)
- [Splitwise 債務簡化演算法解析](https://medium.com/@mithunmk93/algorithm-behind-splitwises-debt-simplification-feature-8ac485e97688)
- [Splitwise 官方部落格 - Debts Made Simple](https://blog.splitwise.com/2012/09/14/debts-made-simple/)
- [Splitwise Feedback & Helpdesk](https://feedback.splitwise.com/)
- [Splitwise 2026 功能評測](https://www.softwaresuggest.com/splitwise)
- [Splitwise Free vs Pro 比較](https://splittyapp.com/learn/splitwise-free-limits/)
