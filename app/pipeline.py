from __future__ import annotations

from typing import Any, Optional

from app.config import GREETINGS
from app.degrade import degrade_message
from app.faq_gate import FAQGate
from app.intent import route_intent
from app.rag import SimpleRAG
from app.schemas import QueryResponse
from app.tools import MockTools, ToolResult


class AssistantPipeline:
    def __init__(self):
        self.faq = FAQGate()
        self.rag = SimpleRAG()
        self.tools = MockTools()

    def handle(self, query: str, inject: Optional[str] = None) -> QueryResponse:
        q = (query or "").strip()
        if not q:
            return QueryResponse(answer="请输入问题。", path="empty")

        if q.lower() in GREETINGS or q in GREETINGS:
            return QueryResponse(
                answer="你好，我是园区运维助手 Demo。可问访客/会议等 FAQ，或查楼栋用电、告警流程。",
                path="greet",
            )

        # 1) FAQ 门禁
        hit = self.faq.match(q)
        if hit:
            return QueryResponse(
                answer=hit.answer,
                path="faq",
                meta={"faq_id": hit.id, "score": hit.score},
            )

        # 2) 意图路由（规则模拟 LoRA）
        intent = route_intent(q)

        # 3) Workflow / 工具
        if intent.intent == "today_power":
            return self._from_tool(
                self.tools.today_power(q, inject=inject),
                intent=intent.intent,
                confidence=intent.confidence,
                formatter=lambda d: f"{d['building']}（{d['code']}）今日用电 {d['today_kwh']} {d['unit']}。",
            )
        if intent.intent == "month_power":
            return self._from_tool(
                self.tools.month_power(q, inject=inject),
                intent=intent.intent,
                confidence=intent.confidence,
                formatter=lambda d: f"{d['building']}（{d['code']}）本月用电 {d['month_kwh']} {d['unit']}。",
            )
        if intent.intent == "resolve_alert":
            # 写操作：只 propose，不静默重试 execute
            tr = self.tools.propose_resolve_alert(q)
            if not tr.ok:
                return QueryResponse(
                    answer=degrade_message(tr.error or "default"),
                    path="workflow",
                    intent=intent.intent,
                    confidence=intent.confidence,
                    degraded=True,
                )
            return QueryResponse(
                answer=tr.data["summary"] + " 请调用 /api/actions/confirm 并携带 token 确认。",
                path="workflow",
                intent=intent.intent,
                confidence=intent.confidence,
                proposal_id=tr.data["proposal_id"],
                meta={"write_guard": "propose_only"},
            )
        if intent.intent in {"energy_advice", "bill_explain"}:
            # 演示：知识类意图直接 RAG（真实项目可走专家/工具）
            answer, meta = self.rag.answer(q)
            return QueryResponse(
                answer=answer,
                path="rag",
                intent=intent.intent,
                confidence=intent.confidence,
                meta={"hits": meta},
            )

        # 4) RAG 兜底
        answer, meta = self.rag.answer(q)
        return QueryResponse(
            answer=answer,
            path="rag",
            intent=intent.intent,
            confidence=intent.confidence,
            meta={"hits": meta, "intent_source": intent.source},
        )

    def _from_tool(
        self,
        tr: ToolResult,
        *,
        intent: str,
        confidence: float,
        formatter,
    ) -> QueryResponse:
        if tr.ok:
            return QueryResponse(
                answer=formatter(tr.data),
                path="workflow",
                intent=intent,
                confidence=confidence,
                meta={"tool": tr.data},
            )
        return QueryResponse(
            answer=degrade_message(tr.error or "default"),
            path="workflow",
            intent=intent,
            confidence=confidence,
            degraded=True,
            meta={"error": tr.error},
        )

    def confirm(self, proposal_id: str, token: str) -> dict[str, Any]:
        from app.config import CONFIRM_TOKEN

        if token != CONFIRM_TOKEN:
            return {"ok": False, "error": "unauthorized"}
        tr = self.tools.execute_proposal(proposal_id)
        if not tr.ok:
            return {"ok": False, "error": tr.error}
        return {"ok": True, "data": tr.data}


# 单例便于评测脚本复用
pipeline = AssistantPipeline()
