"""Claude-based blue agent policy with in-process MCP tools + deterministic RoE.

Uses `claude-agent-sdk` — auth via Claude Code login (no API key required).
Plugs into CybORG/Ray as a `ray.rllib.policy.policy.Policy` subclass.

Each `compute_single_action()` call:
  1. Resets per-step context.
  2. Extracts structured state from the raw CybORG obs (decodes comms vectors).
  3. Bridges sync→async via anyio.run() to query Claude with MCP tools.
  4. The LLM queries observation tools, reasons, then calls one propose_* tool;
     RoE validates inside the tool — denied proposals come back with a reason
     and a suggested alternative, and the LLM may retry within `max_turns`.
  5. Materializes StepContext.proposed_action into a CybORG Action.
  6. Audit-logs the full decision trail.
"""

import os
from pathlib import Path

import anyio
from ray.rllib.policy.policy import Policy
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)

from CybORG.Simulator.Actions import Sleep, Restore, DeployDecoy, Analyse
from CybORG.Simulator.Actions.ConcreteActions.ControlTraffic import (
    BlockTrafficZone,
)

from .audit import AuditLog
from .context import StepContext
from .roe.rules import EpisodeCounters
from .state_extractor import extract_state
from .tools import TOOLS_SERVER, ALLOWED_TOOL_IDS


CAGE4_SUBNETS = [
    "restricted_zone_a",
    "operational_zone_a",
    "restricted_zone_b",
    "operational_zone_b",
    "public_access_zone",
]

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
PROMPT_PATH = Path(__file__).parent / "prompt.md"


class ClaudeDefenderPolicy(Policy):
    def __init__(self, observation_space, action_space, config=None):
        super().__init__(observation_space, action_space, {})
        config = config or {}
        self.name = config.get("agent_name", "blue_agent_4")
        self.subnet = CAGE4_SUBNETS[int(self.name[-1])]
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

        self.last_action_str = "None"
        self.step = 0
        self.audit = AuditLog(
            os.environ.get("AUDIT_LOG_PATH", f"./audit_{self.name}.csv")
        )
        EpisodeCounters.reset()

    def end_episode(self):
        self.step = 0
        self.last_action_str = "None"
        EpisodeCounters.reset()

    def compute_single_action(self, obs=None, prev_action=None, **kwargs):
        StepContext.reset()
        state = extract_state(obs, self.name, self.last_action_str)
        StepContext.state = state

        situation = self._render_situation(state)
        reasoning = anyio.run(self._query_claude, situation)

        if StepContext.proposed_action is None:
            cyborg_action = Sleep()
            final_str = "Sleep (no action proposed)"
        else:
            action_type, params, _ = StepContext.proposed_action
            cyborg_action = self._materialize(action_type, params)
            final_str = f"{action_type}({params})"

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

    async def _query_claude(self, situation: str) -> str:
        opts = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt=self.system_prompt,
            mcp_servers={"defender_tools": TOOLS_SERVER},
            allowed_tools=ALLOWED_TOOL_IDS,
            max_turns=8,
            permission_mode="bypassPermissions",
        )

        reasoning_chunks = []
        async with ClaudeSDKClient(options=opts) as client:
            await client.query(situation)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            reasoning_chunks.append(block.text)
        return "\n".join(reasoning_chunks)

    def _render_situation(self, state: dict) -> str:
        return (
            f"AGENT_NAME: {self.name}\n"
            f"MISSION_PHASE: {state['mission_phase']}\n"
            f"LAST_ACTION: {state['last_action']} → "
            f"status={state['last_action_status']}\n\n"
            "Dùng get_threat_summary() và get_comms_decoded() để điều tra, "
            "sau đó gọi chính xác MỘT tool propose_* để hành động."
        )

    def _materialize(self, action_type: str, params: dict):
        if action_type == "Analyse":
            return Analyse(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "Restore":
            return Restore(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "DeployDecoy":
            return DeployDecoy(session=0, agent=self.name, hostname=params["hostname"])
        if action_type == "BlockTrafficZone":
            return BlockTrafficZone(
                session=0, agent=self.name,
                from_subnet=self.subnet, to_subnet=params["target_zone"],
            )
        return Sleep()

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
