"""Per-step shared state. Tools read state, set the proposed action,
and record RoE rejections. Reset by ClaudeDefenderPolicy at each step.

Mode flags (`mcp_enabled`, `roe_enabled`) là sticky — set 1 lần khi tạo
policy và giữ nguyên qua toàn episode.
"""


class StepContext:
    state: dict = None
    proposed_action: tuple = None
    rejected_attempts: list = []

    # Mode flags — STICKY (không reset mỗi step)
    mcp_enabled: bool = True
    roe_enabled: bool = True
    # Sprint 3 — Setup C-active: khi True, propose_sleep gọi validate
    # (rule_no_sleep_when_threat) thay vì bypass RoE.
    active_mode: bool = False

    # Detailed logger — STICKY (set bởi ClaudeDefenderPolicy mỗi episode)
    logger = None

    @classmethod
    def reset(cls):
        """Reset per-step state. KHÔNG động đến mode flags hay logger."""
        cls.state = None
        cls.proposed_action = None
        cls.rejected_attempts = []

    @classmethod
    def set_mode(cls, mcp_enabled: bool, roe_enabled: bool, active_mode: bool = False):
        """Set mode flags — gọi 1 lần khi khởi tạo policy."""
        cls.mcp_enabled = mcp_enabled
        cls.roe_enabled = roe_enabled
        cls.active_mode = active_mode

    @classmethod
    def set_logger(cls, logger):
        """Set detailed logger — gọi mỗi episode."""
        cls.logger = logger
