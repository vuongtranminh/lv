"""End-to-end smoke test — NO CybORG dependency.

Exercises the full Claude + claude-agent-sdk + in-process MCP + RoE stack
on a hand-crafted observation. Verifies:

  ✓ claude-agent-sdk auth works (no API key — uses Claude Code login)
  ✓ @tool functions registered into the in-process MCP server
  ✓ StepContext.state flows through to observation tools
  ✓ RoE.validate() fires inside proposal tools
  ✓ A propose_* tool sets StepContext.proposed_action
  ✓ Reasoning + rejections captured for audit

Run AFTER `claude /login`. ~5-10s, ~$0.01 with Haiku 4.5.

    python run_smoke.py
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

# Bật verbose để in chi tiết tool I/O và RoE verdict
feas_tools.VERBOSE = True


MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
PROMPT = (Path(__file__).parent / "feasibility/prompt.md").read_text(encoding="utf-8")

# Hand-crafted observation:
#   - host_a has escalate.sh → admin-level IOC (should allow RoE.restore)
#   - blue_agent_2 vector: bits 5-6 = 11 (admin compromise in sender's net), bit 7 = 1 (busy)
#   - blue_agent_3 vector: bit 3 = 1 (reports malice in blue_agent_3's net), bits 5-6 = 01 (user-level)
FAKE_OBS = {
    "phase": "MissionA",
    "success": "TRUE",
    "action": "Sleep",
    "message": [
        [0, 0, 0, 0, 0, 0, 0, 0],          # blue_agent_0
        [0, 0, 0, 0, 0, 0, 0, 0],          # blue_agent_1
        [0, 0, 0, 0, 0, 1, 1, 1],          # blue_agent_2: admin compromise, busy
        [0, 0, 0, 1, 0, 0, 1, 0],          # blue_agent_3: user-level, free
    ],
    "host_a": {
        "System info": {"Hostname": "host_a"},
        "Processes": [{"PID": 1234}],
        "Files": [{"File Name": "escalate.sh"}],
    },
}


def banner(title: str, char: str = "═"):
    line = char * 70
    print(f"\n{line}\n  {title}\n{line}")


def print_indented(text: str, prefix: str = "   "):
    for line in text.split("\n"):
        print(f"{prefix}{line}")


async def run():
    EpisodeCounters.reset()
    StepContext.reset()
    StepContext.state = extract_state(FAKE_OBS, "blue_agent_4", "None")

    # ── 1. Hiển thị observation thô + state đã decode ──────────────────────
    banner("BƯỚC 1 — OBSERVATION từ CybORG (raw — LLM không thấy cái này)")
    print_indented(json.dumps(FAKE_OBS, indent=2, ensure_ascii=False))

    banner("BƯỚC 2 — STATE đã decode (state_extractor.py)")
    print("   Code Python đã dịch 8-bit binary → JSON tiếng người.")
    print("   LLM chỉ nhìn thấy data này (qua tools), không thấy bit thô.\n")
    print_indented(json.dumps(StepContext.state, indent=2, ensure_ascii=False))

    # ── 3. Hiển thị system prompt + user message gửi Claude ────────────────
    banner("BƯỚC 3 — PROMPT GỬI VÀO CLAUDE")

    print("\n▼ SYSTEM PROMPT (Claude đọc 1 lần đầu, sau đó cache):")
    print("─" * 70)
    print_indented(PROMPT)
    print("─" * 70)

    situation = (
        "AGENT_NAME: blue_agent_4\n"
        "MISSION_PHASE: MissionA\n"
        "LAST_ACTION: None\n\n"
        "Dùng get_threat_summary() và get_comms_decoded() để điều tra, "
        "sau đó gọi MỘT tool propose_*."
    )

    print("\n▼ USER MESSAGE (thay đổi mỗi step):")
    print("─" * 70)
    print_indented(situation)
    print("─" * 70)

    # ── 4. Chạy Claude, log từng event ─────────────────────────────────────
    banner("BƯỚC 4 — CLAUDE BẮT ĐẦU SUY LUẬN & GỌI TOOL")

    opts = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=PROMPT,
        mcp_servers={"defender_tools": TOOLS_SERVER},
        allowed_tools=ALLOWED_TOOL_IDS,
        max_turns=8,
        permission_mode="bypassPermissions",
    )

    print(f"\nModel: {MODEL}  |  max_turns: 8\n")
    start = time.monotonic()
    step = 0
    final_usage = None
    tool_call_count = 0

    async with ClaudeSDKClient(options=opts) as client:
        await client.query(situation)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text = block.text.strip()
                        if not text:
                            continue
                        step += 1
                        print(f"\n[{step}] 💭 CLAUDE NÓI:")
                        print_indented(text)
                    elif isinstance(block, ToolUseBlock):
                        step += 1
                        tool_call_count += 1
                        if block.name.startswith("mcp__defender_tools__"):
                            tname = block.name.replace("mcp__defender_tools__", "")
                            label = f"[MCP tool của ta] {tname}"
                        else:
                            label = f"[SDK internal] {block.name}"
                        print(f"\n[{step}] 🔧 CLAUDE GỌI TOOL: {label}")
                        print(f"   Tham số: {json.dumps(block.input, ensure_ascii=False)}")
                        # Tool result sẽ được @tool function tự in (VERBOSE = True)
            elif isinstance(msg, ResultMessage):
                final_usage = msg.usage

    elapsed = time.monotonic() - start

    # ── 5. Tổng kết ────────────────────────────────────────────────────────
    banner("BƯỚC 5 — KẾT QUẢ CUỐI CÙNG")

    print(f"\n   Final proposed action:  {StepContext.proposed_action}")
    print(f"   Rejected attempts:      {StepContext.rejected_attempts}")
    print(f"   Tổng số tool call:      {tool_call_count}")
    print(f"   Wall time:              {elapsed:.2f}s")
    if final_usage:
        print(f"   Input tokens:           {final_usage.get('input_tokens', 'n/a')}")
        print(f"   Cache read tokens:      {final_usage.get('cache_read_input_tokens', 'n/a')}")
        print(f"   Output tokens:          {final_usage.get('output_tokens', 'n/a')}")

    if StepContext.proposed_action is None:
        print("\n   ⚠️  Không có action nào được propose — kiểm tra max_turns / prompt.")
        sys.exit(1)
    print("\n   ✓ Smoke test passed.")


if __name__ == "__main__":
    anyio.run(run)
