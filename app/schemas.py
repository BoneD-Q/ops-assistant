from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    inject: Optional[str] = Field(
        default=None,
        description="评测用故障注入: tool_timeout | tool_error",
    )


class QueryResponse(BaseModel):
    answer: str
    path: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    degraded: bool = False
    proposal_id: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ConfirmRequest(BaseModel):
    proposal_id: str
    token: str
