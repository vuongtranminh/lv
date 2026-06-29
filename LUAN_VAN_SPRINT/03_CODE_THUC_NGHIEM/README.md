# Code Thực nghiệm

Code chính ở **`../../feasibility-mcp-roe/`** — folder này không chứa code, chỉ chứa pointer + roadmap.

## State hiện tại

| Hạng mục | Đã có | Cần làm thêm (Phase 2) |
|---|---|---|
| Decoder pre-parse 8-bit | ✓ `feasibility/state_extractor.py` | — |
| MCP tools (6 tool) | ✓ `feasibility/tools.py` | — |
| RoE rules (3 rule) | ✓ `feasibility/roe/rules.py` | Mở rộng → 8-10 rule (B1) |
| ClaudeDefenderPolicy | ✓ `feasibility/claude_policy.py` | Wire vào CybORG submission (B3) |
| Unit test | ✓ `tests/test_offline.py` — 11/11 pass | Cover rule mới (B2) |
| Scenario test | ✓ 3 scenario | — |
| CybORG submission đầy đủ | ✗ | B3 — wire 4 RL KEEP cho 4 agent còn lại |
| Benchmark runner | ✗ | B4 — script chạy 60 episode |
| Analysis (K-Means cluster) | ✗ | B5 — script phân tích log |

## File cần thêm trong feasibility-mcp-roe/

```
feasibility-mcp-roe/
├── feasibility/
│   ├── roe/
│   │   ├── rules.py            ← có sẵn — 3 rule
│   │   └── rules_v2.py         ← MỚI (B1) — 8-10 rule
│   └── ...
├── tests/
│   ├── test_offline.py         ← có sẵn — 11 test
│   └── test_rules_v2.py        ← MỚI (B2)
├── CybORG_submission/          ← MỚI (B3)
│   ├── __init__.py
│   ├── submission.py
│   └── README.md
└── benchmark/                  ← MỚI (B4, B5)
    ├── run_benchmark.py
    ├── analyze_clustering.py
    └── results/
        ├── ... (output sau khi chạy)
```

## Lệnh nhanh

```bash
# Test offline (đã có)
cd ../../feasibility-mcp-roe
python3 tests/test_offline.py

# Chạy 3 scenario hiện tại (đã có)
python3 run_all_scenarios.py

# Sau khi mở rộng (chưa làm)
python3 tests/test_rules_v2.py
python3 benchmark/run_benchmark.py --setup C --red FiniteState --episodes 5
python3 benchmark/analyze_clustering.py benchmark/results/
```
