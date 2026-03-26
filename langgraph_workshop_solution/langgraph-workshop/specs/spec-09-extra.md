# Spec 09: 前端過程顯示

## 目標
在查詢的過程中，實時顯示目前執行到哪個 node，提高使用者體驗。

## 檔案清單
- `server.py` (修改)
- `frontend/index.html` (修改)

## 規格

### 1. 後端串流實作 (server.py)
- 將 `/api/recommend` 路由從純 JSON 改為 `StreamingResponse`。
- 使用 `graph.stream` 迭代節點。
- 每個節點執行開始時，傳送該節點的名稱或對應的中文狀態。
- 最終結果完成後，傳送完整的資料物件（包含 recommendations 與 response）。

### 2. 前端實時顯示 (frontend/index.html)
- 在 UI 中新增一個進度展示區（例如一個 Stepper 或文字列表）。
- 使用 `Fetch API` 的 `ReadableStream` 讀取後端傳送的資料。
- 隨著進度更新 UI 狀態。

## node 對應顯示名稱
- `parse_input` -> 🔍 正在解析您的需求...
- `recommend` -> 🏪 正在為您搜尋合適的餐廳...
- `format_response` -> ✍️ 正在整理推薦文案...
- 其他（如 `set_budget_*`） -> ⚙️ 正在優化搜尋策略...

## 驗證
1. 輸入需求後，應能看到進度列依序更新。
2. 最終推薦結果應在所有進度完成後正常顯示。
