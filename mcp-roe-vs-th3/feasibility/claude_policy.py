"""Claude-based blue agent policy cho Sprint 4 — so sánh fair với TH3.

Hai setup:
- Setup A-TH3 (mcp_enabled=False, roe_enabled=False):
    dùng nguyên bản acd2025/base.yml, single-shot JSON output
- Setup C-TH3 (mcp_enabled=True, roe_enabled=True):
    dùng acd2025/base.yml đã thay thế 2 chỗ (build_setup_c_prompt),
    multi-turn MCP tool call + RoE V3 deny/approve

Cả 2 setup đều dùng CÙNG prompt content TH3 gốc — chỉ khác paradigm output.
"""

import os
import time
from pathlib import Path

import anyio
from ray.rllib.policy.policy import Policy
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)

from CybORG.Simulator.Actions import Sleep, Restore, DeployDecoy, Analyse, Remove
from CybORG.Simulator.Actions.ConcreteActions.ControlTraffic import (
    BlockTrafficZone, AllowTrafficZone,
)

from .audit import AuditLog
from .context import StepContext
from .detailed_logger import DetailedLogger
from .roe.policy_engine import EpisodeCounters
from .state_extractor import extract_state
from .tools import TOOLS_SERVER, ALLOWED_TOOL_IDS
from .paper_style_th3 import (
    load_th3_base_prompt,
    render_paper_observation,
    parse_paper_response,
)
from .setup_c_override import build_setup_c_prompt


CAGE4_SUBNETS = [
    "restricted_zone_a",
    "operational_zone_a",
    "restricted_zone_b",
    "operational_zone_b",
    "public_access_zone",
]

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")


class ClaudeDefenderPolicy(Policy):
    """Blue agent policy — Sprint 4 fair TH3 comparison.

    config keys:
        agent_name: str (vd "blue_agent_4")
        mcp_enabled: bool (default False) — bật MCP tool call (Setup C)
        roe_enabled: bool (default False) — bật RoE V3 validate (Setup C)

    Setup A: mcp_enabled=False, roe_enabled=False → single-shot JSON
    Setup C: mcp_enabled=True,  roe_enabled=True  → MCP tool call + RoE V3
    """

    def __init__(self, observation_space, action_space, config=None):
        super().__init__(observation_space, action_space, {})
        config = config or {}

        self.name = config.get("agent_name", "blue_agent_4")
        self.subnet = CAGE4_SUBNETS[int(self.name[-1])]

        self.mcp_enabled = config.get("mcp_enabled", False)
        self.roe_enabled = config.get("roe_enabled", False)

        if self.roe_enabled and not self.mcp_enabled:
            raise ValueError("Không thể bật RoE khi MCP tắt.")

        StepContext.set_mode(self.mcp_enabled, self.roe_enabled)

        # Load TH3 base prompt (byte-identical với acd2025/base.yml)
        th3_base = load_th3_base_prompt()

        if self.mcp_enabled:
            # Setup C: thay thế 2 chỗ output-format
            self.system_prompt = build_setup_c_prompt(th3_base)
        else:
            # Setup A: dùng nguyên bản TH3
            self.system_prompt = th3_base

        self.last_action_str = "None"
        self.step = 0

        log_suffix = self._mode_suffix()
        audit_path = os.environ.get(
            "AUDIT_LOG_PATH",
            f"./audit_{self.name}_{log_suffix}.csv",
        )
        self.audit = AuditLog(audit_path)

        detailed_path = os.environ.get(
            "DETAILED_LOG_PATH",
            audit_path.replace("audit_", "detailed_").replace(".csv", ".jsonl"),
        )
        episode_meta = {
            "agent_name": self.name,
            "mcp_enabled": self.mcp_enabled,
            "roe_enabled": self.roe_enabled,
            "setup": "C-TH3" if self.mcp_enabled else "A-TH3",
            "red_variant": os.environ.get("RED_VARIANT", "unknown"),
            "seed": int(os.environ.get("EPISODE_SEED", "0")),
            "model": DEFAULT_MODEL,
            "audit_csv_path": str(audit_path),
            "system_prompt_hash": str(hash(self.system_prompt))[:16],
            "system_prompt_len_chars": len(self.system_prompt),
        }
        self.detailed = DetailedLogger(detailed_path, self.name, episode_meta)
        StepContext.set_logger(self.detailed)

        EpisodeCounters.reset()

    def _mode_suffix(self) -> str:
        if self.mcp_enabled and self.roe_enabled:
            return "setupC_TH3"
        return "setupA_TH3"

    def end_episode(self):
        if self.detailed:
            self.detailed.episode_end(
                cumulative_reward=getattr(self, "_cum_reward", 0.0),
                total_wall_time_s=getattr(self, "_total_wall", 0.0),
                n_steps=self.step,
            )
            self.detailed.close()
            StepContext.set_logger(None)
        self.step = 0
        self.last_action_str = "None"
        EpisodeCounters.reset()

    # ─── Entry point ────────────────────────────────────────────────────────

    def compute_single_action(self, obs=None, prev_action=None, **kwargs):
        t_step_start = time.monotonic()
        StepContext.reset()
        StepContext.set_mode(self.mcp_enabled, self.roe_enabled)
        StepContext.set_logger(self.detailed)
        self.detailed.set_step(self.step)
        self.detailed.step_start(raw_observation=obs)

        state = extract_state(obs, self.name, self.last_action_str)
        StepContext.state = state
        self.detailed.state_extracted(state)

        try:
            if self.mcp_enabled:
                reasoning = anyio.run(self._query_mcp_mode, state)
            else:
                reasoning = anyio.run(self._query_paper_mode, obs)
        except Exception as e:
            self.detailed.error("compute_single_action::query", e)
            reasoning = f"<error: {e}>"

        if StepContext.proposed_action is None:
            cyborg_action = Sleep()
            final_str = "Sleep (no action proposed)"
        else:
            action_type, params, _ = StepContext.proposed_action
            cyborg_action = self._materialize(action_type, params)
            final_str = f"{action_type}({params})"

        self.detailed.action_materialized(final_str, repr(cyborg_action)[:300])

        wall = time.monotonic() - t_step_start
        self.detailed.step_end(
            joint_reward=0.0,
            wall_time_s=wall,
            n_proposed=1 if StepContext.proposed_action else 0,
            n_rejected=len(StepContext.rejected_attempts),
        )

        self.audit.log(
            step=self.step,
            agent=self.name,
            state=state,
            llm_reasoning=reasoning,
            proposed=StepContext.proposed_action,
            rejected=StepContext.rejected_attempts,
            final=final_str,
        )

        self.last_action_str = final_str
        self.step += 1
        return cyborg_action, [], {}

    # ─── Setup C — MCP tool call mode ───────────────────────────────────────

    async def _query_mcp_mode(self, state: dict) -> str:
        situation = (
            f"Agent name: {self.name}\n"
            f"It's your turn. Gather state via MCP tools, then propose an action."
        )

        max_turns = 8

        opts = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt=self.system_prompt,
            mcp_servers={"defender_tools": TOOLS_SERVER},
            allowed_tools=ALLOWED_TOOL_IDS,
            max_turns=max_turns,
            permission_mode="bypassPermissions",
        )

        self.detailed.llm_query(
            system_prompt=self.system_prompt,
            user_message=situation,
            mode="mcp",
            opts_summary={
                "model": DEFAULT_MODEL,
                "max_turns": max_turns,
                "allowed_tools": ALLOWED_TOOL_IDS,
            },
        )

        reasoning_chunks = []
        async with ClaudeSDKClient(options=opts) as client:
            await client.query(situation)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            reasoning_chunks.append(block.text)
                            self.detailed.llm_response_chunk(block.text)
        return "\n".join(reasoning_chunks)

    # ─── Setup A — Single-shot JSON mode (TH3 style) ────────────────────────

    async def _query_paper_mode(self, obs: dict) -> str:
        user_message = render_paper_observation(obs or {}, self.name, self.last_action_str)

        opts = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt=self.system_prompt,
            max_turns=1,
            permission_mode="bypassPermissions",
        )

        self.detailed.llm_query(
            system_prompt=self.system_prompt,
            user_message=user_message,
            mode="paper",
            opts_summary={"model": DEFAULT_MODEL, "max_turns": 1},
        )

        response_text = ""
        async with ClaudeSDKClient(options=opts) as client:
            await client.query(user_message)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
                            self.detailed.llm_response_chunk(block.text)

        parsed = parse_paper_response(response_text)
        if parsed is not None:
            action_type, params, reason = parsed
            self.detailed.event("paper_parse_result",
                                data={"action_type": action_type, "params": params, "reason": reason})
            if action_type not in ("Sleep", "Monitor"):
                StepContext.proposed_action = (action_type, params, reason)
                self.detailed.action_proposed(action_type, params, reason)
        else:
            self.detailed.event("paper_parse_failed",
                                data={"response_preview": response_text[:300]})
        return response_text

    # ─── Materialize ────────────────────────────────────────────────────────

    def _materialize(self, action_type: str, params: dict):
        if action_type == "Analyse":
            return Analyse(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "Restore":
            return Restore(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "Remove":
            return Remove(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "DeployDecoy":
            return DeployDecoy(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "BlockTrafficZone":
            return BlockTrafficZone(
                session=0, agent=self.name,
                from_subnet=self.subnet, to_subnet=params["target_zone"],
            )
        if action_type == "AllowTrafficZone":
            return AllowTrafficZone(
                session=0, agent=self.name,
                from_subnet=self.subnet, to_subnet=params["target_zone"],
            )
        return Sleep()

    # ─── Ray RLlib interface ────────────────────────────────────────────────

    def compute_actions(self, obs_batch, state_batches=None, prev_action_batch=None,
                        prev_reward_batch=None, info_batch=None, episodes=None, **kwargs):
        actions = []
        for obs in obs_batch:
            action, _, _ = self.compute_single_action(obs=obs)
            actions.append(action)
        return actions, [], {}

    def get_weights(self):
        return None

    def set_weights(self, weights):
        pass
