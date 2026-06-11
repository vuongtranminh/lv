"""Orchestrator — run all 3 scenarios + offline tests, save logs.

Usage:
    python run_all_scenarios.py

Produces logs under ./logs/ for inclusion in EXPERIMENT_NOTE.md.
"""

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

SCENARIOS = [
    ("offline_tests",           "tests/test_offline.py"),
    ("scenario_1_happy_path",   "run_smoke.py"),
    ("scenario_2_roe_deny",     "scenario_2_roe_deny.py"),
    ("scenario_3_token_compare", "scenario_3_token_compare.py"),
]


def run_one(name: str, script: str) -> tuple[bool, float, Path]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"{name}_{timestamp}.txt"
    print(f"\n▶ {name} — {script}")
    start = time.monotonic()
    with open(log_path, "w", encoding="utf-8") as f:
        result = subprocess.run(
            [sys.executable, str(ROOT / script)],
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=ROOT,
        )
    elapsed = time.monotonic() - start
    ok = result.returncode == 0
    print(f"  {'✓' if ok else '✗'} exit={result.returncode}  time={elapsed:.1f}s  → {log_path.name}")
    return ok, elapsed, log_path


def main():
    print("═══════════════════════════════════════════════════════════════")
    print("  Running all scenarios — logs → ./logs/                       ")
    print("═══════════════════════════════════════════════════════════════")

    results = []
    for name, script in SCENARIOS:
        results.append((name, *run_one(name, script)))

    print("\n═══════════════════════════════════════════════════════════════")
    print("  Summary                                                       ")
    print("═══════════════════════════════════════════════════════════════")
    for name, ok, elapsed, log_path in results:
        print(f"  {'✓' if ok else '✗'} {name:<30} {elapsed:>6.1f}s   {log_path.name}")

    failed = sum(1 for _, ok, _, _ in results if not ok)
    if failed:
        print(f"\n  {failed} scenario(s) FAILED")
        sys.exit(1)
    print("\n  All scenarios passed ✓")
    sys.exit(0)


if __name__ == "__main__":
    main()
