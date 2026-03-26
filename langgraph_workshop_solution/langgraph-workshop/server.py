from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import asyncio

load_dotenv()  # 必須在 import graph 之前呼叫

from graph.main import build_graph

app = FastAPI(title="Restaurant Recommendation API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph
graph = build_graph()

# 掛載前端靜態檔案
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def read_index():
    return RedirectResponse(url="/frontend/index.html")


class RecommendRequest(BaseModel):
    user_input: str

@app.post("/api/recommend")
async def recommend(req: RecommendRequest):
    async def event_generator():
        try:
            # 使用 graph.stream 迭代節點
            final_result = {}
            async for chunk in graph.astream({"user_input": req.user_input}):
                for node_name, state_update in chunk.items():
                    # 傳送目前節點名稱給前端
                    yield f"data: {json.dumps({'node': node_name})}\n\n"
                    final_result.update(state_update)
                
                # 稍微延遲讓前端有時間顯示進度（僅開發展示用）
                await asyncio.sleep(0.3)

            # 傳送最終結果
            yield f"data: {json.dumps({
                'final': True,
                'preferences': final_result.get('preferences', {}),
                'budget_level': final_result.get('budget_level', ''),
                'recommendations': final_result.get('recommendations', []),
                'response': final_result.get('response', ''),
            })}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
