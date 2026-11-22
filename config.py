# -*- coding: utf-8 -*-
"""全局配置：从 .env 文件或系统环境变量读取，Key 不写死在代码里。"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（本文件所在目录）
BASE_DIR = Path(__file__).resolve().parent
# 知识库文档放这个文件夹
DOCS_DIR = BASE_DIR / "docs"

# 读取同目录下的 .env 文件（没有也不报错）
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

# ---- 以下配置会在 reload_env() 时重新读取 ----
DEEPSEEK_API_KEY = ""
DEEPSEEK_BASE_URL = ""
DEEPSEEK_MODEL = ""
TOP_K = 3
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# 支持读取的文档后缀
SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf", ".docx"}


def reload_env() -> None:
    """重新读取 .env，改完配置后不用重启服务。"""
    global DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
    global TOP_K, CHUNK_SIZE, CHUNK_OVERLAP

    load_dotenv(ENV_FILE, override=True)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
    TOP_K = int(os.getenv("TOP_K", "3"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))


def check_api_key() -> bool:
    """检查 Key 是否已经填好（排除模板里的占位文字）。"""
    if not DEEPSEEK_API_KEY:
        return False
    placeholders = {"在这里粘贴你的deepseekkey", "your_key", "your-api-key", "sk-xxx"}
    return DEEPSEEK_API_KEY.lower() not in placeholders


# 模块导入时先加载一次
reload_env()
