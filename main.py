# -*- coding: utf-8 -*-
"""命令行入口：运行 python main.py 开始对话。"""
from __future__ import annotations

import config
from kb_agent.agent import KnowledgeAgent

COMMANDS = {
    "/reload": "重新读取 docs 文件夹并重建索引",
    "/history": "查看最近对话",
    "quit": "退出",
    "exit": "退出",
}


def main() -> None:
    print("=" * 48)
    print("  个人知识库 Agent（接入 DeepSeek）")
    print("=" * 48)

    if not config.check_api_key():
        print("提示：还没填 API Key，当前只能演示知识库检索，不会调用大模型。")
        print("      把 .env.example 复制为 .env 并填入 Key 后即可正常问答。\n")

    agent = KnowledgeAgent(use_llm=config.check_api_key())

    print("\n可以直接输入问题；可用命令：")
    for cmd, desc in COMMANDS.items():
        print(f"  {cmd:<10} {desc}")
    print()

    while True:
        try:
            question = input("你：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if not question:
            continue
        if question in {"quit", "exit", "退出"}:
            print("再见！")
            break
        if question == "/reload":
            agent.reload()
            continue
        if question == "/history":
            for msg in agent.history:
                role = "你" if msg["role"] == "user" else "助手"
                print(f"{role}：{msg['content']}")
            continue

        agent.ask(question)


if __name__ == "__main__":
    main()
