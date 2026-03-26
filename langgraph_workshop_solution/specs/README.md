# Spec 總覽 — 餐廳推薦 AI Agent

本目錄包含 8 個 spec 檔案，每個 spec 對應一個實作單元。
依序給 AI Agent 執行，即可從零建出完整系統。

## 起始條件

執行前，專案中**只需要**：
```
langgraph-workshop/
├── data/
│   ├── __init__.py
│   └── restaurants.py
└── .env          ← 內含 GOOGLE_API_KEY=...
```
所有其他檔案由 spec 指示 AI 建立。

---

## 建議實作順序

```
Spec 01 → Spec 02 → Spec 03 → Spec 05 → Spec 04 → Spec 07 → Spec 08
 setup      llm      state    graph實作    graph     server   frontend
```

> Spec 06（Prompts 參考文件）不需要單獨執行，Spec 05 已內含所有 prompt 文字。
> Spec 06 保留作為修改 prompt 時的快速查閱索引。

---

## Spec 清單

| 檔案 | 主題 | 產出檔案 |
|---|---|---|
| [spec-01-setup.md](spec-01-setup.md) | 環境設定 | `.env`、虛擬環境 |
| [spec-02-llm.md](spec-02-llm.md) | LLM 初始化與工具函式 | `graph/nodes.py`（頂部） |
| [spec-03-state.md](spec-03-state.md) | Agent State 定義 | `graph/state.py`、`graph/__init__.py` |
| [spec-04-graph.md](spec-04-graph.md) | Graph 架構與組裝 | `graph/main.py` |
| [spec-05-graph-impl.md](spec-05-graph-impl.md) | Graph 節點實作 | `graph/nodes.py`（節點）、`graph/router.py` |
| [spec-06-prompts.md](spec-06-prompts.md) | LLM Prompt 文字 | 填入 Spec 05 的節點函式中 |
| [spec-07-server.md](spec-07-server.md) | FastAPI Server | `server.py` |
| [spec-08-frontend.md](spec-08-frontend.md) | 前端頁面 | `frontend/index.html` |

---

## 系統架構

```
使用者輸入
    │
    ▼
POST /api/recommend          ← server.py (Spec 07)
    │
    ▼
LangGraph StateGraph         ← graph/main.py (Spec 04)
    │
    ├── parse_input_node     ← graph/nodes.py (Spec 05)
    │       └── Gemini LLM   ← Prompt: parse_input (Spec 06)
    │
    ├── budget_router        ← graph/router.py (Spec 05)
    │       └── Gemini LLM   ← Prompt: budget_router (Spec 06)
    │
    ├── set_budget_low/high  ← graph/nodes.py (Spec 05)
    │
    ├── recommend_node       ← graph/nodes.py (Spec 05)
    │       ├── search_restaurants() ← data/restaurants.py
    │       └── Gemini LLM（超過 3 間時）← Prompt: recommend_select (Spec 06)
    │
    └── format_response_node ← graph/nodes.py (Spec 05)
            └── Gemini LLM   ← Prompt: format_response (Spec 06)
                │
                ▼
           前端頁面           ← frontend/index.html (Spec 08)
```

---

## 跨 Spec 依賴

- **Spec 02 的 helpers** (`_extract_text`, `_extract_json`) 被 Spec 05 的所有節點使用
- **Spec 03 的 `AgentState`** 被 Spec 05 的所有節點函式作為型別註解使用
- **Spec 06 的 prompts** 填入 Spec 05 的節點函式 `system_prompt` 變數中
- **Spec 04 的 `build_graph()`** 被 Spec 07 的 server 在啟動時呼叫
- **Spec 07 的 API** 被 Spec 08 的前端 `fetch` 呼叫
