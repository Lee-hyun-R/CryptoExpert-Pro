import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from langchain_core.messages import HumanMessage

from agent import create_crypto_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_CONFIGS = {
    "deepseek-chat": {"name": "deepseek-chat", "provider": "deepseek", "label": "DeepSeek Chat"},
    "qwen3.6-max-preview": {"name": "qwen3.6-max-preview", "provider": "openai", "label": "Qwen 3.6 Max"},
}

agents: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started")
    yield
    logger.info("Shutting down application...")


app = FastAPI(title="CryptoExpert Pro", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatMessage(BaseModel):
    message: str
    thread_id: str | None = None
    model: str = "deepseek-chat"


# 1. 路由：提供前端 HTML 页面
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat/")
async def chat_endpoint(chat_msg: ChatMessage) -> dict:
    thread_id = chat_msg.thread_id or os.urandom(16).hex()
    model = chat_msg.model
    logger.info(f"Chat request received, thread_id: {thread_id}, model: {model}")

    if model not in MODEL_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Invalid model: {model}")

    if model not in agents:
        logger.info(f"Creating new agent for model: {model}")
        try:
            config = MODEL_CONFIGS[model]
            agents[model] = create_crypto_agent(config["name"], config["provider"])
            logger.info(f"Agent created successfully for model: {model}")
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

    agent = agents[model]

    try:
        config = {"configurable": {"thread_id": thread_id}}

        state = agent.get_state(config)
        if state and state.values and "messages" in state.values:
            messages = state.values["messages"]
            cleaned = []
            last_ai_tool_idx = None
            for i, msg in enumerate(messages):
                if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                    last_ai_tool_idx = i
                if msg.type == "tool":
                    last_ai_tool_idx = None

            if last_ai_tool_idx is not None:
                cleaned = [msg for i, msg in enumerate(messages) if i <= last_ai_tool_idx]
                agent.update_state(config, {"messages": cleaned})

        response = agent.invoke(
            {"messages": [HumanMessage(content=chat_msg.message)]},
            config
        )
        ai_reply = response["messages"][-1].content
        logger.info(f"Chat response sent, thread_id: {thread_id}")
        return {"status": "success", "reply": ai_reply, "thread_id": thread_id, "model": model}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{thread_id}")
async def get_history(thread_id: str) -> dict:
    logger.info(f"History request for thread_id: {thread_id}")
    default_model = "deepseek-chat"
    if default_model not in agents:
        config = MODEL_CONFIGS[default_model]
        agents[default_model] = create_crypto_agent(config["name"], config["provider"])
    agent = agents[default_model]
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent.get_state(config)

        if not state or "messages" not in state.values:
            return {"status": "success", "history": []}

        raw_messages = state.values.get("messages", [])
        formatted_history = []

        for msg in raw_messages:
            if msg.type == "human":
                formatted_history.append({"role": "user", "content": msg.content})
            elif msg.type == "ai" and msg.content:
                formatted_history.append({"role": "ai", "content": msg.content})
            elif msg.type == "tool":
                formatted_history.append({"role": "tool", "content": msg.content})

        logger.info(f"History retrieved, {len(formatted_history)} messages")
        return {"status": "success", "history": formatted_history}
    except Exception as e:
        logger.error(f"History error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models")
async def get_models() -> dict:
    return {"status": "success", "models": MODEL_CONFIGS}


@app.delete("/api/chat/{thread_id}")
async def delete_chat(thread_id: str) -> dict:
    logger.info(f"Deleting chat thread: {thread_id}")
    try:
        import sqlite3
        conn = sqlite3.connect("resources/test.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        cursor.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (thread_id,))
        conn.commit()
        conn.close()
        logger.info(f"Chat thread {thread_id} deleted from database")
        return {"status": "success", "message": "Chat deleted"}
    except Exception as e:
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(app, host="127.0.0.1", port=8000)