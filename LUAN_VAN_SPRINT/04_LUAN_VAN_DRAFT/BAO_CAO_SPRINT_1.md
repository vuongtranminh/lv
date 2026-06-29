# BÁO CÁO SPRINT 1 — Khảo sát + Tích hợp + Benchmark Pilot

> **Phạm vi Sprint 1** (theo `SPRINT_4_TUAN.md`): Khảo sát related work + Tích hợp CybORG + Chạy benchmark pilot 3 setup × 1 ep × FiniteState để verify pipeline.

> **Thời gian thực tế**: ~3 ngày tập trung cao độ (đã vượt quá thời lượng dự kiến do nhiều lỗi kỹ thuật phát sinh — chi tiết ở `BAO_CAO_LOI_SPRINT_1.md`).

---

## 1. Mục tiêu Sprint 1 (kế hoạch ban đầu)

Theo `00_SPRINT_PLAN/SPRINT_4_TUAN.md`:

1. **Khảo sát ~15-20 paper liên quan** (Llama Guard, NeMo Guardrails, OPA, CAGE submissions, MCP agents, …)
2. **Tích hợp `claude_policy.py` vào CybORG submission đầy đủ 5 agent**
3. **Draft Chương 2 (Tổng quan tình hình nghiên cứu)**
4. **Verify pipeline 500 step**

Sau khi user yêu cầu thu hẹp phạm vi để tập trung 2 paper TH3 + LT1, Sprint 1 được điều chỉnh lại thành:

- Tích hợp CybORG CAGE 4 trong khung benchmark luận văn
- Implement 3 setup A/B/C theo mode toggle (MCP + RoE)
- Chạy benchmark pilot 3 setup × 1 episode × 500 step × red FiniteState
- Viết báo cáo so sánh kết quả với TH3 paper

---

## 2. Sản phẩm Sprint 1 đã hoàn thành

### 2.1 Code

| Thành phần | File | Trạng thái |
|---|---|---|
| Mode toggle 3 setup (A/B/C) | `feasibility/claude_policy.py` | ✅ Hoàn thành |
| Setup A — paper-style (single-shot) | `feasibility/paper_style.py` | ✅ |
| Setup B — MCP only (RoE bypass) | `feasibility/tools.py` | ✅ |
| Setup C — MCP + RoE đầy đủ | `feasibility/roe/rules.py` (3 rule v1), `rules_v2.py` (8 rule v2 chưa wire) | ✅ |
| Detailed logger JSONL | `feasibility/detailed_logger.py` | ✅ |
| Audit CSV logger | `feasibility/audit.py` | ✅ |
| Checkpoint mid-episode (cloudpickle) | `benchmark/run_benchmark.py` | ✅ (có bug resume — đã fix) |
| Hostname validation (Fix 2026-06-28) | `tools.py` + `state_extractor.py` | ✅ |

### 2.2 Tests

| Test suite | Số test | Trạng thái |
|---|---|---|
| `test_offline.py` (legacy) | 11 | ✅ all pass |
| `test_rules_v2.py` (RoE rule v2) | 13 | ✅ all pass |
| `test_hostname_validation.py` (mới) | 12 | ✅ all pass |
| **Tổng** | **36** | **36/36 pass** |

### 2.3 Dữ liệu benchmark (Setup A/B/C × FiniteState × 1 ep)

| Setup | Reward | Wall time | Step count | Files |
|---|---|---|---|---|
| **A** (TH3-style) | **-660** | 6562s (1h49) | 500/500 | audit_A, detailed_A (3602 event), joint_reward_A |
| **B** (MCP only) | **-2110** | 14544s (4h04) | 500/500 | audit_B, detailed_B (8538 event), joint_reward_B |
| **C** (MCP + RoE) | **-1515** | 15936s (4h26) | 500/500 | audit_C, detailed_C (9774 event), joint_reward_C |

### 2.4 Báo cáo

| Báo cáo | File | Số dòng |
|---|---|---|
| Báo cáo Setup A (chi tiết + so TH3) | `BAO_CAO_SETUP_A.md` | 636 |
| Báo cáo Setup B (chi tiết + so A + TH3) | `BAO_CAO_SETUP_B.md` | 521 |
| Báo cáo Setup C (chi tiết + so A + B + TH3) | `BAO_CAO_SETUP_C.md` | 545 |
| Phân tích reward chi tiết — nguồn phạt | `PHAN_TICH_REWARD.md` | 395 |
| Case study chéo A/B/C tại các step quan trọng | `CASE_STUDY_CHEO.md` | 288 |
| 7 năng lực C mà TH3+A không có + hướng tối ưu | `UU_THE_C_VA_HUONG_TOI_UU.md` | 358 |
| **Tổng** | | **~2743 dòng** |

---

## 3. Kết quả định lượng

### 3.1 Ranking 3 setup × FiniteState × 1 ep

| Setup | Reward | M2 invalid action rate | M5 latency | Note |
|---|---|---|---|---|
| **A** | **-660** | 80.0% (Sleep áp đảo) | 13.07 s/step | Pipeline TH3 nguyên bản, baseline |
| **C** | **-1515** | 0.6% (luôn action) | 31.83 s/step | MCP+RoE, đóng góp luận văn |
| **B** | **-2110** | 0.2% | 29.05 s/step | MCP only, ablation cô lập |

→ **Ranking**: A > C > B

→ **Khoảng cách**:
- C − B = +595 reward (RoE đóng góp tích cực)
- C − A = -855 reward (MCP+RoE chưa thắng baseline TH3)
- B − A = -1450 reward

### 3.2 Đường cong reward 10 mốc step

| Step | A | B | C |
|---|---|---|---|
| 50 | -105 | -115 | -95 (C dẫn) |
| 100 | -230 | -230 | -190 (C dẫn) |
| 150 | -415 | -560 | -480 |
| 200 | -460 | -695 | -675 |
| 250 | -490 | -900 | -815 |
| 300 | -490 (plateau) | -1105 | -905 |
| 350 | -510 | -1325 | -975 |
| 400 | -570 | -1575 | -1135 |
| 450 | -615 | -1810 | -1310 |
| **500** | **-660** | **-2110** | **-1515** |

### 3.3 Action distribution (so với TH3 paper Hình 7)

| Action | TH3 LLM o3-mini | TH3 RL KEEP | Setup A | Setup B | Setup C |
|---|---|---|---|---|---|
| Analyse | 13 | 267 | 95 (19.0%) | 248 (49.6%) | **412 (82.4%)** |
| DeployDecoy | 224 | 6 | 0 | 251 (50.2%) | 85 (17.0%) |
| Remove | 5 | 74 | 2 (0.4%) | 0 | 0 |
| BlockTrafficZone | 4 | 0 | 0 | 0 | 0 |
| Sleep | 0 | 291 | **400 (80%)** | 1 | 3 |
| Restore | 0 | 84 | **3 (0.6%)** | 0 | 0 |

### 3.4 So sánh với TH3 paper

| Kịch bản TH3 paper | Reward | Setup luận văn tương đương |
|---|---|---|
| No blue (sàn ác) | -6334 | — |
| All LLM (GPT-4o-mini) | -6334 | (gần Setup B nếu xóa baseline đồng đội) |
| All RL KEEP (sàn tốt) | -451 | — |
| 1 LLM (o3-mini) + 4 RL KEEP | ≈-500 | (gần Setup A nhưng đồng đội khác) |
| 1 LLM (4o-mini) + 4 RL KEEP | ≈-1850 | (gần Setup B/C) |
| 1 LLM (DeepSeek-V3) + 4 RL KEEP | ≈-2200 | (gần Setup B) |
| **1 LLM (Claude Haiku 4.5) + 4 ReactRemoveBlueAgent — A** | **-660** | LV |
| **1 LLM (Claude Haiku 4.5, MCP) + 4 ReactRemoveBlueAgent — B** | **-2110** | LV |
| **1 LLM (Claude Haiku 4.5, MCP+RoE) + 4 ReactRemoveBlueAgent — C** | **-1515** | LV |

---

## 4. Phân tích kết quả — Lý do ranking A > C > B

### 4.1 Tại sao A thắng (-660)

- 80% Sleep → 85.4% step reward = 0 (không bị phạt)
- 5 destructive đúng level (3 Restore admin + 2 Remove user) → loại bỏ threat hoàn toàn
- Khi BUỘC phải action, A làm ĐÚNG nhờ thấy IOC trực tiếp trong observation thô

### 4.2 Tại sao C ở giữa (-1515)

**Đóng góp tích cực**:
- 323 RoE deny / 322 retry thành công (99.7%) → tự sửa lỗi
- DeployDecoy phân bố đều khắp 52 host (vs B tập trung 1 host)
- Phòng thủ proactive subnet → 0 admin compromise (vs A để xảy ra 3 lần)

**Vấn đề**:
- 100% hostname C target là BỊA (`web-server`, `db-server`, …) thay vì hostname THẬT của CAGE 4 → bug do `get_threat_summary` chỉ trả threats có IOC, không trả full hostname list
- 0 destructive action (Restore/Remove) — RoE chặn 1 Restore duy nhất
- Chi phí ngầm của 497 action mỗi step

### 4.3 Tại sao B tệ nhất (-2110)

- 99.8% action nhưng không có destructive → threat tích lũy không cắt
- Cùng bị hostname hallucination như C
- Không có RoE redirect → tập trung DeployDecoy 1 host (web-server 57 lần)

---

## 5. Phát hiện QUAN TRỌNG cuối Sprint

### 5.1 Bug Hostname Hallucination

**Phát hiện** (qua câu hỏi của user "C có đang bịa hostname không?"): **100% hostname Setup C target là BỊA** — không có host nào khớp với observation thực tế.

**Nguyên nhân**: `get_threat_summary` chỉ trả `threats` (host có IOC). Khi observation không có IOC, tool trả về list rỗng → LLM Claude Haiku 4.5 (đã train trên web/cloud) tự bịa tên `web-server`, `db-server`, ... thay vì hỏi lại.

**Hệ quả**: phần lớn diễn giải về Setup B (-2110) và C (-1515) **bị nhiễu** bởi hallucination này. Setup A không bị vì observation thô có hostname THẬT.

### 5.2 Fix đã làm (chưa re-run)

| File | Thay đổi |
|---|---|
| `feasibility/state_extractor.py` | Thêm hàm `extract_all_hostnames()` + trường `all_hostnames` |
| `feasibility/tools.py` | `get_threat_summary` expose `available_hostnames`; `_propose()` validate hostname |
| `feasibility/prompt.md` | Thêm cảnh báo "PHẢI dùng tên từ available_hostnames, KHÔNG bịa" |
| `tests/test_hostname_validation.py` | 12 test mới (all pass) |

### 5.3 Bài học design

Bài học rút ra cho Chương 5 luận văn:

> *"Pre-parsed observation qua MCP phải tách bạch giữa **THREAT INFO** (host có IOC — nên filter) và **REFERENCE INFO** (hostname hợp lệ — KHÔNG được filter). Filter cả hai cùng lúc gây hallucination về vocabulary, dẫn đến LLM bịa tên không tồn tại — một dạng L1 cụ thể trong context MCP design."*

---

## 6. Đối chiếu với mục tiêu kế hoạch ban đầu

| Mục tiêu kế hoạch | Trạng thái | Ghi chú |
|---|---|---|
| Khảo sát 15-20 paper liên quan | ⚠️ Hạn chế | Tập trung sâu 2 paper TH3 + LT1 theo yêu cầu user |
| Tích hợp claude_policy vào CybORG đầy đủ 5 agent | ✅ Hoàn thành | 5 agent: 1 LLM (blue_agent_4) + 4 ReactRemoveBlueAgent |
| Draft Chương 2 (Tổng quan) | ⚠️ Chưa update | Có sẵn từ phase trước, cần update theo data Sprint 1 |
| Verify pipeline 500 step | ✅ Hoàn thành | 3 setup × 500 step không truncate |
| **Phụ thêm**: chạy benchmark pilot | ✅ Vượt kế hoạch | 3 episode × 500 step = 1500 step tổng |
| **Phụ thêm**: viết báo cáo so sánh | ✅ Vượt kế hoạch | 6 báo cáo tổng 2743 dòng |
| **Phụ thêm**: implement checkpoint resume | ✅ Vượt kế hoạch | Cloudpickle, mỗi 50 step |
| **Phụ thêm**: hostname validation + 12 test mới | ✅ Vượt kế hoạch | Fix bug phát hiện cuối Sprint |

→ **Sprint 1 đã vượt mục tiêu** ở mặt triển khai code + benchmark, nhưng **thiếu** ở khảo sát paper rộng.

---

## 7. Đề xuất cho Sprint 2

Theo kế hoạch ban đầu, Sprint 2 = "Benchmark đầy đủ + mở rộng RoE". Sau Sprint 1 cần điều chỉnh:

### 7.1 Việc CẦN làm trước trong Sprint 2

1. **Re-run Setup B và C sau khi đã fix hostname hallucination** → có data sạch
2. **Verify Setup C có thực sự cải thiện không** với hostname đúng
3. **Cập nhật các báo cáo** đã viết (đính chính phần bị nhiễu bởi hallucination)

### 7.2 Việc theo kế hoạch Sprint 2

1. Wire 8 rule v2 (đã có code + 13 test pass, chưa wire vào policy_engine)
2. Chạy n=5 episode cho mỗi setup × FiniteState
3. Chạy thêm 3 red variant khác (AggressiveFSM, StealthyFSM, ImpactFSM)
4. Mục tiêu: bảng 3 × 4 = 12 cell × n=5 ≈ 60 ep với μ ± σ

### 7.3 Việc đề xuất thêm (từ phân tích Sprint 1)

1. **Thêm tool `propose_sleep`** vào MCP — cho phép C Sleep khi không có threat → giảm chi phí ngầm action
2. **Thêm field `criticality`** vào `get_threat_summary` — LLM tránh host nhạy cảm
3. **Thêm rule SUGGEST Restore** khi host user-level lâu — cho C có cơ hội Restore preemptive
4. **Fix `CommVectorGenerator`** API mismatch — comm vector vẫn rỗng, không verify được L1
5. **Bật prompt caching** (`cache_control=True`) — giảm latency C từ 32s → 20s/step

---

## 8. Kết luận Sprint 1

**Thành công**:
- Pipeline 3 setup A/B/C chạy được đầy đủ 500 step không truncate
- Có dữ liệu pilot đầy đủ để viết báo cáo so sánh với TH3
- 36/36 unit test pass — code chất lượng OK
- Phát hiện và fix bug hostname hallucination nghiêm trọng trước khi viết luận văn cuối

**Hạn chế**:
- Mất ~3 ngày cho debug môi trường (CybORG install, ray, pyarrow, comm_vector, ...) — chi tiết trong `BAO_CAO_LOI_SPRINT_1.md`
- Mất ~4 giờ chạy lại Setup B do bug resume ghi đè log
- n=1 → variance cao, chưa kết luận được xu hướng A > C > B có ổn định không
- 1 red variant — chưa test 3 red khác

**Bài học chính**:
1. **Test resume + log path TRƯỚC khi chạy benchmark dài** — mất 3h Setup B v1 vì bug overwrite
2. **Cross-check observation thực tế VS observation LLM nhận** — phát hiện hallucination
3. **Pre-parsing trong MCP design** phải tách bạch threat info vs reference info
4. **n=1 không đủ kết luận** — cần n=5+ cho mọi cell trong bảng

**Trạng thái dữ liệu**:
- Setup A: ✅ Sạch, đáng tin (dữ liệu đại diện)
- Setup B: ⚠️ Bị nhiễu hallucination, cần re-run
- Setup C: ⚠️ Bị nhiễu hallucination, cần re-run

---

*Báo cáo dựa hoàn toàn vào kết quả thực thi 3 episode A/B/C × FiniteState × 1 ep và 6 báo cáo phân tích chi tiết trong cùng folder. Mọi số liệu trace ngược về JSONL artifact.*
