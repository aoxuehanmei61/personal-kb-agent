# -*- coding: utf-8 -*-
"""网页版服务：FastAPI + SSE 流式输出，运行 python app.py 后打开浏览器。"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

import config
from kb_agent.agent import KnowledgeAgent

app = FastAPI(title="个人知识库 Agent")
STATIC_DIR = Path(__file__).resolve().parent / "static"

# 全局一个 Agent 实例；加锁避免多个请求同时改索引或历史
agent = KnowledgeAgent(use_llm=False)
_lock = threading.Lock()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status():
    return JSONResponse(agent.status())


@app.post("/api/reload")
def reload_docs():
    with _lock:
        # 先重读 .env（方便填完 Key 后不重启服务），再重建索引
        config.reload_env()
        agent.llm = None  # 配置可能变了，下次问答时按新配置重新创建
        agent.reload()
    return JSONResponse({"ok": True, **agent.status()})


@app.post("/api/chat")
async def chat(request: Request):
    payload = await request.json()
    question = (payload.get("question") or "").strip()
    if not question:
        return JSONResponse({"error": "问题不能为空"}, status_code=400)

    def event_stream():
        # 空行分隔的 SSE 事件
        with _lock:
            for event in agent.stream_ask(question):
                data = json.dumps(event, ensure_ascii=False)
                yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 关闭代理缓冲，保证逐字输出
        },
    )


if __name__ == "__main__":
    print(f"知识库文档目录：{config.DOCS_DIR}")
    print(f"API Key 状态：{'已配置' if config.check_api_key() else '未配置（只能演示检索）'}")
    print("打开浏览器访问 http://127.0.0.1:8000\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
