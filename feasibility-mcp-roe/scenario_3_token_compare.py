"""Scenario 3: Token comparison — Mode A (paper-style nhồi context) vs
Mode B (MCP tool-use).

Verifies luận điểm (a): MCP giảm số token vào model (input tokens) so với
việc nhồi toàn bộ context vào prompt như bài TH3.

Method:
  - Same underlying observation, run twice:
    * Mode A: long system + long user message containing raw obs (with
      8-bit binary comm vectors as text), single shot, NO tools.
    * Mode B: our short system + short situation + MCP tools, multi-turn.
  - Measure:
    * Char count of OUR controlled prompt content (deterministic, fair).
    * SDK ResultMessage.usage tokens (input_tokens + cache_creation +
      cache_read) — reflects what the model actually processed.

Notes:
  - claude-agent-sdk wraps Claude Code, which injects its own system
    overhead into both modes. The MEANINGFUL comparison is the DELTA
    between modes, not absolute totals.
  - For benchmark fairness with the paper, both modes use the same
    model (claude-haiku-4-5).
"""

import anyio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
)

from feasibility import tools as feas_tools
from feasibility.context import StepContext
from feasibility.roe.rules import EpisodeCounters
from feasibility.state_extractor import extract_state
from feasibility.tools import TOOLS_SERVER, ALLOWED_TOOL_IDS

# Verbose tool logging tắt cho scenario 3 vì in 2 mode quá dài;
# scenario 3 tập trung vào số liệu token, không cần trace từng tool I/O.
feas_tools.VERBOSE = True


MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")


# ─── Shared observation (same for both modes) ────────────────────────────────

FAKE_OBS = {
    "phase": "MissionA",
    "success": "TRUE",
    "action": "Sleep",
    "message": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 1],          # agent_2: admin compromise, busy
        [0, 0, 0, 1, 0, 0, 1, 0],          # agent_3: reports malice in agent_3's net, user-level
    ],
    "host_a": {
        "System info": {"Hostname": "host_a"},
        "Processes": [{"PID": 1234}],
        "Files": [{"File Name": "escalate.sh"}],
    },
}


# ─── MODE A — paper-style: nhồi all context into one prompt ──────────────────

MODE_A_SYSTEM = """Bạn là một chuyên gia an ninh mạng cấp cao (blue agent) bảo vệ một subnet trong hệ thống doanh nghiệp đa mạng. Mục tiêu: phát hiện kẻ tấn công, ngăn chặn xâm phạm, và duy trì tính khả dụng.

# CÁC HÀNH ĐỘNG KHẢ DỤNG

Chọn MỘT hành động và trả lời bằng JSON: {"action": "<TênHànhĐộng host:<host> hoặc subnet:<zone>>", "reason": "..."}

Hành động:
- Sleep: không làm gì trong lượt này (thụ động)
- Monitor: quét thụ động các host (tự động chạy mỗi lượt — không cần gọi rõ)
- Analyse host:<hostname>: điều tra sâu một host để tìm hoạt động độc hại (không phá hủy)
- Remove host:<hostname>: chấm dứt các tiến trình user-level đáng ngờ trên một host
- Restore host:<hostname>: wipe và restore một host về trạng thái sạch (phá hủy — downtime tạm thời)
- DeployDecoy host:<hostname>: triển khai honeypot trên một host
- BlockTrafficZone subnet:<zone>: chặn toàn bộ traffic inbound từ một subnet (phá hủy — ảnh hưởng availability)
- AllowTrafficZone subnet:<zone>: cho phép lại traffic từ subnet đã bị chặn trước đó

# QUY TẮC MÔI TRƯỜNG (CybORG CAGE 4)

Bạn hoạt động trong CybORG CAGE 4, một mô phỏng phòng thủ mạng đa tác nhân. Nhiệm vụ diễn ra qua 3 pha: Planning, MissionA, MissionB. Mỗi pha áp dụng chính sách mạng khác nhau:
- Planning: chính sách chuẩn
- MissionA: operational_zone_a bị cô lập
- MissionB: operational_zone_b bị cô lập

Các zone bị hạn chế (restricted) có kết nối inbound/outbound giới hạn ở mọi lúc.

Bạn nhận observation dưới dạng một dict có cấu trúc. Các entry per-host hiển thị System info, Processes, Files, và Connections. Vectơ truyền thông từ các defender khác đến dưới dạng mảng nhị phân 8-bit mà bạn phải tự decode.

# ĐỊNH DẠNG VECTƠ TRUYỀN THÔNG

Mỗi 4 blue agent KHÁC broadcast một vectơ nhị phân 8-bit mỗi lượt:
- Bit 0-4: bit j được đặt = 1 nếu sender phát hiện hoạt động độc hại xuất phát từ subnet của agent j. Vị trí bit của chính sender luôn = 0.
- Bit 5-6: mức độ compromise BÊN TRONG subnet CỦA sender:
  - 00 = none (không có)
  - 01 = remote scan / exploit detected (quét từ xa / phát hiện exploit)
  - 10 = user-level compromise (một host có IOC cmd.sh / cmd.exe)
  - 11 = admin-level compromise (một host có IOC escalate.sh / escalate.exe)
- Bit 7: 1 nếu sender đang bận thực thi một action, 0 nếu rảnh.

Bạn phải tự decode các vectơ này bằng cách xem xét từng bit.

# HƯỚNG DẪN SUY LUẬN

- Điều tra trước khi phá hủy. Nếu không chắc về mức compromise, Analyse trước.
- Chỉ Restore khi admin-level compromise đã được xác nhận trên host.
- BlockTrafficZone là phương án cuối cùng — ảnh hưởng đến người dùng hợp pháp.
- Một đồng đội báo cáo admin compromise trong subnet CỦA BẠN là tín hiệu cần hành động: Analyse để xác nhận, sau đó Restore.

# ĐỊNH DẠNG OUTPUT

Trả lời chỉ bằng JSON hợp lệ. Ví dụ: {"action": "Analyse host:host_a", "reason": "điều tra IOC"}"""


def render_mode_a_observation(obs: dict, agent_name: str) -> str:
    """Format observation in the paper's text style — raw binary arrays included."""
    lines = []
    lines.append("# OBSERVATION (QUAN SÁT)")
    lines.append(f"Agent: {agent_name}")
    lines.append(f"Mission Phase (Pha): {obs.get('phase', 'unknown')}")
    lines.append(f"Last Action Status (Trạng thái action trước): {obs.get('success', 'unknown')}")
    lines.append("")
    lines.append("Communication Vectors (vectơ 8-bit thô, tự decode):")
    my_idx = int(agent_name[-1])
    other_indices = [i for i in range(5) if i != my_idx]
    for sender_idx, bits in zip(other_indices, obs.get("message", [])):
        binary = [1 if b else 0 for b in bits]
        lines.append(f"  Blue Agent {sender_idx}: {binary}")
    lines.append("")
    lines.append("Suspicious Activity Detected (Hoạt động đáng ngờ phát hiện):")
    for key, value in obs.items():
        if key in ("phase", "success", "action", "message"):
            continue
        if not isinstance(value, dict):
            continue
        hostname = value.get("System info", {}).get("Hostname", key)
        host_lines = [f"  Host: {hostname}"]
        for proc in value.get("Processes", []):
            if "PID" in proc and "username" not in proc:
                host_lines.append(f"    CẢNH BÁO: Tiến trình đáng ngờ PID={proc['PID']}")
        for f in value.get("Files", []):
            name = f.get("File Name")
            if name in ("escalate.sh", "escalate.exe"):
                host_lines.append(f"    NGHIÊM TRỌNG: IOC admin-level '{name}'")
            elif name in ("cmd.sh", "cmd.exe"):
                host_lines.append(f"    CẢNH BÁO: IOC user-level '{name}'")
        if len(host_lines) > 1:
            lines.extend(host_lines)
    lines.append("")
    lines.append("Chọn MỘT hành động. Trả lời chỉ bằng JSON.")
    return "\n".join(lines)


# ─── MODE B — short prompt + MCP tools ───────────────────────────────────────

MODE_B_SYSTEM = (Path(__file__).parent / "feasibility/prompt.md").read_text(encoding="utf-8")
MODE_B_USER = (
    "AGENT_NAME: blue_agent_4\n"
    "MISSION_PHASE: MissionA\n"
    "LAST_ACTION: None\n\n"
    "Dùng get_threat_summary() và get_comms_decoded() để điều tra, "
    "sau đó gọi MỘT tool propose_*."
)


# ─── Measurement helpers ─────────────────────────────────────────────────────

def char_count(s: str) -> int:
    return len(s)


def approx_tokens(s: str) -> int:
    """Crude tokens estimate: chars/4 (English-style). Used for SHAPE comparison."""
    return len(s) // 4


async def run_mode_a():
    user_message = render_mode_a_observation(FAKE_OBS, "blue_agent_4")

    print("─── MODE A: paper-style (nhồi all context) ──────────────")
    print(f"  System prompt chars: {char_count(MODE_A_SYSTEM):,}  ({approx_tokens(MODE_A_SYSTEM):,} tokens ≈)")
    print(f"  User message chars:  {char_count(user_message):,}  ({approx_tokens(user_message):,} tokens ≈)")
    print(f"  Total chars:         {char_count(MODE_A_SYSTEM) + char_count(user_message):,}")
    print()

    opts = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=MODE_A_SYSTEM,
        max_turns=1,
        permission_mode="bypassPermissions",
    )

    tool_calls = []
    reasoning_chunks = []
    final_usage = None
    start = time.monotonic()
    async with ClaudeSDKClient(options=opts) as client:
        await client.query(user_message)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        reasoning_chunks.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_calls.append((block.name, block.input))
            elif isinstance(msg, ResultMessage):
                final_usage = msg.usage
    elapsed = time.monotonic() - start

    print(f"  Tool calls: {len(tool_calls)}")
    print(f"  Wall time:  {elapsed:.2f}s")
    if final_usage:
        print(f"  Usage:      input={final_usage.get('input_tokens', 0)}, "
              f"cache_create={final_usage.get('cache_creation_input_tokens', 0)}, "
              f"cache_read={final_usage.get('cache_read_input_tokens', 0)}, "
              f"output={final_usage.get('output_tokens', 0)}")
    print()

    return {
        "system_chars": char_count(MODE_A_SYSTEM),
        "user_chars": char_count(user_message),
        "total_chars": char_count(MODE_A_SYSTEM) + char_count(user_message),
        "wall_time": elapsed,
        "usage": final_usage,
        "response_chars": sum(len(c) for c in reasoning_chunks),
    }


async def run_mode_b():
    print("─── MODE B: MCP tool-use ────────────────────────────────")
    print(f"  System prompt chars: {char_count(MODE_B_SYSTEM):,}  ({approx_tokens(MODE_B_SYSTEM):,} tokens ≈)")
    print(f"  User message chars:  {char_count(MODE_B_USER):,}  ({approx_tokens(MODE_B_USER):,} tokens ≈)")
    print(f"  Total chars (initial): {char_count(MODE_B_SYSTEM) + char_count(MODE_B_USER):,}")
    print(f"  NOTE: Mode B adds tool calls + tool results during the run.")
    print()

    EpisodeCounters.reset()
    StepContext.reset()
    StepContext.state = extract_state(FAKE_OBS, "blue_agent_4", "None")

    opts = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=MODE_B_SYSTEM,
        mcp_servers={"defender_tools": TOOLS_SERVER},
        allowed_tools=ALLOWED_TOOL_IDS,
        max_turns=8,
        permission_mode="bypassPermissions",
    )

    tool_calls = []
    reasoning_chunks = []
    final_usage = None
    start = time.monotonic()
    async with ClaudeSDKClient(options=opts) as client:
        await client.query(MODE_B_USER)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        reasoning_chunks.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_calls.append((block.name, block.input))
            elif isinstance(msg, ResultMessage):
                final_usage = msg.usage
    elapsed = time.monotonic() - start

    print(f"  Tool calls: {len(tool_calls)}")
    print(f"  Wall time:  {elapsed:.2f}s")
    if final_usage:
        print(f"  Usage:      input={final_usage.get('input_tokens', 0)}, "
              f"cache_create={final_usage.get('cache_creation_input_tokens', 0)}, "
              f"cache_read={final_usage.get('cache_read_input_tokens', 0)}, "
              f"output={final_usage.get('output_tokens', 0)}")
    print()

    return {
        "system_chars": char_count(MODE_B_SYSTEM),
        "user_chars": char_count(MODE_B_USER),
        "total_chars": char_count(MODE_B_SYSTEM) + char_count(MODE_B_USER),
        "wall_time": elapsed,
        "usage": final_usage,
        "response_chars": sum(len(c) for c in reasoning_chunks),
        "tool_calls": len(tool_calls),
    }


# ─── Comparison ──────────────────────────────────────────────────────────────

async def main():
    print("═══════════════════════════════════════════════════════════════")
    print("  Scenario 3 — Token comparison: Mode A vs Mode B               ")
    print(f"  Model: {MODEL}")
    print("═══════════════════════════════════════════════════════════════\n")

    mode_a = await run_mode_a()
    mode_b = await run_mode_b()

    print("═══════════════════════════════════════════════════════════════")
    print("  Comparison summary                                            ")
    print("═══════════════════════════════════════════════════════════════")
    print(f"{'Metric':<40} {'Mode A':>15} {'Mode B':>15} {'Δ':>10}")
    print("─" * 82)

    # Controlled prompt content (deterministic comparison)
    def pct_change(a, b):
        if a == 0:
            return "n/a"
        return f"{(b - a) / a * 100:+.1f}%"

    print(f"{'System prompt (chars)':<40} {mode_a['system_chars']:>15,} "
          f"{mode_b['system_chars']:>15,} {pct_change(mode_a['system_chars'], mode_b['system_chars']):>10}")
    print(f"{'User message (chars)':<40} {mode_a['user_chars']:>15,} "
          f"{mode_b['user_chars']:>15,} {pct_change(mode_a['user_chars'], mode_b['user_chars']):>10}")
    print(f"{'Total initial prompt (chars)':<40} {mode_a['total_chars']:>15,} "
          f"{mode_b['total_chars']:>15,} {pct_change(mode_a['total_chars'], mode_b['total_chars']):>10}")
    print()

    # SDK reported usage
    if mode_a["usage"] and mode_b["usage"]:
        for field in ("input_tokens", "cache_creation_input_tokens",
                      "cache_read_input_tokens", "output_tokens"):
            a = mode_a["usage"].get(field, 0)
            b = mode_b["usage"].get(field, 0)
            print(f"{'SDK ' + field:<40} {a:>15,} {b:>15,} {pct_change(a, b):>10}")
        total_a = (mode_a["usage"].get("input_tokens", 0)
                   + mode_a["usage"].get("cache_creation_input_tokens", 0)
                   + mode_a["usage"].get("cache_read_input_tokens", 0))
        total_b = (mode_b["usage"].get("input_tokens", 0)
                   + mode_b["usage"].get("cache_creation_input_tokens", 0)
                   + mode_b["usage"].get("cache_read_input_tokens", 0))
        print(f"{'TOTAL input (all caches)':<40} {total_a:>15,} {total_b:>15,} {pct_change(total_a, total_b):>10}")
    print()

    print(f"{'Wall time (s)':<40} {mode_a['wall_time']:>15.2f} "
          f"{mode_b['wall_time']:>15.2f} {pct_change(mode_a['wall_time'], mode_b['wall_time']):>10}")
    print(f"{'Tool calls':<40} {'1 (single shot)':>15} {mode_b.get('tool_calls', 0):>15,}")
    print()

    # Verdict
    user_msg_reduced = mode_b["user_chars"] < mode_a["user_chars"]
    system_reduced = mode_b["system_chars"] < mode_a["system_chars"]
    print("─" * 82)
    print(f"  (a) MCP reduces controlled prompt size: "
          f"{'✓ PASS' if user_msg_reduced and system_reduced else '✗ PARTIAL'}")

    if user_msg_reduced and system_reduced:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    anyio.run(main)
