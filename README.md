# Build Your Own Splitwise (BYOSW) 

絕對免費，全部由 AI 輔助開發（Vibe Coding）的分帳系統。

## 🌟 主要功能 (Features)
- **群組與開銷管理**：建立多個群組，清楚記錄每一筆共同開銷。
- **多種分帳模式**：
  - **均分**：將總金額平均分攤給所有參與者。
  - **指定金額**：各參與者的分攤金額各別指定。
  - **百分比分帳**：依據給定的百分比拆分總額。
- **智慧結算演算法**：運用淨餘額圖與貪婪匹配（Max-Heap），將繁雜的債務關係化簡為最小交易次數（誰最少次數還款給誰）。
- **多幣別與即時匯率**：整合即時台銀匯率擷取服務，支援多幣別花費與結算轉換，並搭配 Redis 作為快取。
- **高度安全性**：以 BCrypt 加密密碼，並使用 JWT 處理身份驗證與操作授權。

## 🏗 技術架構 (Architecture)
本專案的後端採用 **Clean Architecture（乾淨架構）** 打造，嚴格限制各層之間的相依關係，以確保後續維護的品質與高可測性：

### 系統分層設計
1. **API 層 (`app/api/`)**：僅負責接收 HTTP 請求與定義路由，禁止包含任何業務邏輯。
2. **Schemas 層 (`app/schemas/`)**：使用 Pydantic 提供快速的資料驗證 (Validation)。
3. **Services 層 (`app/services/`)**：存放核心的業務邏輯、分帳與結算演算法。
4. **Models 層 (`app/models/`)**：宣告 SQLAlchemy ORM 資料庫實體模型。
5. **Core 層 (`app/core/`)**：基礎設施配置，例如 Config、DB 連線、Security 以及 Redis 注入等。

> **開發規範**：上層可呼叫下層，下層 (如 Models) 嚴禁從上層 (`services/`, `api/`) 匯入任何模組，維持單向依賴。此外所有呼叫流程皆為非同步 (Async)。

### 核心技術棧
- **後端框架**：FastAPI (Python 3.x)
- **資料庫**：PostgreSQL 16 搭配非同步 SQLAlchemy (`asyncpg`)
- **快取系統**：Redis 7
- **資料遷移**：Alembic
- **測試**：pytest + pytest-asyncio
- **容器化**：Docker & Docker Compose

## 🚀 如何本地部署 (Local Deployment)

本專案包含**後端 (FastAPI)** 與**前端行動裝置 App (Expo / React Native)**，根據您的作業系統 (macOS/iOS 或 Windows)，部署與啟動方式會有一些差異。

### 第一部分：後端伺服器 (Backend)

**【前置需求】** 所有作業系統皆需安裝 [Docker](https://www.docker.com/) 與 Git。

#### 1. 設定環境變數
不論作業系統為何，請先將環境變數範例檔複製為正式配置檔：
```bash
# 在專案根目錄執行
cp backend/.env.example backend/.env
```

#### 2. 啟動基礎服務 (DB & Redis)
我們統一透過 Docker 來運行資料庫與快取：
```bash
docker compose up -d db redis
```

#### 3. 啟動 FastAPI 伺服器
您可以依照您的作業系統，選擇在本機啟動 API：

🍎 **macOS / Linux 部署：**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

🪟 **Windows 部署：**
```powershell
cd backend
python -m venv venv
# 透過 Scripts 資料夾啟動虛擬環境
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
啟動後，前往 [http://localhost:8000/docs](http://localhost:8000/docs) 即可造訪 API 介面。

---

### 第二部分：前端行動 App (Mobile)

我們使用 Expo 建構行動版本。請確保已安裝 **Node.js** (建議 v18 以上)。

#### 1. 安裝套件
首先進入 `mobile` 資料夾並安裝依賴：
```bash
cd mobile
npm install
```

#### 2. 啟動 App
🍎 **macOS (目標為 iOS)：**
如果您使用 Mac，您可以藉由 Xcode 啟動 iOS 模擬器：
```bash
# 啟動並在 iOS 模擬器中開啟
npm run ios
```
*(需事先安裝 Xcode 與 iOS Simulator。)*

🪟 **Windows (目標為 Android / Web)：**
由於 Apple 限制，Windows 上無法直接運行 iOS 模擬器。你可以使用 Android 模擬器，或是直接使用 Expo Go App 掃描在實體手機上預覽：
```bash
# 啟動並在 Android 模擬器中開啟 (需事先安裝 Android Studio)
npm run android

# 或是單純啟動 Expo 伺服器，利用實體手機掃描 QR Code
npm start
```
