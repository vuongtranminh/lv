"""Driver — plug ClaudeDefenderPolicy into CybORG CAGE 4 evaluation.

Run AFTER `claude /login`, `pip install -r requirements.txt`, and CybORG
setup at `../llms-are-acd-main` (its install_unified.sh).

The end-to-end smoke test that doesn't need CybORG is `run_smoke.py` —
start there to confirm Claude + MCP + RoE all wired correctly.
"""

import os
import sys
from pathlib import Path

# Make llms-are-acd-main importable from the sibling directory.
SIBLING_REPO = Path(__file__).parent.parent / "llms-are-acd-main"
if SIBLING_REPO.exists():
    sys.path.insert(0, str(SIBLING_REPO))
else:
    print(f"WARNING: expected sibling repo at {SIBLING_REPO} — not found.")


def run_direct_loop(num_episodes: int = 2, max_steps_per_episode: int = 500):
    """Full CybORG simulation. Adapt the integration shape to match the
    existing llms-are-acd-main submission patterns:
        ../llms-are-acd-main/CybORG/Evaluation/llamagym/submission.py
        ../llms-are-acd-main/CybORG/Evaluation/Cybermonics/submission.py
    """
    from feasibility.claude_policy import ClaudeDefenderPolicy  # noqa: F401
    from CybORG import CybORG  # noqa: F401

    raise NotImplementedError(
        "Wire in the 4 RL policies for the other blue agents here. "
        "See ../llms-are-acd-main/CybORG/Agents/LLMAgents/llm_policy.py "
        "and obs_wrapper.py for the existing integration shape."
    )


if __name__ == "__main__":
    run_direct_loop()
