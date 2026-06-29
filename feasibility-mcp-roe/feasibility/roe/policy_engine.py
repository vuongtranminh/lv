"""RoE entry point. Deterministic — never invokes the LLM.

Sprint 2: switched từ 3 rule v1 sang 8 rule v2 (4 precondition + 4 rate-limit).
Code v1 (rules.py) giữ lại làm backup; engine dùng v2 (rules_v2.py).
"""

from .rules import EpisodeCounters as EpisodeCountersV1  # backup
from .rules_v2 import (
    EpisodeCountersV2,
    Verdict,
    validate_v2,
    record_action_v2,
)

# Alias để code khác (run_benchmark.py) tiếp tục import EpisodeCounters
EpisodeCounters = EpisodeCountersV2


def validate(action_type: str, params: dict, state: dict) -> Verdict:
    """Check action với 8 rule v2. Trả Verdict đầu tiên bị deny, hoặc allow nếu pass tất cả rule áp dụng cho action_type."""
    return validate_v2(action_type, params, state)


def record_action(action_type: str, params: dict) -> None:
    """Cập nhật episode counters sau khi action approved.
    Call AFTER validate() returns allowed=True.
    """
    record_action_v2(action_type, params)
