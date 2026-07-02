"""Per-step shared state cho Sprint 4 project.

Đơn giản hơn feasibility-mcp-roe/context.py — KHÔNG có active_mode (Sprint 4
dùng cách thay thế prompt in-place thay vì flag runtime).

Mode flags (mcp_enabled, roe_enabled) là sticky — set 1 lần khi tạo policy
và giữ nguyên qua toàn episode.
"""


class StepContext:
    state: dict = None
    proposed_action: tuple = None
    rejected_attempts: list = []

    # Mode flags — STICKY (không reset mỗi step)
    mcp_enabled: bool = True
    roe_enabled: bool = True

    # Detailed logger — STICKY (set bởi ClaudeDefenderPolicy mỗi episode)
    logger = None

    @classmethod
    def reset(cls):
        """Reset per-step state. KHÔNG động đến mode flags hay logger."""
        cls.state = None
        cls.proposed_action = None
        cls.rejected_attempts = []

    @classmethod
    def set_mode(cls, mcp_enabled: bool, roe_enabled: bool):
        cls.mcp_enabled = mcp_enabled
        cls.roe_enabled = roe_enabled

    @classmethod
    def set_logger(cls, logger):
        cls.logger = logger
