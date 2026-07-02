#!/usr/bin/env bash
# Launch Setup C-active 2 episode (FiniteState) — Sprint 3 Nhánh A đối chứng.
#
# Setup C-active = prompt_active.md + rule_no_sleep_when_threat:
# - Cấm Sleep khi state.threats không rỗng
# - Buộc agent làm theo recommended_action khi priority ∈ {critical, high}
#
# Output:
#   detailed_C_FiniteState_ep0_active.jsonl
#   detailed_C_FiniteState_ep1_active.jsonl
#   joint_reward_C_FiniteState_ep{0,1}_active.json
#
# Wall time ước lượng: ~8h (Setup C tốn ~4h/episode, x2 ep)

set -e

REPO_ROOT="/Users/apple/Workspace/personal/side-projects/demo"
VENV_PY="$REPO_ROOT/llms-are-acd-main/cage-env/bin/python"
PROJECT="$REPO_ROOT/feasibility-mcp-roe"

if [ ! -x "$VENV_PY" ]; then
  echo "ERROR: không tìm thấy cage-env python: $VENV_PY" >&2
  exit 1
fi

cd "$PROJECT"
echo "▶ Launching Setup C-active × FiniteState × 2 ep (Sprint 3 Nhánh A)"
echo "  Python: $VENV_PY"
echo "  CWD:    $PROJECT"
echo

"$VENV_PY" benchmark/run_benchmark.py \
  --setup C \
  --red FiniteState \
  --episodes 2 \
  --tag active \
  --active
