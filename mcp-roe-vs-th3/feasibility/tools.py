"""MCP tools cho Setup C — Sprint 4.

Khác với feasibility-mcp-roe/tools.py:
- KHÔNG có `recommended_action` injection vào get_threat_summary
  (Sprint 4 RoE V3 thuần deny/approve, không active suggestion)
- propose_sleep KHÔNG có active_mode branching (Sprint 3 chứng minh
  buộc hành động làm reward tệ hơn)
"""

import json

from claude_agent_sdk import tool, create_sdk_mcp_server

from .context import StepContext
from .detailed_logger import get_logger
from .roe import policy_engine


VERBOSE = False


def _vlog_result(tool_name: str, payload, max_chars: int = 600):
    if not VERBOSE:
        return
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n      ... (đã rút gọn)"
    indented = "\n".join("      " + line for line in text.split("\n"))
    print(f"   📤 [{tool_name}] kết quả trả về cho Claude:")
    print(indented)
    print()


def _vlog_verdict(tool_name: str, verdict, params: dict):
    if not VERBOSE:
        return
    if verdict.allowed:
        print(f"   ⚖️  RoE thẩm định {tool_name}({params}): ✓ ALLOWED")
    else:
        print(f"   ⚖️  RoE thẩm định {tool_name}({params}): ✗ DENIED")
        print(f"       Lý do:  {verdict.reason}")
        print(f"       Gợi ý:  {verdict.suggested}")


def _text_result(payload) -> dict:
    return {
        "content": [
            {"type": "text", "text": json.dumps(payload, indent=2, ensure_ascii=False)}
        ]
    }


# ─── Observation tools ────────────────────────────────────────────────────────

@tool(
    "get_threat_summary",
    "Get information about the agent's subnet: mission phase, list of threats "
    "(hosts with IOCs + compromise_level + suspicious processes), status of "
    "previous action, and LIST OF VALID HOSTNAMES (available_hostnames). Call "
    "this BEFORE proposing an action. IMPORTANT: when proposing an action with "
    "hostname, you MUST use a name from available_hostnames — do NOT invent "
    "names like 'web-server' or 'db-server'.",
    {},
)
async def get_threat_summary(args):
    get_logger().tool_call("get_threat_summary", {})
    state = StepContext.state or {}
    payload = {
        "phase": state.get("mission_phase"),
        "threats": state.get("threats", []),
        "last_action": state.get("last_action"),
        "last_action_status": state.get("last_action_status"),
        "available_hostnames": state.get("all_hostnames", []),
    }
    # Sprint 4: KHÔNG có recommended_action — RoE V3 thuần deny/approve
    get_logger().tool_result("get_threat_summary", payload)
    _vlog_result("get_threat_summary", payload)
    return _text_result(payload)


@tool(
    "get_comms_decoded",
    "Get pre-decoded reports from other blue agents. The raw 8-bit commvectors "
    "have been pre-parsed: each entry indicates which agent sent it, which "
    "OTHER networks they observed malicious activity in, the compromise level "
    "in THEIR own network, and whether they are currently busy.",
    {},
)
async def get_comms_decoded(args):
    get_logger().tool_call("get_comms_decoded", {})
    state = StepContext.state or {}
    payload = state.get("comms", [])
    get_logger().tool_result("get_comms_decoded", payload)
    _vlog_result("get_comms_decoded", payload)
    return _text_result(payload)


# ─── Action-proposal tools ────────────────────────────────────────────────────

def _propose(action_type: str, params: dict, reason: str) -> dict:
    logger = get_logger()
    tool_name = f"propose_{action_type.lower()}"
    logger.tool_call(tool_name, {**params, "reason": reason})

    # PRE-CHECK: validate hostname (chống LLM bịa tên)
    hostname = params.get("hostname")
    if hostname is not None:
        all_hosts = (StepContext.state or {}).get("all_hostnames", [])
        if all_hosts and hostname not in all_hosts:
            sample = all_hosts[:5]
            payload = {
                "status": "denied",
                "reason": (
                    f"Hostname '{hostname}' does not exist in your subnet. "
                    f"You MUST use a name from available_hostnames."
                ),
                "suggested": (
                    f"Valid hostnames: {sample}"
                    + ("..." if len(all_hosts) > 5 else "")
                ),
                "hostname_validation_failed": True,
            }
            StepContext.rejected_attempts.append(
                (action_type, hostname, "invalid hostname")
            )
            logger.tool_result(tool_name, payload)
            _vlog_result(tool_name, payload)
            return _text_result(payload)

    # BYPASS RoE nếu mode flag tắt (Setup B pattern — không dùng trong Sprint 4)
    if not StepContext.roe_enabled:
        StepContext.proposed_action = (action_type, params, reason)
        payload = {
            "status": "approved",
            "scheduled": f"{action_type} {params}",
            "roe_bypassed": True,
        }
        logger.roe_verdict(action_type, params, allowed=True,
                           reason="RoE bypass (mode flag off)", suggested="")
        logger.action_proposed(action_type, params, reason)
        logger.tool_result(tool_name, payload)
        _vlog_result(tool_name, payload)
        return _text_result(payload)

    # Đường thường: chạy RoE V3.validate()
    verdict = policy_engine.validate(action_type, params, StepContext.state or {})
    logger.roe_verdict(action_type, params,
                       allowed=verdict.allowed,
                       reason=verdict.reason,
                       suggested=verdict.suggested)
    _vlog_verdict(tool_name, verdict, params)

    if verdict.allowed:
        StepContext.proposed_action = (action_type, params, reason)
        policy_engine.record_action(action_type, params)
        payload = {
            "status": "approved",
            "scheduled": f"{action_type} {params}",
        }
        logger.action_proposed(action_type, params, reason)
        logger.tool_result(tool_name, payload)
        _vlog_result(tool_name, payload)
        return _text_result(payload)

    target = params.get("hostname") or params.get("target_zone") or "(unknown)"
    StepContext.rejected_attempts.append((action_type, target, verdict.reason))
    payload = {
        "status": "denied",
        "reason": verdict.reason,
        "suggested": verdict.suggested,
    }
    logger.tool_result(tool_name, payload)
    _vlog_result(tool_name, payload)
    return _text_result(payload)


@tool(
    "propose_analyse",
    "Investigate a host to look for malicious activity. Non-destructive. Use "
    "this to confirm suspicions before taking action.",
    {"hostname": str, "reason": str},
)
async def propose_analyse(args):
    return _propose("Analyse", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_restore",
    "Wipe and restore a host to a known good state. DESTRUCTIVE — temporarily "
    "takes the host offline, affecting legitimate users. RoE policy: requires "
    "confirmed admin-level compromise on the host, AND host in mission-critical "
    "zone during active phase. If denied, RoE will suggest an alternative.",
    {"hostname": str, "reason": str},
)
async def propose_restore(args):
    return _propose("Restore", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_deploy_decoy",
    "Deploy a decoy service on a host. Not destructive to availability but "
    "creates detection signal. RoE policy: max 2 decoys per host, 10 total "
    "per episode.",
    {"hostname": str, "reason": str},
)
async def propose_deploy_decoy(args):
    return _propose("DeployDecoy", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_remove",
    "Terminate suspicious user-level processes on a host. Does NOT cause "
    "downtime (only kills processes). SAFE — use when user-level IOC "
    "(cmd.sh/cmd.exe) is confirmed. Do not keep analysing.",
    {"hostname": str, "reason": str},
)
async def propose_remove(args):
    return _propose("Remove", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_block_traffic",
    "Block all inbound traffic from a zone/subnet. DESTRUCTIVE — affects "
    "legitimate cross-zone services. RoE policy: forbidden for operational "
    "zones in their active mission phase.",
    {"target_zone": str, "reason": str},
)
async def propose_block_traffic(args):
    return _propose(
        "BlockTrafficZone", {"target_zone": args["target_zone"]}, args["reason"]
    )


@tool(
    "propose_sleep",
    "Take no action this turn. Choose when: (1) get_threat_summary returns 0 "
    "threats AND get_comms_decoded reports all 'none' compromise, OR (2) "
    "waiting for a previous Analyse to complete (last_action_status=IN_PROGRESS). "
    "Sleep is ALWAYS approved by RoE V3 (Sprint 4).",
    {"reason": str},
)
async def propose_sleep(args):
    # Sprint 4: RoE V3 Sleep luôn approve (rule R6_sleep_always_ok).
    # KHÔNG có active_mode gate như Sprint 3 (rule đã bị gỡ vì làm reward tệ hơn).
    return _propose("Sleep", {}, args.get("reason", ""))


# In-process MCP server holding all tools
TOOLS_SERVER = create_sdk_mcp_server(
    name="defender_tools",
    version="1.0.0",
    tools=[
        get_threat_summary,
        get_comms_decoded,
        propose_analyse,
        propose_restore,
        propose_remove,
        propose_deploy_decoy,
        propose_block_traffic,
        propose_sleep,
    ],
)

ALLOWED_TOOL_IDS = [
    "mcp__defender_tools__get_threat_summary",
    "mcp__defender_tools__get_comms_decoded",
    "mcp__defender_tools__propose_analyse",
    "mcp__defender_tools__propose_restore",
    "mcp__defender_tools__propose_remove",
    "mcp__defender_tools__propose_sleep",
    "mcp__defender_tools__propose_deploy_decoy",
    "mcp__defender_tools__propose_block_traffic",
]
