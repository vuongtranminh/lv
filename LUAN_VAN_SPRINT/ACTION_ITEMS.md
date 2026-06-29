# ACTION ITEMS — LUẬN VĂN MCP + RoE

> Chỉ dùng 2 paper: LT1 (lý thuyết) + TH3 (thực nghiệm). Phát triển trên TH3 là chính.

---

## A. CHƯƠNG LUẬN VĂN (✅ HOÀN THÀNH 6/7)

- [x] **A1.** Chương 1 — Mở đầu → `04_LUAN_VAN_DRAFT/CHUONG_1_MO_DAU.md` (✅ 5-8 trang)
- [x] **A2.** Chương 2 — Cơ sở lý thuyết (LT1 + TH3 + MCP + RoE) → `04_LUAN_VAN_DRAFT/CHUONG_2_TONG_QUAN.md` (✅ 15-20 trang)
- [x] **A3.** Chương 3 — Thiết kế hệ thống → `04_LUAN_VAN_DRAFT/CHUONG_3_THIET_KE.md` (✅ 10-12 trang)
- [x] **A4.** Chương 4 — Triển khai + Thực nghiệm Phase 0 (Phase 2 đã có thiết kế thí nghiệm, cần data) → `04_LUAN_VAN_DRAFT/CHUONG_4_TRIEN_KHAI.md` (✅ 10-15 trang)
- [⚠] **A5.** Chương 5 — Kết quả & Đánh giá (template + khung phân tích đầy đủ, cần fill [TBD] với benchmark data) → `04_LUAN_VAN_DRAFT/CHUONG_5_KET_QUA.md`
- [x] **A6.** Chương 6 — Kết luận → `04_LUAN_VAN_DRAFT/CHUONG_6_KET_LUAN.md` (✅ 3-5 trang)
- [x] **A7.** Phụ lục → `04_LUAN_VAN_DRAFT/PHU_LUC.md` (✅)

## B. CODE EXPANSION (✅ B1-B7 HOÀN THÀNH)

- [x] **B1.** Mở rộng RoE rules 3 → 8 rule → `feasibility-mcp-roe/feasibility/roe/rules_v2.py` (✅ code thật, chạy được)
- [x] **B2.** Unit tests cho rule mới → `feasibility-mcp-roe/tests/test_rules_v2.py` (✅ **13/13 pass**)
- [x] **B3.** Mode toggle 3 setup gộp 1 codebase:
  - `context.py` — `mcp_enabled`, `roe_enabled` sticky flags
  - `tools.py` — `_propose()` bypass RoE khi flag tắt
  - `paper_style.py` — TH3-baseline prompt + regex parser (Mode A)
  - `claude_policy.py` — branch MCP vs paper-style theo flag
- [x] **B4.** Benchmark runner đầy đủ → `feasibility-mcp-roe/benchmark/run_benchmark.py`
  - Wire CybORG + 4 red variant + 5 blue + green agent
  - Loop 500 step, audit log per-step, joint reward per-episode
  - 1 run = `python benchmark/run_benchmark.py --all` cho 60 ep
- [x] **B5.** Extract metrics M1-M5 → `feasibility-mcp-roe/benchmark/extract_metrics.py`
  - Parse audit + reward JSON → summary.csv với mean ± std
- [x] **B6.** Clustering analysis → `feasibility-mcp-roe/benchmark/analyze_clustering.py` (✅ chạy được khi có OpenAI API key)
- [⚠] **B7.** Smoke test 1 episode (chờ CybORG cài xong) — câu lệnh:
  `python benchmark/run_benchmark.py --setup C --red FiniteState --episodes 1`

## C. CHẠY BENCHMARK (CHỜ USER — chia chunk dần dần)

- [ ] **C1.** Cài CybORG — `cd llms-are-acd-main && ./install_unified.sh` (15-30 phút, 1 lần)
- [ ] **C2.** Smoke test — `python benchmark/run_benchmark.py --setup C --red FiniteState --episodes 1` (~15 phút)
- [ ] **C3.** Chạy 12 chunk × 2.5 giờ = 30 giờ. Tùy chọn:
  - Cách A (theo cặp setup+red): `python benchmark/run_benchmark.py --setup A --red FiniteState --episodes 5` × 12 lần
  - Cách B (auto chia): `python benchmark/run_benchmark.py --chunk N/12` × 12 lần
  - Cách C (chạy ngầm hết): `nohup python benchmark/run_benchmark.py --all > log 2>&1 &`
  - **Resume mặc định** — episode đã xong sẽ skip, không sợ chạy lại
- [ ] **C4.** Xem tiến độ bất cứ lúc nào — `python benchmark/run_benchmark.py --status`
- [ ] **C5.** Extract metric — `python benchmark/extract_metrics.py` → `results/summary.csv`
- [ ] **C6.** Fill data vào CHUONG_5_KET_QUA.md, regen LUAN_VAN_FULL.docx

→ Hướng dẫn chi tiết: `feasibility-mcp-roe/benchmark/RUN_BENCHMARK.md`

## D. BẢO VỆ (✅ 3/4)

- [x] **D1.** Slides outline (20 slide) → `05_BAO_VE/SLIDES_OUTLINE.md` (✅)
- [x] **D2.** Demo script → `05_BAO_VE/DEMO_SCRIPT.md` (✅)
- [x] **D3.** Q&A prep (17 câu hỏi) → `05_BAO_VE/QA_PREP.md` (✅)
- [ ] **D4.** Slides file thật (PowerPoint) — user tự design từ outline

## E. ĐÓNG GÓI CUỐI (✅ E1-E2)

- [x] **E1.** Gộp 7 chương → `04_LUAN_VAN_DRAFT/LUAN_VAN_FULL.md` (✅ 1.638 dòng)
- [x] **E2.** Convert sang Word → `04_LUAN_VAN_DRAFT/LUAN_VAN_FULL.docx` (✅ 55 KB)
- [ ] **E3.** Review, sửa format, fill citation [1] đầy đủ thông tin LT1
- [ ] **E4.** Gửi thầy review draft

---

## TIẾN ĐỘ TỔNG QUAN

| Khối | Đã xong | Còn lại |
|---|---|---|
| A — Chương luận văn | 6/7 (Chương 5 cần data) | Fill [TBD] khi có benchmark |
| B — Code | 3/5 hoàn toàn (B1, B2, B5); B3, B4 skeleton chờ CybORG | Wire CybORG (cần install) |
| C — Benchmark | 0/4 | User cài + chạy |
| D — Defense | 3/4 (chỉ thiếu slides file thật) | User design slides |
| E — Đóng gói | 2/4 | Review + gửi thầy |

**Tổng đã hoàn thành**: ~70% công việc luận văn. Phần còn lại 30% là chạy benchmark + fill data + slides design.

---

## CÒN LẠI (theo thứ tự)

### Bạn cần làm (ngoài tầm AI)

1. **Cài CybORG CAGE 4**: `cd llms-are-acd-main && ./install_unified.sh` (~15-30 phút)
2. **Cập nhật citation [1]**: thông tin đầy đủ tác giả/năm/venue của LT1 trong `LUAN_VAN_FULL.md`
3. **Design slides PowerPoint** theo `05_BAO_VE/SLIDES_OUTLINE.md`

### Mình + bạn cùng làm sau khi CybORG cài xong

4. **Wire CybORG vào `run_benchmark.py`** — fill các phần TODO trong code
5. **Chạy smoke test** 1 episode full → verify pipeline OK
6. **Chạy 60 episode benchmark** (chia 8-10 phiên, mỗi phiên 3-4 giờ)
7. **Fill data vào Chương 5** (`CHUONG_5_KET_QUA.md` các chỗ [TBD])
8. **Regenerate `LUAN_VAN_FULL.docx`**
9. **Gửi thầy review**

---

## FILES KEY

```
LUAN_VAN_SPRINT/
├── ACTION_ITEMS.md                          ← file này
├── 04_LUAN_VAN_DRAFT/
│   ├── LUAN_VAN_FULL.md                     ← ⭐ GỘP 7 CHƯƠNG (1.638 dòng)
│   ├── LUAN_VAN_FULL.docx                   ← ⭐ WORD (55 KB)
│   ├── CHUONG_1_MO_DAU.md                   ← đầy đủ
│   ├── CHUONG_2_TONG_QUAN.md                ← đầy đủ
│   ├── CHUONG_3_THIET_KE.md                 ← đầy đủ
│   ├── CHUONG_4_TRIEN_KHAI.md               ← đầy đủ Phase 0 + thiết kế Phase 2
│   ├── CHUONG_5_KET_QUA.md                  ← template chờ data
│   ├── CHUONG_6_KET_LUAN.md                 ← đầy đủ
│   └── PHU_LUC.md                           ← đầy đủ
├── 05_BAO_VE/
│   ├── SLIDES_OUTLINE.md                    ← đầy đủ
│   ├── DEMO_SCRIPT.md                       ← đầy đủ
│   └── QA_PREP.md                           ← đầy đủ
└── ../feasibility-mcp-roe/
    ├── feasibility/roe/rules_v2.py          ← 8 rule mở rộng (CODE THẬT)
    ├── tests/test_rules_v2.py               ← 13/13 PASS
    └── benchmark/
        ├── run_benchmark.py                 ← skeleton, fill CybORG sau
        └── analyze_clustering.py            ← code đầy đủ, chạy được
```
