# Spec 07: FastAPI Server

## 目標
建立 `server.py`，提供 REST API 給前端呼叫，並同時掛載前端靜態檔案，讓瀏覽器可以直接透過 `http://localhost:8000` 開啟前端頁面。

## 檔案清單
- `server.py`（專案根目錄）

## 依賴
- Spec 04：`build_graph()`（`graph/main.py`）
- Spec 08：`frontend/index.html`（靜態檔掛載需要此目錄存在）

---

## 規格

### 完整實作

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # 必須在 import graph 之前呼叫，確保 GOOGLE_API_KEY 已載入

from graph.main import build_graph

app = FastAPI(title="Restaurant Recommendation API")

# CORS：允許所有來源（前端從 file:// 或不同 port 存取時需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 在啟動時 compile graph（只做一次，不在每個請求中重建）
graph = build_graph()

# 掛載前端靜態檔案，讓 http://localhost:8000/frontend/index.html 可存取
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def read_index():
    """根路徑重導向到前端頁面。"""
    return RedirectResponse(url="/frontend/index.html")


class RecommendRequest(BaseModel):
    user_input: str  # 使用者輸入的自然語言字串


@app.post("/api/recommend")
async def recommend(req: RecommendRequest):
    try:
        result = graph.invoke({"user_input": req.user_input})
        return JSONResponse(
            content={
                "preferences": result.get("preferences", {}),
                "budget_level": result.get("budget_level", ""),
                "recommendations": result.get("recommendations", []),
                "response": result.get("response", ""),
                "error": result.get("error"),
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
```

---

## API 規格

### `POST /api/recommend`

**Request Body（JSON）：**
```json
{"user_input": "我想吃日式料理，預算 200 元"}
```

**成功 Response（HTTP 200）：**
```json
{
  "preferences": {
    "cuisine_type": "japanese",
    "budget": 200,
    "location": ""
  },
  "budget_level": "budget",
  "recommendations": [
    {
      "name": "築地鮮魚",
      "cuisine": "japanese",
      "budget_level": "budget",
      "avg_price": 200,
      "rating": 4.2,
      "location": "台北市大安區",
      "specialty": "平價生魚片丼飯"
    }
  ],
  "response": "為您推薦...",
  "error": null
}
```

**錯誤 Response（HTTP 200，但含 error 欄位）：**
```json
{"error": "錯誤訊息"}
```

> ⚠️ 注意：即使出錯也回傳 HTTP 200，`error` 欄位非 null。前端需檢查此欄位。

### `GET /`
重導向到 `GET /frontend/index.html`

### `GET /frontend/index.html`
回傳前端頁面 HTML

---

## 關鍵設計決策

| 決策 | 原因 |
|---|---|
| `load_dotenv()` 在 import graph 之前 | graph 初始化時呼叫 `get_llm()`，需要 `GOOGLE_API_KEY` 已在環境變數中 |
| `graph = build_graph()` 在模組層級 | 避免每個請求都重新 compile graph（昂貴操作） |
| `JSONResponse` + `charset=utf-8` header | 避免 Windows PowerShell 顯示中文亂碼 |
| CORS `allow_origins=["*"]` | 開發環境，允許 file:// 直接呼叫 API |

---

## 啟動方式

```bash
# 確認虛擬環境已啟動，然後：
uvicorn server:app --reload --port 8000
```

---

## 驗證

### 方式一：瀏覽器
開啟 `http://localhost:8000`，應自動重導向到前端頁面。

### 方式二：Windows PowerShell
```powershell
$body = '{"user_input": "我想吃日式料理，預算 200 元"}'
$r = Invoke-RestMethod -Uri http://localhost:8000/api/recommend -Method POST `
     -Headers @{"Content-Type"="application/json"} `
     -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
Write-Host "cuisine=$($r.preferences.cuisine_type) budget=$($r.preferences.budget) level=$($r.budget_level) recs=$($r.recommendations.Count)"
```

### 方式三：curl（macOS/Linux）
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_input": "我想吃日式料理，預算 200 元"}'
```

✅ 預期：`cuisine=japanese budget=200 level=budget recs>=1`，終端機無亂碼
