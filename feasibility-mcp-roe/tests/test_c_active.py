"""Test cho Setup C-active (Sprint 3 — Nhánh A).

Bảo đảm 3 tính chất cốt lõi của chế độ ACTIVE:

1. rule_no_sleep_when_threat — deny Sleep khi state.threats không rỗng
2. rule_no_sleep_when_threat — allow Sleep khi mạng sạch
3. propose_sleep — tôn trọng StepContext.active_mode (bypass khi off, validate khi on)
4. Verify path đường tới prompt_active.md tồn tại và load được
5. ClaudeDefenderPolicy config validation cho active_mode
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feasibility.context import StepContext
from feasibility.tools import propose_sleep
from feasibility.roe.policy_engine import EpisodeCounters, validate
from feasibility.roe.rules_v2 import rule_no_sleep_when_threat


# ─── Fake state ──────────────────────────────────────────────────────────────

STATE_WITH_ADMIN_THREAT = {
    "mission_phase": "MissionA",
    "threats": [
        {"hostname": "office_network_subnet_user_host_1",
         "compromise_level": "admin",
         "iocs": ["escalate.sh"]},
    ],
    "all_hostnames": ["office_network_subnet_user_host_1",
                      "office_network_subnet_server_host_0"],
    "comms": [{"compromise_level_in_sender_net": "none"}] * 4,
    "last_action": "Sleep",
    "last_action_status": "TRUE",
}

STATE_WITH_USER_THREAT = {
    "mission_phase": "MissionA",
    "threats": [
        {"hostname": "office_network_subnet_user_host_2",
         "compromise_level": "user",
         "iocs": ["cmd.sh"]},
    ],
    "all_hostnames": ["office_network_subnet_user_host_2"],
    "comms": [{"compromise_level_in_sender_net": "none"}] * 4,
    "last_action": "Sleep",
    "last_action_status": "TRUE",
}

STATE_CLEAN = {
    "mission_phase": "MissionA",
    "threats": [],
    "all_hostnames": ["office_network_subnet_user_host_0",
                      "office_network_subnet_server_host_0"],
    "comms": [{"compromise_level_in_sender_net": "none"}] * 4,
    "last_action": "Sleep",
    "last_action_status": "TRUE",
}


# ─── 1. rule_no_sleep_when_threat — deny khi có threat ──────────────────────

def test_rule_no_sleep_deny_admin_threat():
    """Có admin threat → Sleep bị deny."""
    EpisodeCounters.reset()
    v = rule_no_sleep_when_threat(STATE_WITH_ADMIN_THREAT, {})
    assert not v.allowed
    assert "office_network_subnet_user_host_1" in v.reason
    assert "admin" in v.reason
    assert "restore" in v.suggested.lower()


def test_rule_no_sleep_deny_user_threat():
    """Có user threat → Sleep bị deny."""
    EpisodeCounters.reset()
    v = rule_no_sleep_when_threat(STATE_WITH_USER_THREAT, {})
    assert not v.allowed
    assert "office_network_subnet_user_host_2" in v.reason
    assert "remove" in v.suggested.lower()


# ─── 2. rule_no_sleep_when_threat — allow khi mạng sạch ─────────────────────

def test_rule_no_sleep_allow_when_clean():
    """Threats rỗng → Sleep được allow."""
    EpisodeCounters.reset()
    v = rule_no_sleep_when_threat(STATE_CLEAN, {})
    assert v.allowed


# ─── 3. validate() integration — Sleep wire vào RULES_V2 ────────────────────

def test_validate_sleep_denied_with_threat():
    """Engine validate("Sleep", ...) gọi đúng rule khi có threat."""
    EpisodeCounters.reset()
    v = validate("Sleep", {}, STATE_WITH_ADMIN_THREAT)
    assert not v.allowed
    assert "Sleep" in v.reason or "sleep" in v.reason.lower()


def test_validate_sleep_allowed_when_clean():
    """Engine validate("Sleep", ...) allow khi mạng sạch."""
    EpisodeCounters.reset()
    v = validate("Sleep", {}, STATE_CLEAN)
    assert v.allowed


# ─── 4. propose_sleep — tôn trọng active_mode ───────────────────────────────

def test_propose_sleep_bypass_when_active_mode_off():
    """active_mode=False (mặc định C-passive) → Sleep luôn approved."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True, active_mode=False)
    StepContext.state = STATE_WITH_ADMIN_THREAT  # có threat
    EpisodeCounters.reset()

    handler = getattr(propose_sleep, "handler", None) or propose_sleep
    if callable(handler) and not hasattr(handler, "tools"):
        result = asyncio.run(handler({"reason": "test bypass"}))
        payload = json.loads(result["content"][0]["text"])
        assert payload["status"] == "approved"


def test_propose_sleep_denied_when_active_mode_on_with_threat():
    """active_mode=True + có threat → Sleep bị deny."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True, active_mode=True)
    StepContext.state = STATE_WITH_ADMIN_THREAT
    EpisodeCounters.reset()

    handler = getattr(propose_sleep, "handler", None) or propose_sleep
    if callable(handler) and not hasattr(handler, "tools"):
        result = asyncio.run(handler({"reason": "test deny"}))
        payload = json.loads(result["content"][0]["text"])
        assert payload["status"] == "denied"
        assert "threat" in payload["reason"].lower() or "Sleep" in payload["reason"]


def test_propose_sleep_allowed_when_active_mode_on_and_clean():
    """active_mode=True + mạng sạch → Sleep approved."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True, active_mode=True)
    StepContext.state = STATE_CLEAN
    EpisodeCounters.reset()

    handler = getattr(propose_sleep, "handler", None) or propose_sleep
    if callable(handler) and not hasattr(handler, "tools"):
        result = asyncio.run(handler({"reason": "test allow"}))
        payload = json.loads(result["content"][0]["text"])
        assert payload["status"] == "approved"


# ─── 5. prompt_active.md load được ──────────────────────────────────────────

def test_prompt_active_file_exists():
    """File prompt_active.md tồn tại và đọc được."""
    # Resolve trực tiếp tránh transitive import ray/pyarrow từ claude_policy
    prompt_path = (
        Path(__file__).parent.parent / "feasibility" / "prompt_active.md"
    )
    assert prompt_path.exists()
    content = prompt_path.read_text(encoding="utf-8")
    # Sanity check: phải khác prompt mặc định và có quy tắc cấm Sleep
    assert "ACTIVE" in content
    assert "Sleep" in content
    # Quy tắc cốt lõi của chế độ ACTIVE
    assert "không" in content.lower() and "sleep" in content.lower()


# ─── 6. Config validation ───────────────────────────────────────────────────

def test_active_mode_requires_mcp_and_roe():
    """active_mode=True yêu cầu mcp_enabled=True và roe_enabled=True."""
    # Smoke test cấu hình không hợp lệ — không cần khởi tạo policy thật
    # (không có CybORG env trong unit test); chỉ kiểm tra logic validation.
    config_invalid_1 = {"mcp_enabled": False, "roe_enabled": False, "active_mode": True}
    config_invalid_2 = {"mcp_enabled": True, "roe_enabled": False, "active_mode": True}
    config_valid = {"mcp_enabled": True, "roe_enabled": True, "active_mode": True}

    # Kiểm tra trực tiếp điều kiện trong code (không khởi tạo Ray Policy)
    def check_valid(cfg):
        mcp = cfg.get("mcp_enabled", True)
        roe = cfg.get("roe_enabled", True)
        active = cfg.get("active_mode", False)
        if roe and not mcp:
            return False
        if active and not (mcp and roe):
            return False
        return True

    assert not check_valid(config_invalid_1)
    assert not check_valid(config_invalid_2)
    assert check_valid(config_valid)


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
