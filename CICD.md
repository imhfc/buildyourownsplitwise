# CI/CD 自動部署指南（GitHub Actions + Self-Hosted Runner）

> 使用 GitHub Actions 搭配 self-hosted runner，push 到 main 時自動部署，支援 health check 和自動 rollback。
> 部署目標為 `jason@211.20.120.114`。

- Repo：`imhfc/buildyourownsplitwise`
- Actions：https://github.com/imhfc/buildyourownsplitwise/actions
- Workflow 檔案：`.github/workflows/deploy.yml`

## 架構概覽

```
本機 git push → GitHub Actions → self-hosted runner (211.20.120.114) →
  寫 .env → build → backup :bak → 確保 DB → alembic migrate → 重啟 backend/caddy →
    health check pass → 清理 :bak
    health check fail → alembic downgrade → 還原 :bak → 重啟
```

## 部署流程詳解

### Step 0 — Clean workspace + Checkout

清理上次 docker 運行留下的 root-owned 檔案，然後 checkout 最新程式碼。

### Step 1 — Write .env from GitHub Variables

從 GitHub repo Variables 讀取設定，寫入根目錄 `.env` 和 `mobile/.env`。未設定的變數不會寫入，由 `docker-compose.yml` 的 `${VAR:-default}` 提供預設值。

> 必須在 build 之前執行，因為 Caddy build 需要 `mobile/.env` 中的 `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`。

### Step 2 — Build new images

```
docker compose build --no-cache backend caddy
```

舊容器繼續運行，使用者無感。只 build `backend` 和 `caddy`，`db` 使用官方 image 不需要 build。

### Step 3 — Backup current images

將目前運行的 backend/caddy image tag 為 `:bak`，作為 rollback 快照。

### Step 4 — Run Alembic migration

先確保 DB 容器在運行（`docker compose up -d db`）並等待 `pg_isready`，然後用新 build 的 backend image 跑 `alembic upgrade head`。沒有新 migration 時為 no-op。

### Step 5 — Restart + Health check

只重啟 `backend` 和 `caddy`（db 不動），然後對 `http://localhost:${BACKEND_PORT}/health` 做最多 10 次 health check，每次間隔 3 秒。

### Step 5a — Rollback（僅 health check 失敗時）

1. `alembic downgrade -1` 回退 schema
2. 將 `:bak` image 還原回 `:latest`
3. 重新啟動 backend/caddy
4. 驗證舊版本是否正常運行

### Step 6 — Cleanup

刪除 `:bak` image 和 dangling images，釋放磁碟空間。

## GitHub Variables 設定

位置：`imhfc/buildyourownsplitwise` → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab

### Port 設定（可選）

不設定則使用 `docker-compose.yml` 中的預設值。

| Variable | 預設值 | 說明 |
|----------|--------|------|
| `DB_PORT` | `5432` | PostgreSQL 對外 port |
| `BACKEND_PORT` | `8000` | FastAPI 對外 port |
| `CADDY_HTTP_PORT` | `80` | Caddy HTTP port |
| `CADDY_HTTPS_PORT` | `443` | Caddy HTTPS port |

### 應用設定（建議設定）

不設定則使用 `docker-compose.yml` 中的 dev 預設值，**生產環境務必設定 `SECRET_KEY`**。

| Variable | 預設值 | 說明 |
|----------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://splitewise:splitewise@db:5432/splitewise` | DB 連線字串（docker 內部用 `db` hostname） |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT 簽名密鑰，**生產環境必改** |
| `GOOGLE_CLIENT_IDS` | （空） | Google OAuth Client ID（前後端共用，自動寫入 `mobile/.env` 作為 `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`） |
| `ALLOWED_ORIGINS` | `*` | CORS 允許來源，生產環境應設為實際網域 |

## 資料庫說明

此部署方案的 PostgreSQL 資料庫是透過 `docker-compose.yml` 中的 `db` service 啟動的 **本機 Docker 容器**（`postgres:16-alpine`），資料存放在 Docker volume `pgdata` 中，不連接任何外部雲端資料庫。

### 預設帳號密碼

| 項目 | 值 |
|------|-----|
| 使用者 | `splitewise` |
| 密碼 | `splitewise` |
| 資料庫名稱 | `splitewise` |
| 連線字串 | `postgresql+asyncpg://splitewise:splitewise@db:5432/splitewise` |

> 以上為 dev 預設值。生產環境應透過 GitHub Variables 設定 `DATABASE_URL` 覆蓋，使用強密碼。

## Self-Hosted Runner 設定

### 0. SSH 進入部署主機

```bash
ssh jason@211.20.120.114
```

GitHub self-hosted runner 是以 `jason` 身分安裝與運行的，所有部署相關的檔案、Docker 權限、runner 設定都屬於此帳號。

### 1. 在主機上安裝 runner

```bash
# imhfc/buildyourownsplitwise → Settings → Actions → Runners → New self-hosted runner
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

## 注意事項

- 每個 Alembic migration 都必須實作 `downgrade()`，否則自動 rollback 會失敗
- `docker-compose.yml` 的 `name: buildyourownsplitwise` 讓容器名稱為 `buildyourownsplitwise-<service>-1`
- Workflow 檔案位於 `.github/workflows/deploy.yml`
- 手動觸發：`imhfc/buildyourownsplitwise` → Actions → Deploy to Self-Hosted → Run workflow
