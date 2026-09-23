from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class IntentResult:
    intent: str
    confidence: float
    source: str  # "rules" 模拟 LoRA 高置信；"fallback" 模拟低置信走 RAG


# 规则表：演示「高置信短路」；真实项目此处为 Qwen2.5-7B + LoRA
_RULES: list[tuple[str, list[str], float]] = [
    ("today_power", [r"今日.*(用电|电量)", r"(今天|今日).*(用了?多少|用电)", r"今日用电"], 0.92),
    ("month_power", [r"(本月|月).*电", r"月用电"], 0.90),
    ("resolve_alert", [r"消(掉|除)?告警", r"告警.*消"], 0.93),
    ("energy_advice", [r"节能", r"节电", r"负荷.*建议"], 0.88),
    ("bill_explain", [r"账单", r"电费", r"尖峰"], 0.86),
]


def route_intent(query: str, threshold: float = 0.85) -> IntentResult:
    q = query.strip()
    best: IntentResult | None = None
    for intent, patterns, conf in _RULES:
        for pat in patterns:
            if re.search(pat, q):
                cand = IntentResult(intent=intent, confidence=conf, source="rules")
                if best is None or cand.confidence > best.confidence:
                    best = cand
                break
    if best and best.confidence >= threshold:
        return best
    # 低置信 / 未命中 → 模拟回退 RAG（真实项目可再打 LLM）
    return IntentResult(intent="rag_fallback", confidence=0.40, source="fallback")
