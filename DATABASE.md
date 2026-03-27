# 資料庫連線資訊

## Neon PostgreSQL

| 項目 | 值 |
|------|-----|
| 服務商 | [Neon](https://neon.tech) |
| PostgreSQL 版本 | 17.8 |
| 區域 | AWS us-east-1 |
| Host | `ep-crimson-voice-am0m4miy-pooler.c-5.us-east-1.aws.neon.tech` |
| Port | `5432` |
| 資料庫名稱 | `neondb` |
| 使用者 | `neondb_owner` |
| SSL | 必須啟用（`sslmode=require`） |

## 連線字串格式

```
# 標準 PostgreSQL
postgresql://neondb_owner:<PASSWORD>@ep-crimson-voice-am0m4miy-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require

# SQLAlchemy async（本專案使用）
postgresql+asyncpg://neondb_owner:<PASSWORD>@ep-crimson-voice-am0m4miy-pooler.c-5.us-east-1.aws.neon.tech/neondb?ssl=require
```

> 將 `<PASSWORD>` 替換為實際密碼。密碼請向專案管理員索取，或至 [Neon Dashboard](https://console.neon.tech) 查看。

## 本地開發設定

1. 複製 `backend/.env.example` 為 `backend/.env`
2. 將 `DATABASE_URL` 替換為上方的 SQLAlchemy async 連線字串（填入實際密碼）
3. `.env` 已在 `.gitignore` 中，不會被提交

## 注意事項

- Neon 免費方案有 **0.5 GB** 儲存限制
- 無流量時會自動 **scale-to-zero**，首次連線可能需要數秒喚醒
- 使用內建 **連線池（pooler）**，無需額外設定 PgBouncer
