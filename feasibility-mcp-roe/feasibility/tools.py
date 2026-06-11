"""@tool functions exposed to Claude via an in-process MCP server.

Two classes of tool:
(1) OBSERVATION TOOLS — query StepContext.state (set by ClaudeDefenderPolicy
    before each Claude query). Returns pre-decoded JSON — the LLM never
    parses raw 8-bit comms vectors (addresses Limitation 1).
(2) PROPOSAL TOOLS — every action goes through RoE.validate(); denied
    proposals return a structured reason + alternative so the LLM can
    retry without going through the LLM's own interpretation
    (addresses Limitation 2).

Tools are registered into `TOOLS_SERVER` (a real in-process MCP server
via `create_sdk_mcp_server`) so Claude consumes them via the MCP protocol.
"""

import json

from claude_agent_sdk import tool, create_sdk_mcp_server

from .context import StepContext
from .roe import policy_engine


# Bật/tắt verbose logging của tools. Scenario set = True khi muốn xem chi tiết.
VERBOSE = False


def _vlog(msg=""):
    if VERBOSE:
        print(msg)


def _vlog_result(tool_name: str, payload, max_chars: int = 600):
    """In ra kết quả tool đã trả về cho Claude (rút gọn nếu quá dài)."""
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
    """In ra phán quyết RoE cho propose_* tool."""
    if not VERBOSE:
        return
    if verdict.allowed:
        print(f"   ⚖️  RoE thẩm định {tool_name}({params}): ✓ ALLOWED")
    else:
        print(f"   ⚖️  RoE thẩm định {tool_name}({params}): ✗ DENIED")
        print(f"       Lý do:  {verdict.reason}")
        print(f"       Gợi ý:  {verdict.suggested}")


def _text_result(payload) -> dict:
    """MCP tool result wrapping JSON-serialized payload."""
    return {
        "content": [
            {"type": "text", "text": json.dumps(payload, indent=2, ensure_ascii=False)}
        ]
    }


# ─── Observation tools ────────────────────────────────────────────────────────

@tool(
    "get_threat_summary",
    "Lấy thông tin về các threat cấp host trong subnet của agent này: phase, "
    "danh sách threats (hostname + compromise_level + IOCs + tiến trình đáng "
    "ngờ + connections), và trạng thái của hành động trước đó. Gọi tool này "
    "TRƯỚC khi hành động.",
    {},
)
async def get_threat_summary(args):
    state = StepContext.state or {}
    payload = {
        "phase": state.get("mission_phase"),
        "threats": state.get("threats", []),
        "last_action": state.get("last_action"),
        "last_action_status": state.get("last_action_status"),
    }
    _vlog_result("get_threat_summary", payload)
    return _text_result(payload)


@tool(
    "get_comms_decoded",
    "Lấy báo cáo đã decode từ các blue agent khác. Vectơ truyền thông 8-bit "
    "thô đã được pre-parse: mỗi entry cho biết agent nào gửi, họ quan sát "
    "thấy mạng KHÁC nào có hoạt động độc hại, mức độ compromise trong mạng "
    "CỦA HỌ, và họ có đang bận hay không.",
    {},
)
async def get_comms_decoded(args):
    state = StepContext.state or {}
    payload = state.get("comms", [])
    _vlog_result("get_comms_decoded", payload)
    return _text_result(payload)


# ─── Action-proposal tools (every one goes through RoE) ───────────────────────

def _propose(action_type: str, params: dict, reason: str) -> dict:
    verdict = policy_engine.validate(action_type, params, StepContext.state or {})
    _vlog_verdict(f"propose_{action_type.lower()}", verdict, params)

    if verdict.allowed:
        StepContext.proposed_action = (action_type, params, reason)
        policy_engine.record_action(action_type, params)
        payload = {
            "status": "approved",
            "scheduled": f"{action_type} {params}",
        }
        _vlog_result(f"propose_{action_type.lower()}", payload)
        return _text_result(payload)

    target = params.get("hostname") or params.get("target_zone") or "(unknown)"
    StepContext.rejected_attempts.append((action_type, target, verdict.reason))
    payload = {
        "status": "denied",
        "reason": verdict.reason,
        "suggested": verdict.suggested,
    }
    _vlog_result(f"propose_{action_type.lower()}", payload)
    return _text_result(payload)


@tool(
    "propose_analyse",
    "Điều tra một host để tìm hoạt động độc hại. KHÔNG phá hủy. Luôn được "
    "RoE cho phép. Dùng như mặc định an toàn hoặc để xác nhận compromise "
    "trước khi hành động phá hủy.",
    {"hostname": str, "reason": str},
)
async def propose_analyse(args):
    return _propose("Analyse", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_restore",
    "Wipe và restore một host về trạng thái sạch. PHÁ HỦY — tạm thời đưa "
    "host offline, ảnh hưởng đến người dùng hợp pháp (green users). Chính "
    "sách RoE: yêu cầu xác nhận admin-level compromise trên host. Nếu bị "
    "từ chối, RoE sẽ trả về gợi ý thay thế.",
    {"hostname": str, "reason": str},
)
async def propose_restore(args):
    return _propose("Restore", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_deploy_decoy",
    "Triển khai honeypot (mồi nhử)/decoy trên một host. Không phá hủy về "
    "availability nhưng tạo signal. Chính sách RoE: tối đa 2 decoy / host "
    "/ episode.",
    {"hostname": str, "reason": str},
)
async def propose_deploy_decoy(args):
    return _propose("DeployDecoy", {"hostname": args["hostname"]}, args["reason"])


@tool(
    "propose_block_traffic",
    "Chặn toàn bộ traffic inbound từ một zone/subnet. PHÁ HỦY — ảnh hưởng "
    "các dịch vụ hợp pháp xuyên zone. Chính sách RoE: tối đa 1 block / "
    "zone / episode.",
    {"target_zone": str, "reason": str},
)
async def propose_block_traffic(args):
    return _propose(
        "BlockTrafficZone", {"target_zone": args["target_zone"]}, args["reason"]
    )


# In-process MCP server holding all tools
TOOLS_SERVER = create_sdk_mcp_server(
    name="defender_tools",
    version="1.0.0",
    tools=[
        get_threat_summary,
        get_comms_decoded,
        propose_analyse,
        propose_restore,
        propose_deploy_decoy,
        propose_block_traffic,
    ],
)

# Allowed-tool IDs (MCP naming: mcp__{server}__{tool}). Add to
# ClaudeAgentOptions.allowed_tools to skip Claude Code permission prompts.
ALLOWED_TOOL_IDS = [
    "mcp__defender_tools__get_threat_summary",
    "mcp__defender_tools__get_comms_decoded",
    "mcp__defender_tools__propose_analyse",
    "mcp__defender_tools__propose_restore",
    "mcp__defender_tools__propose_deploy_decoy",
    "mcp__defender_tools__propose_block_traffic",
]
