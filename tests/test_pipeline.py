from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.pipeline import AssistantPipeline


def test_faq_hit_and_business_miss():
    p = AssistantPipeline()
    r = p.handle("访客登记怎么办理？")
    assert r.path == "faq"
    r2 = p.handle("A座今日用电多少？")
    assert r2.path != "faq"
    assert r2.path == "workflow"


def test_write_guard_propose_confirm():
    p = AssistantPipeline()
    r = p.handle("帮我消掉告警 ALERT-1001")
    assert r.proposal_id
    bad = p.confirm(r.proposal_id, "wrong")
    assert bad["ok"] is False
    ok = p.confirm(r.proposal_id, "demo-operator")
    assert ok["ok"] is True


def test_degrade_on_inject():
    p = AssistantPipeline()
    r = p.handle("A座今日用电多少？", inject="tool_timeout")
    assert r.degraded is True
    assert r.path == "workflow"
