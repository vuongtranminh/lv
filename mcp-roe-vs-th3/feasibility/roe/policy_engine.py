"""RoE V3 engine entry point. Deterministic, không invoke LLM.

Sprint 4. API tương thích với run_benchmark.py (từ feasibility-mcp-roe).
"""

from .rules_v3 import (
    EpisodeCountersV3,
    Verdict,
    validate_v3,
    record_action_v3,
)

EpisodeCounters = EpisodeCountersV3


def validate(action_type: str, params: dict, state: dict) -> Verdict:
    return validate_v3(action_type, params, state)


def record_action(action_type: str, params: dict) -> None:
    record_action_v3(action_type, params)
