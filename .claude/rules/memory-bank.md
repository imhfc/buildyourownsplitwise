# Memory Bank 規則

> 觸發情境：載入/更新 Memory Bank、Context 達閾值

## 載入策略

按需載入，不自動載入全部。

| 檔案 | 路徑 | 觸發條件 |
|------|------|---------|
| **preferences** | `project-context/` | 用戶表達偏好、輸出風格 |
| **progress** | `project-context/` | 查詢/更新進度、開始/完成任務 |
| **decisions** | `project-context/` | 做決策前、查詢過去決策 |

讀取時使用 category 或 tags 篩選，避免載入全部。

## 自動更新

| 事件 | 更新檔案 | 方式 |
|------|---------|------|
| 任務完成 | progress.yaml | 自動更新 |
| 偏好變更 | preferences.yaml | 自動更新 |
| 做出決策 | decisions.yaml | 主動提示 |
