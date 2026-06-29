"""Claude-based blue agent policy với 3 mode toggle.

Mode flags (truyền qua config):
- mcp_enabled=True, roe_enabled=True   → Setup C — Đề xuất đầy đủ (MCP + RoE)
- mcp_enabled=True, roe_enabled=False  → Setup B — MCP only (cô lập đóng góp MCP)
- mcp_enabled=False, roe_enabled=False → Setup A — Baseline kiểu TH3 (nhồi prompt + parse JSON)

Plugged vào CybORG qua interface của ray.rllib.policy.policy.Policy.
"""

import os
import re
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

import time

from .audit import AuditLog
from .context import StepContext
from .detailed_logger import DetailedLogger
from .roe.policy_engine import EpisodeCounters  # alias → EpisodeCountersV2
from .state_extractor import extract_state
from .tools import TOOLS_SERVER, ALLOWED_TOOL_IDS
from .paper_style import PAPER_SYSTEM_PROMPT, render_paper_observation, parse_paper_response


CAGE4_SUBNETS = [
    "restricted_zone_a",
    "operational_zone_a",
    "restricted_zone_b",
    "operational_zone_b",
    "public_access_zone",
]

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
MCP_PROMPT_PATH = Path(__file__).parent / "prompt.md"
MCP_ACTIVE_PROMPT_PATH = Path(__file__).parent / "prompt_active.md"


class ClaudeDefenderPolicy(Policy):
    """Blue agent policy với mode toggle.

    config keys:
        agent_name: str (vd "blue_agent_4")
        mcp_enabled: bool (default True)
        roe_enabled: bool (default True)
        active_mode: bool (default False) — Sprint 3: bật rule_no_sleep_when_threat
            và load prompt_active.md (buộc agent hành động khi có threat).
            Chỉ có hiệu lực khi mcp_enabled=True và roe_enabled=True.
    """

    def __init__(self, observation_space, action_space, config=None):
        super().__init__(observation_space, action_space, {})
        config = config or {}

        self.name = config.get("agent_name", "blue_agent_4")
        self.subnet = CAGE4_SUBNETS[int(self.name[-1])]

        self.mcp_enabled = config.get("mcp_enabled", True)
        self.roe_enabled = config.get("roe_enabled", True)
        self.active_mode = config.get("active_mode", False)

        # Validate mode combination
        if self.roe_enabled and not self.mcp_enabled:
            raise ValueError("Không thể bật RoE khi MCP tắt (RoE phụ thuộc MCP tool).")
        if self.active_mode and not (self.mcp_enabled and self.roe_enabled):
            raise ValueError(
                "active_mode=True yêu cầu cả mcp_enabled và roe_enabled phải True."
            )

        # Set sticky mode flags vào StepContext (tools đọc)
        StepContext.set_mode(self.mcp_enabled, self.roe_enabled, self.active_mode)

        self.client = anyio.from_thread.start_blocking_portal  # placeholder
        # Sprint 3: load prompt_active khi active_mode bật
        prompt_path = MCP_ACTIVE_PROMPT_PATH if self.active_mode else MCP_PROMPT_PATH
        self.mcp_system_prompt = prompt_path.read_text(encoding="utf-8")
        self.paper_system_prompt = PAPER_SYSTEM_PROMPT

        self.last_action_str = "None"
        self.step = 0

        log_suffix = self._mode_suffix()
        audit_path = os.environ.get(
            "AUDIT_LOG_PATH",
            f"./audit_{self.name}_{log_suffix}.csv",
        )
        self.audit = AuditLog(audit_path)

        # Detailed JSONL logger — ghi mọi event chi tiết
        detailed_path = os.environ.get(
            "DETAILED_LOG_PATH",
            audit_path.replace("audit_", "detailed_").replace(".csv", ".jsonl"),
        )
        episode_meta = {
            "agent_name": self.name,
            "mcp_enabled": self.mcp_enabled,
            "roe_enabled": self.roe_enabled,
            "active_mode": self.active_mode,
            "model": DEFAULT_MODEL,
            "audit_csv_path": str(audit_path),
            "system_prompt_mcp_hash": str(hash(self.mcp_system_prompt))[:16],
            "system_prompt_paper_hash": str(hash(self.paper_system_prompt))[:16],
        }
        self.detailed = DetailedLogger(detailed_path, self.name, episode_meta)
        StepContext.set_logger(self.detailed)

        EpisodeCounters.reset()

    def _mode_suffix(self) -> str:
        if self.mcp_enabled and self.roe_enabled:
            if self.active_mode:
                return "setupC_active"
            return "setupC_mcp_roe"
        if self.mcp_enabled and not self.roe_enabled:
            return "setupB_mcp_only"
        return "setupA_baseline"

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
        StepContext.set_mode(self.mcp_enabled, self.roe_enabled, self.active_mode)
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

        # Lấy action proposed (mcp mode set StepContext, paper mode parse trực tiếp)
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
            joint_reward=0.0,  # filled in run_benchmark via env
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

    # ─── Mode MCP (Setup B, C) ──────────────────────────────────────────────

    async def _query_mcp_mode(self, state: dict) -> str:
        situation = (
            f"Tên agent: {self.name}\n"
            f"Pha nhiệm vụ: {state['mission_phase']}\n"
            f"Hành động trước: {state['last_action']} → trạng thái={state['last_action_status']}\n\n"
            "Dùng get_threat_summary() và get_comms_decoded() để điều tra, "
            "sau đó gọi chính xác MỘT tool propose_* để hành động."
        )

        # max_turns = 8 cho cả Setup B và Setup C để đảm bảo so sánh fair:
        # khi so B vs C chỉ có MỘT biến đổi (RoE on/off), không phải hai (RoE + max_turns).
        # Setup B không có RoE deny nên LLM tự kết thúc sớm (~3-4 turn thực dùng),
        # max_turns=8 chỉ là TRẦN không bao giờ chạm tới ⇒ không gây overhead.
        max_turns = 8

        opts = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt=self.mcp_system_prompt,
            mcp_servers={"defender_tools": TOOLS_SERVER},
            allowed_tools=ALLOWED_TOOL_IDS,
            max_turns=max_turns,
            permission_mode="bypassPermissions",
        )

        self.detailed.llm_query(
            system_prompt=self.mcp_system_prompt,
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

    # ─── Mode Paper (Setup A — baseline TH3) ────────────────────────────────

    async def _query_paper_mode(self, obs: dict) -> str:
        """Kiểu TH3: nhồi observation text + raw bit vào prompt, single shot,
        LLM trả JSON action qua text, parse bằng regex.
        """
        user_message = render_paper_observation(obs or {}, self.name, self.last_action_str)

        opts = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt=self.paper_system_prompt,
            max_turns=1,
            permission_mode="bypassPermissions",
        )

        self.detailed.llm_query(
            system_prompt=self.paper_system_prompt,
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

        # Parse text response → set StepContext.proposed_action
        parsed = parse_paper_response(response_text)
        if parsed is not None:
            action_type, params, reason = parsed
            self.detailed.event("paper_parse_result",
                                data={"action_type": action_type, "params": params, "reason": reason})
            # Mode A không có RoE — accept mọi action (trừ Sleep/Monitor không cần proposed_action)
            if action_type not in ("Sleep", "Monitor"):
                StepContext.proposed_action = (action_type, params, reason)
                self.detailed.action_proposed(action_type, params, reason)
        else:
            self.detailed.event("paper_parse_failed",
                                data={"response_preview": response_text[:300]})
        return response_text

    # ─── Materialize action → CybORG Action ─────────────────────────────────

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
