from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.config import DATA


def _tokens(text: str) -> set[str]:
    text = text.lower()
    zh = set(re.findall(r"[\u4e00-\u9fff]", text))
    en = set(re.findall(r"[a-z0-9\-]+", text))
    return zh | en


@dataclass
class RAGHit:
    id: str
    title: str
    text: str
    score: float


class SimpleRAG:
    """内存关键词重叠检索：演示 RAG 兜底，不依赖向量库。"""

    def __init__(self, path=None):
        path = path or (DATA / "docs.json")
        self.docs = json.loads(path.read_text(encoding="utf-8"))
        self._doc_tokens = [(d, _tokens(d["title"] + d["text"])) for d in self.docs]

    def retrieve(self, query: str, top_k: int = 2) -> list[RAGHit]:
        qt = _tokens(query)
        scored: list[RAGHit] = []
        for d, dt in self._doc_tokens:
            inter = len(qt & dt)
            if inter <= 0:
                continue
            scored.append(
                RAGHit(id=d["id"], title=d["title"], text=d["text"], score=float(inter))
            )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def answer(self, query: str) -> tuple[str, list[dict]]:
        hits = self.retrieve(query)
        if not hits:
            return (
                "未在知识库中找到直接依据。请换个问法，或提供楼栋编码 / 告警号等业务主键。",
                [],
            )
        ctx = "\n\n".join(f"【{h.title}】{h.text}" for h in hits)
        answer = f"根据园区知识库：\n{ctx}"
        meta = [{"id": h.id, "title": h.title, "score": h.score} for h in hits]
        return answer, meta
