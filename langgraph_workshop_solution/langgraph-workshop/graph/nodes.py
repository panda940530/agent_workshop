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
        model='gemini-2.5-flash-lite',
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


def parse_input_node(state: AgentState) -> dict:
    llm = get_llm()
    system_prompt = """你是一個餐廳偏好解析器。請根據使用者的輸入，擷取以下資訊並回傳為純 JSON 格式：
- cuisine_type: "japanese", "italian", "taiwanese", "korean", 或 "thai"
    - "thai": 包含打拋、冬蔭功、泰式咖哩、酸辣等描述
    - "japanese": 包含壽司、拉麵、丼飯、居酒屋等描述
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


def set_budget_low(state: AgentState) -> dict:
    return {"budget_level": "budget"}


def set_budget_high(state: AgentState) -> dict:
    return {"budget_level": "premium"}


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
