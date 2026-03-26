import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from graph.state import AgentState


def budget_router(state: AgentState) -> str:
    user_input = state.get("user_input", "")
    prefs = state.get("preferences", {})
    budget = prefs.get("budget", 0)

    llm = ChatGoogleGenerativeAI(
        model='gemini-2.5-flash-lite',
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
