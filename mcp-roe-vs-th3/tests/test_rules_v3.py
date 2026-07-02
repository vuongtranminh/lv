"""Test 6 rule RoE V3 (reward-focused).

Kiểm tra từng rule + integration validate() + counter behavior.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feasibility.roe.rules_v3 import (
    EpisodeCountersV3,
    Verdict,
    validate_v3,
    record_action_v3,
    rule_restore_only_admin_and_critical,
    rule_block_operational_forbidden,
    rule_restore_max_per_episode,
    rule_analyse_max_per_host,
    rule_decoy_quota,
    rule_sleep_always_ok,
    _zone_of,
    _is_critical_now,
    MAX_RESTORES_TOTAL,
    MAX_ANALYSES_PER_HOST,
    MAX_DECOYS_PER_HOST,
    MAX_DECOYS_TOTAL,
)


# ─── Fixtures / helpers ──────────────────────────────────────────────────────

def state_with_threat(hostname, level, phase="MissionA"):
    return {
        "mission_phase": phase,
        "threats": [{"hostname": hostname, "compromise_level": level, "iocs": []}],
    }


def state_clean(phase="MissionA"):
    return {"mission_phase": phase, "threats": []}


# ─── Helper functions ───────────────────────────────────────────────────────

def test_zone_of_extracts_operational():
    assert _zone_of("operational_zone_a_subnet_server_host_0") == "operational_zone_a_subnet"


def test_zone_of_extracts_office():
    assert _zone_of("office_network_subnet_user_host_1") == "office_network_subnet"


def test_zone_of_empty_input():
    assert _zone_of("") == ""
    assert _zone_of("weird_name_no_subnet") == ""


def test_is_critical_operational_a_in_missiona():
    assert _is_critical_now("operational_zone_a_subnet", "MissionA")


def test_is_critical_operational_b_in_missiona():
    assert not _is_critical_now("operational_zone_b_subnet", "MissionA")


def test_is_critical_operational_b_in_missionb():
    assert _is_critical_now("operational_zone_b_subnet", "MissionB")


def test_is_critical_planning_phase_none_critical():
    assert not _is_critical_now("operational_zone_a_subnet", "Planning")


# ─── R1: RESTORE_ONLY_ADMIN_AND_CRITICAL ────────────────────────────────────

def test_r1_restore_denied_user_level():
    EpisodeCountersV3.reset()
    state = state_with_threat("operational_zone_a_subnet_server_host_0", "user", "MissionA")
    v = rule_restore_only_admin_and_critical(state, {"hostname": "operational_zone_a_subnet_server_host_0"})
    assert not v.allowed
    assert "user" in v.reason.lower() or "admin" in v.reason.lower()
    assert v.rule_name == "R1"


def test_r1_restore_denied_admin_but_not_critical_zone():
    EpisodeCountersV3.reset()
    state = state_with_threat("office_network_subnet_user_host_1", "admin", "MissionA")
    v = rule_restore_only_admin_and_critical(state, {"hostname": "office_network_subnet_user_host_1"})
    assert not v.allowed
    assert "office_network_subnet" in v.reason or "critical" in v.reason.lower()
    assert v.rule_name == "R1"


def test_r1_restore_allowed_admin_in_critical_zone():
    EpisodeCountersV3.reset()
    state = state_with_threat("operational_zone_a_subnet_server_host_0", "admin", "MissionA")
    v = rule_restore_only_admin_and_critical(state, {"hostname": "operational_zone_a_subnet_server_host_0"})
    assert v.allowed
    assert v.rule_name == "R1"


def test_r1_restore_denied_admin_in_operational_b_during_missiona():
    """operational_zone_b không phải critical khi phase = MissionA."""
    EpisodeCountersV3.reset()
    state = state_with_threat("operational_zone_b_subnet_server_host_0", "admin", "MissionA")
    v = rule_restore_only_admin_and_critical(state, {"hostname": "operational_zone_b_subnet_server_host_0"})
    assert not v.allowed


def test_r1_restore_allowed_admin_in_operational_b_during_missionb():
    EpisodeCountersV3.reset()
    state = state_with_threat("operational_zone_b_subnet_server_host_0", "admin", "MissionB")
    v = rule_restore_only_admin_and_critical(state, {"hostname": "operational_zone_b_subnet_server_host_0"})
    assert v.allowed


# ─── R2: BLOCK_OPERATIONAL_FORBIDDEN ────────────────────────────────────────

def test_r2_block_operational_a_denied_in_missiona():
    v = rule_block_operational_forbidden(
        state_clean("MissionA"), {"target_zone": "operational_zone_a"},
    )
    assert not v.allowed
    assert v.rule_name == "R2"


def test_r2_block_operational_b_allowed_during_missiona():
    v = rule_block_operational_forbidden(
        state_clean("MissionA"), {"target_zone": "operational_zone_b"},
    )
    assert v.allowed


def test_r2_block_office_always_allowed():
    v = rule_block_operational_forbidden(
        state_clean("MissionA"), {"target_zone": "office_network"},
    )
    assert v.allowed


def test_r2_block_operational_a_allowed_in_planning():
    v = rule_block_operational_forbidden(
        state_clean("Planning"), {"target_zone": "operational_zone_a"},
    )
    assert v.allowed


# ─── R3: RESTORE_MAX_PER_EPISODE ────────────────────────────────────────────

def test_r3_restore_allowed_under_quota():
    EpisodeCountersV3.reset()
    EpisodeCountersV3.restores_total = MAX_RESTORES_TOTAL - 1
    v = rule_restore_max_per_episode(state_clean(), {"hostname": "any"})
    assert v.allowed


def test_r3_restore_denied_at_quota():
    EpisodeCountersV3.reset()
    EpisodeCountersV3.restores_total = MAX_RESTORES_TOTAL
    v = rule_restore_max_per_episode(state_clean(), {"hostname": "any"})
    assert not v.allowed
    assert v.rule_name == "R3"


# ─── R4: ANALYSE_MAX_PER_HOST ───────────────────────────────────────────────

def test_r4_analyse_allowed_first_time():
    EpisodeCountersV3.reset()
    v = rule_analyse_max_per_host(state_clean(), {"hostname": "host_x"})
    assert v.allowed


def test_r4_analyse_denied_after_max():
    EpisodeCountersV3.reset()
    EpisodeCountersV3.analyses_per_host["host_x"] = MAX_ANALYSES_PER_HOST
    v = rule_analyse_max_per_host(state_clean(), {"hostname": "host_x"})
    assert not v.allowed
    assert v.rule_name == "R4"


def test_r4_analyse_other_host_still_allowed():
    EpisodeCountersV3.reset()
    EpisodeCountersV3.analyses_per_host["host_x"] = MAX_ANALYSES_PER_HOST
    v = rule_analyse_max_per_host(state_clean(), {"hostname": "host_y"})
    assert v.allowed


# ─── R5: DECOY_QUOTA ────────────────────────────────────────────────────────

def test_r5_decoy_allowed_first_time():
    EpisodeCountersV3.reset()
    v = rule_decoy_quota(state_clean(), {"hostname": "host_x"})
    assert v.allowed


def test_r5_decoy_denied_per_host_max():
    EpisodeCountersV3.reset()
    EpisodeCountersV3.decoys_per_host["host_x"] = MAX_DECOYS_PER_HOST
    v = rule_decoy_quota(state_clean(), {"hostname": "host_x"})
    assert not v.allowed
    assert v.rule_name == "R5"


def test_r5_decoy_denied_total_max():
    EpisodeCountersV3.reset()
    EpisodeCountersV3.decoys_total = MAX_DECOYS_TOTAL
    v = rule_decoy_quota(state_clean(), {"hostname": "brand_new_host"})
    assert not v.allowed


# ─── R6: SLEEP_ALWAYS_OK ────────────────────────────────────────────────────

def test_r6_sleep_allowed_when_threat_present():
    """R6 khác biệt lớn với Sprint 3 rule_no_sleep_when_threat — Sleep LUÔN OK."""
    state = state_with_threat("host_x", "admin", "MissionA")
    v = rule_sleep_always_ok(state, {})
    assert v.allowed
    assert v.rule_name == "R6"


def test_r6_sleep_allowed_when_clean():
    v = rule_sleep_always_ok(state_clean(), {})
    assert v.allowed


# ─── Integration: validate() end-to-end ─────────────────────────────────────

def test_validate_restore_admin_critical_zone_passes_all_rules():
    EpisodeCountersV3.reset()
    state = state_with_threat("operational_zone_a_subnet_server_host_0", "admin", "MissionA")
    v = validate_v3("Restore", {"hostname": "operational_zone_a_subnet_server_host_0"}, state)
    assert v.allowed


def test_validate_restore_denied_quota_first():
    """Khi both R1 pass và R3 fail → R3 fire trước (thứ tự trong RULES_V3)."""
    EpisodeCountersV3.reset()
    EpisodeCountersV3.restores_total = MAX_RESTORES_TOTAL
    state = state_with_threat("operational_zone_a_subnet_server_host_0", "admin", "MissionA")
    v = validate_v3("Restore", {"hostname": "operational_zone_a_subnet_server_host_0"}, state)
    assert not v.allowed
    # R1 chạy trước, thì R1 pass, R3 mới deny → verdict.rule_name = R3
    assert v.rule_name == "R3"


def test_validate_remove_always_allowed():
    """Remove không có rule nào → luôn allow."""
    EpisodeCountersV3.reset()
    state = state_with_threat("host_x", "user")
    v = validate_v3("Remove", {"hostname": "host_x"}, state)
    assert v.allowed
    assert "ALL_PASS" in v.rule_name


def test_validate_unknown_action_allowed():
    v = validate_v3("Monitor", {}, state_clean())
    assert v.allowed


# ─── Counter behavior ───────────────────────────────────────────────────────

def test_record_restore_increments():
    EpisodeCountersV3.reset()
    record_action_v3("Restore", {"hostname": "host_x"})
    assert EpisodeCountersV3.restores_total == 1
    record_action_v3("Restore", {"hostname": "host_y"})
    assert EpisodeCountersV3.restores_total == 2


def test_record_decoy_updates_both_counters():
    EpisodeCountersV3.reset()
    record_action_v3("DeployDecoy", {"hostname": "host_x"})
    assert EpisodeCountersV3.decoys_per_host["host_x"] == 1
    assert EpisodeCountersV3.decoys_total == 1


def test_record_analyse_tracks_per_host():
    EpisodeCountersV3.reset()
    record_action_v3("Analyse", {"hostname": "host_x"})
    record_action_v3("Analyse", {"hostname": "host_x"})
    record_action_v3("Analyse", {"hostname": "host_y"})
    assert EpisodeCountersV3.analyses_per_host["host_x"] == 2
    assert EpisodeCountersV3.analyses_per_host["host_y"] == 1


def test_reset_clears_all():
    EpisodeCountersV3.restores_total = 3
    EpisodeCountersV3.decoys_total = 5
    EpisodeCountersV3.decoys_per_host = {"h": 2}
    EpisodeCountersV3.analyses_per_host = {"h": 1}
    EpisodeCountersV3.reset()
    assert EpisodeCountersV3.restores_total == 0
    assert EpisodeCountersV3.decoys_total == 0
    assert EpisodeCountersV3.decoys_per_host == {}
    assert EpisodeCountersV3.analyses_per_host == {}


# ─── runner ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import inspect

    tests = [
        (name, fn) for name, fn in globals().items()
        if name.startswith("test_") and inspect.isfunction(fn)
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(0 if failed == 0 else 1)
