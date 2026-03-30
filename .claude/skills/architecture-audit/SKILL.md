---
name: architecture-audit
description: 自動化 Clean Architecture 合規審查，確保 FastAPI 專案遵循分層架構規範。Use this skill when 使用者要求「架構審查」「架構合規」「分層檢查」。
---

# Architecture Audit Skill

> 自動化 Clean Architecture 合規審查（FastAPI + React Native）

## 觸發條件

- 「架構審查」「架構合規」「分層檢查」「Clean Architecture 審查」

## 概述

此 Skill 審查專案是否遵循 CLAUDE.md 定義的 Clean Architecture 規範。

## 審查架構

### 後端分層結構
```
backend/app/
├── api/          # 展示層 — 路由，僅請求/回應
├── schemas/      # DTO — Pydantic 驗證
├── services/     # 業務邏輯 — 核心領域
├── models/       # ORM — SQLAlchemy 資料層
└── core/         # 基礎設施 — 設定、DB、安全、DI
```

### 前端結構
```
mobile/
├── app/          # 路由/畫面（Expo Router）
├── components/   # 可重用 UI 元件
├── stores/       # Zustand 全域狀態
├── services/     # API 呼叫層
├── lib/          # 工具函式
└── i18n/         # 多語系
```

## 檢查項（17 項）

### Critical（必須 100% 通過）

| ID | 檢查項 | 說明 |
|----|--------|------|
| C-1 | API 層無業務邏輯 | api/*.py 不能包含資料庫查詢或計算邏輯 |
| C-2 | 無反向依賴 | services 不能 import api，models 不能 import services |
| C-3 | 金額使用 Decimal | 所有金額欄位使用 Numeric(12,2)，禁止 float |
| C-4 | 認證無硬編碼密鑰 | SECRET_KEY 等必須從環境變數讀取 |

### High

| ID | 檢查項 | 說明 |
|----|--------|------|
| H-1 | 所有 API 使用 async def | 非同步優先 |
| H-2 | 資源擁有權檢查 | 寫入/刪除操作驗證使用者權限 |
| H-3 | 分帳總和驗證 | 指定金額加總 = 總金額，百分比加總 = 100% |
| H-4 | Pydantic schema 驗證 | 所有輸入透過 schema 驗證 |
| H-5 | Migration 不可修改 | 已存在的 Alembic migration 禁止變動 |

### Medium

| ID | 檢查項 | 說明 |
|----|--------|------|
| M-1 | 時間戳記使用 UTC | server_default=func.now() |
| M-2 | API 版本前綴 | 所有端點 /api/v1/ |
| M-3 | 分頁支援 | 列表端點支援 skip/limit |
| M-4 | 錯誤格式統一 | {"detail": "..."} |

### Low

| ID | 檢查項 | 說明 |
|----|--------|------|
| L-1 | PEP 8 命名 | snake_case 函式、PascalCase 類別 |
| L-2 | 檔案組織 | 每個模型一個檔案 |
| L-3 | i18n 完整 | 所有使用者文字透過 t() |
| L-4 | Mobile 品質關卡通過 | quality-gate.sh 全部 PASS |

## 評分標準

| 等級 | 分數 | 說明 |
|------|------|------|
| A | 90-100% | 優秀，可直接上線 |
| B | 80-89% | 良好，少量改善 |
| C | 70-79% | 合格，需要改善 |
| D | 60-69% | 不合格，需重構 |
| F | <60% | 嚴重不合規 |

**Critical 項目必須 100% 通過，否則直接 F**

## 執行流程

```
Phase 1: 載入規範（讀取 CLAUDE.md）
Phase 2: 規劃審查（識別待檢查檔案）
Phase 3: 執行審查（逐項檢查）
Phase 4: 驗證完整性（確認 17 項全部檢查）
```

## 輸出報告

```markdown
# 架構合規審查報告

## 評分：[A/B/C/D/F] (XX%)

## Critical 項目
- [PASS/FAIL] C-1: API 層無業務邏輯
- [PASS/FAIL] C-2: 無反向依賴
- [PASS/FAIL] C-3: 金額使用 Decimal
- [PASS/FAIL] C-4: 認證無硬編碼密鑰

## High 項目
...

## 違規摘要
| 檔案 | 違規項 | 嚴重度 | 建議修正 |
|------|--------|--------|---------|

## 改善建議
1. ...
2. ...
```
