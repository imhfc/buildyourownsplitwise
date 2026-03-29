# CI/CD 自動部署指南（GitHub Actions + Self-Hosted Runner）

> 此方案使用 GitHub Actions 搭配 self-hosted runner，push 到 main 時自動部署，支援 health check 和自動 rollback。
> 預計部署在新的 VM 上，與現有 Cron 方案（CICD.md）的舊 VM 獨立運作。

## ⚠️ Repository 同步說明

由於目前的開發者不是原始 repository（`imhfc/buildyourownsplitwise`）的 owner，無法直接在該 repo 設定 self-hosted runner 和 GitHub Actions。因此採用以下架構：

```
imhfc/buildyourownsplitwise (原始 repo)
        │
        │  每分鐘透過 ncbs_gcp 自動 gh sync
        ▼
aiinpocket/buildyourownsplitwise (fork/mirror repo)
        │
        │  GitHub Actions + self-hosted runner
        ▼
      VM 部署
```

**實際運作方式：**
- `ncbs_gcp` 每分鐘將 `imhfc/buildyourownsplitwise` 同步到 `aiinpocket/buildyourownsplitwise`
- Self-hosted runner 註冊在 `aiinpocket/buildyourownsplitwise`
- **查看 Variables / Secrets 設定**：到 `aiinpocket/buildyourownsplitwise` → Settings → Secrets and variables → Actions
- **查看 Workflow 執行紀錄**：到 `aiinpocket/buildyourownsplitwise` → Actions tab
- **手動觸發部署**：也是從 `aiinpocket/buildyourownsplitwise` 的 Actions 頁面操作

## 架構概覽

```
本機 git push → GitHub Actions → self-hosted runner (VM) →
  build → backup :bak → 寫 .env → alembic migrate → 重啟 backend/caddy →
    health check pass → 清理 :bak
    health check fail → alembic downgrade → 還原 :bak → 重啟
```

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

只重啟 `backend` 和 `caddy`（db/redis 不動），然後對 `http://localhost:${BACKEND_PORT}/health` 做最多 10 次 health check，每次間隔 3 秒。

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
| `GOOGLE_CLIENT_IDS` | （空） | Google OAuth Client ID（前後端共用，自動寫入 `mobile/.env` 作為 `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`） |
| `ALLOWED_ORIGINS` | `*` | CORS 允許來源，生產環境應設為實際網域 |

## Self-Hosted Runner 設定

### 0. 進入 VM 後的第一步

SSH 進入 VM 後，**必須先切換到 `ap01` 使用者**再進行任何操作：

```bash
sudo su - ap01
```

GitHub self-hosted runner 是以 `ap01` 身分安裝與運行的，所有部署相關的檔案、Docker 權限、runner 設定都屬於此帳號。未切換身分直接操作可能導致權限問題或路徑錯誤。

### 1. 在 VM 上安裝 runner

```bash
# 確認已切換至 ap01 使用者
# sudo su - ap01

# GitHub repo → Settings → Actions → Runners → New self-hosted runner
# 依照頁面指示下載並設定，以下為大致流程：

mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.XXX.X.tar.gz -L https://github.com/actions/runner/releases/download/vX.XXX.X/actions-runner-linux-x64-2.XXX.X.tar.gz
tar xzf ./actions-runner-linux-x64-2.XXX.X.tar.gz
./config.sh --url https://github.com/aiinpocket/buildyourownsplitwise --token <TOKEN>
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
- 手動觸發：GitHub repo → Actions → Deploy to Self-Hosted → Run workflow
