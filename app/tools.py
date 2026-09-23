from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.config import DATA


@dataclass
class ToolResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    degraded: bool = False


class MockTools:
    """进程内 mock：对应真实项目里 Knowledge/查询类 MCP，不含真实库。"""

    def __init__(self):
        self.biz = json.loads((DATA / "mock_biz.json").read_text(encoding="utf-8"))
        self.proposals: dict[str, dict[str, Any]] = {}

    def _building_key(self, query: str) -> Optional[str]:
        q = query.upper().replace("座", "")
        for key in self.biz["buildings"]:
            # A1 / A座 / A
            short = key[0]
            if key in q or f"{short}座" in query or re_building(query, short, key):
                return key
        return None

    def today_power(self, query: str, inject: Optional[str] = None) -> ToolResult:
        if inject == "tool_timeout":
            time.sleep(0.05)
            return ToolResult(ok=False, error="timeout", degraded=True)
        if inject == "tool_error":
            return ToolResult(ok=False, error="upstream_5xx", degraded=True)
        key = self._building_key(query)
        if not key:
            return ToolResult(ok=False, error="unknown_building", degraded=True)
        b = self.biz["buildings"][key]
        return ToolResult(
            ok=True,
            data={
                "building": b["name"],
                "code": key,
                "today_kwh": b["today_kwh"],
                "unit": "kWh",
            },
        )

    def month_power(self, query: str, inject: Optional[str] = None) -> ToolResult:
        if inject == "tool_timeout":
            return ToolResult(ok=False, error="timeout", degraded=True)
        if inject == "tool_error":
            return ToolResult(ok=False, error="upstream_5xx", degraded=True)
        key = self._building_key(query)
        if not key:
            return ToolResult(ok=False, error="unknown_building", degraded=True)
        b = self.biz["buildings"][key]
        return ToolResult(
            ok=True,
            data={
                "building": b["name"],
                "code": key,
                "month_kwh": b["month_kwh"],
                "unit": "kWh",
            },
        )

    def propose_resolve_alert(self, query: str) -> ToolResult:
        alert_id = None
        for aid in self.biz["alerts"]:
            if aid in query.upper() or aid in query:
                alert_id = aid
                break
        if not alert_id:
            # 默认演示告警
            alert_id = "ALERT-1001"
        alert = self.biz["alerts"].get(alert_id)
        if not alert:
            return ToolResult(ok=False, error="alert_not_found", degraded=True)
        pid = f"prop_{uuid.uuid4().hex[:8]}"
        self.proposals[pid] = {
            "type": "resolve_alert",
            "alert_id": alert_id,
            "alert": alert,
            "status": "pending",
        }
        return ToolResult(
            ok=True,
            data={
                "proposal_id": pid,
                "summary": f"提议消除告警 {alert_id}（{alert['message']}），待值班员确认。",
            },
        )

    def execute_proposal(self, proposal_id: str) -> ToolResult:
        prop = self.proposals.get(proposal_id)
        if not prop:
            return ToolResult(ok=False, error="proposal_not_found")
        if prop["status"] != "pending":
            return ToolResult(ok=False, error="already_handled")
        aid = prop["alert_id"]
        if aid in self.biz["alerts"]:
            self.biz["alerts"][aid]["status"] = "resolved"
        prop["status"] = "executed"
        return ToolResult(
            ok=True,
            data={"alert_id": aid, "status": "resolved", "message": f"告警 {aid} 已消除"},
        )

    def knowledge_search(self, query: str) -> ToolResult:
        # 轻量：交给 RAG 模块；此处仅占位
        return ToolResult(ok=True, data={"hint": "use_rag"})


def re_building(query: str, short: str, key: str) -> bool:
    q = query.upper()
    return short in q and ("用电" in query or "电量" in query or key in q)
