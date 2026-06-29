"""Unit tests cho rules_v2.py — 8 rule mở rộng cho Phase 2.

Phủ:
- 3 rule precondition × 2-3 case mỗi rule
- 4 rule rate-limit × 2 case mỗi rule
- 2 case integration (chain rule + record action)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feasibility.roe.rules_v2 import (
    EpisodeCountersV2,
    validate_v2,
    record_action_v2,
    MAX_DECOYS_PER_HOST,
    MAX_DECOYS_TOTAL,
    MAX_RESTORES_TOTAL,
)


# ─── PRECONDITION RULES ──────────────────────────────────────────────────────

def test_restore_denied_when_user_compromise():
    EpisodeCountersV2.reset()
    state = {
        "mission_phase": "MissionA",
        "threats": [{"hostname": "host_a", "compromise_level": "user"}],
    }
    v = validate_v2("Restore", {"hostname": "host_a"}, state)
    assert not v.allowed
    assert "admin" in v.reason.lower()
    assert "analyse" in v.suggested.lower()


def test_restore_allowed_when_admin_compromise():
    EpisodeCountersV2.reset()
    state = {
        "mission_phase": "MissionA",
        "threats": [{"hostname": "host_a", "compromise_level": "admin"}],
    }
    v = validate_v2("Restore", {"hostname": "host_a"}, state)
    assert v.allowed


def test_restore_denied_in_planning_phase():
    EpisodeCountersV2.reset()
    state = {
        "mission_phase": "Planning",
        "threats": [{"hostname": "host_a", "compromise_level": "admin"}],
    }
    v = validate_v2("Restore", {"hostname": "host_a"}, state)
    assert not v.allowed
    assert "planning" in v.reason.lower()


def test_block_critical_zone_denied():
    EpisodeCountersV2.reset()
    state = {"last_action_status": "TRUE"}
    v = validate_v2(
        "BlockTrafficZone",
        {"target_zone": "restricted_zone_a"},
        state,
    )
    assert not v.allowed
    assert "critical" in v.reason.lower() or "trọng yếu" in v.reason.lower()


def test_block_non_critical_zone_allowed():
    EpisodeCountersV2.reset()
    state = {"last_action_status": "TRUE"}
    v = validate_v2(
        "BlockTrafficZone",
        {"target_zone": "public_access_zone"},
        state,
    )
    assert v.allowed


def test_block_denied_when_agent_busy():
    EpisodeCountersV2.reset()
    state = {"last_action_status": "IN_PROGRESS"}
    v = validate_v2(
        "BlockTrafficZone",
        {"target_zone": "public_access_zone"},
        state,
    )
    assert not v.allowed
    assert "busy" in v.reason.lower() or "chưa hoàn tất" in v.reason.lower()


# ─── RATE-LIMIT RULES ────────────────────────────────────────────────────────

def test_block_rate_limit():
    EpisodeCountersV2.reset()
    state = {"last_action_status": "TRUE"}

    v1 = validate_v2("BlockTrafficZone", {"target_zone": "public_access_zone"}, state)
    assert v1.allowed
    record_action_v2("BlockTrafficZone", {"target_zone": "public_access_zone"})

    v2 = validate_v2("BlockTrafficZone", {"target_zone": "public_access_zone"}, state)
    assert not v2.allowed
    assert "đã bị block" in v2.reason.lower()


def test_block_different_zones_independent():
    EpisodeCountersV2.reset()
    state = {"last_action_status": "TRUE"}

    v1 = validate_v2("BlockTrafficZone", {"target_zone": "public_access_zone"}, state)
    assert v1.allowed
    record_action_v2("BlockTrafficZone", {"target_zone": "public_access_zone"})

    # Zone khác — vẫn cho phép (nếu không phải critical)
    v2 = validate_v2("BlockTrafficZone", {"target_zone": "operational_zone_a"}, state)
    assert v2.allowed  # operational_zone_a không có trong CRITICAL_ZONES


def test_decoy_per_host_limit():
    EpisodeCountersV2.reset()
    state = {}

    for _ in range(MAX_DECOYS_PER_HOST):
        v = validate_v2("DeployDecoy", {"hostname": "host_a"}, state)
        assert v.allowed
        record_action_v2("DeployDecoy", {"hostname": "host_a"})

    v_over = validate_v2("DeployDecoy", {"hostname": "host_a"}, state)
    assert not v_over.allowed
    assert "đã có" in v_over.reason.lower()


def test_decoy_global_quota():
    EpisodeCountersV2.reset()
    state = {}

    # Tăng total counter đến giới hạn (dùng 5 host khác nhau, mỗi host 2 decoy)
    for h in range(5):
        host = f"host_{h}"
        for _ in range(2):
            v = validate_v2("DeployDecoy", {"hostname": host}, state)
            assert v.allowed
            record_action_v2("DeployDecoy", {"hostname": host})

    # Đến lượt host thứ 6 — vượt global quota
    v_over = validate_v2("DeployDecoy", {"hostname": "host_new"}, state)
    assert not v_over.allowed
    assert "quota" in v_over.reason.lower() or "tổng" in v_over.reason.lower()


def test_restore_max_per_episode():
    EpisodeCountersV2.reset()
    state = {
        "mission_phase": "MissionA",
        "threats": [{"hostname": "host_a", "compromise_level": "admin"}],
    }

    for _ in range(MAX_RESTORES_TOTAL):
        v = validate_v2("Restore", {"hostname": "host_a"}, state)
        assert v.allowed
        record_action_v2("Restore", {"hostname": "host_a"})

    v_over = validate_v2("Restore", {"hostname": "host_a"}, state)
    assert not v_over.allowed
    assert "quota" in v_over.reason.lower() or "đã đạt" in v_over.reason.lower()


# ─── INTEGRATION TESTS ───────────────────────────────────────────────────────

def test_chain_of_rules_for_restore():
    """Restore phải pass cả 3 rule: needs_admin, phase_constraint, max_per_episode."""
    EpisodeCountersV2.reset()

    # Case 1: admin compromise + MissionA + chưa hit quota → allow
    state = {
        "mission_phase": "MissionA",
        "threats": [{"hostname": "host_a", "compromise_level": "admin"}],
    }
    v = validate_v2("Restore", {"hostname": "host_a"}, state)
    assert v.allowed

    # Case 2: cùng state nhưng Planning phase → deny (rule_restore_phase_constraint fire trước)
    state2 = dict(state)
    state2["mission_phase"] = "Planning"
    v2 = validate_v2("Restore", {"hostname": "host_a"}, state2)
    assert not v2.allowed
    # Có thể deny vì admin pass nhưng phase deny — kiểm tra reason hợp lý
    assert "phase" in v2.reason.lower() or "planning" in v2.reason.lower() or "admin" in v2.reason.lower()


def test_unknown_action_allowed_by_default():
    """Analyse và các action không có rule → mặc định allow."""
    EpisodeCountersV2.reset()
    v = validate_v2("Analyse", {"hostname": "host_a"}, {})
    assert v.allowed


# ─── runner ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import inspect

    tests = [
        (name, fn)
        for name, fn in globals().items()
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
