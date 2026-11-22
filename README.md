# 个人知识库 Agent（接入 DeepSeek）

一个小型 RAG 项目：把你自己的文档（Markdown / TXT / PDF / Word）放进 `docs` 文件夹，
Agent 先在本地检索相关内容，再调用 DeepSeek 据此回答，尽量不瞎编。

提供两种用法：**网页版**（推荐，浏览器里聊、逐字流式输出、可点开引用原文）和命令行版。

## 目录结构

```
deepseek-kb-agent/
├── app.py               # 网页版入口（FastAPI + SSE）
├── main.py              # 命令行版入口
├── config.py            # 读取 .env 里的配置
├── start_web.bat        # 一键启动网页版（双击）
├── requirements.txt     # 依赖清单
├── .env.example         # 配置模板，复制成 .env 后填 Key
├── docs/                # 你的知识库文档放这里
│   └── 示例笔记.md
├── static/
│   └── index.html       # 网页界面
└── kb_agent/
    ├── loader.py        # 读取并切分文档
    ├── retriever.py     # 本地检索（TF-IDF + 中文分词）
    ├── llm.py           # DeepSeek 调用（OpenAI 兼容接口，流式输出）
    └── agent.py         # 组装：检索 → 拼资料 → 问答
```

## 一、安装依赖

在项目目录下打开终端，执行：

```powershell
python -m pip install -r requirements.txt
```

## 二、配置 API Key

1. 复制 `.env.example` 为 `.env`：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 打开 `.env`，把 `DEEPSEEK_API_KEY` 后面换成你自己的 Key
   （申请地址：https://platform.deepseek.com → API Keys）。

> Key 只写在本地 `.env` 里，不会提交到代码仓库（`.gitignore` 已忽略 `.env`）。

## 三、放入知识库文档

把 `.md / .txt / .pdf / .docx` 文档直接放进 `docs` 文件夹即可，支持子文件夹。
`docs/示例笔记.md` 是测试样例，确认跑通后可以删掉。

## 四、运行

### 网页版（推荐）

双击 `start_web.bat`，或在项目目录执行：

```powershell
python app.py
```

然后浏览器打开 http://127.0.0.1:8000

界面上可以做这些事：

- 直接在下面输入框提问，答案逐字流式显示；
- 每条回答下面的琥珀色标签就是引用的资料，点开能看到原文片段；
- 左侧能看到文档列表、文本块数量、模型状态，还能一键重新加载文档。

### 命令行版

```powershell
python main.py
```

启动后直接输入问题回车。常用命令：

| 命令      | 作用                     |
| --------- | ------------------------ |
| `/reload` | 文档有更新，重新加载索引 |
| `/history`| 查看最近对话             |
| `quit`    | 退出                     |

## 工作流程

1. `loader.py` 读取 `docs` 里的文档，切成一段段文本块；
2. `retriever.py` 对问题做分词，用 TF-IDF 余弦相似度找出最相关的几段；
3. `agent.py` 把这几段连同问题一起发给 DeepSeek；
4. `llm.py` 流式返回答案，并标注参考资料来源。

## 常见问题

- **提示“还没填 API Key”**：说明 `.env` 没配好，或还是模板里的占位文字。
  填好 Key 后在网页上点“重新加载文档”即可生效，不用重启服务。
- **调用模型失败**：先检查网络能否访问 `api.deepseek.com`，再确认 Key 有效、余额充足。
- **PDF 读不出内容**：扫描件（图片型 PDF）没有文字层，需要先 OCR。
- **检索不够准**：可在 `.env` 里调大 `TOP_K` 多取几段；后续可把 `retriever.py`
  换成 embedding 语义向量检索。
- **想换端口**：改 `app.py` 最后一行的 `port=8000` 即可。

## 后续可扩展方向

- 接入本地 embedding 模型做语义检索；
- 支持上传文档、多会话保存；
- 引用片段高亮命中的关键词；
- 打包成桌面应用或 Docker 部署。
