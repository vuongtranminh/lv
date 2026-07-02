"""Setup C — thay thế ĐÚNG chỗ trong prompt TH3 gốc để dùng MCP + RoE.

Đây là **thay đổi DUY NHẤT** so với prompt TH3 gốc (`acd2025/base.yml`).

Nguyên tắc:
- Prompt TH3 gốc GIỮ NGUYÊN 100% byte-identical trong `prompts/acd2025/base.yml`
- Setup A: driver load base.yml và dùng nguyên xi
- Setup C: driver load base.yml, sau đó **thay thế ĐÚNG 2 đoạn** liên quan đến
  output format (JSON) bằng đoạn tương ứng cho MCP tool call + RoE.

Các phần KHÔNG thay đổi (giữ 100% TH3 gốc):
- `# DESCRIPTION` (giới thiệu vai trò defender)
- `## AVAILABLE ACTIONS` (mô tả 6 action Remove/Restore/Block/Allow/DeployDecoy/Analyse)
- `# ENVIRONMENT RULES` (network structure, defense setup, mission phases, reward structure)
- `# COMMVECTOR FORMAT` (blue agent networks, message structure)
- `# OBSERVATION STRUCTURE` (Last Action Status, Suspicious Activity levels)

Các phần THAY THẾ (chỉ 2 chỗ, đều liên quan output format):
1. Đoạn "Respond EXACTLY with one response as a dictionary..." → "Each turn, use MCP tools..."
2. Đoạn "## EXAMPLE RESPONSES" (5 JSON example) → 5 tool call example
"""

# ─── THAY THẾ 1: Instruction về format output ─────────────────────────────

# Đoạn GỐC trong TH3 base.yml (mô tả cách LLM trả JSON dictionary)
JSON_OUTPUT_INSTRUCTION_ORIGINAL = """Respond EXACTLY with one response as a dictionary with the following keys:
- action: ONLY ONE action from `## AVAILABLE ACTIONS`, always including the required parameter. For <hostname>, you can ONLY execute an action on hosts from your assigned network in
`## BLUE AGENT NETWORKS` with your assigned BLUE AGENT number. For <subnet_id>, you can choose ANY subnet from the network.
- reason: ONLY ONE reason for your choice.

Review examples from `## EXAMPLE RESPONSES` if you are unsure."""

# Đoạn THAY THẾ (mô tả cách LLM dùng MCP tool + RoE deny/approve)
MCP_INTERACTION_INSTRUCTION = """Each turn, use MCP tools to interact with the environment:
- Call `get_threat_summary()` and `get_comms_decoded()` to gather structured state. Commvector bits are already decoded — you do NOT need to parse bits manually.
- Call EXACTLY ONE `propose_<action>` tool to commit an action. For <hostname>, you can ONLY execute an action on hosts from your assigned network in
`## BLUE AGENT NETWORKS` with your assigned BLUE AGENT number. For <subnet_id>, you can choose ANY subnet from the network. Include a brief `reason` argument.
- A deterministic Rules of Engagement (RoE) layer validates each proposal. If a tool returns `{"status": "denied", "reason": "...", "suggested": "..."}`, read the reason and propose a DIFFERENT action that respects the constraint.

Review examples from `## EXAMPLE RESPONSES` if you are unsure."""


# ─── THAY THẾ 2: 5 example response ─────────────────────────────────────────

# Đoạn GỐC — 5 example ở dạng JSON dictionary
EXAMPLE_RESPONSES_ORIGINAL = """## EXAMPLE RESPONSES
- Example 1:
{"action": "Remove host:restricted_zone_a_subnet_user_host_0", "reason": "Host has been compromised"}
- Example 2:
{"action": "BlockTrafficZone subnet:operational_zone_a_subnet", "reason": "Zone is in an active mission phase"}
- Example 3:
{"action": "Analyse host:restricted_zone_b_subnet_server_host_2", "reason": "Host is in a mission-critical zone"}
- Example 4:
{"action": "Restore host:restricted_zone_b_subnet_server_host_2", "reason": "Host has been detected to have a privileged escalation"}
- Example 5:
{"action": "DeployDecoy host:restricted_zone_a_subnet_server_host_1", "reason": "Preventative measure to detect red activity"}"""

# Đoạn THAY THẾ — 5 example ở dạng MCP tool call
EXAMPLE_RESPONSES_MCP = """## EXAMPLE RESPONSES
- Example 1:
propose_remove(hostname="restricted_zone_a_subnet_user_host_0", reason="Host has been compromised")
- Example 2:
propose_block_traffic(target_zone="operational_zone_a_subnet", reason="Zone is in an active mission phase")
- Example 3:
propose_analyse(hostname="restricted_zone_b_subnet_server_host_2", reason="Host is in a mission-critical zone")
- Example 4:
propose_restore(hostname="restricted_zone_b_subnet_server_host_2", reason="Host has been detected to have a privileged escalation")
- Example 5:
propose_deploy_decoy(hostname="restricted_zone_a_subnet_server_host_1", reason="Preventative measure to detect red activity")"""


# ─── Hàm build prompt Setup C ───────────────────────────────────────────────

def build_setup_c_prompt(th3_base_content: str) -> str:
    """Build prompt cho Setup C = TH3 gốc với 2 chỗ đã thay thế.

    Args:
        th3_base_content: nội dung field `content` từ acd2025/base.yml

    Returns:
        System prompt cho Setup C (đã thay 2 đoạn output format).

    Raises:
        ValueError: nếu không tìm thấy đoạn gốc trong prompt (TH3 có thể đã đổi format).
    """
    result = th3_base_content

    # Thay thế 1: instruction output format
    if JSON_OUTPUT_INSTRUCTION_ORIGINAL not in result:
        raise ValueError(
            "Không tìm thấy đoạn JSON_OUTPUT_INSTRUCTION_ORIGINAL trong base.yml. "
            "TH3 có thể đã cập nhật prompt — cần đối chiếu và điều chỉnh string match."
        )
    result = result.replace(JSON_OUTPUT_INSTRUCTION_ORIGINAL, MCP_INTERACTION_INSTRUCTION)

    # Thay thế 2: 5 example response
    if EXAMPLE_RESPONSES_ORIGINAL not in result:
        raise ValueError(
            "Không tìm thấy đoạn EXAMPLE_RESPONSES_ORIGINAL trong base.yml. "
            "TH3 có thể đã cập nhật examples — cần đối chiếu và điều chỉnh string match."
        )
    result = result.replace(EXAMPLE_RESPONSES_ORIGINAL, EXAMPLE_RESPONSES_MCP)

    return result


def load_th3_base_content(base_yml_path) -> str:
    """Load base.yml và trích trường content của prompt system đầu tiên."""
    import yaml
    with open(base_yml_path, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    # base.yml có cấu trúc: prompts: [ {role: "system", content: "..."} ]
    return doc["prompts"][0]["content"]
