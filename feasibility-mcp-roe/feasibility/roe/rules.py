"""Rules of Engagement — 3 deterministic rules for the feasibility study.

Each rule takes (state, params) and returns a Verdict. Episode-level
counters track stateful constraints (block / decoy rate limits).
"""

from dataclasses import dataclass


@dataclass
class Verdict:
    allowed: bool
    reason: str = ""
    suggested: str = ""


class EpisodeCounters:
    """Stateful counters reset by ClaudeDefenderPolicy at episode start."""
    blocks_per_zone: dict = {}
    decoys_per_host: dict = {}

    @classmethod
    def reset(cls):
        cls.blocks_per_zone = {}
        cls.decoys_per_host = {}

    @classmethod
    def record_block(cls, zone):
        cls.blocks_per_zone[zone] = cls.blocks_per_zone.get(zone, 0) + 1

    @classmethod
    def record_decoy(cls, host):
        cls.decoys_per_host[host] = cls.decoys_per_host.get(host, 0) + 1


def rule_restore_needs_admin(state: dict, params: dict) -> Verdict:
    """Restore is destructive — only allow if admin-level compromise confirmed."""
    host = params.get("hostname")
    if not host:
        return Verdict(False, "Restore yêu cầu một hostname.")

    host_threat = next(
        (t for t in state.get("threats", []) if t["hostname"] == host),
        None,
    )
    level = host_threat["compromise_level"] if host_threat else "none"

    if level != "admin":
        return Verdict(
            allowed=False,
            reason=(
                f"Restore yêu cầu xác nhận admin-level compromise; "
                f"host '{host}' hiện đang ở mức '{level}'."
            ),
            suggested=f"propose_analyse(hostname='{host}', reason='thu thập thêm bằng chứng')",
        )
    return Verdict(True)


def rule_block_rate_limit(state: dict, params: dict) -> Verdict:
    """Max 1 BlockTrafficZone per zone per episode (preserve availability)."""
    zone = params.get("target_zone")
    if not zone:
        return Verdict(False, "BlockTrafficZone yêu cầu một target_zone.")

    blocks = EpisodeCounters.blocks_per_zone.get(zone, 0)
    if blocks >= 1:
        return Verdict(
            allowed=False,
            reason=f"Zone '{zone}' đã bị block {blocks} lần trong episode này.",
            suggested="propose_deploy_decoy hoặc propose_analyse trên một host trong zone đó thay vào đó",
        )
    return Verdict(True)


def rule_decoy_per_host(state: dict, params: dict) -> Verdict:
    """Max 2 decoys per host per episode (avoid signal noise)."""
    host = params.get("hostname")
    if not host:
        return Verdict(False, "DeployDecoy yêu cầu một hostname.")

    decoys = EpisodeCounters.decoys_per_host.get(host, 0)
    if decoys >= 2:
        return Verdict(
            allowed=False,
            reason=f"Host '{host}' đã có {decoys} decoy.",
            suggested="propose_deploy_decoy trên một host khác, hoặc propose_analyse",
        )
    return Verdict(True)


RULES = {
    "Restore": rule_restore_needs_admin,
    "BlockTrafficZone": rule_block_rate_limit,
    "DeployDecoy": rule_decoy_per_host,
}
