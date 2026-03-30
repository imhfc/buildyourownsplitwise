---
name: review-code
description: 專業代碼審查，自動規劃審查策略、多維度並行審查。Use this skill when 使用者要求「審查」「Review」「檢查」「掃描」「驗證」「安全」。
---

# Review Code Skill

> 組合 Review Coordinator + REVIEW Agents 完成專業代碼審查

## 執行流程

```
Step 1: 規劃審查範圍和策略
Step 2: 並行執行多維度審查
Step 3: 整合結果並生成報告
```

## 使用場景

### 1. 全面代碼審查
- API 端點安全審計
- Service 層邏輯審查
- 多文件品質檢查

### 2. 專項審查
- 安全漏洞掃描（OWASP Top 10）
- Clean Architecture 層級檢查
- Python PEP 8 規範
- React Native 最佳實踐

## 使用方式

```bash
# 斜線命令
/review-code 審查 expense_service.py 的安全性

# 自然語言
審查最近的變更
檢查 auth.py 的安全性
Review group_service 的程式碼品質
```

## 審查策略

| 策略 | 檔案數 | 深度 |
|------|--------|------|
| quick_check | 1-3 | 快速掃描，重點安全 |
| standard_review | 4-10 | 完整多維度審查 |
| comprehensive_review | 10+ | 深度審查 + 架構分析 |
| security_audit | 任意 | 專注安全漏洞 |

## 審查維度

### 後端 (Python/FastAPI)

#### 1. 安全性
- SQL Injection（SQLAlchemy 參數化查詢）
- 認證/授權（JWT token 檢查、資源擁有權驗證）
- 密碼處理（bcrypt hashing）
- 環境變數（無硬編碼密鑰）
- CORS 設定

#### 2. 架構合規
- Clean Architecture 分層（api → services → models）
- API 層禁止業務邏輯
- Services 禁止 import api
- 所有操作使用 async/await

#### 3. 資料完整性
- 金額使用 Decimal(12,2)，禁止 float
- 時間戳記使用 UTC
- 外鍵約束、NOT NULL
- 分帳總和驗證（均分、百分比、指定金額）

#### 4. 程式碼品質
- PEP 8 規範
- Type hints
- 錯誤處理（HTTPException with proper status codes）
- N+1 查詢問題

### 前端 (React Native/Expo)

#### 1. UI/UX 規範
- 所有文字透過 i18n `t()` 函式
- 按鈕使用 `<Button>` variant，禁止硬編碼顏色
- 數字輸入搭配 regex 過濾
- KeyboardAvoidingView 包裹表單

#### 2. 狀態管理
- 表單用 useState，全域用 Zustand
- useFocusEffect + useCallback 刷新資料
- API 呼叫有 loading 狀態，防重複送出

#### 3. 安全性
- secureTextEntry 用於密碼欄位
- API 呼叫需 try/catch
- 敏感資料不存 AsyncStorage

## 輸出格式

```markdown
# 代碼審查報告

## 摘要
- 審查範圍：X 個檔案
- 發現問題：Y 個（Critical: a, High: b, Medium: c, Low: d）

## Critical 問題
### [C-1] 問題描述
- 檔案：path/to/file.py:42
- 風險：...
- 建議修正：...

## High 問題
...

## 建議改善
...
```
