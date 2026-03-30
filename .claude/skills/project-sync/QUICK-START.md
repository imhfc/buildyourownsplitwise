# Fetch Profile 快速開始

三種使用方式，選擇最適合你的：

## 方式 1：Shell 函數（推薦）

**優點**：最簡單，在任何微服務中都能使用

**設定一次**（永久生效）：
```bash
# 在 ~/.zshrc 或 ~/.bashrc 加入：
source /Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent/.claude/skills/project-sync/scripts/setup-alias.sh

# 重新載入
source ~/.zshrc
```

**使用**：
```bash
cd /path/to/any/microservice
fetch-profile                    # 自動偵測並複製
fetch-profile --milestone v0.9
```

---

## 方式 2：微服務包裝腳本（動態路徑）

**優點**：不需設定，自動找主專案

**使用**：
```bash
cd /Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt
bash setup/fetch-profile.sh      # 自動找主專案並執行
bash setup/fetch-profile.sh --milestone v0.9
```

**動態搜尋**：
1. 環境變數 `PROJECT_PROJECT_DIR`
2. 同層目錄 `../fine-tune-ai-agent`
3. 父目錄搜尋（多種命名）
4. 向上兩層搜尋

---

## 方式 3：直接調用主專案

**優點**：完全控制，適合腳本化

**使用**：
```bash
# 指定微服務
bash /path/to/fine-tune-ai-agent/.claude/skills/project-sync/scripts/fetch-profile.sh --service ModuleA

# 從微服務專案使用相對路徑
cd /Users/chaokenyuan/Desktop/Work/projects/Service_custr-relationship-mgmt
bash ../fine-tune-ai-agent/.claude/skills/project-sync/scripts/fetch-profile.sh --service ModuleA
```

---

## 常用選項

```bash
--milestone v0.9        # 指定里程碑（v0.9|v1.0|v2.0）
--with-gradle          # 同時複製 gradle 設定
--update               # 強制更新快取
--dry-run              # 預覽模式
--help                 # 顯示完整說明
```

---

## 支援的微服務

- `CAM` - Service_customer-agreement-mgmt
- `UM` - Service_user-management
- `OM` - Service_order-management
- `EM` - Service_event-management
- `PM` - Service_profile-management
- `SM` - Service_sales-management

---

## 複製的檔案

**預設（Resources）**：
- application-ibm.yaml
- application-local.yaml
- clientTruststore.p12

**可選（加 --with-gradle）**：
- gradle/wrapper/gradle-wrapper.properties
- platform.gradle
- settings.gradle

---

## 疑難排解

### 找不到主專案

**方式 2** 使用時，如果自動搜尋失敗：
```bash
export PROJECT_PROJECT_DIR=/Users/chaokenyuan/Desktop/Work/projects/fine-tune-ai-agent
```

### 找不到微服務

**方式 3** 使用時，確認：
- `BASE_DIR` 設定正確（在 `.claude/skills/project-sync/scripts/install.conf`）
- 微服務目錄名稱正確

### 找不到配置

確認：
- 里程碑名稱正確（v0.9, v1.0, v2.0）
- 網路連線正常（首次使用）

強制重新同步：
```bash
fetch-profile --update
```

---

## 完整文件

詳細說明請參閱：`.claude/skills/project-sync/USAGE.md`
