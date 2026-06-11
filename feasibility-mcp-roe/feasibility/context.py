"""Per-step shared state. Tools read state, set the proposed action,
and record RoE rejections. Reset by ClaudeDefenderPolicy at each step.
"""


class StepContext:
    state: dict = None
    proposed_action: tuple = None  # (action_type, params, reason) or None
    rejected_attempts: list = []   # list of (action_type, target, reason)

    @classmethod
    def reset(cls):
        cls.state = None
        cls.proposed_action = None
        cls.rejected_attempts = []
