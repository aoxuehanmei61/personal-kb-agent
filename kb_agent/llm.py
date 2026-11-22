# -*- coding: utf-8 -*-
"""DeepSeek 大模型调用：走 OpenAI 兼容接口，支持流式输出。"""
from __future__ import annotations

from typing import List, Dict

import config

# 给模型的角色设定：优先依据知识库，允许通用闲聊
SYSTEM_PROMPT = (
    "你是一个个人知识库助手，用户会跟你聊天或问知识库里的事情。规则：\n"
    "1. 如果【参考资料】里能找到依据，就以资料为准回答，并在末尾用“来源：文件名”标注；\n"
    "2. 如果资料里没有相关内容，不要硬凑，直接基于你自己的通用知识正常回答；\n"
    "   这种回答要在开头简短说明“（知识库里没有相关内容，以下是通用回答）”；\n"
    "3. 用户只是打招呼、闲聊时，自然地回应就好，不必提知识库；\n"
    "4. 全程用简洁、口语化的中文，不要编造资料里不存在的事实细节。"
)


class LLMError(RuntimeError):
    pass


class DeepSeekLLM:
    def __init__(self) -> None:
        if not config.check_api_key():
            raise LLMError(
                "还没填 DeepSeek API Key：请把项目根目录的 .env.example 复制为 .env，"
                "并填入 DEEPSEEK_API_KEY。"
            )
        from openai import OpenAI

        self.client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
        self.model = config.DEEPSEEK_MODEL

    def _build_messages(self, context: str, question: str,
                        history: List[Dict[str, str]] | None) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        if history:
            messages.extend(history)
        user_content = f"【参考资料】\n{context}\n\n【用户问题】\n{question}"
        messages.append({"role": "user", "content": user_content})
        return messages

    def stream_answer(self, context: str, question: str,
                      history: List[Dict[str, str]] | None = None):
        """逐段产出答案文本，供命令行和网页共用。"""
        messages = self._build_messages(context, question, history)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.3,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                yield text

    def answer(self, context: str, question: str,
               history: List[Dict[str, str]] | None = None) -> str:
        """命令行版本：边收边打印，返回完整答案文本。"""
        answer_parts: List[str] = []
        print("\n助手：", end="", flush=True)
        for text in self.stream_answer(context, question, history):
            answer_parts.append(text)
            print(text, end="", flush=True)
        print()
        return "".join(answer_parts)
