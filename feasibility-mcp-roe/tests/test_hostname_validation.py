"""Tests cho bug "LLM bịa hostname" — verify fix hoạt động:
1. extract_state trả về `all_hostnames` đầy đủ (cả host không có IOC).
2. get_threat_summary expose `available_hostnames`.
3. _propose() reject hostname KHÔNG trong all_hostnames.
4. _propose() accept hostname có trong all_hostnames (qua RoE bình thường).
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from feasibility.context import StepContext
from feasibility.state_extractor import extract_state, extract_all_hostnames
from feasibility.tools import (
    _propose,
    get_threat_summary,
    propose_analyse,
    propose_restore,
    propose_deploy_decoy,
)


# ─── Fake observation từ CybORG CAGE 4 ───────────────────────────────────────

FAKE_OBS_3_HOSTS = {
    "phase": 1,
    "success": "TRUE",
    "message": [[0]*8, [0]*8, [0]*8, [0]*8],
    "office_network_subnet_user_host_1": {
        "System info": {"Hostname": "office_network_subnet_user_host_1"},
        "Files": [{"File Name": "escalate.sh"}],  # IOC admin
        "Processes": [],
    },
    "office_network_subnet_user_host_2": {
        "System info": {"Hostname": "office_network_subnet_user_host_2"},
        "Files": [],  # KHÔNG có IOC
        "Processes": [],
    },
    "office_network_subnet_server_host_0": {
        "System info": {"Hostname": "office_network_subnet_server_host_0"},
        "Files": [],
        "Processes": [],
    },
}


# ─── 1. extract_state trả về all_hostnames đầy đủ ────────────────────────────

def test_extract_all_hostnames_returns_all_3():
    """all_hostnames phải có cả 3 host, kể cả 2 host không IOC."""
    hosts = extract_all_hostnames(FAKE_OBS_3_HOSTS)
    assert len(hosts) == 3, f"Expected 3 hosts, got {len(hosts)}: {hosts}"
    assert "office_network_subnet_user_host_1" in hosts
    assert "office_network_subnet_user_host_2" in hosts
    assert "office_network_subnet_server_host_0" in hosts


def test_extract_all_hostnames_skips_meta_keys():
    """Không lấy 'phase', 'success', 'action', 'message' làm hostname."""
    hosts = extract_all_hostnames(FAKE_OBS_3_HOSTS)
    assert "phase" not in hosts
    assert "success" not in hosts
    assert "message" not in hosts


def test_extract_state_includes_all_hostnames():
    """extract_state() phải trả về trường all_hostnames."""
    state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")
    assert "all_hostnames" in state
    assert len(state["all_hostnames"]) == 3


def test_extract_state_threats_vs_all_hostnames():
    """threats CHỈ host có IOC, all_hostnames có TẤT CẢ."""
    state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")
    # Threats: chỉ host có escalate.sh
    assert len(state["threats"]) == 1
    assert state["threats"][0]["hostname"] == "office_network_subnet_user_host_1"
    # All hostnames: cả 3
    assert len(state["all_hostnames"]) == 3


def test_extract_state_empty_observation():
    """observation=None trả về all_hostnames=[]."""
    state = extract_state(None, "blue_agent_4", "None")
    assert state["all_hostnames"] == []


# ─── 2. get_threat_summary expose available_hostnames ────────────────────────

def test_get_threat_summary_includes_available_hostnames():
    """Tool get_threat_summary phải build payload có available_hostnames.

    Gọi handler bên trong tool object (claude_agent_sdk wrap @tool thành
    SdkMcpTool, handler là attribute riêng).
    """
    StepContext.reset()
    StepContext.state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")
    handler = getattr(get_threat_summary, "handler", None)
    if handler is None:
        # Fallback: kiểm tra logic gián tiếp qua state đã set
        assert "all_hostnames" in StepContext.state
        assert len(StepContext.state["all_hostnames"]) == 3
        return
    result = asyncio.run(handler({}))
    payload = json.loads(result["content"][0]["text"])
    assert "available_hostnames" in payload
    assert len(payload["available_hostnames"]) == 3


# ─── 3. _propose() reject hostname bịa ───────────────────────────────────────

def test_propose_rejects_hallucinated_hostname():
    """LLM bịa tên 'web-server' → _propose() phải deny ngay."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True)
    StepContext.state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")

    result = _propose("Analyse", {"hostname": "web-server"}, "test")
    payload = json.loads(result["content"][0]["text"])

    assert payload["status"] == "denied"
    assert payload.get("hostname_validation_failed") is True
    assert "KHÔNG TỒN TẠI" in payload["reason"]
    # suggested phải chứa hostname hợp lệ
    assert "office_network" in payload["suggested"]


def test_propose_rejects_common_hallucinations():
    """Test một loạt tên bịa thường gặp."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True)
    StepContext.state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")

    for fake in ("web-server", "db-server", "api-gateway", "auth-server",
                 "dns-resolver", "cache-server", "domain-controller"):
        result = _propose("DeployDecoy", {"hostname": fake}, "test")
        payload = json.loads(result["content"][0]["text"])
        assert payload["status"] == "denied", f"Expected deny for {fake}"
        assert payload.get("hostname_validation_failed") is True


# ─── 4. _propose() accept hostname hợp lệ ────────────────────────────────────

def test_propose_accepts_valid_hostname():
    """Hostname đúng → đi qua RoE bình thường (không bị validation chặn)."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True)
    StepContext.state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")

    # Analyse luôn được RoE allow
    result = _propose(
        "Analyse",
        {"hostname": "office_network_subnet_user_host_1"},
        "test",
    )
    payload = json.loads(result["content"][0]["text"])
    assert payload["status"] == "approved"
    assert payload.get("hostname_validation_failed") is not True


def test_propose_restore_valid_admin_host():
    """Restore với hostname đúng + admin compromise → RoE approve."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True)
    StepContext.state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")

    result = _propose(
        "Restore",
        {"hostname": "office_network_subnet_user_host_1"},  # đúng + admin
        "Admin compromise xác nhận",
    )
    payload = json.loads(result["content"][0]["text"])
    assert payload["status"] == "approved"


def test_propose_restore_valid_user_level_denied_by_roe():
    """Hostname đúng + user level → validation pass, RoE deny vì rule_restore_needs_admin."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=True)
    # Đổi sang host user level
    obs = {
        "phase": 1,
        "success": "TRUE",
        "message": [[0]*8]*4,
        "host_a": {
            "System info": {"Hostname": "host_a"},
            "Files": [{"File Name": "cmd.sh"}],  # user level
            "Processes": [],
        },
    }
    StepContext.state = extract_state(obs, "blue_agent_4", "None")

    result = _propose("Restore", {"hostname": "host_a"}, "test")
    payload = json.loads(result["content"][0]["text"])
    # KHÔNG phải hostname validation fail
    assert payload.get("hostname_validation_failed") is not True
    # RoE deny vì user level
    assert payload["status"] == "denied"
    assert "admin-level" in payload["reason"]


# ─── 5. Setup B (RoE bypass) — validation hostname VẪN active ────────────────

def test_hostname_validation_active_even_when_roe_disabled():
    """Setup B (roe_enabled=False) — hostname validation vẫn phải reject bịa."""
    StepContext.reset()
    StepContext.set_mode(mcp_enabled=True, roe_enabled=False)
    StepContext.state = extract_state(FAKE_OBS_3_HOSTS, "blue_agent_4", "None")

    result = _propose("Analyse", {"hostname": "web-server"}, "test")
    payload = json.loads(result["content"][0]["text"])
    assert payload["status"] == "denied"
    assert payload.get("hostname_validation_failed") is True
