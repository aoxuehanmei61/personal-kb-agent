# -*- coding: utf-8 -*-
"""本地检索：TF-IDF + 中文分词（jieba）+ 余弦相似度，不依赖外部向量服务。

说明：DeepSeek 官方暂不提供 embedding 接口，所以这里用本地 TF-IDF 做召回；
以后想换成语义向量，只要改这个文件的 fit / search 即可，上层不用动。
"""
from __future__ import annotations

import math
from collections import Counter
from typing import List, Dict

import jieba

import config


def _tokenize(text: str) -> List[str]:
    """中文分词，去掉纯空白和单字符噪声。"""
    words = jieba.lcut(text.lower())
    return [w.strip() for w in words if w.strip() and not w.isspace()]


class Retriever:
    def __init__(self) -> None:
        self.chunks: List[Dict[str, str]] = []
        self._df: Counter = Counter()          # 每个词出现在多少个文本块里
        self._idf: Dict[str, float] = {}
        self._vectors: List[Dict[str, float]] = []  # 每个文本块的 TF-IDF 稀疏向量
        self._norms: List[float] = []

    def fit(self, chunks: List[Dict[str, str]]) -> None:
        """根据文本块建立索引。"""
        self.chunks = chunks
        self._df.clear()
        self._idf.clear()
        self._vectors.clear()
        self._norms.clear()

        tokenized: List[List[str]] = []
        for chunk in chunks:
            words = _tokenize(chunk["text"])
            tokenized.append(words)
            for word in set(words):
                self._df[word] += 1

        n = max(len(chunks), 1)
        self._idf = {
            word: math.log((n + 1) / (df + 1)) + 1.0
            for word, df in self._df.items()
        }

        for words in tokenized:
            tf = Counter(words)
            total = max(len(words), 1)
            vector: Dict[str, float] = {}
            for word, count in tf.items():
                tfidf = (count / total) * self._idf.get(word, 1.0)
                vector[word] = tfidf
            self._vectors.append(vector)
            self._norms.append(math.sqrt(sum(v * v for v in vector.values())))

    def _vectorize(self, words: List[str]) -> Dict[str, float]:
        tf = Counter(words)
        total = max(len(words), 1)
        return {
            word: (count / total) * self._idf.get(word, 1.0)
            for word, count in tf.items()
        }

    @staticmethod
    def _cosine(vec_a: Dict[str, float], norm_a: float,
                vec_b: Dict[str, float], norm_b: float) -> float:
        if norm_a == 0 or norm_b == 0:
            return 0.0
        # 稀疏向量点积：遍历较短的那个
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        dot = sum(value * vec_b.get(word, 0.0) for word, value in vec_a.items())
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int | None = None) -> List[Dict]:
        """返回最相关的文本块，按相似度从高到低，附带 score。"""
        top_k = top_k or config.TOP_K
        if not self.chunks:
            return []

        words = _tokenize(query)
        q_vec = self._vectorize(words)
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))

        scored: List[Dict] = []
        for idx, chunk in enumerate(self.chunks):
            score = self._cosine(q_vec, q_norm, self._vectors[idx], self._norms[idx])
            if score > 0:
                scored.append({**chunk, "score": round(score, 4), "index": idx})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]
