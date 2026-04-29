from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage

# 导入你写的逻辑
from agent import init_crypto_agent
from langchain.messages import HumanMessage

app = FastAPI(title="CryptoExpert Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化 Agent
agent = init_crypto_agent()


# 定义请求数据格式
class ChatMessage(BaseModel):
    message: str
    thread_id: str = "1"


# 1. 路由：提供前端 HTML 页面
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# 2. 路由：处理聊天 API
@app.post("/api/chat/")
async def chat_endpoint(chat_msg: ChatMessage):
    try:
        config = {"configurable": {"thread_id": chat_msg.thread_id}}

        # 调用 Agent (这里建议使用 ainvoke 进行异步处理，但 invoke 也能跑)
        response = agent.invoke(
            {"messages": [HumanMessage(content=chat_msg.message)]},
            config
        )

        ai_reply = response['messages'][-1].content
        return {"status": "success", "reply": ai_reply}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/history/{thread_id}")
async def get_history(thread_id: str):
    try:
        config = {"configurable": {"thread_id": thread_id}}

        # 从 Sqlite 获取当前 thread_id 的状态
        state = agent.get_state(config)

        # 如果没有历史记录，返回空列表
        if not state or "messages" not in state.values:
            return {"status": "success", "history": []}

        raw_messages = state.values["messages"]
        formatted_history = []

        for msg in raw_messages:
            # 过滤消息类型：只提取用户(human)和AI(ai)的消息文本
            # 排除掉工具消息(ToolMessage)以保持前端简洁
            if msg.type == "human":
                formatted_history.append({"role": "user", "content": msg.content})
            elif msg.type == "ai" and msg.content:
                formatted_history.append({"role": "ai", "content": msg.content})

        return {"status": "success", "history": formatted_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(app, host="127.0.0.1", port=8000)