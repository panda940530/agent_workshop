# Spec 03: Agent State 定義

## 目標
定義整個 LangGraph Agent 在執行過程中傳遞的狀態結構（`AgentState`）。
State 是各節點之間唯一的溝通媒介——每個節點讀取 state、回傳要更新的欄位。

## 檔案清單
- `graph/state.py`（新建）
- `graph/__init__.py`（新建，空檔案，讓 graph/ 成為 Python package）

## 依賴
- 無（此 spec 無外部依賴）

---

## 規格

### graph/__init__.py
空檔案，內容為空即可。

### graph/state.py

```python
from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):
    user_input: str          # 使用者原始輸入文字
    preferences: Dict[str, Any]   # 解析後的偏好，格式見下方
    budget_level: str        # "budget" 或 "premium"
    recommendations: List[Dict[str, Any]]  # 推薦餐廳列表，格式見下方
    response: str            # 最終回應文字（LLM 生成）
    error: str               # 錯誤訊息（若有）
```

---

## 欄位規格

### `user_input: str`
使用者原始輸入的自然語言字串。
例：`"我想吃日式料理，預算 200 元"`

Graph 入口時唯一需要填入的欄位，其他欄位由各節點逐步填入。

---

### `preferences: Dict[str, Any]`
由 `parse_input_node` 填入，格式：
```json
{
  "cuisine_type": "japanese",  // "japanese" | "italian" | "taiwanese" | "korean" | "thai"
  "budget": 200,               // 整數，單位元；無法解析時預設 500
  "location": ""               // 地點字串；未提及時為空字串
}
```

---

### `budget_level: str`
由 `set_budget_low` 或 `set_budget_high` 填入：
- `"budget"` — 平價路線
- `"premium"` — 高級路線

---

### `recommendations: List[Dict[str, Any]]`
由 `recommend_node` 填入，最多 3 筆，每筆格式：
```json
{
  "name": "築地鮮魚",
  "cuisine": "japanese",
  "budget_level": "budget",
  "avg_price": 200,
  "rating": 4.2,
  "location": "台北市大安區",
  "specialty": "平價生魚片丼飯"
}
```
此格式直接來自 `data/restaurants.py` 的 `RESTAURANT_DB`，無需轉換。

---

### `response: str`
由 `format_response_node` 填入，LLM 生成的繁體中文推薦文字。
若有 `error`，此欄位改存錯誤訊息。

---

### `error: str`
由 `recommend_node` 在完全找不到餐廳時填入。
`format_response_node` 偵測此欄位後直接回傳錯誤訊息而不呼叫 LLM。

---

## 注意事項

- `total=False` 代表所有欄位都是可選的。Graph 一開始只有 `user_input`，其他欄位由節點逐步填入。
- 節點回傳 `dict` 時，LangGraph 會自動合併（merge）到現有 state，不需要回傳完整 state。

---

## 驗證

```bash
python -c "
from graph.state import AgentState
# 確認 TypedDict 可正常 import
s: AgentState = {'user_input': '測試'}
print('State OK:', s)
"
```

✅ 印出 `State OK: {'user_input': '測試'}`
