"""Rules of Engagement — Version 2 (mở rộng cho Phase 2).

Mở rộng từ 3 rule trong rules.py lên 8 rule:
- 4 precondition rule (kiểm tra state)
- 4 rate-limit rule (giới hạn theo episode counter)

So với rules.py:
- Kế thừa: rule_restore_needs_admin, rule_block_rate_limit, rule_decoy_per_host
- Thêm mới:
  - rule_restore_phase_constraint
  - rule_block_critical_zone_forbidden
  - rule_no_block_when_busy
  - rule_decoy_global_quota
  - rule_restore_max_per_episode
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Verdict:
    allowed: bool
    reason: str = ""
    suggested: str = ""


# ─── Episode-level counters ──────────────────────────────────────────────────

class EpisodeCountersV2:
    """Bộ đếm trạng thái xuyên step trong 1 episode. Reset đầu mỗi episode."""

    blocks_per_zone: Dict[str, int] = {}
    decoys_per_host: Dict[str, int] = {}
    restores_total: int = 0
    decoys_total: int = 0

    @classmethod
    def reset(cls):
        cls.blocks_per_zone = {}
        cls.decoys_per_host = {}
        cls.restores_total = 0
        cls.decoys_total = 0

    @classmethod
    def record_block(cls, zone: str):
        cls.blocks_per_zone[zone] = cls.blocks_per_zone.get(zone, 0) + 1

    @classmethod
    def record_decoy(cls, host: str):
        cls.decoys_per_host[host] = cls.decoys_per_host.get(host, 0) + 1
        cls.decoys_total += 1

    @classmethod
    def record_restore(cls, host: str):
        cls.restores_total += 1


# ─── Hằng số ─────────────────────────────────────────────────────────────────

CRITICAL_ZONES = {
    "restricted_zone_a",
    "restricted_zone_b",
}

MAX_BLOCKS_PER_ZONE = 1
MAX_DECOYS_PER_HOST = 2
MAX_DECOYS_TOTAL = 10
MAX_RESTORES_TOTAL = 5


# ─── PRECONDITION RULES (4 rule) ─────────────────────────────────────────────

def rule_restore_needs_admin(state: dict, params: dict) -> Verdict:
    """Restore chỉ allow khi host có admin-level compromise xác nhận."""
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


def rule_restore_phase_constraint(state: dict, params: dict) -> Verdict:
    """Không Restore trong phase Planning (chưa đến nhiệm vụ chính)."""
    phase = state.get("mission_phase", "unknown")
    if phase == "Planning":
        host = params.get("hostname", "?")
        return Verdict(
            allowed=False,
            reason=(
                f"Restore không được phép trong phase Planning. "
                f"Phase hiện tại: '{phase}'."
            ),
            suggested=f"propose_deploy_decoy(hostname='{host}', reason='chuẩn bị phát hiện')",
        )
    return Verdict(True)


def rule_block_critical_zone_forbidden(state: dict, params: dict) -> Verdict:
    """Không block traffic giữa 2 vùng vận hành (operational) trọng yếu."""
    zone = params.get("target_zone")
    if not zone:
        return Verdict(False, "BlockTrafficZone yêu cầu một target_zone.")

    if zone in CRITICAL_ZONES:
        return Verdict(
            allowed=False,
            reason=(
                f"Zone '{zone}' nằm trong danh sách vùng trọng yếu (critical zones), "
                f"không được block để bảo đảm tính khả dụng dịch vụ."
            ),
            suggested=f"propose_deploy_decoy hoặc propose_analyse trên host trong zone '{zone}'",
        )
    return Verdict(True)


def rule_no_block_when_busy(state: dict, params: dict) -> Verdict:
    """Không block traffic khi agent đang ở trạng thái busy (last action chưa xong)."""
    last_action_status = state.get("last_action_status", "")
    if last_action_status == "IN_PROGRESS":
        zone = params.get("target_zone", "?")
        return Verdict(
            allowed=False,
            reason=(
                "Agent đang trong trạng thái busy (last_action chưa hoàn tất). "
                "Không cho phép action phá hủy mới."
            ),
            suggested=f"propose_analyse trên một host để đợi action trước hoàn tất",
        )
    return Verdict(True)


# ─── RATE-LIMIT RULES (4 rule) ───────────────────────────────────────────────

def rule_block_rate_limit(state: dict, params: dict) -> Verdict:
    """Max 1 BlockTrafficZone / zone / episode (bảo toàn availability)."""
    zone = params.get("target_zone")
    if not zone:
        return Verdict(False, "BlockTrafficZone yêu cầu một target_zone.")

    blocks = EpisodeCountersV2.blocks_per_zone.get(zone, 0)
    if blocks >= MAX_BLOCKS_PER_ZONE:
        return Verdict(
            allowed=False,
            reason=f"Zone '{zone}' đã bị block {blocks} lần trong episode này (giới hạn: {MAX_BLOCKS_PER_ZONE}).",
            suggested="propose_deploy_decoy hoặc propose_analyse trên một host trong zone đó thay vào đó",
        )
    return Verdict(True)


def rule_decoy_per_host(state: dict, params: dict) -> Verdict:
    """Max 2 decoy / host / episode (tránh nhiễu tín hiệu)."""
    host = params.get("hostname")
    if not host:
        return Verdict(False, "DeployDecoy yêu cầu một hostname.")

    decoys = EpisodeCountersV2.decoys_per_host.get(host, 0)
    if decoys >= MAX_DECOYS_PER_HOST:
        return Verdict(
            allowed=False,
            reason=f"Host '{host}' đã có {decoys} decoy (giới hạn: {MAX_DECOYS_PER_HOST}).",
            suggested="propose_deploy_decoy trên một host khác, hoặc propose_analyse",
        )
    return Verdict(True)


def rule_decoy_global_quota(state: dict, params: dict) -> Verdict:
    """Max 10 decoy tổng / episode (kiểm soát tổng resource)."""
    total = EpisodeCountersV2.decoys_total
    if total >= MAX_DECOYS_TOTAL:
        host = params.get("hostname", "?")
        return Verdict(
            allowed=False,
            reason=(
                f"Đã đạt quota tổng decoy của episode ({total}/{MAX_DECOYS_TOTAL}). "
                f"Không cho phép thêm decoy mới."
            ),
            suggested=f"propose_analyse(hostname='{host}', reason='ưu tiên investigate')",
        )
    return Verdict(True)


def rule_restore_max_per_episode(state: dict, params: dict) -> Verdict:
    """Max 5 Restore / episode (bảo toàn availability)."""
    total = EpisodeCountersV2.restores_total
    if total >= MAX_RESTORES_TOTAL:
        host = params.get("hostname", "?")
        return Verdict(
            allowed=False,
            reason=(
                f"Đã đạt quota tổng Restore của episode ({total}/{MAX_RESTORES_TOTAL}). "
                f"Cần xem xét lại chiến lược thay vì restore thêm."
            ),
            suggested=f"propose_block_traffic trên zone của host '{host}' (nếu chưa block) hoặc propose_analyse",
        )
    return Verdict(True)


# ─── Lookup table ────────────────────────────────────────────────────────────

# Mỗi action có thể có NHIỀU rule áp dụng. Khi validate: chạy tuần tự,
# fail-fast — rule nào deny trước thì return ngay.
RULES_V2 = {
    "Restore": [
        rule_restore_needs_admin,
        rule_restore_phase_constraint,
        rule_restore_max_per_episode,
    ],
    "BlockTrafficZone": [
        rule_block_critical_zone_forbidden,
        rule_no_block_when_busy,
        rule_block_rate_limit,
    ],
    "DeployDecoy": [
        rule_decoy_per_host,
        rule_decoy_global_quota,
    ],
    # Analyse không có rule → luôn allow (action an toàn)
}


def validate_v2(action_type: str, params: dict, state: dict) -> Verdict:
    """Chạy chuỗi rule cho action_type. Trả Verdict đầu tiên bị deny, hoặc allow nếu pass hết."""
    rules = RULES_V2.get(action_type, [])
    for rule in rules:
        verdict = rule(state, params)
        if not verdict.allowed:
            return verdict
    return Verdict(True)


def record_action_v2(action_type: str, params: dict) -> None:
    """Cập nhật counter sau khi action được approve."""
    if action_type == "BlockTrafficZone":
        EpisodeCountersV2.record_block(params.get("target_zone", ""))
    elif action_type == "DeployDecoy":
        EpisodeCountersV2.record_decoy(params.get("hostname", ""))
    elif action_type == "Restore":
        EpisodeCountersV2.record_restore(params.get("hostname", ""))


# ─── ACTIVE SUGGESTION (Sprint 2 — D2 fix) ──────────────────────────────────

def recommend_next_action(state: dict) -> dict:
    """Trả về action ĐƯỢC ĐỀ XUẤT mà LLM nên gọi tiếp, dựa trên state hiện tại.

    Khác Verdict (chỉ deny/allow): hàm này CHỦ ĐỘNG suggest. Dùng để inject
    `recommended_action` vào tool result `get_threat_summary` — giúp LLM
    không "loay hoay" mãi với Analyse.

    Logic ưu tiên:
    1. Có host admin → đề xuất Restore host đó
    2. Có host user → đề xuất Remove host đó
    3. Mạng sạch (0 threats + comms all none) → đề xuất Sleep
    4. Có host chưa được Analyse → đề xuất Analyse host trọng yếu
    5. Mạng "không xác định" → đề xuất DeployDecoy
    """
    threats = state.get("threats", [])

    # Priority 1: admin host → Restore
    admin_threats = [t for t in threats if t.get("compromise_level") == "admin"]
    if admin_threats:
        # Check quota Restore (max 5/episode)
        if EpisodeCountersV2.restores_total < MAX_RESTORES_TOTAL:
            return {
                "action": "Restore",
                "hostname": admin_threats[0]["hostname"],
                "reason": (
                    f"Host '{admin_threats[0]['hostname']}' có IOC admin "
                    f"({admin_threats[0].get('iocs', [])}) — Restore ngay để cắt threat."
                ),
                "priority": "critical",
            }

    # Priority 2: user-level host → Remove
    user_threats = [t for t in threats if t.get("compromise_level") == "user"]
    if user_threats:
        return {
            "action": "Remove",
            "hostname": user_threats[0]["hostname"],
            "reason": (
                f"Host '{user_threats[0]['hostname']}' có IOC user-level "
                f"({user_threats[0].get('iocs', [])}) — Remove sớm tránh leo thang."
            ),
            "priority": "high",
        }

    # Priority 3: mạng "sạch" → Sleep
    comms = state.get("comms", [])
    all_comms_none = all(
        c.get("compromise_level_in_sender_net") == "none" for c in comms
    )
    if not threats and all_comms_none and comms:
        return {
            "action": "Sleep",
            "reason": "Không có threat + đồng đội không báo gì — giảm chi phí ngầm.",
            "priority": "low",
        }

    # Priority 4: có host chưa decoy → DeployDecoy
    all_hosts = state.get("all_hostnames", [])
    for h in all_hosts:
        if EpisodeCountersV2.decoys_per_host.get(h, 0) < MAX_DECOYS_PER_HOST:
            if EpisodeCountersV2.decoys_total < MAX_DECOYS_TOTAL:
                return {
                    "action": "DeployDecoy",
                    "hostname": h,
                    "reason": f"Phòng thủ chủ động — host '{h}' chưa đạt quota decoy.",
                    "priority": "low",
                }
            break  # đã đạt quota tổng

    # Fallback: Analyse host bất kỳ
    if all_hosts:
        return {
            "action": "Analyse",
            "hostname": all_hosts[0],
            "reason": "Kiểm tra định kỳ — không có signal đặc biệt nào.",
            "priority": "low",
        }

    return {"action": "Sleep", "reason": "Không có host nào để hành động.", "priority": "low"}
