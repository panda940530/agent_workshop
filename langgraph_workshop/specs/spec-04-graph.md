# Spec 04: Graph 架構

## 目標
在 `graph/main.py` 中組裝完整的 LangGraph `StateGraph`，定義所有節點、邊、與條件路由，並提供 `build_graph()` 函式回傳 compile 後的 graph。

## 檔案清單
- `graph/main.py`（新建）

## 依賴
- Spec 03：`AgentState`（`graph/state.py`）
- Spec 05：所有節點函式（`graph/nodes.py`, `graph/router.py`）

> ⚠️ 建議先完成 Spec 03 + Spec 05 再實作此 spec，但也可以先建立結構、等 Spec 05 完成後再驗證。

---

## 規格

### 節點清單

| 節點名稱（字串 key） | 對應函式 | 來源檔案 |
|---|---|---|
| `"parse_input"` | `parse_input_node` | `graph/nodes.py` |
| `"set_budget_low"` | `set_budget_low` | `graph/nodes.py` |
| `"set_budget_high"` | `set_budget_high` | `graph/nodes.py` |
| `"recommend"` | `recommend_node` | `graph/nodes.py` |
| `"format_response"` | `format_response_node` | `graph/nodes.py` |

### 邊與流程

```
START
  │
  ▼
parse_input
  │
  ├─[budget_router 回傳 "budget"]──▶ set_budget_low
  │                                          │
  └─[budget_router 回傳 "premium"]─▶ set_budget_high
                                             │
                                  (兩條路都接到)
                                             ▼
                                         recommend
                                             │
                                             ▼
                                      format_response
                                             │
                                             ▼
                                            END
```

**條件路由說明：**
- `parse_input` 節點執行完後，由 `budget_router` 函式（來自 `graph/router.py`）判斷走哪條邊
- `budget_router` 回傳 `"budget"` → 走 `set_budget_low`
- `budget_router` 回傳 `"premium"` → 走 `set_budget_high`

---

### graph/main.py 完整實作

```python
from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from graph.nodes import (
    parse_input_node,
    set_budget_low,
    set_budget_high,
    recommend_node,
    format_response_node,
)
from graph.router import budget_router


def build_graph():
    workflow = StateGraph(AgentState)

    # 註冊節點
    workflow.add_node("parse_input", parse_input_node)
    workflow.add_node("set_budget_low", set_budget_low)
    workflow.add_node("set_budget_high", set_budget_high)
    workflow.add_node("recommend", recommend_node)
    workflow.add_node("format_response", format_response_node)

    # 起點 → parse_input
    workflow.add_edge(START, "parse_input")

    # parse_input → 條件路由 → set_budget_low 或 set_budget_high
    workflow.add_conditional_edges(
        "parse_input",
        budget_router,
        {
            "budget": "set_budget_low",
            "premium": "set_budget_high",
        }
    )

    # set_budget_* → recommend → format_response → 終點
    workflow.add_edge("set_budget_low", "recommend")
    workflow.add_edge("set_budget_high", "recommend")
    workflow.add_edge("recommend", "format_response")
    workflow.add_edge("format_response", END)

    return workflow.compile()
```

---

## 驗證

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from graph.main import build_graph

graph = build_graph()
result = graph.invoke({'user_input': '我想吃日式料理，預算 200 元'})
print('preferences:', result.get('preferences'))
print('budget_level:', result.get('budget_level'))
print('recs count:', len(result.get('recommendations', [])))
print('response length:', len(result.get('response', '')))
"
```

✅ 預期：
- `preferences` 包含 `cuisine_type: japanese`、`budget: 200`
- `budget_level` 為 `budget`
- `recs count` ≥ 1
- `response length` > 50
