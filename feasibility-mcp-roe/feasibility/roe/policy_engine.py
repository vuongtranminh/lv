"""RoE entry point. Deterministic — never invokes the LLM."""

from .rules import RULES, Verdict, EpisodeCounters


def validate(action_type: str, params: dict, state: dict) -> Verdict:
    """Check a proposed action against RoE. Unknown actions default to allowed."""
    rule = RULES.get(action_type)
    if rule is None:
        return Verdict(True)
    return rule(state, params)


def record_action(action_type: str, params: dict) -> None:
    """Update episode counters after an action is approved.
    Call AFTER validate() returns allowed=True.
    """
    if action_type == "BlockTrafficZone":
        EpisodeCounters.record_block(params.get("target_zone"))
    elif action_type == "DeployDecoy":
        EpisodeCounters.record_decoy(params.get("hostname"))
