"""Offline tests — no CybORG, no Claude API key needed.

Validates the deterministic core: comms-vector decoder, RoE engine, episode
counters. Run BEFORE attempting any CybORG integration.

    python tests/test_offline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feasibility.state_extractor import decode_commvector, extract_state
from feasibility.roe import policy_engine
from feasibility.roe.rules import EpisodeCounters


# ─── Comms-vector decoder ─────────────────────────────────────────────────────

def test_decode_commvector_no_compromise():
    bits = [0, 0, 0, 0, 0, 0, 0, 0]
    result = decode_commvector(bits, from_agent_idx=3, my_agent_idx=4)
    assert result["from"] == "blue_agent_3"
    assert result["reports_malicious_in_other_networks"] == []
    assert result["compromise_level_in_sender_net"] == "none"
    assert result["sender_busy"] is False


def test_decode_commvector_admin_compromise_busy():
    # Agent 3 reports agent 0's net has malice; sender has admin compromise + busy
    bits = [1, 0, 0, 0, 0, 1, 1, 1]
    result = decode_commvector(bits, from_agent_idx=3, my_agent_idx=4)
    assert result["reports_malicious_in_other_networks"] == ["blue_agent_0"]
    assert result["compromise_level_in_sender_net"] == "admin"
    assert result["sender_busy"] is True


def test_decode_skips_self():
    # Bit at position == from_agent_idx is ignored (agents don't self-report)
    bits = [0, 0, 0, 1, 0, 0, 0, 0]
    result = decode_commvector(bits, from_agent_idx=3, my_agent_idx=4)
    assert result["reports_malicious_in_other_networks"] == []


def test_extract_state_with_admin_ioc():
    obs = {
        "phase": "MissionA",
        "success": "TRUE",
        "message": [[0] * 8, [0] * 8, [0] * 8, [0] * 8],
        "host_a": {
            "System info": {"Hostname": "host_a"},
            "Files": [{"File Name": "escalate.sh"}],
        },
    }
    state = extract_state(obs, "blue_agent_4", "Sleep")
    threats = state["threats"]
    assert len(threats) == 1
    assert threats[0]["hostname"] == "host_a"
    assert threats[0]["compromise_level"] == "admin"


# ─── RoE: restore-needs-admin ─────────────────────────────────────────────────

def test_restore_denied_when_no_admin():
    EpisodeCounters.reset()
    state = {"threats": [{"hostname": "host_a", "compromise_level": "user"}]}
    v = policy_engine.validate("Restore", {"hostname": "host_a"}, state)
    assert not v.allowed
    assert "admin" in v.reason.lower()
    assert "analyse" in v.suggested.lower()


def test_restore_allowed_when_admin():
    EpisodeCounters.reset()
    state = {"threats": [{"hostname": "host_a", "compromise_level": "admin"}]}
    v = policy_engine.validate("Restore", {"hostname": "host_a"}, state)
    assert v.allowed


def test_restore_denied_when_host_not_in_threats():
    EpisodeCounters.reset()
    state = {"threats": []}
    v = policy_engine.validate("Restore", {"hostname": "host_x"}, state)
    assert not v.allowed
    assert "none" in v.reason.lower()


# ─── RoE: block-rate-limit ────────────────────────────────────────────────────

def test_block_first_allowed_second_denied():
    EpisodeCounters.reset()

    v1 = policy_engine.validate("BlockTrafficZone", {"target_zone": "zone_a"}, {})
    assert v1.allowed
    policy_engine.record_action("BlockTrafficZone", {"target_zone": "zone_a"})

    v2 = policy_engine.validate("BlockTrafficZone", {"target_zone": "zone_a"}, {})
    assert not v2.allowed
    assert "đã bị block" in v2.reason.lower()


def test_block_different_zones_independent():
    EpisodeCounters.reset()

    v1 = policy_engine.validate("BlockTrafficZone", {"target_zone": "zone_a"}, {})
    assert v1.allowed
    policy_engine.record_action("BlockTrafficZone", {"target_zone": "zone_a"})

    v2 = policy_engine.validate("BlockTrafficZone", {"target_zone": "zone_b"}, {})
    assert v2.allowed  # different zone, independent counter


# ─── RoE: decoy rate limit ────────────────────────────────────────────────────

def test_decoy_max_two_per_host():
    EpisodeCounters.reset()

    for _ in range(2):
        v = policy_engine.validate("DeployDecoy", {"hostname": "h1"}, {})
        assert v.allowed
        policy_engine.record_action("DeployDecoy", {"hostname": "h1"})

    v3 = policy_engine.validate("DeployDecoy", {"hostname": "h1"}, {})
    assert not v3.allowed


def test_unknown_action_allowed_by_default():
    v = policy_engine.validate("Analyse", {"hostname": "any"}, {})
    assert v.allowed


# ─── runner ───────────────────────────────────────────────────────────────────

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
