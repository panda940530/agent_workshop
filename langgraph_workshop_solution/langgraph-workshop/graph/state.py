from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):
    user_input: str          # 使用者原始輸入文字
    preferences: Dict[str, Any]   # 解析後的偏好
    budget_level: str        # "budget" 或 "premium"
    recommendations: List[Dict[str, Any]]  # 推薦餐廳列表
    response: str            # 最終回應文字（LLM 生成）
    error: str               # 錯誤訊息（若有）
