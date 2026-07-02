"""Rules of Engagement — Version 3 (reward-focused).

Sprint 4. Bộ 6 rule mới thiết kế dựa trên phân tích reward function CAGE 4
(BlueRewardMachine.py). Khác RoE V2 (safety-focused):

- V2: "Bảo vệ khỏi hành động phá hủy không có căn cứ"
- V3: "Tối ưu reward — deny khi hành động sẽ gây phạt gián tiếp (Green fail,
  Red Impact cơ hội), approve khi không"

Chỉ deny/approve thuần. KHÔNG có recommended_action như V2 — RoE V3 chỉ can
thiệp khi LLM đề xuất action sai; LLM tự quyết định action dựa trên prompt.

Căn cứ reward CAGE 4 (BlueRewardMachine.py):
- Blue action KHÔNG có direct cost
- Penalty đến từ: Green work fails (LWF), Green service fails (ASF), Red Impact (RIA)
- Zone × Phase quyết định mức phạt:
    * operational_zone_a trong Phase 1 (MissionA): LWF -10, RIA -10
    * operational_zone_b trong Phase 2 (MissionB): LWF -10, RIA -10
    * Các zone khác: -1 đến -3
"""

from dataclasses import dataclass
from typing import Dict, Set


@dataclass
class Verdict:
    """Kết quả kiểm định của một rule."""
    allowed: bool
    reason: str = ""
    suggested: str = ""
    rule_name: str = ""


# ─── Zone / Phase constants ──────────────────────────────────────────────────

CRITICAL_ZONE_PHASE = {
    # Phase name → set các zone mission-critical trong phase đó
    "MissionA": {"operational_zone_a_subnet"},
    "MissionB": {"operational_zone_b_subnet"},
    # Phase 0 (Planning) — không có mission-critical zone
    "Planning": set(),
}


# ─── Episode counters ────────────────────────────────────────────────────────

class EpisodeCountersV3:
    """State đếm xuyên step, reset đầu mỗi episode."""

    restores_total: int = 0
    decoys_total: int = 0
    decoys_per_host: Dict[str, int] = {}
    analyses_per_host: Dict[str, int] = {}
    blocks_per_zone: Dict[str, int] = {}

    @classmethod
    def reset(cls):
        cls.restores_total = 0
        cls.decoys_total = 0
        cls.decoys_per_host = {}
        cls.analyses_per_host = {}
        cls.blocks_per_zone = {}

    @classmethod
    def record_restore(cls, hostname: str):
        cls.restores_total += 1

    @classmethod
    def record_decoy(cls, hostname: str):
        cls.decoys_total += 1
        cls.decoys_per_host[hostname] = cls.decoys_per_host.get(hostname, 0) + 1

    @classmethod
    def record_analyse(cls, hostname: str):
        cls.analyses_per_host[hostname] = cls.analyses_per_host.get(hostname, 0) + 1

    @classmethod
    def record_block(cls, zone: str):
        cls.blocks_per_zone[zone] = cls.blocks_per_zone.get(zone, 0) + 1


# ─── Hằng số tuning ──────────────────────────────────────────────────────────

MAX_RESTORES_TOTAL = 5      # Restore quota per episode
MAX_ANALYSES_PER_HOST = 2   # Analyse quá 2 lần cùng host không thêm info
MAX_DECOYS_PER_HOST = 2     # Decoy per host
MAX_DECOYS_TOTAL = 10       # Total decoy budget


# ─── Helper — resolve zone từ hostname ──────────────────────────────────────

def _zone_of(hostname: str) -> str:
    """Trích zone name từ hostname format `<zone>_subnet_<role>_host_<idx>`.

    Ví dụ:
      'operational_zone_a_subnet_server_host_0' → 'operational_zone_a_subnet'
      'office_network_subnet_user_host_1' → 'office_network_subnet'
    """
    if not hostname or "_subnet_" not in hostname:
        return ""
    return hostname.split("_subnet_")[0] + "_subnet"


def _is_critical_now(zone: str, phase: str) -> bool:
    """Zone có phải mission-critical trong phase hiện tại không?"""
    return zone in CRITICAL_ZONE_PHASE.get(phase, set())


# ─── R1: RESTORE_ONLY_ADMIN_AND_CRITICAL ────────────────────────────────────

def rule_restore_only_admin_and_critical(state: dict, params: dict) -> Verdict:
    """Restore chỉ được phép khi VỪA có admin compromise VỪA host trong
    mission-critical zone của phase hiện tại.

    Căn cứ reward:
    - Restore = 5 tick downtime → 5 step Green LWF/ASF cascade
    - Cascade phạt ước tính: 5-10 điểm ở zone thường, đến 50 điểm ở operational
      active zone
    - Chỉ đáng nếu ngăn RIA trong operational active (mỗi lần -10, có thể xảy
      ra 5-10 lần trong phần còn lại của episode)
    """
    host = params.get("hostname", "")
    if not host:
        return Verdict(False, "Restore yêu cầu hostname.", rule_name="R1")

    threats = state.get("threats", [])
    host_threat = next((t for t in threats if t.get("hostname") == host), None)
    level = host_threat.get("compromise_level") if host_threat else "none"

    if level != "admin":
        return Verdict(
            allowed=False,
            reason=f"Restore chỉ được phép khi compromise=admin; host '{host}' hiện '{level}'.",
            suggested=f"propose_remove(hostname='{host}') hoặc propose_analyse để xác nhận",
            rule_name="R1",
        )

    zone = _zone_of(host)
    phase = state.get("mission_phase", "")
    if not _is_critical_now(zone, phase):
        return Verdict(
            allowed=False,
            reason=(
                f"Host '{host}' thuộc zone '{zone}' — không phải mission-critical "
                f"trong phase '{phase}'. Restore ở đây tốn 5 tick downtime "
                f"nhưng không ngăn được phạt cao. Dùng Remove."
            ),
            suggested=f"propose_remove(hostname='{host}')",
            rule_name="R1",
        )

    return Verdict(True, rule_name="R1")


# ─── R2: BLOCK_OPERATIONAL_FORBIDDEN ────────────────────────────────────────

def rule_block_operational_forbidden(state: dict, params: dict) -> Verdict:
    """Cấm BlockTrafficZone khi target = operational_zone_a trong Phase 1
    hoặc operational_zone_b trong Phase 2.

    Căn cứ reward:
    - Block operational active zone → Green trong zone không truy cập được
      service ngoài → ASF fail liên tục
    - Zone active phạt -10/ASF fail. Block liên tục nhiều step = phạt lớn
    """
    zone = params.get("target_zone", "")
    if not zone:
        return Verdict(False, "BlockTrafficZone yêu cầu target_zone.", rule_name="R2")

    zone_normalized = zone if zone.endswith("_subnet") else f"{zone}_subnet"
    phase = state.get("mission_phase", "")

    if _is_critical_now(zone_normalized, phase):
        return Verdict(
            allowed=False,
            reason=(
                f"Zone '{zone}' đang mission-critical trong phase '{phase}'. "
                f"Block sẽ gây Green fail cascade với mức phạt -10/lần."
            ),
            suggested=f"propose_deploy_decoy hoặc propose_analyse trên host trong zone thay vào đó",
            rule_name="R2",
        )
    return Verdict(True, rule_name="R2")


# ─── R3: RESTORE_MAX_PER_EPISODE ────────────────────────────────────────────

def rule_restore_max_per_episode(state: dict, params: dict) -> Verdict:
    """Deny Restore nếu đã dùng ≥ 5 Restore trong episode.

    Căn cứ reward:
    - Mỗi Restore trung bình gây 3-5 Green fail cascade
    - 5 Restore ≈ 15-25 phạt gián tiếp cộng dồn
    - Vượt 5 = quá nhiều cascade damage, không còn lợi ích ngăn RIA
    """
    if EpisodeCountersV3.restores_total >= MAX_RESTORES_TOTAL:
        host = params.get("hostname", "?")
        return Verdict(
            allowed=False,
            reason=(
                f"Đã dùng đủ quota Restore của episode ({EpisodeCountersV3.restores_total}"
                f"/{MAX_RESTORES_TOTAL}). Không cho Restore thêm."
            ),
            suggested=f"propose_remove(hostname='{host}') hoặc propose_block_traffic",
            rule_name="R3",
        )
    return Verdict(True, rule_name="R3")


# ─── R4: ANALYSE_MAX_PER_HOST ───────────────────────────────────────────────

def rule_analyse_max_per_host(state: dict, params: dict) -> Verdict:
    """Deny Analyse cùng host quá 2 lần trong episode.

    Căn cứ reward:
    - Analyse tốn 2 tick agent busy
    - Analyse lần 3+ không mang info mới (env trả snapshot đầy đủ mỗi step)
    - Tick busy = Blue không phản ứng → Red có cơ hội RIA
    """
    host = params.get("hostname", "")
    if not host:
        return Verdict(False, "Analyse yêu cầu hostname.", rule_name="R4")

    n = EpisodeCountersV3.analyses_per_host.get(host, 0)
    if n >= MAX_ANALYSES_PER_HOST:
        return Verdict(
            allowed=False,
            reason=(
                f"Đã Analyse host '{host}' {n} lần trong episode "
                f"(giới hạn: {MAX_ANALYSES_PER_HOST}). Analyse thêm không mang info mới."
            ),
            suggested=(
                f"Nếu có IOC → propose_remove hoặc propose_restore theo mức compromise. "
                f"Nếu không IOC → propose_sleep hoặc analyse host khác."
            ),
            rule_name="R4",
        )
    return Verdict(True, rule_name="R4")


# ─── R5: DECOY_QUOTA ────────────────────────────────────────────────────────

def rule_decoy_quota(state: dict, params: dict) -> Verdict:
    """Deny DeployDecoy nếu (host đã có ≥ 2 decoy) HOẶC (tổng ≥ 10).

    Căn cứ reward:
    - Decoy có chi phí 0 direct
    - Nhưng nhiều decoy tạo nhiễu, có thể gây Green vô tình access → LWF cascade
    - Giới hạn 2/host và 10/total giống RoE V2 (đã proven ổn)
    """
    host = params.get("hostname", "")
    if not host:
        return Verdict(False, "DeployDecoy yêu cầu hostname.", rule_name="R5")

    per_host = EpisodeCountersV3.decoys_per_host.get(host, 0)
    if per_host >= MAX_DECOYS_PER_HOST:
        return Verdict(
            allowed=False,
            reason=f"Host '{host}' đã có {per_host} decoy (giới hạn: {MAX_DECOYS_PER_HOST}).",
            suggested="propose_deploy_decoy trên host khác",
            rule_name="R5",
        )

    if EpisodeCountersV3.decoys_total >= MAX_DECOYS_TOTAL:
        return Verdict(
            allowed=False,
            reason=(
                f"Đã dùng đủ quota decoy tổng ({EpisodeCountersV3.decoys_total}"
                f"/{MAX_DECOYS_TOTAL})."
            ),
            suggested="propose_analyse hoặc propose_sleep",
            rule_name="R5",
        )
    return Verdict(True, rule_name="R5")


# ─── R6: SLEEP_ALWAYS_OK ────────────────────────────────────────────────────

def rule_sleep_always_ok(state: dict, params: dict) -> Verdict:
    """Sleep LUÔN được approve — bất kể state.

    Căn cứ reward:
    - Sleep có chi phí 0 direct và 0 gián tiếp (Green không phụ thuộc Blue
      action để làm việc — chỉ phụ thuộc host state, mà Sleep không thay đổi
      host state)
    - Sleep là default an toàn nhất khi LLM không chắc
    - Buộc LLM hành động (rule_no_sleep_when_threat của Sprint 3) đã chứng
      minh reward tệ hơn → RoE V3 bỏ hoàn toàn
    """
    return Verdict(True, rule_name="R6")


# ─── Lookup table & validate() ──────────────────────────────────────────────

RULES_V3 = {
    "Restore": [
        rule_restore_only_admin_and_critical,
        rule_restore_max_per_episode,
    ],
    "BlockTrafficZone": [
        rule_block_operational_forbidden,
    ],
    "Analyse": [
        rule_analyse_max_per_host,
    ],
    "DeployDecoy": [
        rule_decoy_quota,
    ],
    "Sleep": [
        rule_sleep_always_ok,
    ],
    # Remove: không có rule — luôn allow (Remove an toàn, kill process only)
}


def validate_v3(action_type: str, params: dict, state: dict) -> Verdict:
    """Chạy chuỗi rule cho action_type. Trả Verdict đầu tiên deny, hoặc allow."""
    rules = RULES_V3.get(action_type, [])
    for rule in rules:
        verdict = rule(state, params)
        if not verdict.allowed:
            return verdict
    return Verdict(True, rule_name=f"{action_type}:ALL_PASS")


def record_action_v3(action_type: str, params: dict) -> None:
    """Cập nhật counter sau khi action approve."""
    if action_type == "Restore":
        EpisodeCountersV3.record_restore(params.get("hostname", ""))
    elif action_type == "DeployDecoy":
        EpisodeCountersV3.record_decoy(params.get("hostname", ""))
    elif action_type == "Analyse":
        EpisodeCountersV3.record_analyse(params.get("hostname", ""))
    elif action_type == "BlockTrafficZone":
        EpisodeCountersV3.record_block(params.get("target_zone", ""))
