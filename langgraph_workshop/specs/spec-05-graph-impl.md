# Spec 05: Graph 節點實作

## 目標
實作所有 LangGraph 節點函式（`graph/nodes.py`）與條件路由函式（`graph/router.py`）。
每個函式接收 `AgentState`，回傳要更新的欄位 dict；LangGraph 自動合併到 state。

## 檔案清單
- `graph/nodes.py`（在 Spec 02 的 helpers 下方繼續新增節點函式）
- `graph/router.py`（新建）

## 依賴
- Spec 02：`get_llm`, `_extract_text`, `_extract_json`（已在 nodes.py 頂部）
- Spec 03：`AgentState`

---

## 節點一覽

| 函式名稱 | 所在檔案 | 呼叫 LLM | 主要職責 |
|---|---|---|---|
| `parse_input_node` | nodes.py | ✅ | 解析使用者輸入為結構化偏好 |
| `set_budget_low` | nodes.py | ❌ | 設定 budget_level = "budget" |
| `set_budget_high` | nodes.py | ❌ | 設定 budget_level = "premium" |
| `recommend_node` | nodes.py | 條件性 | 搜尋餐廳，超過 3 間時用 LLM 篩選 |
| `format_response_node` | nodes.py | ✅ | 生成繁體中文推薦文字 |
| `budget_router` | router.py | ✅ | 判斷走 budget 或 premium 路線 |

---

## graph/nodes.py — 節點函式（接在 Spec 02 helpers 之後）

### `parse_input_node`

**職責：** 呼叫 LLM 解析 `user_input`，產生 `preferences` dict。

```python
def parse_input_node(state: AgentState) -> dict:
    llm = get_llm()
    system_prompt = """你是一個餐廳偏好解析器。請根據使用者的輸入，擷取以下資訊並回傳為純 JSON 格式：
- cuisine_type: "japanese", "italian", "taiwanese", "korean", 或 "thai"
- budget: 預算金額 (整數)。若無則回傳 null
- location: 地點字串。若無則回傳 ""

只能回傳 JSON 字串，不要包含 ```json 標籤或其他文字。"""
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.get("user_input", ""))
        ])
        content = _extract_text(response.content)
        prefs = _extract_json(content)

        # 驗證 cuisine_type
        VALID_CUISINES = ["japanese", "italian", "taiwanese", "korean", "thai"]
        if "cuisine_type" not in prefs or prefs["cuisine_type"] not in VALID_CUISINES:
            prefs["cuisine_type"] = "taiwanese"

        # 驗證 budget
        if "budget" not in prefs or not isinstance(prefs["budget"], (int, float)):
            prefs["budget"] = 500

        # 驗證 location
        if "location" not in prefs:
            prefs["location"] = ""

        return {"preferences": prefs}
    except Exception as e:
        print(f"parse_input error: {e}")
        return {"preferences": {"cuisine_type": "taiwanese", "budget": 500, "location": ""}}
```

**Fallback：** 任何例外 → `{"cuisine_type": "taiwanese", "budget": 500, "location": ""}`

---

### `set_budget_low` / `set_budget_high`

**職責：** 設定 `budget_level`，無 LLM 呼叫。

```python
def set_budget_low(state: AgentState) -> dict:
    return {"budget_level": "budget"}


def set_budget_high(state: AgentState) -> dict:
    return {"budget_level": "premium"}
```

---

### `recommend_node`

**職責：** 三層漸進式搜尋，超過 3 間時用 LLM 篩選最佳 3 間。

**搜尋邏輯（依序嘗試，直到有結果）：**

```
第一層：search_restaurants(cuisine, budget_level, max_price=budget)
         → 若結果 < 2 間，繼續

第二層：search_restaurants(cuisine, budget_level=None, max_price=budget)
         → 若結果仍為 0，繼續

第三層：search_restaurants(cuisine, budget_level=None, max_price=None)
         → 若仍為 0，回傳 error
```

```python
def recommend_node(state: AgentState) -> dict:
    prefs = state.get("preferences", {})
    cuisine = prefs.get("cuisine_type")
    budget = prefs.get("budget")
    budget_level = state.get("budget_level")

    # 三層搜尋
    results = search_restaurants(cuisine=cuisine, budget_level=budget_level, max_price=budget)
    if len(results) < 2:
        results = search_restaurants(cuisine=cuisine, budget_level=None, max_price=budget)
    if not results:
        results = search_restaurants(cuisine=cuisine, budget_level=None, max_price=None)
    if not results:
        return {"error": "抱歉，找不到符合條件的餐廳。"}

    # 超過 3 間 → LLM 挑選最佳 3 間
    if len(results) > 3:
        llm = get_llm()
        system_prompt = "你是一個餐廳挑選助手。請從以下餐廳列表中挑選出最適合的 3 間，並以純 JSON 格式回傳這 3 間餐廳的名稱列表，例如: [\"餐廳A\", \"餐廳B\", \"餐廳C\"]。"
        user_prompt = f"使用者偏好: {json.dumps(prefs, ensure_ascii=False)}\n候選餐廳: {json.dumps(results, ensure_ascii=False)}"
        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            content = _extract_text(response.content)
            selected_names = _extract_json(content)   # 回傳 list[str]，餐廳名稱
            filtered = [r for r in results if r["name"] in selected_names]
            if filtered:
                results = filtered
            # 若 LLM 選出的名稱沒有對應到任何餐廳，保留原列表
        except Exception:
            pass  # LLM 失敗時直接用原列表

    results = results[:3]  # 最多 3 間
    return {"recommendations": results}
```

---

### `format_response_node`

**職責：** 有 error 時直接回傳錯誤；否則呼叫 LLM 生成繁體中文推薦文。

```python
def format_response_node(state: AgentState) -> dict:
    if state.get("error"):
        return {"response": state["error"]}

    recs = state.get("recommendations", [])
    if not recs:
        return {"response": "抱歉，目前沒有推薦的餐廳。"}

    llm = get_llm()
    system_prompt = """你是一個專業的美食推薦助理。請用繁體中文、自然且有溫度的語氣向使用者介紹餐廳。
介紹內容需包含餐廳名稱、地點、價格、評分、特色，並適當加上 emoji 讓語意生動。"""
    user_prompt = f"使用者需求: {state.get('user_input', '')}\n精選推薦餐廳清單: {json.dumps(recs, ensure_ascii=False)}\n請幫我撰寫一段推薦文。"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        content = _extract_text(response.content)
        return {"response": content}
    except Exception:
        # Fallback：純文字列表
        return {"response": "為您推薦以下餐廳：\n" + "\n".join(
            [f"- {r['name']}: {r['specialty']}" for r in recs]
        )}
```

---

## graph/router.py — 條件路由

### `budget_router`

**職責：** 判斷 budget vs premium，回傳字串供 LangGraph 路由使用。

**注意：** 此函式使用 `temperature=0.0`（確定性）而非 `get_llm()` 的預設值 0.2。

```python
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from graph.state import AgentState


def budget_router(state: AgentState) -> str:
    user_input = state.get("user_input", "")
    prefs = state.get("preferences", {})
    budget = prefs.get("budget", 0)

    llm = ChatGoogleGenerativeAI(
        model='gemini-3.1-flash-lite-preview',
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        temperature=0.0,    # 確定性路由，不要隨機
        timeout=30,
        max_retries=2
    )

    system_prompt = """綜合考慮使用者的預算金額和語氣來判斷消費意願。
例如「隨便吃 500 元」應歸類為 budget，而「慶祝生日 400 元」也可能應歸類為 premium。
請直接回傳字串 "budget" 或 "premium"，不要有其他文字。"""
    user_prompt = f"使用者輸入: {user_input}\n預算: {budget}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        content = response.content
        if isinstance(content, list):
            content = "".join([
                c.get("text", "")
                for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            ])
        content = content.strip().lower()
        return "premium" if "premium" in content else "budget"
    except Exception:
        # Fallback：純數字判斷
        return "budget" if isinstance(budget, (int, float)) and budget <= 300 else "premium"
```

**回傳值：** `"budget"` 或 `"premium"`（字串，LangGraph 用來對應條件邊）

---

## 常見錯誤

| 症狀 | 原因 | 解法 |
|---|---|---|
| `cuisine=taiwanese budget=500`（fallback 觸發） | `_extract_text` 或 `_extract_json` 未正確處理 | 確認 Spec 02 helpers 已正確實作 |
| `recs=0` | 三層搜尋都未找到 | 檢查 `cuisine_type` 是否有拼錯 |
| `budget_router` 總是回傳 `budget` | LLM 回應包含多餘文字，`"premium"` 字串判斷邏輯未觸發 | 確認 `.strip().lower()` 後用 `in` 判斷 |

---

## 驗證

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from graph.nodes import parse_input_node, recommend_node

# 測試 parse_input_node
state = {'user_input': '我想吃日式料理，預算 200 元'}
result = parse_input_node(state)
print('parse_input:', result['preferences'])
assert result['preferences']['cuisine_type'] == 'japanese', f'Expected japanese, got {result[\"preferences\"][\"cuisine_type\"]}'
assert result['preferences']['budget'] == 200, f'Expected 200, got {result[\"preferences\"][\"budget\"]}'

# 測試 recommend_node（需先有 preferences 和 budget_level）
state['preferences'] = result['preferences']
state['budget_level'] = 'budget'
rec_result = recommend_node(state)
print('recommend:', len(rec_result.get('recommendations', [])), '間餐廳')
assert len(rec_result.get('recommendations', [])) >= 1
print('All nodes OK')
"
```

✅ 印出 `parse_input: {cuisine_type: japanese, budget: 200, ...}`、推薦 ≥ 1 間、`All nodes OK`
