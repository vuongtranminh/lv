# mcp-roe-vs-th3

**Sprint 4 project** — so sánh fair MCP+RoE với baseline TH3 khi giữ nguyên prompt content, model, và red variant.

## Mục đích

Kết quả Sprint 3 phát hiện: Setup A của luận văn KHÔNG dùng prompt TH3 → so sánh "MCP+RoE" với "baseline TH3" không fair. Project mới này cô lập biến số "MCP+RoE" bằng cách:

- **Setup A-TH3**: dùng nguyên bản prompt TH3 `acd2025/base.yml` (142 dòng tiếng Anh), single-shot JSON output
- **Setup C-TH3**: cùng nội dung prompt TH3 (chỉ đổi phần output section sang MCP tool call) + RoE V3 (6 rule reward-focused, deny/approve thuần)

Xem [SETUP_REPORT.md](SETUP_REPORT.md) cho chi tiết đầy đủ về thiết kế, câu hỏi nghiên cứu, và kỳ vọng kết quả.

## Cấu trúc project

```
mcp-roe-vs-th3/
├── SETUP_REPORT.md              # Báo cáo thiết kế Sprint 4
├── README.md                    # File này
│
├── feasibility/
│   ├── prompts/
│   │   ├── acd2025/
│   │   │   ├── base.yml            # BYTE-IDENTICAL với TH3 gốc (source of truth)
│   │   │   └── base.md             # Extract readable của base.yml (Setup A)
│   │   ├── setup_c_final.md        # Setup C prompt sau khi 2 chỗ thay thế
│   │   └── regenerate_md.py        # Script tái sinh .md từ .yml
│   │
│   ├── setup_c_override.py         # 4 hằng số: 2 đoạn gốc TH3 + 2 đoạn thay thế MCP
│   │
│   ├── roe/
│   │   ├── rules_v3.py             # 6 rule reward-focused
│   │   └── policy_engine.py        # Engine adapter
│   │
│   ├── tools.py                    # MCP tools (KHÔNG có recommended_action) — TODO
│   ├── claude_policy.py            # Driver 2 setup — TODO
│   └── ...                         # Các file reuse từ feasibility-mcp-roe
│
├── benchmark/
│   ├── run_benchmark.py            # Runner — TODO
│   └── results/                     # Output
│
└── tests/
    └── test_rules_v3.py            # 34 test cho RoE V3 (34/34 pass)
```

## Trạng thái triển khai

| Component | Status |
|---|---|
| SETUP_REPORT.md | ✅ Đầy đủ |
| Prompt TH3 (`acd2025/base.yml`) | ✅ Byte-identical với TH3, giữ nguyên tên và cấu trúc thư mục |
| MCP override cho Setup C (`setup_c_override.py`) | ✅ 2 thay thế in-place (JSON instruction + 5 examples → MCP tool call) |
| RoE V3 (6 rule) | ✅ |
| Test RoE V3 | ✅ 34/34 pass |
| tools.py (MCP, không recommended_action) | ⏳ TODO |
| claude_policy.py (driver 2 setup) | ⏳ TODO |
| run_benchmark.py | ⏳ TODO |
| Integration smoke test | ⏳ TODO |
| Benchmark A-TH3 × FiniteState × 2 ep | ⏳ TODO (~4h) |
| Benchmark C-TH3 × FiniteState × 2 ep | ⏳ TODO (~8h) |

## Kế hoạch triển khai tiếp

Xem [SETUP_REPORT.md §8](SETUP_REPORT.md) cho lộ trình 5-7 ngày.

Sau khi em duyệt thiết kế trong SETUP_REPORT.md:
1. Viết `tools.py` (adapt từ feasibility-mcp-roe/tools.py, gỡ recommended_action injection)
2. Viết `claude_policy.py` (2 nhánh: paper-style JSON parse cho A, MCP tool call cho C)
3. Viết `run_benchmark.py` (adapt từ feasibility-mcp-roe/benchmark/run_benchmark.py)
4. Smoke test 10 step mỗi setup
5. Chạy benchmark đầy đủ

## Chạy test RoE V3

```bash
cd mcp-roe-vs-th3
python3.11 tests/test_rules_v3.py
```

Kết quả kỳ vọng: **34/34 passed**.

## Liên hệ với project cũ

Project `feasibility-mcp-roe/` (Sprint 1-3) vẫn giữ nguyên, không bị ảnh hưởng. Dữ liệu benchmark cũ và log JSONL vẫn còn để tham chiếu.

Sprint 4 (project này) chạy trên logic riêng, kết quả sẽ được tổng hợp cùng Sprint 1-3 khi viết Chương 5 luận văn.
