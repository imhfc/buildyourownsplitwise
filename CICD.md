# CI/CD 自動部署指南（Cron + deploy.sh）

> 此方案使用 VM 上的 cron 每分鐘輪詢 GitHub，適合不需要 GitHub Actions runner 的場景。
> GitHub Actions 方案請參閱 [CICD_2.md](./CICD_2.md)。

## 架構概覽

```
本機 git push → GitHub → VM cron (每分鐘) → git pull → docker compose build → docker compose up -d
```

## 環境資訊

| 項目 | 值 |
|------|-----|
| GCP VM 名稱 | `buildyourownsplitewise` |
| Zone | `us-central1-a` |
| 外部 IP | `35.206.96.99` |
| VM 使用者 | `jasonhung.ibm` |
| 專案路徑 | `~/buildyourownsplitwise` |
| API 位址 | `http://35.206.96.99:8000/docs` |
| Compose project name | `buildyourownsplitwise`（容器名稱為 `buildyourownsplitwise-backend-1` 等） |

## 運作方式

1. Cron 每分鐘執行 `deploy.sh`
2. 腳本執行 `git pull --ff-only` 檢查是否有新 commit
3. 若有變更：
   - 自動清理佔用 port 的非 `buildyourownsplitwise` 專案 container
   - `docker-compose build` 重建 image
   - `docker-compose up -d` 重啟服務
4. 若 build 失敗，舊容器繼續運行，不會中斷服務

## 初始設定步驟

### 1. VM 產生 SSH Key

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
# 複製 public key 到 GitHub → Settings → SSH and GPG keys
```

### 2. 驗證 SSH 連線

```bash
ssh -T git@github.com
# 預期輸出: Hi imhfc! You've successfully authenticated...
```

### 3. Clone 專案

```bash
cd ~
git clone git@github.com:imhfc/buildyourownsplitwise.git
cd buildyourownsplitwise
```

### 4. 首次啟動

```bash
# 根目錄 .env — port 設定（可選，不建則用預設值）
cp .env.example .env

# 後端 .env — 應用設定（必要）
cp backend/.env.example backend/.env
# 編輯 backend/.env 設定正式環境的 SECRET_KEY、DATABASE_URL 等

# 啟動服務
sudo docker-compose up -d
```

### 5. 設定 Cron

```bash
# 安裝 cron（若尚未安裝）
sudo apt-get install -y cron
sudo systemctl enable cron && sudo systemctl start cron

# 新增排程
echo '* * * * * /bin/bash $HOME/buildyourownsplitwise/deploy.sh' | crontab -

# 驗證
crontab -l
```

## 常用維運指令

```bash
# SSH 進 VM
gcloud compute ssh buildyourownsplitewise --zone=us-central1-a

# 查看部署 log
tail -f ~/buildyourownsplitwise/deploy.log

# 查看容器狀態
sudo docker-compose -f ~/buildyourownsplitwise/docker-compose.yml ps

# 手動重啟服務
cd ~/buildyourownsplitwise && sudo docker-compose restart

# 查看容器 log
sudo docker-compose -f ~/buildyourownsplitwise/docker-compose.yml logs -f backend

# 查看 cron 排程
crontab -l
```

## 已知問題與解法

### Port 衝突

**問題：** VM 上若有其他 container 佔用 port，`docker-compose up` 會失敗。

**解法：** `deploy.sh` 在每次部署前會自動檢查並清理非 `buildyourownsplitwise` 專案的衝突 container。若需手動處理：

```bash
# 查看誰佔了 port
sudo ss -tlnp | grep 8000

# 找到並停止衝突容器
sudo docker ps --filter "publish=8000"
sudo docker stop <container_id> && sudo docker rm <container_id>
```

### Git Pull 衝突

**問題：** 若在 VM 上直接修改檔案，`git pull --ff-only` 會失敗。

**解法：** 永遠不要在 VM 上直接改 code。所有變更都在本機做，push 到 GitHub 讓自動部署處理。

## 注意事項

- VM 上的 Docker 不支援 `docker compose` 子命令，必須用 `docker-compose`
- Repo 名稱是 `buildyourownsplitwise`（不是 buildyourownsplite**wi**se）
- deploy.sh 使用 file lock 防止併發執行
- build 失敗不會影響正在運行的服務
- Compose project name 為 `buildyourownsplitwise`，容器名稱格式：`buildyourownsplitwise-<service>-1`
