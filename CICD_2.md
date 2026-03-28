# CI/CD 自動部署指南（GitHub Actions + Self-Hosted Runner）

> 此方案使用 GitHub Actions 搭配 self-hosted runner，push 到 main 時自動部署，支援 health check 和自動 rollback。
> Cron 輪詢方案請參閱 [CICD.md](./CICD.md)。

## 架構概覽

```
本機 git push → GitHub Actions → self-hosted runner (VM) →
  build → backup :bak → 寫 .env → alembic migrate → 重啟 backend/caddy →
    health check pass → 清理 :bak
    health check fail → alembic downgrade → 還原 :bak → 重啟
```

## 與 Cron 方案的差異

| 比較項目 | Cron (CICD.md) | GitHub Actions (本文) |
|----------|----------------|----------------------|
| 觸發方式 | 每分鐘輪詢 git pull | push to main 即觸發 |
| 環境設定 | 手動編輯 VM 上的 `.env` | 從 GitHub Variables 自動寫入 |
| DB migration | 手動 SSH 跑 alembic | 自動執行 alembic upgrade |
| Rollback | 無（build 失敗保留舊容器） | 自動 rollback image + schema |
| Health check | 無 | 自動檢查 `/health` endpoint |
| 舊 image 清理 | 無 | 自動清理 :bak + dangling images |

## 部署流程詳解

### Step 1 — Build new images

```
docker compose build --no-cache backend caddy
```

舊容器繼續運行，使用者無感。只 build `backend` 和 `caddy`，`db` 和 `redis` 使用官方 image 不需要 build。

### Step 2 — Backup current images

將目前運行的 backend/caddy image tag 為 `:bak`，作為 rollback 快照。

### Step 3 — Write .env from GitHub Variables

從 GitHub repo Variables 讀取設定，寫入根目錄 `.env`。未設定的變數不會寫入，由 `docker-compose.yml` 的 `${VAR:-default}` 提供預設值。

### Step 3a — Run Alembic migration

在啟動新 code 之前，用新 build 的 backend image 跑 `alembic upgrade head`。沒有新 migration 時為 no-op。

### Step 4 — Restart + Health check

只重啟 `backend` 和 `caddy`（db/redis 不動），然後對 `http://localhost:8000/health` 做最多 10 次 health check，每次間隔 3 秒。

### Step 4a — Rollback（僅 health check 失敗時）

1. `alembic downgrade -1` 回退 schema
2. 將 `:bak` image 還原回 `:latest`
3. 重新啟動 backend/caddy
4. 驗證舊版本是否正常運行

### Step 5 — Cleanup

刪除 `:bak` image 和 dangling images，釋放磁碟空間。

## GitHub Variables 設定

位置：GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab

### Port 設定（可選）

不設定則使用 `docker-compose.yml` 中的預設值。

| Variable | 預設值 | 說明 |
|----------|--------|------|
| `DB_PORT` | `5432` | PostgreSQL 對外 port |
| `REDIS_PORT` | `6379` | Redis 對外 port |
| `BACKEND_PORT` | `8000` | FastAPI 對外 port |
| `CADDY_HTTP_PORT` | `80` | Caddy HTTP port |
| `CADDY_HTTPS_PORT` | `443` | Caddy HTTPS port |

### 應用設定（建議設定）

不設定則使用 `docker-compose.yml` 中的 dev 預設值，**生產環境務必設定 `SECRET_KEY`**。

| Variable | 預設值 | 說明 |
|----------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://splitewise:splitewise@db:5432/splitewise` | DB 連線字串（docker 內部用 `db` hostname） |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 連線字串（docker 內部用 `redis` hostname） |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT 簽名密鑰，**生產環境必改** |
| `GOOGLE_CLIENT_IDS` | （空） | Google OAuth Web Client ID |
| `ALLOWED_ORIGINS` | `*` | CORS 允許來源，生產環境應設為實際網域 |

## Self-Hosted Runner 設定

### 1. 在 VM 上安裝 runner

```bash
# GitHub repo → Settings → Actions → Runners → New self-hosted runner
# 依照頁面指示下載並設定，以下為大致流程：

mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.XXX.X.tar.gz -L https://github.com/actions/runner/releases/download/vX.XXX.X/actions-runner-linux-x64-2.XXX.X.tar.gz
tar xzf ./actions-runner-linux-x64-2.XXX.X.tar.gz
./config.sh --url https://github.com/imhfc/buildyourownsplitwise --token <TOKEN>
```

### 2. 設為系統服務（開機自動啟動）

```bash
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

### 3. 確認 runner 所需工具

```bash
# runner 使用者需要有 docker 權限
sudo usermod -aG docker $USER

# 確認工具存在
docker compose version
curl --version
```

## 與 Cron 方案共存

兩套方案可以共存，但建議**擇一使用**，避免同時部署造成衝突：

- **使用 GitHub Actions 時：** 移除 cron 排程
  ```bash
  crontab -r   # 或 crontab -e 手動刪除那行
  ```
- **保留 Cron 作為 fallback：** 若 GitHub Actions runner 掛了，cron 仍然能自動部署，但不會有 rollback 和 health check。

## 注意事項

- 每個 Alembic migration 都必須實作 `downgrade()`，否則自動 rollback 會失敗
- `docker-compose.yml` 的 `name: buildyourownsplitwise` 讓容器名稱為 `buildyourownsplitwise-<service>-1`
- Workflow 檔案位於 `.github/workflows/deploy.yml`
- 手動觸發：GitHub repo → Actions → Deploy to Self-Hosted → Run workflow
