# Spec 08: 前端頁面

## 目標
建立單一 HTML 檔案（`frontend/index.html`），HTML + CSS + JavaScript 全部寫在同一個檔案中，串接後端 API 並展示推薦結果。

## 檔案清單
- `frontend/index.html`（新建）

## 依賴
- Spec 07：後端 API `POST http://localhost:8000/api/recommend`

---

## API 串接規格（前端需遵守）

### 請求
```javascript
const response = await fetch("http://localhost:8000/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_input: userInput })
});
const data = await response.json();
```

### 回應欄位
| 欄位 | 型別 | 說明 |
|---|---|---|
| `data.preferences.cuisine_type` | string | 料理類型（`"japanese"` 等） |
| `data.preferences.budget` | number | 預算金額 |
| `data.budget_level` | string | `"budget"` 或 `"premium"` |
| `data.recommendations` | array | 餐廳陣列，最多 3 筆 |
| `data.recommendations[i].name` | string | 餐廳名稱 |
| `data.recommendations[i].location` | string | 地點 |
| `data.recommendations[i].avg_price` | number | 平均價格 |
| `data.recommendations[i].rating` | number | 評分（滿分 5） |
| `data.recommendations[i].specialty` | string | 特色菜 |
| `data.response` | string | LLM 生成的推薦文字 |
| `data.error` | string \| null | 錯誤訊息（無錯誤時為 null） |

---

## 頁面功能規格

### 1. 標題區
- 應用名稱：`智慧餐廳推薦`

### 2. 輸入區
- 文字輸入框
  - `placeholder`：`例如：我想吃日式料理，預算 200 元`
  - 按下 Enter 鍵等同點擊推薦按鈕
- 「推薦」按鈕
  - 點擊後發送 API 請求
  - 請求期間：按鈕文字改為「推薦中...」並設為 `disabled`
  - 請求完成後：恢復按鈕文字與可點擊狀態

### 3. 錯誤訊息區
- 預設隱藏，以下情況顯示：
  - 輸入框為空時點擊按鈕：顯示「請先輸入你的餐廳需求」
  - API 回傳 `error` 欄位非 null：顯示 `data.error`
  - `fetch` 拋出例外（後端未啟動）：顯示「無法連線到伺服器，請確認後端是否已啟動」

### 4. Loading 狀態
- 請求期間顯示 loading 提示（文字或動畫）
- 請求完成後隱藏

### 5. Agent 決策過程區
- API 成功後顯示，失敗時隱藏
- 展示三個資訊（用標籤/卡片方式呈現）：
  - 料理類型：`preferences.cuisine_type` → 中文對照（見下方 cuisineMap）
  - 預算：`preferences.budget` 元
  - 路線：`budget_level` → `"budget"` 顯示為「平價」，`"premium"` 顯示為「高級」

### 6. 推薦結果區
- API 成功後顯示，失敗時隱藏
- 上方：`response` 欄位的文字內容（支援換行 `\n` → `<br>`）
- 下方：每間餐廳一張卡片，顯示：
  - 餐廳名稱（顯著）
  - 地點（`location`）
  - 平均價格：`$` + `avg_price` 元
  - 評分：`rating` / 5.0（可加星星符號 ⭐）
  - 特色：`specialty`

---

## 資料對照表（JavaScript）

```javascript
const cuisineMap = {
    'japanese':  '🍣 日式料理',
    'italian':   '🍝 義式料理',
    'taiwanese': '🍚 台式料理',
    'korean':    '🌶️ 韓式料理',
    'thai':      '🇹🇭 泰式料理'
};

const budgetLevelMap = {
    'budget':  '平價',
    'premium': '高級'
};
```

---

## 完整 JavaScript 流程

```javascript
async function getRecommendation() {
    const userInput = document.getElementById('userInput').value.trim();

    // 1. 驗證輸入
    if (!userInput) {
        showError('請先輸入你的餐廳需求');
        return;
    }
    hideError();

    // 2. 設定 loading 狀態
    setLoading(true);

    try {
        // 3. 呼叫 API
        const response = await fetch('http://localhost:8000/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: userInput })
        });
        const data = await response.json();

        // 4. 檢查 API 錯誤
        if (data.error) {
            showError(data.error);
            return;
        }

        // 5. 顯示結果
        displayDecision(data.preferences, data.budget_level);
        displayRecommendations(data.response, data.recommendations);

    } catch (e) {
        showError('無法連線到伺服器，請確認後端是否已啟動');
    } finally {
        // 6. 恢復按鈕狀態（無論成功或失敗）
        setLoading(false);
    }
}
```

---

## 視覺風格

> ⚡ **這個區塊自由發揮！** 以下為示範風格，請根據自己的喜好替換。

風格範例：
- 「日式和風：深色背景 (#1e1b18) 搭配暖金色 (#c29957)，Noto Serif TC 字型」
- 「賽博龐克：深紫背景，霓虹綠/粉紅高亮，等寬字型」
- 「極簡北歐：大量留白，淡灰底色，細線邊框，Inter 字型」
- 「復古台灣：磚紅色調，毛筆感標題字型，復古圖案邊框」
- 「可愛卡通：粉色系，大圓角，陰影卡片，手寫字型」

**功能需求（固定，不可省略）：**
- 頁面在手機與桌面都能正常顯示（響應式）
- 餐廳卡片在桌面排成 2-3 欄，在手機排成 1 欄
- Loading 狀態有視覺回饋（文字或 spinner）
- 錯誤訊息用紅色或警示色顯示

---

## 驗證

### 測試 A：正常流程
1. 開啟 `http://localhost:8000`
2. 輸入「我想吃日式料理，預算 200 元」，點擊推薦
3. ✅ 應看到 Agent 決策區（cuisine=日式料理、budget=200、路線=平價）和餐廳卡片

### 測試 B：空輸入驗證
1. 不輸入任何文字，直接按推薦
2. ✅ 應顯示「請先輸入你的餐廳需求」

### 測試 C：後端未啟動
1. 停止後端 server
2. 輸入任意文字並按推薦
3. ✅ 應顯示「無法連線到伺服器，請確認後端是否已啟動」
