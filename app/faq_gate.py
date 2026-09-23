from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from rank_bm25 import BM25Okapi

from app.config import DATA, FAQ_BUSINESS_SKIP_PATTERNS


def _tokenize(text: str) -> list[str]:
    # 中英简易切词：连续中文单字 + 英文/数字串
    text = text.lower().strip()
    parts = re.findall(r"[\u4e00-\u9fff]|[a-z0-9\-]+", text)
    return parts or [text]


@dataclass
class FAQHit:
    id: str
    question: str
    answer: str
    score: float


class FAQGate:
    """多层门禁：业务黑名单 → BM25 阈值 → 才允许秒回。"""

    def __init__(self, path=None, min_score: float = 1.2):
        path = path or (DATA / "faq.json")
        self.items = json.loads(path.read_text(encoding="utf-8"))
        self.corpus = [_tokenize(x["question"]) for x in self.items]
        self.bm25 = BM25Okapi(self.corpus)
        self.min_score = min_score

    def _blocked(self, query: str) -> bool:
        q = query.lower()
        return any(p in q for p in FAQ_BUSINESS_SKIP_PATTERNS)

    def match(self, query: str) -> Optional[FAQHit]:
        if self._blocked(query):
            return None
        tokens = _tokenize(query)
        scores = self.bm25.get_scores(tokens)
        idx = int(scores.argmax())
        score = float(scores[idx])
        if score < self.min_score:
            return None
        item = self.items[idx]
        return FAQHit(
            id=item["id"],
            question=item["question"],
            answer=item["answer"],
            score=score,
        )
