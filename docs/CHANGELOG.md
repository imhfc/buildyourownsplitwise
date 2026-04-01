# CHANGELOG

本文件記錄專案所有功能更新、修復與重要變更，作為開發參考。

---

## [Unreleased] - 2026-04-01

### 功能一：群組邀請連結（完整分享 / 加入流程）

**後端**

- 新增 `invite_token`（String(32), unique, indexed）和 `invite_token_created_at` 欄位至 `groups` 資料表
  - Migration: `e5f6a7b8c9d0_add_invite_token_to_groups.py`
- Group model 新增 `invite_token` / `invite_token_created_at` 欄位
- GroupService 新增四個方法：
  - `create_invite_token()` - 產生 32 字元 hex token（需群組成員身份）
  - `revoke_invite_token()` - 撤銷邀請 token（需管理員）
  - `regenerate_invite_token()` - 重新產生 token，舊 token 失效（需管理員）
  - `get_invite_info()` - 透過 token 取得群組資訊（不需認證）
  - `accept_invite()` - 接受邀請加入群組；已是成員回傳 409
- 新增 `invites` router（`backend/app/api/invites.py`）：
  - `GET /api/v1/invite/{token}` - 取得群組資訊（不需登入）
  - `POST /api/v1/invite/{token}/accept` - 接受邀請加入群組
- Groups router 新增端點：
  - `POST /groups/{group_id}/invite` - 建立/取得邀請 token
  - `DELETE /groups/{group_id}/invite` - 撤銷邀請 token
  - `POST /groups/{group_id}/invite/regenerate` - 重新產生邀請 token
- Schemas 新增：
  - `InviteTokenResponse` - 回傳邀請 token 及建立時間
  - `InviteInfoResponse` - 回傳群組摘要（group_id, name, description, member_count）

**前端**

- 新增 `InviteShareModal` 元件（`mobile/components/InviteShareModal.tsx`）：
  - 顯示邀請連結（唯讀輸入欄位）
  - 複製連結按鈕（web 使用 clipboard API）
  - 分享到 LINE 按鈕（產生 LINE 分享 URL）
  - 管理員可重新產生/撤銷邀請
  - 支援 loading 與 error 狀態
- 新增加入群組頁面（`mobile/app/join/[token].tsx`）：
  - 加入前顯示群組資訊（名稱、描述、成員數）
  - 加入成功後導向群組詳情頁
  - 處理 edge case：無效 token、已是成員
  - 未登入時導向登入頁，登入後自動跳回加入流程
- `_layout.tsx` 新增 `join/[token]` 路由，允許未登入使用者存取
- `auth store` 新增 `pendingInviteToken` 狀態，登入後自動處理待接受邀請
- `login.tsx` Google 登入與信箱登入完成後檢查 pending invite token
- `group/[id].tsx` 成員頁籤新增邀請分享按鈕（Link icon），點擊開啟 InviteShareModal
- `api.ts` 新增 `groupsAPI.createInvite()` / `regenerateInvite()` / `revokeInvite()` 及 `inviteAPI.getInfo()` / `accept()`
- i18n 三語言新增邀請相關翻譯鍵值（invite_link, share_invite, share_to_line, copy_link, link_copied, revoke_invite, regenerate_invite, join_group, joined_successfully, already_member, invalid_invite 等）

---

### 功能二：群組排序（拖曳重新排列）

**後端**

- `group_members` 資料表新增 `sort_order` 欄位（Integer, default 0）
  - Migration: `c3d4e5f6a7b8_add_sort_order_to_group_members.py`
- GroupMember model 新增 `sort_order` 欄位
- `list_user_groups()` 改為依 `sort_order ASC` → `created_at DESC` 排序
- 新增 `reorder_groups()` service 方法，根據傳入的 group_id 清單更新排序
- 新增 `PUT /groups/reorder` 端點，接受 group_id 清單進行排序
- Schemas 新增 `ReorderGroupsRequest`，`GroupListResponse` 新增 `sort_order` 欄位

**前端**

- 首頁群組列表改用 `DraggableFlatList`（`react-native-draggable-flatlist`）實現拖曳排序
- 新增 `GripVertical` 圖示作為拖曳把手
- 長按觸發拖曳模式，拖曳結束後自動儲存排序至後端
- 排序失敗時自動重新載入恢復原狀
- `package.json` 新增依賴：`react-native-draggable-flatlist ^4.0.3`
- `api.ts` 新增 `groupsAPI.reorder()` 方法

---

### 功能三：消費編輯

**後端**

- `update_expense()` 授權邏輯變更：
  - 舊：僅付款人（paid_by）可編輯
  - 新：任何參與消費的成員（付款人或分帳參與者）皆可編輯

**前端**

- `group/[id].tsx` 消費項目改為可點擊，點擊後開啟編輯 Modal
- 新增 `editingExpenseId` 狀態追蹤正在編輯的消費
- `handleSubmitExpense()` 同時處理新增與編輯（取代原本的 `handleAddExpense()`）
- Modal 標題依狀態顯示「編輯消費」或「新增消費」
- 編輯時表單自動帶入現有資料
- `ExpenseItem` interface 新增 `paid_by`, `splits`, `note`, `expense_date` 欄位
- `api.ts` 新增 `ExpenseUpdatePayload` interface 和 `expensesAPI.update()` 方法
- i18n 三語言新增 `edit_expense` 翻譯

---

### 功能四：使用者頭像顯示

**後端**

- Google 登入時頭像更新邏輯變更：
  - 舊：僅在使用者無頭像時設定（`if not user.avatar_url and avatar_url`）
  - 新：每次登入皆從 Google 同步頭像（`if user and avatar_url: user.avatar_url = avatar_url`）

**前端**

- `Avatar` 元件新增 `avatarUrl` optional prop，有值時顯示實際圖片取代首字母
- 新增 `imageSizeMap` 對應不同尺寸的圖片大小
- `account.tsx` 傳入 `avatarUrl={user?.avatar_url}` 顯示使用者頭像
- `friends.tsx` 重構 `renderAvatar()`，統一使用 `Avatar` 元件並傳入 avatar URL

---

### 功能五：UI/UX 改善與主題支援

- `theme.tsx` 新增 `useThemeClassName()` hook，回傳主題 class 字串供 Portal/Modal 使用
- 首頁（`index.tsx`）確認刪除 Modal、建立群組 Modal 套用 `themeClass`
- 好友頁面（`friends.tsx`）新增好友 Modal、移除好友 Modal 套用主題
- 群組詳情（`group/[id].tsx`）多個 Modal 套用主題
- 確保 Modal 在 dark mode / 色系切換時正確呈現

---

### 檔案變更總覽

**新增檔案（5）**

| 檔案 | 說明 |
|------|------|
| `backend/alembic/versions/c3d4e5f6a7b8_add_sort_order_to_group_members.py` | DB migration：群組成員排序欄位 |
| `backend/alembic/versions/e5f6a7b8c9d0_add_invite_token_to_groups.py` | DB migration：群組邀請 token 欄位 |
| `backend/app/api/invites.py` | 邀請 API 端點 |
| `mobile/app/join/[token].tsx` | 加入群組頁面 |
| `mobile/components/InviteShareModal.tsx` | 邀請分享 Modal 元件 |

**修改檔案（22）**

| 檔案 | 涉及功能 |
|------|---------|
| `backend/app/api/groups.py` | 邀請端點、排序端點 |
| `backend/app/main.py` | 註冊 invites router |
| `backend/app/models/group.py` | invite_token、sort_order 欄位 |
| `backend/app/schemas/group.py` | 邀請/排序相關 schema |
| `backend/app/services/auth_service.py` | Google 頭像同步 |
| `backend/app/services/expense_service.py` | 消費編輯授權放寬 |
| `backend/app/services/group_service.py` | 邀請/排序 service 方法 |
| `mobile/app/(auth)/login.tsx` | pending invite 處理 |
| `mobile/app/(tabs)/account.tsx` | 頭像顯示 |
| `mobile/app/(tabs)/friends.tsx` | 頭像、主題支援 |
| `mobile/app/(tabs)/index.tsx` | 拖曳排序、主題支援 |
| `mobile/app/_layout.tsx` | join 路由、認證邏輯 |
| `mobile/app/group/[id].tsx` | 消費編輯、邀請分享、主題 |
| `mobile/components/ui/avatar.tsx` | avatarUrl 支援 |
| `mobile/i18n/en.json` | 英文翻譯新增 |
| `mobile/i18n/ja.json` | 日文翻譯新增 |
| `mobile/i18n/zh-TW.json` | 繁中翻譯新增 |
| `mobile/lib/theme.tsx` | useThemeClassName hook |
| `mobile/package.json` | draggable-flatlist 依賴 |
| `mobile/package-lock.json` | lock 檔更新 |
| `mobile/services/api.ts` | 邀請/排序/消費編輯 API |
| `mobile/stores/auth.ts` | pendingInviteToken 狀態 |

---

## [2026-03-xx] - 餘額 API、消費編輯、expense_date、好友頁面重構、i18n 擴充

> commit: d47d175

- 新增餘額 API
- 消費編輯功能
- expense_date 欄位
- 好友頁面重構
- i18n 擴充

---

## [2026-03-xx] - 資安修改與 Google 登入

> commit: 6e4ff8b

- 資安相關修改
- Google 登入整合完成

---

## [2026-03-xx] - 部署與 CI/CD

> commit: b5aee97

- deploy.yml 的 SECRET_KEY 從 vars 改為 secrets，避免明文洩露

> commit: 148fd8d

- 清理無關 skills 並整合 CI/CD 文件
