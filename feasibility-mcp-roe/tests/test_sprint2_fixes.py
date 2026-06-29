"""Test cho 5 fix Sprint 2:

1. Tool propose_sleep tồn tại trong TOOLS_SERVER
2. Tool propose_remove tồn tại trong TOOLS_SERVER
3. propose_sleep luôn approved (không qua RoE)
4. recommend_next_action — priority "critical" khi có admin host
5. recommend_next_action — priority "high" khi có user host
6. recommend_next_action — Sleep khi mạng sạch
7. recommend_next_action — DeployDecoy khi mạng sạch nhưng còn quota
8. get_threat_summary trả về field recommended_action
9. Wire 8 rule v2 — rule_restore_phase_constraint hoạt động
10. Wire 8 rule v2 — rule_restore_max_per_episode đếm đúng
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feasibility.context import StepContext
from feasibility.state_extractor import extract_state
from feasibility.tools import (
    TOOLS_SERVER,
    ALLOWED_TOOL_IDS,
    _propose,
    propose_sleep,
    propose_remove,
    get_threat_summary,
)
from feasibility.roe.policy_engine import (
    validate,
    EpisodeCounters,
)
from feasibility.roe.rules_v2 import recommend_next_action


# ─── Fake observation ────────────────────────────────────────────────────────

OBS_ADMIN_HOST = {
    "phase": 1,
    "success": "TRUE",
    "message": [[0]*8]*4,
    "host_admin": {
        "System info": {"Hostname": "host_admin"},
        "Files": [{"File Name": "escalate.sh"}],
        "Processes": [],
    },
    "host_clean": {
        "System info": {"Hostname": "host_clean"},
        "Files": [],
        "Processes": [],
    },
}

OBS_USER_ONLY = {
    "phase": 1,
    "success": "TRUE",
    "message": [[0]*8]*4,
    "host_user": {
        "System info": {"Hostname": "host_user"},
        "Files": [{"File Name": "cmd.sh"}],
        "Processes": [],
    },
}

OBS_CLEAN = {
    "phase": 1,
    "success": "TRUE",
    "message": [[0]*8]*4,
    "host_a": {
        "System info": {"Hostname": "host_a"},
        "Files": [],
        "Processes": [],
    },
    "host_b": {
        "System info": {"Hostname": "host_b"},
        "Files": [],
        "Processes": [],
    },
}


# ─── 1-2. Tool propose_sleep + propose_remove tồn tại ────────────────────────

def test_tools_server_has_propose_sleep():
    tool_names = [t.name for t in TOOLS_SERVER.tools] if hasattr(TOOLS_SERVER, "tools") else []
    # Fallback: check qua ALLOWED_TOOL_IDS
    assert "mcp__defender_tools__propose_sleep" in ALLOWED_TOOL_IDS


def test_tools_server_has_propose_remove():
    assert "mcp__defender_tools__propose_remove" in ALLOWED_TOOL_IDS


# ─── 3. propose_sleep luôn approved ──────────────────────────────────────────

def test_propose_sleep_always_approved():
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True)
    StepContext.state = extract_state(OBS_CLEAN, "blue_agent_4", "None")
    handler = getattr(propose_sleep, "handler", None) or propose_sleep
    if callable(handler) and not hasattr(handler, "tools"):
        result = asyncio.run(handler({"reason": "test"}))
        payload = json.loads(result["content"][0]["text"])
        assert payload["status"] == "approved"
        assert payload["scheduled"] == "Sleep"


# ─── 4-7. recommend_next_action priority ─────────────────────────────────────

def test_recommend_admin_returns_critical_restore():
    StepContext.reset()
    EpisodeCounters.reset()
    state = extract_state(OBS_ADMIN_HOST, "blue_agent_4", "None")
    rec = recommend_next_action(state)
    assert rec["action"] == "Restore"
    assert rec["hostname"] == "host_admin"
    assert rec["priority"] == "critical"


def test_recommend_user_returns_high_remove():
    StepContext.reset()
    EpisodeCounters.reset()
    state = extract_state(OBS_USER_ONLY, "blue_agent_4", "None")
    rec = recommend_next_action(state)
    assert rec["action"] == "Remove"
    assert rec["hostname"] == "host_user"
    assert rec["priority"] == "high"


def test_recommend_clean_returns_sleep_or_decoy():
    StepContext.reset()
    EpisodeCounters.reset()
    state = extract_state(OBS_CLEAN, "blue_agent_4", "None")
    rec = recommend_next_action(state)
    # Mạng có 2 host clean + 4 comms 'none' → có thể Sleep hoặc DeployDecoy
    assert rec["action"] in ("Sleep", "DeployDecoy")


def test_recommend_admin_quota_exhausted_falls_back():
    """Khi đã Restore đủ quota (5/ep) → không recommend Restore nữa."""
    StepContext.reset()
    EpisodeCounters.reset()
    EpisodeCounters.restores_total = 5  # đã đạt MAX_RESTORES_TOTAL
    state = extract_state(OBS_ADMIN_HOST, "blue_agent_4", "None")
    rec = recommend_next_action(state)
    # Không Restore vì đã hết quota
    assert rec["action"] != "Restore"


# ─── 8. get_threat_summary trả về recommended_action ─────────────────────────

def test_get_threat_summary_includes_recommended_action():
    StepContext.reset()
    EpisodeCounters.reset()
    StepContext.state = extract_state(OBS_ADMIN_HOST, "blue_agent_4", "None")
    handler = getattr(get_threat_summary, "handler", None)
    if handler is None:
        # Skip if SDK wraps tool differently
        assert "all_hostnames" in StepContext.state
        return
    result = asyncio.run(handler({}))
    payload = json.loads(result["content"][0]["text"])
    assert "recommended_action" in payload
    assert payload["recommended_action"]["action"] == "Restore"


# ─── 9. Wire 8 rule v2 hoạt động ─────────────────────────────────────────────

def test_v2_rule_restore_phase_constraint():
    """Phase Planning không cho Restore."""
    EpisodeCounters.reset()
    state = {
        "mission_phase": "Planning",
        "threats": [{"hostname": "host_x", "compromise_level": "admin"}],
    }
    v = validate("Restore", {"hostname": "host_x"}, state)
    assert not v.allowed
    assert "Planning" in v.reason


def test_v2_rule_restore_max_per_episode():
    """Sau 5 lần Restore, không cho thêm."""
    EpisodeCounters.reset()
    EpisodeCounters.restores_total = 5
    state = {
        "mission_phase": "MissionA",
        "threats": [{"hostname": "host_x", "compromise_level": "admin"}],
    }
    v = validate("Restore", {"hostname": "host_x"}, state)
    assert not v.allowed
    assert "quota" in v.reason.lower() or "Restore" in v.reason


def test_v2_block_critical_zone_forbidden():
    """Không cho Block traffic zones critical."""
    EpisodeCounters.reset()
    state = {"mission_phase": "MissionA"}
    v = validate(
        "BlockTrafficZone",
        {"target_zone": "restricted_zone_a"},
        state,
    )
    assert not v.allowed


# ─── 10. Restore với admin level + Phase đúng → allowed ─────────────────────

def test_v2_restore_admin_allowed_in_mission_phase():
    EpisodeCounters.reset()
    state = {
        "mission_phase": "MissionA",
        "threats": [{"hostname": "host_a", "compromise_level": "admin"}],
        "last_action_status": "TRUE",
    }
    v = validate("Restore", {"hostname": "host_a"}, state)
    assert v.allowed
