# Spec 02: LLM 初始化與共用工具函式

## 目標
在 `graph/nodes.py` 頂部建立 LLM 初始化函式與兩個共用 helper，供所有節點統一使用。
這兩個 helper 是整個系統的防呆核心——Gemini 的 `response.content` 有時回傳 `str`，有時回傳 `list[dict]`，必須統一處理。

## 檔案清單
- `graph/nodes.py`（頂部，import 區塊之後）

## 依賴
- 已完成 Spec 01（環境設定）

---

## 規格

### graph/nodes.py — 檔案開頭（import + 三個函式）

```python
import json
import re
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from graph.state import AgentState
from data.restaurants import search_restaurants


def get_llm():
    """初始化並回傳 Gemini LLM 實例。所有節點都透過此函式取得 LLM。"""
    return ChatGoogleGenerativeAI(
        model='gemini-3.1-flash-lite-preview',
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        temperature=0.2,
        timeout=30,
        max_retries=2
    )


def _extract_text(content) -> str:
    """
    將 Gemini response.content 統一轉為純字串。

    Gemini 有時回傳純字串，有時回傳 list of dicts，格式如：
      [{"type": "text", "text": "..."}, ...]
    兩種情況都要能正確處理。
    """
    if isinstance(content, list):
        return "".join([
            c.get("text", "")
            for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        ])
    return str(content)


def _extract_json(text: str):
    """
    從 LLM 輸出中穩健地提取 JSON，處理 markdown code fence 包裹的情況。

    LLM 有時回傳純 JSON，有時用 ```json ... ``` 包裹，兩種都能處理。
    若解析失敗會拋出 json.JSONDecodeError，呼叫端需自行 try/except。
    """
    text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)
```

---

## 注意事項

- **`get_llm()` 每次呼叫都回傳新實例**，不使用全域快取，避免跨請求狀態污染。
- **`temperature=0.2`** 用於一般節點；`budget_router` 另外用 `temperature=0.0` 確保路由決策確定性（見 Spec 05）。
- **`_extract_text` 必須在每個呼叫 LLM 的地方使用**，直接用 `response.content` 字串操作是常見錯誤來源。
- **`_extract_json` 失敗時拋例外**，呼叫端 try/except 後執行 fallback 邏輯。

---

## 驗證

在專案根目錄執行：

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from graph.nodes import get_llm, _extract_text, _extract_json

# 測試 get_llm
llm = get_llm()
r = llm.invoke('ping')
print('LLM OK:', type(r.content))

# 測試 _extract_text（str 格式）
assert _extract_text('hello') == 'hello'

# 測試 _extract_text（list 格式）
assert _extract_text([{'type':'text','text':'hi'},{'type':'other','text':'x'}]) == 'hi'

# 測試 _extract_json（純 JSON）
assert _extract_json('{\"a\": 1}') == {'a': 1}

# 測試 _extract_json（markdown fence）
assert _extract_json('\`\`\`json\n{\"a\": 1}\n\`\`\`') == {'a': 1}

print('All helpers OK')
"
```

✅ 印出 `All helpers OK`
