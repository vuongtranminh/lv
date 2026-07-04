"""Benchmark runner — chạy 60 episode đầy đủ cho Phase 2.

Một file duy nhất, 3 setup bật/tắt bằng mode flag:
- Setup A (baseline TH3): mcp_enabled=False, roe_enabled=False
- Setup B (MCP only):      mcp_enabled=True,  roe_enabled=False
- Setup C (MCP + RoE):     mcp_enabled=True,  roe_enabled=True

Cấu hình:
- 3 setup × 4 red variant × 5 episode = 60 episode
- 500 step / episode
- Wall time ước tính: ~30 giờ

Output:
- benchmark/results/audit_<setup>_<red>_ep<N>.csv  — audit log từng step
- benchmark/results/joint_reward_<setup>_<red>_ep<N>.json  — joint reward
- benchmark/results/run_log.json                  — tiến độ tổng
- benchmark/results/summary.csv                   — metric tổng hợp (sau khi extract_metrics.py)

Sử dụng:
    python benchmark/run_benchmark.py --all                   # 60 episode
    python benchmark/run_benchmark.py --setup C --red FiniteState --episodes 1   # 1 episode (smoke)
    python benchmark/run_benchmark.py --setup B --red AggressiveFSM --episodes 5
"""

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
# Để import CybORG agents bên TH3 (CommVectorGenerator):
TH3_PATH = Path(__file__).parent.parent.parent / "llms-are-acd-main"
if TH3_PATH.exists():
    sys.path.insert(0, str(TH3_PATH))
# CybORG core (Sim engine) ở cage-challenge-4/ — package editable install
CAGE4_PATH = TH3_PATH / "cage-challenge-4"
if CAGE4_PATH.exists():
    sys.path.insert(0, str(CAGE4_PATH))

# ─── Lazy import CybORG (chỉ load khi thực sự cần chạy) ──────────────────────

CYBORG_AVAILABLE = False
CVG_AVAILABLE = False
EMPTY_MESSAGE = None
ClaudeDefenderPolicy = None  # lazy

def _lazy_import_cyborg():
    """Import CybORG + Claude policy. Chỉ gọi khi thực sự chạy episode.
    --status/--help không cần load heavy deps.
    """
    global CYBORG_AVAILABLE, CVG_AVAILABLE, EMPTY_MESSAGE, ClaudeDefenderPolicy
    global np, CybORG, BaseAgent, EnterpriseScenarioGenerator
    global FiniteStateRedAgent, AggressiveFSMAgent, StealthyFSMAgent, ImpactFSMAgent
    global EnterpriseGreenAgent, ReactRemoveBlueAgent, CommVectorGenerator

    if CYBORG_AVAILABLE:
        return True
    try:
        import numpy as _np
        from CybORG import CybORG as _CybORG
        from CybORG.Agents import BaseAgent as _BaseAgent
        from CybORG.Simulator.Scenarios.EnterpriseScenarioGenerator import (
            EnterpriseScenarioGenerator as _ESG,
        )
        from CybORG.Agents.SimpleAgents.FiniteStateRedAgent import FiniteStateRedAgent as _FSR
        from CybORG.Agents.SimpleAgents.AggressiveFSMAgent import AggressiveFSMAgent as _AFM
        from CybORG.Agents.SimpleAgents.StealthyFSMAgent import StealthyFSMAgent as _SFM
        from CybORG.Agents.SimpleAgents.ImpactFSMAgent import ImpactFSMAgent as _IFM
        from CybORG.Agents.SimpleAgents.EnterpriseGreenAgent import EnterpriseGreenAgent as _EGA
        from CybORG.Agents.SimpleAgents.ReactRemoveBlueAgent import ReactRemoveBlueAgent as _RRB
        from CybORG.Agents.Wrappers.BlueFixedActionWrapper import EMPTY_MESSAGE as _EM
        from feasibility.claude_policy import ClaudeDefenderPolicy as _CDP

        np = _np
        CybORG = _CybORG
        BaseAgent = _BaseAgent
        EnterpriseScenarioGenerator = _ESG
        FiniteStateRedAgent = _FSR
        AggressiveFSMAgent = _AFM
        StealthyFSMAgent = _SFM
        ImpactFSMAgent = _IFM
        EnterpriseGreenAgent = _EGA
        ReactRemoveBlueAgent = _RRB
        EMPTY_MESSAGE = _EM
        ClaudeDefenderPolicy = _CDP
        CYBORG_AVAILABLE = True

        try:
            # CommVectorGenerator là MODULE — import từ namespace comm_vector
            from CybORG.Agents.LLMAgents.comm_vector import CommVectorGenerator as _CVG
            CommVectorGenerator = _CVG
            CVG_AVAILABLE = True
        except ImportError:
            CVG_AVAILABLE = False
        return True
    except ImportError as e:
        print(f"ERROR: CybORG chưa cài đầy đủ. Detail: {e}", file=sys.stderr)
        print("Chạy `cd llms-are-acd-main && ./install_unified.sh` trước khi run benchmark.", file=sys.stderr)
        return False


# ─── Cấu hình ────────────────────────────────────────────────────────────────

SETUPS = {
    "A": {"mcp_enabled": False, "roe_enabled": False, "label": "TH3_faithful"},
    "C": {"mcp_enabled": True,  "roe_enabled": True,  "label": "TH3_prompt_plus_MCP_RoE_V3"},
}

EPISODES_PER_CONFIG = 5
STEPS_PER_EPISODE = 500
LLM_BLUE_AGENT = "blue_agent_4"

# Checkpoint mid-episode: save mỗi N step để máy tắt giữa chừng vẫn resume được
CHECKPOINT_EVERY = 50

OUTPUT_DIR = Path(__file__).parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def red_agent_class(red_variant: str):
    if not _lazy_import_cyborg():
        raise RuntimeError("CybORG chưa cài")
    return {
        "FiniteState":   FiniteStateRedAgent,
        "AggressiveFSM": AggressiveFSMAgent,
        "StealthyFSM":   StealthyFSMAgent,
        "ImpactFSM":     ImpactFSMAgent,
    }[red_variant]


RED_AGENTS = ["FiniteState", "AggressiveFSM", "StealthyFSM", "ImpactFSM"]


def build_cyborg_env(red_variant: str, seed: int) -> "CybORG":
    """Khởi tạo CybORG (sim mode) với red variant + scenario CAGE 4."""
    sg = EnterpriseScenarioGenerator(
        blue_agent_class=ReactRemoveBlueAgent,
        green_agent_class=EnterpriseGreenAgent,
        red_agent_class=red_agent_class(red_variant),
        steps=STEPS_PER_EPISODE,
    )
    return CybORG(sg, "sim", seed=seed)


def build_blue_policies(setup: str) -> dict:
    """Tạo dict {agent_name: policy}. LLM_BLUE_AGENT dùng ClaudeDefenderPolicy
    theo setup; 4 agent còn lại dùng ReactRemoveBlueAgent (baseline).
    """
    cfg = SETUPS[setup]
    policies = {}
    for i in range(5):
        name = f"blue_agent_{i}"
        if name == LLM_BLUE_AGENT:
            policies[name] = ClaudeDefenderPolicy(
                observation_space=None,
                action_space=None,
                config={
                    "agent_name": name,
                    "mcp_enabled": cfg["mcp_enabled"],
                    "roe_enabled": cfg["roe_enabled"],
                },
            )
        else:
            policies[name] = ReactRemoveBlueAgent(name)
    return policies


def get_action_from_policy(policy, obs, agent_name: str, action_space=None):
    """Unified call. ClaudeDefenderPolicy có compute_single_action;
    BaseAgent có get_action(obs, action_space).

    BaseAgent (ReactRemoveBlueAgent) đôi khi KeyError vì IP runtime không nằm
    trong scenario static map → fallback Sleep cho step đó.
    """
    if ClaudeDefenderPolicy is not None and isinstance(policy, ClaudeDefenderPolicy):
        action, _, _ = policy.compute_single_action(obs=obs)
        return action
    try:
        return policy.get_action(obs, action_space=action_space)
    except (KeyError, Exception) as e:
        # Baseline agent crash → log warning, fallback Sleep
        print(f"  ⚠ baseline {agent_name} get_action crash ({type(e).__name__}: {e}) → Sleep", file=sys.stderr)
        from CybORG.Simulator.Actions import Sleep
        return Sleep()


def inject_phase(obs: dict, env) -> dict:
    """Thêm obs['phase'] = mission_phase (PhaseWrapper-style)."""
    try:
        obs["phase"] = env.environment_controller.state.mission_phase
    except (AttributeError, TypeError):
        obs["phase"] = "unknown"
    return obs


def build_messages_dict(policies: dict, observations: dict, last_actions: dict) -> dict:
    """Tạo dict messages 8-bit cho parallel_step.

    CommVectorGenerator là MODULE (không phải class) — gọi
    CommVectorGenerator.create_comm_message(obs, last_action, host_ip_map).
    Nếu không có thì fallback EMPTY_MESSAGE (M4 sẽ measure rỗng).
    """
    messages = {}
    if CVG_AVAILABLE:
        try:
            for name in policies:
                obs = observations.get(name, {})
                last_act = last_actions.get(name, None)
                try:
                    msg = CommVectorGenerator.create_comm_message(obs, last_act, {})
                except TypeError:
                    # Một số version không cần host_ip_map
                    msg = CommVectorGenerator.create_comm_message(obs, last_act)
                messages[name] = np.array(msg, dtype=np.int8) if not isinstance(msg, np.ndarray) else msg
        except Exception:
            messages = {name: np.array(EMPTY_MESSAGE) for name in policies}
    else:
        messages = {name: np.array(EMPTY_MESSAGE) for name in policies}
    return messages


def sum_reward_dict(rews_for_agent) -> float:
    """rews[agent] có thể là dict {action_key: float} hoặc float."""
    if isinstance(rews_for_agent, dict):
        return float(sum(rews_for_agent.values()))
    return float(rews_for_agent)


# ─── Checkpoint mid-episode (cloudpickle) ────────────────────────────────────

def _ckpt_path(tag: str) -> Path:
    return OUTPUT_DIR / f"checkpoint_{tag}.pkl"


def save_checkpoint(tag: str, env, observations: dict, last_actions: dict,
                    cumulative_reward: float, step_rewards: list, next_step: int,
                    roe_counters_state):
    """Lưu snapshot mid-episode để resume khi máy tắt giữa chừng."""
    import cloudpickle
    payload = {
        "env": env,
        "observations": observations,
        "last_actions": last_actions,
        "cumulative_reward": cumulative_reward,
        "step_rewards": step_rewards,
        "next_step": next_step,
        "roe_counters_state": roe_counters_state,
    }
    tmp_path = _ckpt_path(tag).with_suffix(".pkl.tmp")
    with open(tmp_path, "wb") as f:
        cloudpickle.dump(payload, f)
    # Atomic rename — tránh checkpoint half-written nếu crash đúng lúc dump
    tmp_path.replace(_ckpt_path(tag))


def load_checkpoint(tag: str):
    """Đọc checkpoint nếu tồn tại. Trả về dict hoặc None."""
    import cloudpickle
    path = _ckpt_path(tag)
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            return cloudpickle.load(f)
    except Exception as e:
        print(f"  ⚠ checkpoint corrupted: {e}, sẽ chạy từ đầu", file=sys.stderr)
        return None


def delete_checkpoint(tag: str):
    """Xoá checkpoint sau khi episode hoàn thành."""
    path = _ckpt_path(tag)
    if path.exists():
        path.unlink()


def _capture_roe_counters_state():
    """Snapshot RoE EpisodeCounters v2 (đã wire trong policy_engine)."""
    from feasibility.roe.policy_engine import EpisodeCounters
    return {
        "blocks_per_zone": dict(EpisodeCounters.blocks_per_zone),
        "decoys_per_host": dict(EpisodeCounters.decoys_per_host),
        "restores_total": getattr(EpisodeCounters, "restores_total", 0),
        "decoys_total": getattr(EpisodeCounters, "decoys_total", 0),
    }


def _restore_roe_counters_state(state):
    """Restore RoE EpisodeCounters v2."""
    from feasibility.roe.policy_engine import EpisodeCounters
    EpisodeCounters.blocks_per_zone = dict(state.get("blocks_per_zone", {}))
    EpisodeCounters.decoys_per_host = dict(state.get("decoys_per_host", {}))
    if hasattr(EpisodeCounters, "restores_total"):
        EpisodeCounters.restores_total = state.get("restores_total", 0)
    if hasattr(EpisodeCounters, "decoys_total"):
        EpisodeCounters.decoys_total = state.get("decoys_total", 0)


# ─── Episode loop ────────────────────────────────────────────────────────────

def run_single_episode(setup: str, red_variant: str, episode_idx: int, seed: int,
                       run_tag: str = None) -> dict:
    """Chạy 1 episode, ghi log per-step + joint reward.

    run_tag: nếu set, output file = <setup>_<red>_ep<N>_<run_tag>.{csv,json,jsonl}
    """
    if not _lazy_import_cyborg():
        raise RuntimeError("CybORG chưa cài — không thể chạy episode")

    cfg = SETUPS[setup]
    base_tag = f"{setup}_{red_variant}_ep{episode_idx}"
    tag = f"{base_tag}_{run_tag}" if run_tag else base_tag
    print(f"\n▶ {tag} (mcp={cfg['mcp_enabled']}, roe={cfg['roe_enabled']}, prompt=TH3 acd2025/base.yml)")

    audit_path = OUTPUT_DIR / f"audit_{tag}.csv"
    reward_path = OUTPUT_DIR / f"joint_reward_{tag}.json"
    detailed_path = OUTPUT_DIR / f"detailed_{tag}.jsonl"

    os.environ["AUDIT_LOG_PATH"] = str(audit_path)
    os.environ["DETAILED_LOG_PATH"] = str(detailed_path)
    os.environ["RED_VARIANT"] = red_variant
    os.environ["EPISODE_SEED"] = str(seed)

    # Resume từ checkpoint nếu có
    ckpt = load_checkpoint(tag)
    if ckpt is not None:
        env = ckpt["env"]
        observations = ckpt["observations"]
        last_actions = ckpt["last_actions"]
        cumulative_reward = ckpt["cumulative_reward"]
        step_rewards = list(ckpt["step_rewards"])
        start_step = ckpt["next_step"]
        _restore_roe_counters_state(ckpt["roe_counters_state"])
        print(f"  ⟳ RESUME từ checkpoint: step {start_step}/{STEPS_PER_EPISODE}, "
              f"reward đã có={cumulative_reward:.2f}")
        # AuditLog + DetailedLogger ĐÃ chuyển sang mode "a" (append) — file log
        # cũ KHÔNG bị ghi đè. Step counter của LLM agent cũng restore từ checkpoint
        # để mọi event mới có step number đúng (không reset về 0).
        policies = build_blue_policies(setup)
        # Restore step counter cho LLM agent (blue_agent_4)
        for name, pol in policies.items():
            if hasattr(pol, "step") and not isinstance(pol, ReactRemoveBlueAgent):
                pol.step = start_step
                if hasattr(pol, "detailed") and pol.detailed is not None:
                    pol.detailed.set_step(start_step)
    else:
        env = build_cyborg_env(red_variant, seed=seed)
        policies = build_blue_policies(setup)

        reset_ret = env.reset()
        # parallel env API trả (obs, info); cũ hơn có thể trả chỉ obs
        if isinstance(reset_ret, tuple):
            observations, _info = reset_ret[0], reset_ret[1] if len(reset_ret) > 1 else {}
        else:
            observations = {name: env.get_observation(name) for name in policies}

        last_actions = {name: None for name in policies}
        cumulative_reward = 0.0
        step_rewards = []
        start_step = 0

    t_start = time.monotonic()
    truncated_all = False

    try:
        for step in range(start_step, STEPS_PER_EPISODE):
            # Inject phase
            for name in policies:
                obs = observations.get(name) or env.get_observation(name)
                observations[name] = inject_phase(obs, env)

            # Get actions per agent
            actions = {}
            for name, policy in policies.items():
                try:
                    action_space = env.get_action_space(name)
                except Exception:
                    action_space = None
                actions[name] = get_action_from_policy(
                    policy, observations[name], name, action_space=action_space,
                )
                last_actions[name] = actions[name]

            # Build messages dict
            messages = build_messages_dict(policies, observations, last_actions)

            # Step env — thử parallel_step trước, fallback step
            try:
                obs_d, rews, dones, info = env.parallel_step(actions, messages=messages)
            except AttributeError:
                # Fallback cho version cũ
                step_ret = env.step(actions=actions, messages=messages)
                if len(step_ret) == 4:
                    obs_d, rews, dones, info = step_ret
                elif len(step_ret) == 5:
                    obs_d, rews, dones, _trunc, info = step_ret
                else:
                    obs_d = {n: env.get_observation(n) for n in policies}
                    rews = env.get_rewards()
                    dones = {}
                    info = {}

            observations = obs_d
            # Tính joint reward (sum blue agents)
            joint = 0.0
            if isinstance(rews, dict):
                for name in policies:
                    if name in rews:
                        joint += sum_reward_dict(rews[name])
            cumulative_reward += joint
            step_rewards.append(joint)

            # Episode termination
            if isinstance(dones, dict) and dones.get("__all__", False):
                truncated_all = True
                print(f"  episode ended early at step {step}")
                break

            if step % 50 == 0:
                elapsed = time.monotonic() - t_start
                print(f"  step {step}/{STEPS_PER_EPISODE}  reward={cumulative_reward:.2f}  "
                      f"elapsed={elapsed:.0f}s")

            # Save checkpoint mỗi CHECKPOINT_EVERY step
            if (step + 1) % CHECKPOINT_EVERY == 0 and (step + 1) < STEPS_PER_EPISODE:
                try:
                    save_checkpoint(
                        tag, env, observations, last_actions,
                        cumulative_reward, step_rewards, next_step=step + 1,
                        roe_counters_state=_capture_roe_counters_state(),
                    )
                    print(f"  💾 checkpoint saved @ step {step+1}")
                except Exception as e:
                    print(f"  ⚠ save_checkpoint FAIL: {e}", file=sys.stderr)
    finally:
        for p in policies.values():
            if hasattr(p, "end_episode"):
                p.end_episode()

    result = {
        "setup": setup,
        "red_variant": red_variant,
        "episode_idx": episode_idx,
        "seed": seed,
        "mcp_enabled": cfg["mcp_enabled"],
        "roe_enabled": cfg["roe_enabled"],
        "cumulative_joint_reward": cumulative_reward,
        "step_rewards": step_rewards,
        "wall_time_seconds": time.monotonic() - t_start,
        "audit_log": str(audit_path),
        "detailed_log": str(detailed_path),
        "truncated_all": truncated_all,
    }
    with open(reward_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    # Episode hoàn thành → xoá checkpoint
    delete_checkpoint(tag)
    print(f"  ✓ {tag} → reward={cumulative_reward:.2f}, wall={result['wall_time_seconds']:.0f}s")
    return result


# ─── Cấu hình hoàn thiện episode ─────────────────────────────────────────────

def episode_done(setup: str, red: str, ep: int, run_tag: str = None) -> bool:
    """Episode đã chạy xong nếu file joint_reward_<tag>.json tồn tại + parse được."""
    suffix = f"_{run_tag}" if run_tag else ""
    path = OUTPUT_DIR / f"joint_reward_{setup}_{red}_ep{ep}{suffix}.json"
    if not path.exists():
        return False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return "cumulative_joint_reward" in data
    except Exception:
        return False


def all_configs():
    """Yield tất cả (setup, red, ep) — 60 config tổng."""
    for setup in SETUPS:
        for red in RED_AGENTS:
            for ep in range(EPISODES_PER_CONFIG):
                yield setup, red, ep


def list_configs(force: bool = False) -> list:
    """Trả về list [(setup, red, ep), ...] cần chạy. force=True → bỏ qua check resume."""
    out = []
    for setup, red, ep in all_configs():
        if force or not episode_done(setup, red, ep):
            out.append((setup, red, ep))
    return out


# ─── Run all (resume by default) ─────────────────────────────────────────────

def run_all(force: bool = False, chunk_spec: str = None):
    """Chạy episode còn lại. Mặc định resume (skip episode đã có joint_reward_*.json).

    chunk_spec: "N/M" — chia 60 config (hoặc remaining) thành M phần, chạy phần thứ N (1-indexed).
    """
    if not _lazy_import_cyborg():
        print("ERROR: CybORG chưa cài. Không thể chạy benchmark.", file=sys.stderr)
        sys.exit(1)

    todo = list_configs(force=force)
    total_60 = sum(1 for _ in all_configs())
    done_count = total_60 - len(todo)

    # Áp dụng chunk_spec nếu có
    if chunk_spec:
        try:
            idx_str, total_str = chunk_spec.split("/")
            chunk_idx = int(idx_str)
            chunk_total = int(total_str)
            assert 1 <= chunk_idx <= chunk_total
        except (ValueError, AssertionError):
            print(f"ERROR: --chunk phải có dạng N/M (ví dụ 3/12), nhận: {chunk_spec}", file=sys.stderr)
            sys.exit(1)
        # Chia todo thành chunk_total phần, lấy phần idx
        size = (len(todo) + chunk_total - 1) // chunk_total
        start = (chunk_idx - 1) * size
        end = min(start + size, len(todo))
        todo = todo[start:end]
        print(f"Chunk {chunk_idx}/{chunk_total}: chạy {len(todo)} config (config {start+1}–{end} trong todo)")

    print(f"\n=== KẾ HOẠCH ===")
    print(f"Đã xong:   {done_count}/{total_60} episode")
    print(f"Còn chạy:  {len(todo)} episode")
    if len(todo) == 0:
        print("→ Không có gì để chạy. Dùng --force để chạy lại từ đầu.")
        return
    eta_h = len(todo) * 0.5  # ~30 phút/ep
    print(f"ETA:       ~{eta_h:.1f} giờ (giả định 30 phút/episode)")
    print()

    t_start = time.monotonic()
    log_path = OUTPUT_DIR / "run_log.json"
    log_summary = {}
    if log_path.exists():
        try:
            log_summary = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            log_summary = {}
    log_summary.setdefault("started_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    log_summary.setdefault("configs", [])
    log_summary["last_resumed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    for setup, red, ep in todo:
        config_meta = {"setup": setup, "red": red, "episode": ep}
        try:
            result = run_single_episode(setup, red, ep, seed=ep)
            config_meta["status"] = "completed"
            config_meta["reward"] = result["cumulative_joint_reward"]
        except Exception as e:
            config_meta["status"] = "failed"
            config_meta["error"] = str(e)
            config_meta["traceback"] = traceback.format_exc()
            print(f"  ✗ FAILED: {e}", file=sys.stderr)
        log_summary["configs"].append(config_meta)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_summary, f, indent=2, ensure_ascii=False)

    log_summary["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    log_summary["total_wall_time_seconds_this_run"] = time.monotonic() - t_start
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_summary, f, indent=2, ensure_ascii=False)

    # Đếm tổng tiến độ sau khi chạy
    new_done = sum(1 for s, r, e in all_configs() if episode_done(s, r, e))
    print(f"\n=== TỔNG KẾT RUN ===")
    print(f"Tổng episode đã xong: {new_done}/{total_60}")
    print(f"Run này wall time:    {(time.monotonic() - t_start)/3600:.1f} giờ")
    print(f"Log:                  {log_path}")


# ─── Status command ──────────────────────────────────────────────────────────

def print_status():
    """In bảng tiến độ: từng (setup, red) có bao nhiêu episode đã chạy."""
    print(f"=== TIẾN ĐỘ BENCHMARK ({OUTPUT_DIR}) ===\n")
    header = f"{'Setup':<6} {'Red':<14} | " + " ".join(f"ep{i}" for i in range(EPISODES_PER_CONFIG)) + " | done"
    print(header)
    print("-" * len(header))
    total_done = 0
    total = 0
    for setup in SETUPS:
        for red in RED_AGENTS:
            cells = []
            n_done = 0
            for ep in range(EPISODES_PER_CONFIG):
                total += 1
                if episode_done(setup, red, ep):
                    cells.append("✓  ")
                    n_done += 1
                    total_done += 1
                else:
                    cells.append("·  ")
            print(f"{setup:<6} {red:<14} | {' '.join(cells)}| {n_done}/{EPISODES_PER_CONFIG}")
    print("-" * len(header))
    print(f"\nTổng: {total_done}/{total} episode hoàn thành")
    pct = (100.0 * total_done / total) if total else 0
    eta_h = (total - total_done) * 0.5
    print(f"Tiến độ: {pct:.1f}%  •  ETA còn lại: ~{eta_h:.1f} giờ\n")

    # Gợi ý chunk tiếp theo
    todo = list_configs()
    if todo:
        first = todo[0]
        print(f"Episode kế tiếp: setup={first[0]}, red={first[1]}, ep={first[2]}")
        print(f"  → python benchmark/run_benchmark.py --setup {first[0]} --red {first[1]} --episodes {EPISODES_PER_CONFIG}")
        print(f"  hoặc chạy nguyên chunk: python benchmark/run_benchmark.py --chunk 1/12")
    else:
        print("✓ Đã chạy đủ 60 episode. Chạy `python benchmark/extract_metrics.py` để tổng hợp.")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Phase 2 (3 setup × 4 red × 5 ep). Hỗ trợ resume + chunked run."
    )
    parser.add_argument("--all", action="store_true", help="Chạy 60 ep (resume mặc định)")
    parser.add_argument("--setup", choices=list(SETUPS.keys()), help="Chạy 1 setup A/B/C")
    parser.add_argument("--red", choices=RED_AGENTS, help="Red variant cụ thể")
    parser.add_argument("--episodes", type=int, default=1, help="Số episode khi chạy --setup --red")
    parser.add_argument("--force", action="store_true", help="Chạy lại cả episode đã xong (mặc định: skip)")
    parser.add_argument("--chunk", type=str, help="Chia 60 ep thành M phần, chạy phần N. VD: --chunk 3/12")
    parser.add_argument("--status", action="store_true", help="Xem tiến độ — không chạy gì")
    parser.add_argument("--tag", type=str, default=None,
                        help="Suffix file output (vd --tag sprint3 → audit_A_FiniteState_ep0_sprint3.csv). "
                             "Dùng để tách biệt với log lần chạy trước.")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.all or args.chunk:
        run_all(force=args.force, chunk_spec=args.chunk)
    elif args.setup and args.red:
        for ep in range(args.episodes):
            if not args.force and episode_done(args.setup, args.red, ep, run_tag=args.tag):
                print(f"  ⊙ skip {args.setup}_{args.red}_ep{ep}"
                      f"{'_' + args.tag if args.tag else ''} (đã có joint_reward_*.json)")
                continue
            run_single_episode(args.setup, args.red, ep, seed=ep,
                               run_tag=args.tag)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
