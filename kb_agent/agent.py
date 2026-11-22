# -*- coding: utf-8 -*-
"""Agent 组装：检索知识库 → 拼参考资料 → 交给 DeepSeek 回答。"""
from __future__ import annotations

from typing import List, Dict

from kb_agent.loader import load_documents
from kb_agent.retriever import Retriever
from kb_agent.llm import DeepSeekLLM, LLMError
import config


class KnowledgeAgent:
    def __init__(self, use_llm: bool = True) -> None:
        self.retriever = Retriever()
        self.llm: DeepSeekLLM | None = None
        self.history: List[Dict[str, str]] = []
        self._use_llm = use_llm
        self._index()

    def _index(self) -> None:
        chunks = load_documents()
        self.retriever.fit(chunks)
        print(f"已加载知识库：共 {len(chunks)} 个文本块。")

    def reload(self) -> None:
        """文档更新后重新建索引。"""
        self._index()

    def _build_context(self, hits: List[Dict]) -> str:
        blocks = []
        for idx, hit in enumerate(hits, start=1):
            blocks.append(f"[{idx}] 来源：{hit['source']}\n{hit['text']}")
        return "\n\n".join(blocks)

    def status(self) -> Dict:
        """给网页用的知识库概况。"""
        sources: Dict[str, int] = {}
        for chunk in self.retriever.chunks:
            sources[chunk["source"]] = sources.get(chunk["source"], 0) + 1
        return {
            "chunks": len(self.retriever.chunks),
            "documents": [{"name": name, "chunks": count} for name, count in sorted(sources.items())],
            "has_key": config.check_api_key(),
            "model": config.DEEPSEEK_MODEL,
        }

    def stream_ask(self, question: str):
        """流式问答：依次产出 sources / delta / error / done 事件，供网页 SSE 使用。"""
        hits = self.retriever.search(question)

        # 第一件事：把命中的资料片段推给前端，方便用户看依据
        yield {
            "type": "sources",
            "items": [
                {
                    "source": hit["source"],
                    "score": hit["score"],
                    "text": hit["text"],
                }
                for hit in hits
            ],
        }

        if not config.check_api_key():
            yield {
                "type": "error",
                "message": "还没配置 DeepSeek API Key，请在项目根目录的 .env 里填入 DEEPSEEK_API_KEY 后重启服务。",
            }
            yield {"type": "done"}
            return

        # 没命中检索也照常交给模型：闲聊、通用问题不该被拦掉
        context = self._build_context(hits) if hits else "（本轮知识库没有检索到相关资料）"

        try:
            if self.llm is None:
                self.llm = DeepSeekLLM()
            full_text: List[str] = []
            for piece in self.llm.stream_answer(context, question, self.history[-6:]):
                full_text.append(piece)
                yield {"type": "delta", "text": piece}
        except LLMError as exc:
            yield {"type": "error", "message": str(exc)}
            yield {"type": "done"}
            return
        except Exception as exc:
            yield {"type": "error", "message": f"调用模型失败：{exc}"}
            yield {"type": "done"}
            return

        answer = "".join(full_text)
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        yield {"type": "done"}

    def ask(self, question: str) -> str:
        hits = self.retriever.search(question)
        context = self._build_context(hits) if hits else "（本轮知识库没有检索到相关资料）"

        # 没配 Key 时，只把检索结果打出来，方便先调试检索链路
        if not self._use_llm:
            print("\n【检索到的参考资料】")
            print(context)
            return ""

        try:
            if self.llm is None:
                self.llm = DeepSeekLLM()
            answer = self.llm.answer(context, question, history=self.history[-6:])
        except LLMError as exc:
            print(f"\n[提示] {exc}")
            return ""
        except Exception as exc:  # 网络 / 接口报错统一兜底
            print(f"\n[调用模型失败] {exc}")
            return ""

        # 记录最近对话，供多轮上下文使用
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        return answer
