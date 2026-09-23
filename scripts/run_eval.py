from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.pipeline import AssistantPipeline  # noqa: E402


def _kw_hit(answer: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    return all(k in answer for k in keywords)


def eval_faq_gate(p: AssistantPipeline) -> dict:
    data = json.loads((ROOT / "data/eval/faq_gate.json").read_text(encoding="utf-8"))
    hit_ok = miss_ok = 0
    for item in data["must_hit"]:
        r = p.handle(item["query"])
        if r.path == item["expect_path"]:
            hit_ok += 1
    for item in data["must_miss"]:
        r = p.handle(item["query"])
        if r.path != item["expect_not_path"]:
            miss_ok += 1
    return {
        "must_hit": f"{hit_ok}/{len(data['must_hit'])}",
        "must_miss": f"{miss_ok}/{len(data['must_miss'])}",
        "pass": hit_ok == len(data["must_hit"]) and miss_ok == len(data["must_miss"]),
    }


def eval_routing(p: AssistantPipeline) -> dict:
    rows = json.loads((ROOT / "data/eval/routing_smoke.json").read_text(encoding="utf-8"))
    ok = 0
    details = []
    for row in rows:
        r = p.handle(row["query"])
        path_ok = r.path == row["expect_path"]
        intent_ok = (not row.get("expect_intent")) or r.intent == row["expect_intent"]
        kw_ok = _kw_hit(r.answer, row.get("keywords") or [])
        good = path_ok and intent_ok and kw_ok
        ok += int(good)
        details.append({"id": row["id"], "pass": good, "path": r.path, "intent": r.intent})
    return {"score": f"{ok}/{len(rows)}", "pass": ok == len(rows), "details": details}


def eval_resilience(p: AssistantPipeline) -> dict:
    rows = json.loads((ROOT / "data/eval/resilience_smoke.json").read_text(encoding="utf-8"))
    ok = 0
    details = []
    for row in rows:
        alive = True
        degraded = False
        proposal = False
        try:
            r = p.handle(row["query"], inject=row.get("inject"))
            degraded = r.degraded
            proposal = bool(r.proposal_id)
        except Exception as e:  # noqa: BLE001
            alive = False
            details.append({"id": row["id"], "pass": False, "error": str(e)})
            continue
        good = alive == row["expect_alive"]
        if row.get("expect_degraded") is True:
            good = good and degraded
        if row.get("expect_degraded") is False:
            good = good and (not degraded)
        if row.get("expect_proposal"):
            good = good and proposal
        ok += int(good)
        details.append(
            {
                "id": row["id"],
                "pass": good,
                "alive": alive,
                "degraded": degraded,
                "proposal": proposal,
            }
        )
    return {"score": f"{ok}/{len(rows)}", "pass": ok == len(rows), "details": details}


def main():
    p = AssistantPipeline()
    report = {
        "faq_gate": eval_faq_gate(p),
        "routing_smoke": eval_routing(p),
        "resilience_smoke": eval_resilience(p),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not all(report[k]["pass"] for k in report):
        sys.exit(1)


if __name__ == "__main__":
    main()
