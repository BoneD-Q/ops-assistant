from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# 业务问法黑名单：命中则禁止 FAQ 秒回（对齐「防截胡查数」）
FAQ_BUSINESS_SKIP_PATTERNS = [
    "用电",
    "电量",
    "电费",
    "账单",
    "告警",
    "消警",
    "工单",
    "节能",
    "负荷",
]

GREETINGS = {"你好", "您好", "hello", "hi", "在吗", "早上好", "晚上好"}

CONFIRM_TOKEN = "demo-operator"
