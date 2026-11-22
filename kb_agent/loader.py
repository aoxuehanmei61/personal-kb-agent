# -*- coding: utf-8 -*-
"""文档加载与切分：把 docs 文件夹里的 md/txt/pdf/docx 读出来，切成小块。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import config


# ---------- 各类型文件的文本提取 ----------

def _read_text_file(path: Path) -> str:
    """读取纯文本 / Markdown。"""
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    """读取 PDF（pypdf，只取文字层）。"""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _read_docx(path: Path) -> str:
    """读取 Word 文档（python-docx）。"""
    from docx import Document

    doc = Document(str(path))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def _extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return _read_text_file(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    return ""


# ---------- 切分 ----------

def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """先按段落拆，再把过长的段落按字符长度二次切分，保留少量重叠。"""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        # 单段就超长，直接硬切
        if len(para) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(para), chunk_size - overlap):
                piece = para[i : i + chunk_size]
                if piece:
                    chunks.append(piece)
            continue

        # 把段落往当前块里拼，拼不下就先存起来
        if len(current) + len(para) + 1 > chunk_size and current:
            chunks.append(current)
            # 留一点上一段尾巴做重叠
            current = current[-overlap:] + "\n" + para
        else:
            current = f"{current}\n{para}" if current else para

    if current:
        chunks.append(current)
    return [c.strip() for c in chunks if c.strip()]


# ---------- 对外主入口 ----------

def load_documents(docs_dir: Path | None = None) -> List[Dict[str, str]]:
    """遍历文档目录，返回 [{"text": 文本块, "source": 文件名}, ...]。"""
    docs_dir = docs_dir or config.DOCS_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)

    chunks: List[Dict[str, str]] = []
    files = [p for p in docs_dir.rglob("*") if p.suffix.lower() in config.SUPPORTED_SUFFIXES]

    for path in files:
        try:
            text = _extract_text(path)
            if not text.strip():
                continue
            for piece in _split_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                chunks.append({"text": piece, "source": path.name})
        except Exception as exc:  # 单个文件读失败不影响整体
            print(f"[警告] 读取 {path.name} 失败：{exc}")

    return chunks
