# byosp UI Design Specification

> 此文件為 byosp 應用程式的 UI 設計唯一真相來源。所有視覺設計決策必須遵循此規範。

---

## 1. 設計哲學

**Core Vibe**: Minimalist, organic-tech, fluid, connected.

設計應呈現神經網路與乾淨現代科技的融合感 -- 極簡、有機、流動、高連結性。

### 設計原則

| 原則 | 說明 |
|------|------|
| **極簡** | 去除一切不必要的視覺元素，讓內容自己說話 |
| **有機科技** | 圓潤流暢的形狀，模仿 logo 的曲線和節點連線 |
| **高對比留白** | 深炭灰 + 純白，大量 negative space |
| **克制用色** | 色彩極度節制，accent 色僅用於關鍵互動點 |

---

## 2. 色彩系統

### 2.1 品牌色板（byosp 預設主題）

**Light Mode**:

| 角色 | HSL | 用途 |
|------|-----|------|
| Primary | `222 47% 11%` | 深炭灰（shadcn zinc），CTA 按鈕、重要文字 |
| Primary Foreground | `0 0% 100%` | 白色，按鈕文字 |
| Background | `0 0% 100%` | 純白背景 |
| Card | `0 0% 100%` | 卡片表面（純白 + 邊框區隔） |
| Accent | `174 30% 94%` | 淡 teal，active state / hover |
| Accent Foreground | `174 30% 25%` | 深 teal，accent 上的文字 |
| Ring | `222 47% 11%` | 與 primary 一致 |
| Muted Foreground | `215 16% 47%` | 次要文字 |
| Border | `214 32% 91%` | 極淡邊框 |

**Dark Mode**:

| 角色 | HSL | 說明 |
|------|-----|------|
| Primary | `210 40% 98%` | 近白色前景（反轉高對比） |
| Primary Foreground | `224 71% 4%` | 近黑背景作為按鈕文字 |
| Background | `224 71% 4%` | 近黑背景帶深藍色相 |
| Card | `224 71% 4%` | 卡片表面 |
| Accent | `174 20% 14%` | 深 teal accent |
| Border | `216 34% 17%` | 微光邊框 |

### 2.2 功能色

| 語意 | Light HSL | Dark HSL | 用途 |
|------|-----------|----------|------|
| Income | `160 84% 39%` | `160 50% 48%` | 收入/別人欠你 |
| Expense | `0 84% 60%` | `0 50% 52%` | 支出/你欠別人 |
| Destructive | `0 84% 60%` | `0 50% 52%` | 危險操作 |
| Warning | `38 92% 50%` | `38 55% 52%` | 警告 |
| Settled | `210 5% 47%` | `210 4% 42%` | 已結清（灰色） |

### 2.3 用色規則

- **Primary 色（炭灰/白）用於所有 CTA 按鈕**，不隨 accent 變動
- **Accent teal 只用於**: focus ring、active indicator、tab bar 選中態、subtle hover
- **功能色（income/expense/destructive）不可替換**，語意固定
- **禁止使用非系統定義的硬編碼顏色**（如 `bg-blue-500`）

---

## 3. 排版

### 3.1 字體

- 使用系統預設 geometric sans-serif（San Francisco / Roboto / Inter）
- 品牌元素（app name、tab label）使用 **小寫格式**，呼應 logo "byosp" 的小寫風格

### 3.2 字級

| 層級 | 大小 | 字重 | 用途 |
|------|------|------|------|
| Display | `text-lg` | `font-semibold` | 頁面主數字（餘額等） |
| Title | `text-base` | `font-semibold` | 區塊標題、Modal 標題 |
| Body | `text-sm` | `font-medium` | 卡片標題、列表項目名稱 |
| Caption | `text-xs` | `font-medium` | 副標題、成員數、幣別標籤 |
| Section Label | `text-xs uppercase tracking-wider` | `font-medium` | 區塊分類標籤 |

### 3.3 排版規則

- 標題層級不超過 3 層（Display > Body > Caption）
- 數字使用 `tabular-nums` class 確保等寬對齊
- 金額顯示統一用 `toLocaleString` + 2 位小數

---

## 4. 形狀與圓角

> 避免尖銳攻擊性的直角。所有元素使用柔和圓角，呼應 logo 的流暢曲線。

| 元素 | 圓角 | 說明 |
|------|------|------|
| Card | `rounded-xl` | 12px，主要容器 |
| Button | `rounded-lg` | 8px，所有互動按鈕（shadcn 標準） |
| Input | `rounded-lg` | 8px，輸入欄位 |
| Badge | `rounded-full` | 完全圓形 |
| FAB | `rounded-full` | 完全圓形 |
| Modal sheet | `rounded-t-xl` | 底部彈出 sheet 頂部 |
| Dialog | `rounded-xl` | 確認對話框 |
| Avatar | `rounded-full` | 完全圓形 |

---

## 5. 間距與留白

### 5.1 頁面級

- 頁面內邊距：`p-4`（16px）
- 列表底部留 `pb-20`（80px），為 FAB 留空間

### 5.2 卡片內部

- 卡片內邊距：`p-3.5`（14px）
- 卡片間距：`mb-2`（8px）
- 區塊間距：`mb-5`~`mb-6`（20~24px）

### 5.3 留白原則

- **寧多不少** -- 元素間留白不足時加大，不可壓縮
- 視覺分組用留白取代分隔線（首選）或極淡 border
- 區塊標籤（Section Label）與內容間距 `mb-2`

---

## 6. 卡片設計

```
Card = rounded-xl + border border-border + bg-card
```

- **不使用陰影**（純邊框區隔），保持平面極簡感
- Dark mode 下邊框自動變為 `216 34% 17%`（微光線條）
- 卡片可按壓時（`onPress`），使用 `Pressable` 包裹
- 已結清群組卡片加 `opacity-60`

---

## 7. 按鈕設計

**尺寸（對齊 shadcn/ui 標準）：**

| Size | 高度 | 內距 | 字級 |
|------|------|------|------|
| `default` | `h-10` (40px) | `px-4` | `text-sm` |
| `sm` | `h-9` (36px) | `px-3` | `text-sm` |
| `lg` | `h-11` (44px) | `px-6` | `text-sm` |
| `icon` | `h-10 w-10` | - | `text-sm` |

**所有按鈕文字統一 `text-sm`（14px）**，不隨 size 變化。

| Variant | 用途 | 樣式 |
|---------|------|------|
| `default` | 主要 CTA | `bg-primary text-primary-foreground rounded-lg` |
| `outline` | 次要操作 | `border border-input bg-background rounded-lg` |
| `destructive` | 危險操作 | `bg-destructive text-white rounded-lg` |
| `ghost` | 低調操作 | 無背景，hover 時 `bg-accent` |

- 按鈕按壓回饋：`active:opacity-90`
- FAB 按壓回饋：`active:scale-[0.95]`
- Disabled 態：`opacity-50`

---

## 8. 圖示規範

- 圖示庫：**phosphor-react-native**（line art 風格，與 logo 一致）
- 預設大小：`20px`（Tab bar / 列表圖示）、`22px`（Action icon）
- Weight：未選中 `regular`（線條），選中 `fill`（填充）
- 顏色：跟隨文字色或 `muted-foreground`，不使用彩色圖示
- Tab bar icon 大小：`20px`

---

## 9. Tab Bar 設計

- 背景：`#FFFFFF`（light）/ `#0A0C0F`（dark）
- 分隔線：1px `border-top`，`rgba(0,0,0,0.06)` / `rgba(255,255,255,0.06)`
- 高度：`50px`
- Label 字級：`10px`，`font-weight: 500`，`letter-spacing: 0.2px`
- Active 色：跟隨當前 color scheme 的 preview 色
- Inactive 色：`#A1A1AA`（light）/ `#52525B`（dark）
- Badge 樣式：`16px` 圓形，`bg-foreground text-background`（克制的單色設計）
- **不使用陰影**，僅用 border-top 分隔

---

## 10. Modal / Sheet 設計

### Bottom Sheet（建立群組等）
- `rounded-t-2xl` 頂部圓角
- `border-t border-border` 頂部邊框
- 頂部拖曳指示器：`h-1 w-8 rounded-full bg-muted-foreground/20`
- 標題使用 `text-base font-semibold`
- 關閉按鈕：`X` icon，`20px`，`muted-foreground` 色

### Dialog（確認刪除等）
- `rounded-2xl border border-border`
- Backdrop：`bg-black/50`
- 按鈕排列：`flex-row gap-2 justify-end`，使用 `size="sm"`

---

## 11. 登入頁設計

- 全畫面 `bg-background`，垂直置中
- Logo 大小：`120px`，帶入場動畫（scale + fade）
- Subtitle：`text-sm text-muted-foreground tracking-wide`
- Logo 與按鈕間距：`mb-20`（大量留白）
- Google 登入按鈕：`size="lg"`，全寬
- Footer 文字：`text-xs opacity-50`

---

## 12. 首頁設計

### 結構（由上到下）

1. **Overall Balance** -- 一行文字 + 金額數字，不用卡片包裹
2. **Pending Settlements** -- section label + 卡片列表
3. **Pending Invitations** -- section label + 卡片列表
4. **Active Groups** -- 可拖曳排序的卡片列表
5. **Settled Groups** -- 收合式，點擊展開

### 群組卡片

- 左側拖曳把手（`DotsSixVertical`，`18px`）
- 中間：群組名（`text-sm font-medium`）+ 描述 + 成員數
- 右側：淨餘額（`income` 或 `destructive` 色）
- 右滑刪除/離開

---

## 13. Dark Mode 規則

延續 CLAUDE.md 既有規範，加上 byosp 品牌特化：

- Background 帶 `hue 210`（blue-gray），saturation `8-10%`
- Lightness 階梯：bg `4%` > card `9%` > secondary `13%` > accent `14%` > border `15%`
- Primary 反轉為亮色（`86% lightness`），實現深底淺字高對比
- 功能色飽和度降低（`50%` range），亮度適度提升

---

## 14. 多色系支援

byosp 品牌色為預設主題。使用者可在帳號設定切換至其他色系：

| ID | 名稱 | 主色 Hue |
|----|------|---------|
| `byosp` | 經典品牌 | 210（炭灰） |
| `blue` | 信任藍 | 217 |
| `green` | 活力綠 | 160 |
| `purple` | 科技紫 | 258 |
| `warm` | 翡翠金 | 165 |
| `coral` | 珊瑚橘 | 16 |
| `slate` | 石板灰 | 215 |

切換色系時，`primary`、`ring`、`accent` 等變數跟隨變動，但 `income`/`expense`/`destructive` 等語意色保持固定。
