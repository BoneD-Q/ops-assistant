from __future__ import annotations

import time
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def with_retry(
    fn: Callable[[], T],
    *,
    retries: int = 2,
    delays: tuple[float, ...] = (0.01, 0.02),
    retryable: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """读路径可重试；调用方对写操作不要包 with_retry。"""
    last: Exception | None = None
    for i in range(retries + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — demo 简化
            last = e
            if retryable and not retryable(e):
                raise
            if i >= retries:
                break
            time.sleep(delays[min(i, len(delays) - 1)])
    assert last is not None
    raise last


def degrade_message(kind: str) -> str:
    mapping = {
        "timeout": "查询服务暂时超时，请稍后重试。今日数据暂不可用。",
        "upstream_5xx": "上游接口异常，已降级。请稍后重试或联系值班员。",
        "unknown_building": "未识别楼栋编码。请使用如 A1 / B2 / C3 后再问。",
        "default": "工具暂时不可用，已兜底。会话未中断，可换个问题继续。",
    }
    return mapping.get(kind, mapping["default"])
