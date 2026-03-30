# Fetch Profile 使用指南

從 navi-profile 倉庫為微服務拉取本地開發配置。

## 快速開始

### 方式 1：使用 Shell 函數（推薦）

1. 設定 shell 函數（首次）：

```bash
# 在你的 ~/.zshrc 或 ~/.bashrc 中加入：
source /Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/skills/project-sync/scripts/setup-alias.sh
```

2. 重新載入 shell：

```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

3. 在任何微服務專案中使用：

```bash
cd /Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt
fetch-profile                    # 自動偵測微服務並複製配置
fetch-profile --milestone v0.9    # 指定里程碑
fetch-profile --with-gradle      # 同時複製 gradle 設定
fetch-profile --dry-run          # 預覽模式
```

### 方式 2：使用微服務包裝腳本（動態路徑）

在微服務專案中使用，自動尋找主專案：

```bash
cd /Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt
bash setup/fetch-profile.sh                # 自動偵測 CRM 並動態找主專案
bash setup/fetch-profile.sh --milestone v0.9
bash setup/fetch-profile.sh --with-gradle
```

**動態路徑搜尋順序**：
1. 環境變數 `PROJECT_PROJECT_DIR`
2. 同層目錄搜尋 `fine-tune-ai-agent`
3. 父目錄搜尋（支援多種命名）
4. 向上兩層搜尋

**設定環境變數（可選）**：
```bash
export PROJECT_PROJECT_DIR=/path/to/fine-tune-ai-agent
```

### 方式 3：直接調用主專案腳本

從任何位置調用：

```bash
bash /Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/skills/project-sync/scripts/fetch-profile.sh --service ModuleA
bash /Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/skills/project-sync/scripts/fetch-profile.sh --service ModuleA --milestone v0.9
```

或使用相對路徑（從微服務專案）：

```bash
cd /Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt
bash ../fine-tune-ai-agent/.claude/skills/project-sync/scripts/fetch-profile.sh --service ModuleA
```

## 支援的微服務

- `CAM` - Service_customer-agreement-mgmt
- `UM` - Service_user-management
- `OM` - Service_order-management
- `EM` - Service_event-management
- `PM` - Service_profile-management
- `SM` - Service_sales-management

## 可用選項

```
--milestone <DXX>  指定開發里程碑 (v0.9|v1.0|v2.0，預設: v1.0)
--with-gradle      同時複製 gradle 設定 (預設只複製 resources)
--update           強制更新快取 repo
--dry-run          只顯示會複製的檔案，不實際執行
--service <名稱>   指定微服務 (使用 shell 函數時自動偵測)
--branch <分支>    指定 profile repo 分支 (預設: main)
--help             顯示說明
```

## 複製的檔案

**Resources 配置（預設）**：
- `services/{service}/src/main/resources/application-ibm.yaml`
- `services/{service}/src/main/resources/application-local.yaml`
- `services/{service}/src/main/resources/clientTruststore.p12`

**Gradle 設定（需加 --with-gradle）**：
- `gradle/wrapper/gradle-wrapper.properties`
- `platform.gradle`
- `settings.gradle`

## 配置說明

### install.conf

主專案配置檔案位於：`.claude/skills/project-sync/scripts/install.conf`

重要配置項：
- `BASE_DIR`: 微服務專案所在目錄
- `PROFILE_REPO`: navi-profile Git 倉庫
- `PROFILE_BRANCH`: 使用的分支
- `PROFILE_CACHE_DIR`: 本地快取目錄
- `DEFAULT_MILESTONE`: 預設里程碑

### 快取管理

快取位置：`~/.cache/navi-profile`

清除快取：
```bash
rm -rf ~/.cache/navi-profile
```

## 注意事項

1. 腳本會自動偵測當前微服務（使用 shell 函數時）
2. 配置檔案快取於 `~/.cache/navi-profile`
3. 這些檔案不應提交到 git（已有 pre-commit hook 保護）
4. 首次執行會從遠端克隆 navi-profile 倉庫
5. 離線時會使用本地快取

## 疑難排解

### 錯誤：找不到微服務

確認：
1. `BASE_DIR` 設定正確（在 install.conf 中）
2. 微服務專案目錄名稱符合預期格式
3. 使用正確的微服務代號

### 錯誤：找不到配置目錄

確認：
1. 里程碑名稱正確（v0.9, v1.0, v2.0）
2. navi-profile 倉庫已正確克隆到快取目錄
3. 網路連線正常（首次使用時）

### 強制重新同步

```bash
fetch-profile --update
```
