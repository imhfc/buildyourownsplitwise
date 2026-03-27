# SpliteWise UI 設計規範

## 技術選型

### 核心 UI 技術棧

| 層級         | 技術                                          | 用途                     |
| ------------ | --------------------------------------------- | ------------------------ |
| 樣式系統     | **NativeWind v4** (Tailwind CSS for RN)       | 統一樣式語法，支援暗色模式 |
| 元件庫       | **React Native Reusables (RNR)**              | shadcn/ui 風格元件，複製到專案中 |
| 無障礙原語   | **React Native Primitives** (@rn-primitives)  | Radix-like 無障礙基礎元件 |
| 圖標         | **Lucide React Native**                       | 輕量、一致的圖標系統      |
| 動畫         | **React Native Reanimated**                   | 高效能手勢與動畫          |
| 導航         | **Expo Router** (已安裝)                      | 檔案路由系統              |

### 為什麼選 RNR + NativeWind？

1. **shadcn/ui 模式** — 元件複製到專案中，100% 可控，不被框架鎖定
2. **Tailwind 語法** — Web 開發者零學習成本，className 直覺易讀
3. **暗色模式內建** — `dark:` 前綴即可，無需額外配置
4. **Expo 原生支援** — 官方文件以 Expo 為主要開發環境
5. **社群活躍** — 2025 年成長最快的 RN UI 方案

---

## 1. 色彩系統 (Color System)

### 1.1 語意化色彩 Token

採用 CSS 變數 + NativeWind，支援 Light / Dark 主題自動切換。

```
Light Mode                          Dark Mode
──────────────────────────────────────────────────
--background:    #FFFFFF             #09090B
--foreground:    #09090B             #FAFAFA
--card:          #FFFFFF             #09090B
--card-foreground: #09090B           #FAFAFA
--popover:       #FFFFFF             #09090B
--popover-foreground: #09090B        #FAFAFA

--primary:       #2563EB (Blue)      #60A5FA
--primary-foreground: #FFFFFF        #09090B

--secondary:     #F4F4F5             #27272A
--secondary-foreground: #18181B      #FAFAFA

--muted:         #F4F4F5             #27272A
--muted-foreground: #71717A          #A1A1AA

--accent:        #F4F4F5             #27272A
--accent-foreground: #18181B         #FAFAFA

--destructive:   #EF4444 (Red)       #DC2626

--border:        #E4E4E7             #27272A
--input:         #E4E4E7             #27272A
--ring:          #2563EB             #60A5FA
```

### 1.2 功能色彩 (Functional Colors)

| 用途         | 色碼                | 使用場景               |
| ------------ | ------------------- | ---------------------- |
| 收入/正值    | `#10B981` (Emerald) | 別人欠你的金額          |
| 支出/負值    | `#EF4444` (Red)     | 你欠別人的金額          |
| 已結清       | `#6B7280` (Gray)    | 已完成的結算            |
| 主操作       | `#2563EB` (Blue)    | CTA 按鈕、主要操作      |
| 次要操作     | `#7C3AED` (Purple)  | 輔助功能、標籤          |
| 警告         | `#F59E0B` (Amber)   | 提醒、待處理事項        |

### 1.3 分帳者色彩池 (Avatar Colors)

用於區分群組成員，最多支援 10 人，避免色盲混淆：

```
#2563EB  (Blue)
#7C3AED  (Purple)
#059669  (Emerald)
#DC2626  (Red)
#D97706  (Amber)
#0891B2  (Cyan)
#DB2777  (Pink)
#4F46E5  (Indigo)
#65A30D  (Lime)
#9333EA  (Violet)
```

---

## 2. 排版系統 (Typography)

### 2.1 字型

| 平台    | 字型                       |
| ------- | -------------------------- |
| iOS     | SF Pro (系統預設)           |
| Android | Roboto (系統預設)           |
| 數字    | `SF Mono` / `Roboto Mono`  |

### 2.2 字級 (Font Scale)

使用 Tailwind 的字級系統，金額數字使用等寬字型：

| Token        | 大小   | 行高   | 字重       | 用途                   |
| ------------ | ------ | ------ | ---------- | ---------------------- |
| `text-3xl`   | 30px   | 36px   | `font-bold`    | 頁面標題、金額總覽     |
| `text-2xl`   | 24px   | 32px   | `font-bold`    | 區塊標題              |
| `text-xl`    | 20px   | 28px   | `font-semibold` | 卡片標題              |
| `text-lg`    | 18px   | 28px   | `font-medium`  | 重要資訊（金額）      |
| `text-base`  | 16px   | 24px   | `font-normal`  | 內文、表單輸入         |
| `text-sm`    | 14px   | 20px   | `font-normal`  | 輔助說明、標籤         |
| `text-xs`    | 12px   | 16px   | `font-medium`  | 時間戳記、Badge        |

### 2.3 金額顯示規則

- 金額一律使用 **等寬字型** 確保數字對齊
- 正數（別人欠你）：`text-emerald-600` + `+` 前綴
- 負數（你欠別人）：`text-red-500` + `-` 前綴
- 零/已平衡：`text-muted-foreground`
- 幣別符號放在金額前方：`NT$ 1,250`

---

## 3. 間距系統 (Spacing)

### 3.1 基準單位

以 **4px** 為基準單位，使用 Tailwind spacing scale：

| Token | 值    | 用途                         |
| ----- | ----- | ---------------------------- |
| `p-1` | 4px   | 圖標內部間距                  |
| `p-2` | 8px   | 緊湊元件內距                  |
| `p-3` | 12px  | 列表項目間距                  |
| `p-4` | 16px  | 卡片內距、區塊間距（標準）     |
| `p-5` | 20px  | 頁面水平邊距                  |
| `p-6` | 24px  | 區塊之間的垂直間距            |
| `p-8` | 32px  | 頁面頂部/底部安全區域         |

### 3.2 頁面佈局

```
Safe Area Insets
├── 頁面水平邊距: px-5 (20px)
├── 區塊垂直間距: gap-6 (24px)
├── 卡片內距: p-4 (16px)
├── 列表項目間距: gap-3 (12px)
└── 底部 Tab Bar 安全區域: pb-safe
```

---

## 4. 元件規範 (Components)

### 4.1 按鈕 (Button)

RNR 的 Button 元件，四種變體：

| 變體        | 用途                 | 樣式                                          |
| ----------- | -------------------- | --------------------------------------------- |
| `default`   | 主要操作（建立群組）  | `bg-primary text-primary-foreground rounded-xl` |
| `secondary` | 次要操作（取消）      | `bg-secondary text-secondary-foreground`        |
| `outline`   | 輔助操作（篩選）      | `border border-input bg-background`             |
| `destructive` | 危險操作（刪除）    | `bg-destructive text-white`                     |
| `ghost`     | 低強調（更多選項）    | 無背景，hover 時顯示                             |

**尺寸：**
- `default`: h-12 px-5 (觸控友好，48px 高)
- `sm`: h-9 px-3
- `lg`: h-14 px-8 (全寬 CTA)
- `icon`: h-10 w-10 (圖標按鈕)

**規則：**
- 每個畫面最多 **1 個** `default` 按鈕作為主要 CTA
- 所有可點擊區域最小 **44x44px**（Apple HIG 規範）
- 按鈕圓角統一使用 `rounded-xl` (12px)

### 4.2 卡片 (Card)

```
Card                     rounded-2xl border border-border bg-card shadow-sm
├── CardHeader           p-4 pb-2
│   ├── CardTitle        text-xl font-semibold
│   └── CardDescription  text-sm text-muted-foreground
├── CardContent          p-4 pt-0
└── CardFooter           p-4 pt-0 flex-row justify-end gap-2
```

**群組卡片特殊規則：**
- 左側顯示群組成員 Avatar 堆疊（最多 3 個 + `+N`）
- 右側顯示該群組的淨餘額（正/負色彩）
- 點擊整張卡片進入群組詳情

### 4.3 列表項目 (List Item)

費用和結算紀錄使用統一的列表格式：

```
┌─────────────────────────────────────────────┐
│ [Icon]  費用描述                    NT$ 420  │
│         付款人 · 3月27日              均分    │
└─────────────────────────────────────────────┘
```

- 左側：類別圖標 (40x40, `rounded-full bg-muted`)
- 中間：標題 (`text-base font-medium`) + 副標題 (`text-sm text-muted-foreground`)
- 右側：金額 (`text-lg font-semibold`) + 分帳方式標籤

### 4.4 輸入框 (Input)

```
Input       h-12 rounded-xl border border-input bg-background px-4 text-base
            focus:ring-2 focus:ring-ring
Label       text-sm font-medium text-foreground mb-1.5
Helper      text-xs text-muted-foreground mt-1
Error       text-xs text-destructive mt-1
```

**規則：**
- 浮動標籤或頂部標籤（不使用 placeholder 當標籤）
- 錯誤狀態：`border-destructive` + 錯誤訊息
- 金額輸入框右側顯示幣別 Badge

### 4.5 Avatar

```
Size        用途                  樣式
xs (24px)   列表中小頭像          text-xs
sm (32px)   堆疊頭像組            text-sm
md (40px)   列表項目              text-base
lg (56px)   個人資料              text-xl
xl (80px)   設定頁大頭像          text-2xl
```

- 顯示使用者名稱首字（中文取第一個字，英文取前兩個字母大寫）
- 背景色從「分帳者色彩池」依序分配
- 圓形：`rounded-full`

### 4.6 底部操作表 (Bottom Sheet)

用於新增消費、選擇分帳方式等操作：

```
BottomSheet
├── Handle Bar       w-10 h-1 rounded-full bg-muted-foreground/30 self-center mb-4
├── Title            text-xl font-semibold px-5
├── Content          px-5 gap-4
└── Footer           px-5 pb-safe gap-2
    ├── Button (default)    "儲存"
    └── Button (ghost)      "取消"
```

**規則：**
- 背景使用 `bg-background` + 頂部 `rounded-t-3xl`
- 背景遮罩 `bg-black/50`
- 支援拖曳手勢關閉
- 使用 `@gorhom/bottom-sheet`

### 4.7 分帳可視化元件 (Expense Split Visualization)

獨特的分帳比例顯示元件：

```
┌──────────────────────────────────────────┐
│  ████████████  ████████  ████  ████████  │
│  Alice 35%     Bob 25%   你 10% Carol 30% │
└──────────────────────────────────────────┘
```

- 水平堆疊條 (Stacked Bar)，每人一個顏色段
- 段落寬度按比例分配
- 下方顯示名稱 + 百分比/金額
- 使用分帳者色彩池

---

## 5. 圖標系統 (Icons)

### 5.1 圖標庫

使用 **Lucide React Native** 取代 MaterialCommunityIcons：
- 更現代的線條風格
- 與 shadcn/ui / RNR 生態一致
- 輕量：僅打包使用到的圖標

### 5.2 標準圖標對照表

| 功能       | 圖標名稱         | 使用場景         |
| ---------- | ---------------- | ---------------- |
| 群組       | `Users`          | Tab、群組相關    |
| 新增       | `Plus`           | FAB、新增按鈕    |
| 消費       | `Receipt`        | 消費紀錄         |
| 結算       | `ArrowLeftRight` | 結算相關         |
| 設定       | `Settings`       | Tab、設定頁      |
| 刪除       | `Trash2`         | 刪除操作         |
| 編輯       | `Pencil`         | 編輯操作         |
| 返回       | `ChevronLeft`    | 導航返回         |
| 金額       | `DollarSign`     | 金額輸入         |
| 搜尋       | `Search`         | 搜尋功能         |
| 登出       | `LogOut`         | 登出按鈕         |
| 餐飲       | `UtensilsCrossed`| 費用分類         |
| 交通       | `Car`            | 費用分類         |
| 購物       | `ShoppingBag`    | 費用分類         |
| 住宿       | `Home`           | 費用分類         |
| 娛樂       | `Gamepad2`       | 費用分類         |
| 其他       | `MoreHorizontal` | 費用分類         |

### 5.3 圖標尺寸

| 場景         | 尺寸   | Tailwind          |
| ------------ | ------ | ----------------- |
| Tab Bar      | 24px   | `size-6`          |
| 列表圖標     | 20px   | `size-5`          |
| 按鈕內圖標   | 16px   | `size-4`          |
| 裝飾/空狀態  | 48px   | `size-12`         |

---

## 6. 動畫與互動 (Motion & Interaction)

### 6.1 動畫原則

- **有目的** — 動畫應引導注意力或提供回饋，不是裝飾
- **快速** — 大部分過渡 200-300ms
- **自然** — 使用 spring 動畫模擬物理特性

### 6.2 標準動畫

| 互動             | 動畫                           | 時長     |
| ---------------- | ------------------------------ | -------- |
| 頁面切換         | Shared Element Transition       | 300ms    |
| 列表項目進入     | FadeIn + SlideUp               | 200ms    |
| 按鈕按下         | Scale(0.97) + Opacity(0.7)     | 100ms    |
| 卡片按下         | Scale(0.98)                    | 150ms    |
| Bottom Sheet 展開 | Spring (damping: 20)          | ~400ms   |
| Toast 通知       | SlideDown + FadeIn             | 250ms    |
| 數字變化         | 數字滾動動畫                    | 300ms    |
| 滑動刪除         | SwipeLeft + FadeOut            | 200ms    |

### 6.3 手勢互動

- **左滑列表項**：顯示刪除/編輯操作
- **下拉刷新**：Pull-to-Refresh 更新列表
- **長按卡片**：顯示快捷操作選單

---

## 7. 暗色模式 (Dark Mode)

### 7.1 實作方式

使用 NativeWind 的 `dark:` 前綴，跟隨系統設定：

```tsx
<View className="bg-background dark:bg-background">
  <Text className="text-foreground dark:text-foreground">
    ...
  </Text>
</View>
```

由於使用 CSS 變數，`dark:` 前綴會自動套用對應的暗色值。

### 7.2 暗色模式規則

- 避免純黑 `#000000`，使用 `#09090B` 作為背景
- 卡片使用微妙的邊框 `border-border` 區分層級，而非陰影
- 圖片/圖標需確認在暗色背景下的可見性
- 功能色（紅/綠）在暗色模式下適當降低飽和度

---

## 8. 頁面佈局規範 (Screen Layouts)

### 8.1 群組列表頁（首頁）

```
┌─ Safe Area ──────────────────────────────┐
│                                          │
│  SpliteWise                    [Avatar]  │  ← Header
│                                          │
│  ┌─ 總覽卡片 ─────────────────────────┐  │
│  │  你的淨餘額                        │  │
│  │  + NT$ 2,350              3 個群組  │  │
│  └────────────────────────────────────┘  │
│                                          │
│  群組                                    │
│  ┌────────────────────────────────────┐  │
│  │ 🏠 日本旅遊     NT$ +1,200        │  │
│  │    4 人 · 12 筆消費                │  │
│  ├────────────────────────────────────┤  │
│  │ 🍽 室友伙食費    NT$ -450          │  │
│  │    3 人 · 8 筆消費                 │  │
│  ├────────────────────────────────────┤  │
│  │ 🎮 週末聚會      NT$ +1,600       │  │
│  │    5 人 · 3 筆消費                 │  │
│  └────────────────────────────────────┘  │
│                                          │
│                              [+ FAB]     │  ← 浮動新增按鈕
│                                          │
│  [群組]              [設定]              │  ← Tab Bar
└──────────────────────────────────────────┘
```

### 8.2 群組詳情頁

```
┌─ Header ─────────────────────────────────┐
│  ← 返回    日本旅遊            [...]     │
├──────────────────────────────────────────┤
│                                          │
│  ┌─ 餘額總覽 ─────────────────────────┐  │
│  │  [Avatar堆疊]                      │  │
│  │  你借出了 NT$ 1,200               │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │ ████████ ████ ██████████████ │  │  │
│  │  │ Alice    你   Bob            │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [消費紀錄]  [結算]                      │  ← Tabs
│                                          │
│  3月27日                                 │
│  ┌────────────────────────────────────┐  │
│  │ 🍽 晚餐       Alice 付   NT$ 1,800│  │
│  │               均分 4 人            │  │
│  ├────────────────────────────────────┤  │
│  │ 🚗 計程車     你付了     NT$ 600  │  │
│  │               均分 4 人            │  │
│  └────────────────────────────────────┘  │
│                                          │
│  3月26日                                 │
│  ┌────────────────────────────────────┐  │
│  │ ...                                │  │
│  └────────────────────────────────────┘  │
│                                          │
│                    [+ 新增消費 FAB]       │
└──────────────────────────────────────────┘
```

### 8.3 新增消費（Bottom Sheet）

```
┌──────────────────────────────────────────┐
│  ──── (Handle)                           │
│                                          │
│  新增消費                       ✕ 關閉   │
│                                          │
│  消費描述                                │
│  ┌────────────────────────────────────┐  │
│  │ 晚餐                              │  │
│  └────────────────────────────────────┘  │
│                                          │
│  金額                                    │
│  ┌──────────────────────────── [TWD] ─┐  │
│  │ 1,800                              │  │
│  └────────────────────────────────────┘  │
│                                          │
│  付款人                                  │
│  ┌────────────────────────────────────┐  │
│  │ [A] Alice  ✓                       │  │
│  │ [B] Bob                            │  │
│  │ [你] Jason                         │  │
│  └────────────────────────────────────┘  │
│                                          │
│  分帳方式                                │
│  [ 均分 ] [ 比例 ] [ 精確金額 ] [ 份數 ] │
│                                          │
│  ┌─ 儲存 ────────────────────────────┐   │
│  │             儲存消費               │   │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 9. 空狀態與載入 (Empty & Loading States)

### 9.1 空狀態

每個列表都需要空狀態，包含：
- 一個大圖標 (`size-12 text-muted-foreground`)
- 標題文字 (`text-lg font-medium`)
- 說明文字 (`text-sm text-muted-foreground`)
- CTA 按鈕（如適用）

範例：
```
         [Users 圖標]
     還沒有任何群組
   建立一個群組開始分帳吧！

     [建立群組 按鈕]
```

### 9.2 載入狀態

- 列表：使用 **Skeleton** 佔位元件（3-5 個灰色閃爍方塊）
- 按鈕：顯示 Spinner + 禁用狀態
- 頁面：全螢幕居中 Spinner
- 下拉刷新：使用原生 RefreshControl

---

## 10. 遷移計畫 (Migration from React Native Paper)

### 階段一：基礎建設
1. 安裝 NativeWind v4 + Tailwind CSS v4
2. 設定 `global.css` 定義 CSS 變數（色彩 token）
3. 安裝 RNR CLI 並初始化
4. 複製基礎元件：Button、Card、Input、Text

### 階段二：共用元件
5. 建立 Avatar 元件
6. 建立 BottomSheet 包裝元件
7. 建立 Skeleton 載入元件
8. 設定 Lucide 圖標

### 階段三：頁面遷移
9. 遷移 `_layout.tsx`（移除 PaperProvider，改用 NativeWind ThemeProvider）
10. 逐頁遷移，保持功能不變
11. 新增暗色模式切換

### 階段四：增強
12. 加入動畫（Reanimated）
13. 加入手勢互動（Swipeable）
14. 最終 UI 微調與測試
