# BÁO CÁO TIẾN ĐỘ LUẬN VĂN + KẾ HOẠCH TẬP TRUNG 3 TUẦN

**Học viên**: Trần Minh Vương

**Đề tài**: Tích hợp Giao thức ngữ cảnh mô hình (Model Context Protocol — MCP) và Quy tắc giao chiến (Rules of Engagement — RoE) vào tác nhân phòng thủ mạng dùng Mô hình ngôn ngữ lớn — mở rộng bài báo *Large Language Models are Autonomous Cyber Defenders* (Castro và cộng sự, IEEE CAI 2025).

**Repository mã nguồn**: <https://github.com/vuongtranminh/lv>

---

## 1. Tóm lược kết quả

Từ khi được thầy gợi ý đến nay, em đã thực hiện được ba pha công việc:

- **Pha khảo sát + thiết kế**: đọc kỹ hai bài báo nền (TH3 và LT1), phân tích ba hạn chế của bài báo TH3 cần khắc phục (ảo giác đọc vectơ truyền thông 8-bit, lệ thuộc cách viết prompt, thiếu định hướng phần thưởng), thiết kế kiến trúc ba phương án thí nghiệm (Setup A — baseline TH3, Setup B — chỉ MCP, Setup C — MCP và RoE đầy đủ).
- **Pha triển khai và chạy thử nghiệm đầu (Sprint 1)**: triển khai một bộ mã nguồn duy nhất với ba chế độ bật/tắt, chạy benchmark thử nghiệm ba phương án trên red FiniteStateRedAgent (mỗi phương án một episode). Phát hiện 17 lỗi qua phân tích log chi tiết.
- **Pha sửa lỗi và chạy lại (Sprint 2)**: sửa năm lỗi nghiêm trọng nhất (đặc biệt lỗi LLM tự bịa tên hostname trong tool call), thêm các quy tắc RoE mới, thêm tool cho phép LLM ngừng hành động khi mạng sạch. Chạy lại Setup C → reward đạt **−585**, **lần đầu vượt baseline TH3 +75 điểm** (Setup A: −660).

**Sản phẩm**: 1 bộ mã nguồn (đã commit 5 lần lên GitHub), 48 unit test pass, 10 báo cáo phân tích chi tiết (~3000 dòng), 7 chương luận văn draft.

---

## 2. Đã làm được những gì — chi tiết theo từng pha

### 2.1 Pha khảo sát + thiết kế

- Đọc kỹ hai bài báo nền:
  - **TH3** — *Large Language Models are Autonomous Cyber Defenders* (Castro và cộng sự, IEEE CAI 2025)
  - **LT1** — bài báo về cách tiếp cận lý thuyết quyết định cho phản ứng mạng tự động
- Phân tích **ba hạn chế** của bài báo TH3 mà luận văn cần khắc phục:
  - **Hạn chế thứ nhất**: LLM ảo giác khi đọc vectơ truyền thông 8 bit (mỗi tác nhân broadcast 8 bit thông tin trạng thái) — LLM hiểu sai vị trí bit
  - **Hạn chế thứ hai**: LLM lệ thuộc vào cách viết prompt, dễ vào vòng lặp hành động không có ngưỡng dừng
  - **Hạn chế thứ ba**: Không có cơ chế chính sách bắt buộc các hành động phá hủy (như Restore wipe host) phải có điều kiện đủ
- Thiết kế kiến trúc ba phương án thí nghiệm cô lập (ablation study):
  - **Setup A** — baseline TH3, single-shot prompt, LLM tự decode bit
  - **Setup B** — Setup A cộng thêm MCP tool calling (chưa có RoE)
  - **Setup C** — Setup B cộng thêm RoE (đóng góp đầy đủ của luận văn)
- Cài đặt môi trường mô phỏng CybORG CAGE 4 trên máy local, tích hợp với mô hình Claude Haiku 4.5 thông qua thư viện claude-agent-sdk của Anthropic

### 2.2 Pha triển khai (Sprint 1)

- Triển khai **một bộ mã nguồn duy nhất**, ba phương án bật/tắt bằng cờ chế độ (mcp_enabled, roe_enabled) — tránh trùng lặp code
- Triển khai 4 MCP tool cho LLM gọi: get_threat_summary, get_comms_decoded, propose_analyse, propose_restore, propose_deploy_decoy, propose_block_traffic
- Triển khai 3 RoE rule phiên bản 1 + 8 RoE rule phiên bản 2 (phiên bản 2 chỉ wire vào engine ở Sprint 2)
- Cơ chế lưu điểm checkpoint giữa episode + resume an toàn (dùng thư viện cloudpickle)
- Bộ ghi log chi tiết theo định dạng JSON Lines, ghi từng tool call, từng phán quyết RoE, từng hành động cuối cùng
- Chạy benchmark thử nghiệm — 3 phương án trên red FiniteState × 1 episode × 500 step:

| Lần chạy | Phương án | Reward cuối | Wall time |
|---|---|---|---|
| 1 | A (baseline tái hiện TH3) | **−660** | 1 giờ 49 phút |
| 2 | B (chỉ MCP) | **−2110** | 4 giờ 04 phút |
| 3 | C phiên bản 1 (MCP + RoE pre-fix) | **−1515** | 4 giờ 26 phút |

### 2.3 Pha phân tích lỗi + sửa chữa (Sprint 2)

Qua phân tích log chi tiết của 3 lần chạy, em phát hiện **17 lỗi** chia thành 5 nhóm:
- Nhóm A — môi trường cài đặt (5 lỗi): script cài thiếu Python, gói thư viện xung đột phiên bản, v.v.
- Nhóm B — tích hợp API của CybORG (3 lỗi): baseline blue agent crash với IP runtime, mismatch chữ ký hàm step, v.v.
- Nhóm C — ghi log + resume (3 lỗi nghiêm trọng): ghi đè log khi resume, mất 350 step log
- Nhóm D — thiết kế kỹ thuật (3 lỗi quan trọng nhất): **LLM tự bịa tên hostname**, RoE thiếu cơ chế gợi ý chủ động, LLM vòng lặp Analyse không có ngưỡng dừng
- Nhóm E — phán đoán + giả định sai (3 lỗi): suy diễn không khớp dữ liệu thực

**Năm lỗi nghiêm trọng nhất đã được sửa**:

| # | Lỗi | Trạng thái sửa |
|---|---|---|
| 1 | LLM phương án B và C tự **bịa tên hostname 100%** (vd: `web-server` thay vì tên thật `office_network_subnet_user_host_1`) | Đã sửa: thêm field `available_hostnames` vào tool result + kiểm tra hostname trong `_propose()` + 12 unit test mới |
| 2 | RoE chỉ "từ chối" (deny), không "đề xuất chủ động" (suggest) — LLM không biết phải Restore khi cần | Đã sửa: thêm hàm `recommend_next_action()` trả về action gợi ý theo mức ưu tiên (critical / high / low) |
| 3 | LLM Setup A lặp Analyse cùng host 74 lần liên tiếp khi thấy IOC cmd.sh — không leo lên Remove | Đã sửa: cập nhật prompt thêm quy tắc "phản ứng theo mức IOC" + ngưỡng "không Analyse cùng host quá 2 lần" |
| 4 | Thiếu tool `propose_sleep` (không cho phép LLM ngủ khi mạng sạch) và `propose_remove` (Remove user-level không exposed riêng) | Đã sửa: thêm 2 tool mới vào MCP server |
| 5 | Phiên bản 2 với 8 quy tắc RoE đã có code + 13 test pass nhưng chưa wire vào engine | Đã sửa: chuyển policy_engine sang phiên bản 2, cập nhật import |

**Tổng bộ test**: 48/48 pass (24 cũ + 12 hostname validation + 12 Sprint 2 fixes).

### 2.4 Chạy lại Setup C sau khi sửa (Sprint 2)

Sau khi sửa 5 lỗi trên, em chạy lại Setup C trên cùng cấu hình (red FiniteState, seed 0):

| Phương án | Reward cuối | Wall time | So với Setup A baseline |
|---|---|---|---|
| Setup C phiên bản 2 (post-fix) | **−585** | 3 giờ 59 phút | **+75 điểm (lần đầu vượt baseline TH3)** |

**Cải thiện so với Setup C phiên bản 1**: +930 điểm reward (từ −1515 lên −585).

---

## 3. Kết quả định lượng và định tính

### 3.1 Bảng tổng hợp 4 lần chạy

| Lần chạy | Phương án | Phiên bản code | Reward | Wall time |
|---|---|---|---|---|
| 1 | A (baseline TH3) | Sprint 1 | **−660** | 1 giờ 49 phút |
| 2 | B (chỉ MCP) | Sprint 1 | −2110 | 4 giờ 04 phút |
| 3 | C (MCP + RoE) | Sprint 1 — pre-fix | −1515 | 4 giờ 26 phút |
| 4 | C (MCP + RoE) | Sprint 2 — post-fix | **−585** | 3 giờ 59 phút |

So với các kịch bản TH3 paper báo cáo (Hình 4 và Hình 5):
- Sàn ác — không có blue agent: −6334
- Sàn tốt — toàn bộ blue là RL KEEP: −451
- 1 LLM o3-mini + 4 RL KEEP: ≈−500
- 1 LLM GPT-4o-mini + 4 RL KEEP: ≈−1850

→ Setup C phiên bản 2 của luận văn (−585) **nằm trong vùng tốt nhất của TH3**, gần với cấu hình "1 LLM o3-mini + 4 RL KEEP".

### 3.2 Điểm mà MCP và RoE đã chứng minh được — có bằng chứng định lượng

- **Cấu trúc tool call chặt chẽ**: 3938 tool call qua hai phương án có MCP, 0 lần parse JSON thất bại
- **Cơ chế tự sửa lỗi**: 322 trên 323 lần (99.7%) LLM đề xuất hành động khác sau khi RoE từ chối
- **Khử ảo giác hostname**: từ 100% bịa tên xuống 0%
- **Triệt tiêu vòng lặp hành động**: Setup C phiên bản 1 có 40 chuỗi Analyse cùng host, sau khi sửa Sprint 2 còn 0 chuỗi
- **Phân phối phòng thủ đều khắp 50 host** (defense in depth) thay vì tập trung 1 host
- **Khả năng giải thích**: 8980 đến 9774 sự kiện log mỗi episode, truy vết được từng quyết định — TH3 paper không có

### 3.3 Hạn chế còn lại

- **Chưa kiểm chứng MCP + RoE vượt TH3 trong điều kiện kiểm soát**: cùng seed nhưng môi trường tiến triển khác giữa các phương án (do hành động blue agent khác nhau → red tấn công host khác nhau), nên không so sánh trực tiếp 1-1 được
- **Mới có n=1 episode** mỗi phương án, chưa có khoảng tin cậy thống kê (cần n=2 hoặc n=5)
- **Mới test 1 red duy nhất** (FiniteState), chưa test AggressiveFSM / StealthyFSM / ImpactFSM / DegradeServiceFSM
- **Hạn chế thứ nhất của TH3 (ảo giác bit) chưa kiểm chứng trực tiếp**: vectơ truyền thông trong môi trường thử nghiệm luôn rỗng (chưa kích hoạt được)
- **Setup C phiên bản 2 có hành vi quá thụ động**: 500/500 step đều chọn Sleep — cần điều chỉnh prompt cho cân bằng hơn giữa Sleep và hành động chủ động

---

## 4. Danh sách tài liệu kèm theo (đường dẫn GitHub)

### 4.1 Các chương luận văn (draft hiện tại)

| File | Mô tả | Đường dẫn |
|---|---|---|
| Chương 1 — Mở đầu | Giới thiệu đề tài, mục tiêu, đóng góp | [CHUONG_1_MO_DAU.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_1_MO_DAU.md) |
| Chương 2 — Tổng quan | Khảo sát TH3, LT1, các bài liên quan | [CHUONG_2_TONG_QUAN.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_2_TONG_QUAN.md) |
| Chương 3 — Thiết kế | Kiến trúc 3 phương án A/B/C, cô lập biến | [CHUONG_3_THIET_KE.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_3_THIET_KE.md) |
| Chương 4 — Triển khai | Cài đặt code, MCP tool, RoE rule | [CHUONG_4_TRIEN_KHAI.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_4_TRIEN_KHAI.md) |
| Chương 5 — Kết quả | Template chờ fill data benchmark đầy đủ | [CHUONG_5_KET_QUA.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_5_KET_QUA.md) |
| Chương 6 — Kết luận | Tổng kết đóng góp, hạn chế, hướng phát triển | [CHUONG_6_KET_LUAN.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_6_KET_LUAN.md) |
| Phụ lục | Cách reproduce, tham chiếu TH3 paper | [PHU_LUC.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/PHU_LUC.md) |
| Bản gộp đầy đủ | 7 chương merge thành 1 file | [LUAN_VAN_FULL.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/LUAN_VAN_FULL.md) |

### 4.2 Báo cáo phân tích chi tiết từ benchmark (~3000 dòng)

| File | Mô tả | Đường dẫn |
|---|---|---|
| Báo cáo Setup A | Phân tích chi tiết Setup A, so sánh với TH3 paper | [BAO_CAO_SETUP_A.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_SETUP_A.md) |
| Báo cáo Setup B | Phân tích Setup B (chỉ MCP), so sánh với Setup A và TH3 | [BAO_CAO_SETUP_B.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_SETUP_B.md) |
| Báo cáo Setup C | Phân tích Setup C (MCP + RoE), so sánh tay tư A/B/C/TH3 | [BAO_CAO_SETUP_C.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_SETUP_C.md) |
| Phân tích reward | Cơ chế tính reward, vì sao A/B/C được điểm như vậy | [PHAN_TICH_REWARD.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/PHAN_TICH_REWARD.md) |
| Case study chéo | So sánh A/B/C tại các step quan trọng (cùng step, khác quyết định) | [CASE_STUDY_CHEO.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CASE_STUDY_CHEO.md) |
| Ưu thế Setup C và hướng tối ưu | 7 năng lực C có mà TH3 không có + 7 hướng cải thiện | [UU_THE_C_VA_HUONG_TOI_UU.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/UU_THE_C_VA_HUONG_TOI_UU.md) |
| Báo cáo Sprint 1 | Tổng kết công việc Sprint 1, sản phẩm và số liệu | [BAO_CAO_SPRINT_1.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_SPRINT_1.md) |
| Báo cáo 17 lỗi Sprint 1 | 17 lỗi chia 5 nhóm, nguyên nhân, khắc phục, bài học | [BAO_CAO_LOI_SPRINT_1.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_LOI_SPRINT_1.md) |
| Báo cáo Sprint 2 | Tổng kết 5 fix + re-run Setup C, phân tích nghịch lý phát hiện qua log | [BAO_CAO_SPRINT_2.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_SPRINT_2.md) |
| Tổng kết 2 sprint | Ưu/nhược điểm, MCP+RoE thực sự làm được gì | [BAO_CAO_TONG_KET_2_SPRINT.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_TONG_KET_2_SPRINT.md) |

### 4.3 Mã nguồn

| Thư mục / file | Mô tả | Đường dẫn |
|---|---|---|
| Mã nguồn chính | Toàn bộ implementation MCP + RoE | [feasibility-mcp-roe/](https://github.com/vuongtranminh/lv/tree/main/feasibility-mcp-roe) |
| Driver chính | Class ClaudeDefenderPolicy — 3 phương án bật/tắt | [claude_policy.py](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/feasibility/claude_policy.py) |
| MCP tool | 6 tool: get_threat_summary, get_comms_decoded, propose_* | [tools.py](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/feasibility/tools.py) |
| RoE rule phiên bản 2 | 8 rule (4 precondition + 4 rate-limit) | [roe/rules_v2.py](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/feasibility/roe/rules_v2.py) |
| Prompt MCP | System prompt cho Setup B và C | [prompt.md](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/feasibility/prompt.md) |
| Prompt paper-style | System prompt cho Setup A (theo TH3 paper) | [paper_style.py](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/feasibility/paper_style.py) |
| Bộ ghi log chi tiết | Ghi mọi event định dạng JSON Lines | [detailed_logger.py](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/feasibility/detailed_logger.py) |
| Runner benchmark | Chạy 3 phương án × N red × M episode, có checkpoint | [run_benchmark.py](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/run_benchmark.py) |
| Test unit | 48 test, 4 file | [tests/](https://github.com/vuongtranminh/lv/tree/main/feasibility-mcp-roe/tests) |

### 4.4 Dữ liệu benchmark thô (log JSON Lines, 32000+ event)

| File | Mô tả | Đường dẫn |
|---|---|---|
| Log Setup A | 3602 event của lần chạy A | [detailed_A_FiniteState_ep0.jsonl](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/detailed_A_FiniteState_ep0.jsonl) |
| Log Setup B | 8538 event của lần chạy B | [detailed_B_FiniteState_ep0.jsonl](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/detailed_B_FiniteState_ep0.jsonl) |
| Log Setup C phiên bản 1 | 9774 event (pre-fix) | [detailed_C_FiniteState_ep0_sprint1.jsonl](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/detailed_C_FiniteState_ep0_sprint1.jsonl) |
| Log Setup C phiên bản 2 | 8980 event (post-fix) | [detailed_C_FiniteState_ep0.jsonl](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/detailed_C_FiniteState_ep0.jsonl) |
| Tổng kết Setup A | Reward + step rewards + meta | [joint_reward_A_FiniteState_ep0.json](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/joint_reward_A_FiniteState_ep0.json) |
| Tổng kết Setup B | Tương tự | [joint_reward_B_FiniteState_ep0.json](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/joint_reward_B_FiniteState_ep0.json) |
| Tổng kết Setup C phiên bản 1 | Tương tự | [joint_reward_C_FiniteState_ep0_sprint1.json](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/joint_reward_C_FiniteState_ep0_sprint1.json) |
| Tổng kết Setup C phiên bản 2 | Tương tự | [joint_reward_C_FiniteState_ep0.json](https://github.com/vuongtranminh/lv/blob/main/feasibility-mcp-roe/benchmark/results/joint_reward_C_FiniteState_ep0.json) |

### 4.5 Lịch sử commit GitHub

| Commit hash | Mô tả | Thời gian |
|---|---|---|
| `18fc1c1` | Sprint 2 re-run Setup C: reward −585 (vượt A +75) + báo cáo trung thực | Mới nhất |
| `5408b07` | Sprint 2 fixes: tool propose_sleep/remove + 8 rule v2 + recommended_action + báo cáo Sprint 1 | |
| `684f063` | Fix hostname hallucination: LLM B/C bịa tên host khi tool thiếu reference | |
| `e577f40` | Lưu trữ đầy đủ: TH3 paper PDF + cage-challenge-4 (CybORG core) | |
| `3e10121` | Phase 0: Benchmark ablation MCP+RoE (Setup A/B/C × FiniteState × 1 ep) | |

Lịch sử đầy đủ: <https://github.com/vuongtranminh/lv/commits/main>

---

## 5. Kế hoạch tập trung 3 tuần

### 5.1 Thời gian

| Khung giờ | Thời gian |
|---|---|
| Thứ 2 đến Thứ 6 (ngoài giờ làm việc) | **6 giờ mỗi ngày** |
| Thứ 7 và Chủ Nhật | **12 giờ mỗi ngày** |
| **Tổng mỗi tuần** | **54 giờ** |
| **Tổng 3 tuần** | **162 giờ tập trung** |

### 5.2 Mục tiêu sản phẩm cuối (deadline cuối tuần thứ 3)

1. **Bản nộp báo cáo luận văn hoàn chỉnh**
2. **Bảng số liệu benchmark đầy đủ** — em xin ý kiến thầy về phương án
3. **Repository mã nguồn public-ready** trên GitHub

### 5.3 Lịch 3 tuần

#### Tuần 1 — Hoàn thiện mã nguồn + Chạy benchmark đầy đủ

**Mục tiêu cuối tuần**: hoàn thành benchmark theo phương án thầy phê duyệt + bảng số liệu metric.

Các việc cần làm trong tuần:
- Sửa prompt để LLM cân bằng giữa Sleep và chủ động (khắc phục vấn đề Setup C phiên bản 2 chọn Sleep 100% trong 500 step). Thêm quy tắc "phải Analyse ít nhất 1 lần mỗi 5 step"
- Inject quan sát tổng hợp có IOC để kiểm tra Setup C có ra Restore khi thấy admin compromise thật
- Chạy benchmark Setup A, B, C trên các red theo phương án (xem mục 6 — xin ý kiến thầy)
- Tổng hợp số liệu + extract metric M1 đến M5 (Joint reward, Invalid action rate, RoE deny rate, Comms misread rate, Step latency) ra file CSV
- Viết script phân cụm reasoning (K-Means + PCA) tương đương TH3 §IV.A Bảng IV

**Deadline cuối Tuần 1**: file số liệu benchmark + bảng tóm tắt μ ± σ cho từng cell.

#### Tuần 2 — Viết Chương 4 (Triển khai) + Chương 5 (Kết quả)

**Mục tiêu cuối tuần**: hai chương quan trọng nhất của luận văn đã hoàn thiện.

Các việc cần làm trong tuần:
- Viết Chương 5 — Kết quả: bảng số liệu, đường cong reward, phân tích định tính, sample reasoning, đánh giá đa metric, so sánh với TH3 paper
- Viết Chương 4 — Triển khai: kiến trúc chi tiết, code path, design decisions, phần "lỗi đã gặp + bài học design"
- Cập nhật Chương 1, 2, 3 cho khớp với số liệu Sprint 2 và Tuần 1 mới
- Merge 7 chương → bản gộp LUAN_VAN_FULL.md, convert sang docx, review tổng

**Deadline cuối Tuần 2**: bản luận văn Word phiên bản 1 và gửi thầy review.

#### Tuần 3 — Hoàn thiện + Review + Nộp báo cáo

**Mục tiêu cuối tuần**: bản nộp báo cáo luận văn hoàn chỉnh.

Các việc cần làm trong tuần:
- Review toàn bộ 6 chương, sửa lỗi đánh máy + format
- Bổ sung Phụ lục: tham chiếu chi tiết đến TH3 paper (trang, mục, hình), liệt kê 48 unit test, lệnh reproduce
- Bổ sung Tài liệu tham khảo: thông tin đầy đủ tác giả/năm/venue cho TH3 và LT1
- Sửa cuối theo feedback của thầy cuối Tuần 2 (nếu có)
- Dọn repository: README đầy đủ, file .gitignore sạch, tag phiên bản v1.0
- Convert bản gộp sang docx + kiểm tra format Word
- Nộp bản hoàn chỉnh cho thầy

**Deadline cuối Tuần 3**: NỘP BÁO CÁO LUẬN VĂN.

### 5.4 Buffer dự phòng

Có thể kéo dài sang đầu Tuần 4 nếu cần fix bug benchmark hoặc bù chương chưa hoàn thiện. Tổng tối đa: 4 tuần.

### 5.5 Báo cáo định kỳ với thầy

- **Cuối Tuần 1**: gửi email báo cáo số liệu benchmark + bảng tóm tắt
- **Cuối Tuần 2**: gửi draft luận văn Word phiên bản 1 cho thầy review
- **Cuối Tuần 3**: nộp bản hoàn chỉnh

---

## 6. Câu hỏi xin ý kiến thầy về phạm vi benchmark

Bài báo TH3 (mục IV.A Hình 5) báo cáo reward qua **5 red variant**: FiniteState, AggressiveFSM, StealthyFSM, ImpactFSM, DegradeServiceFSM. Em đang phân vân giữa hai phương án:

| Phương án | Phạm vi | Số episode | Wall time chạy | Ưu / Nhược |
|---|---|---|---|---|
| **Phương án 1 — Đầy đủ** | 3 phương án × 5 red × 2 episode | **30 episode** | ~100 giờ | Khớp 100% TH3 paper, có bảng đầy đủ μ ± σ cho cả A, B, C |
| **Phương án 2 — Tập trung Setup C** | A + B chỉ chạy FiniteState × 2 ep (4 ep) + C chạy 5 red × 2 ep (10 ep) | **14 episode** | ~52 giờ | Setup C (đóng góp chính) verify robust qua 5 red. A và B chỉ làm baseline tham chiếu. Tiết kiệm 50 giờ chạy → dành cho phân tích sâu |

**Lý do em đề xuất Phương án 2**:
- Setup A và B chủ yếu để chứng minh "MCP + RoE > baseline" — chỉ cần 1 red đại diện là đủ
- Setup C là phần đóng góp khoa học chính → cần verify đầy đủ 5 red như TH3
- Tiết kiệm 50 giờ chạy → dành cho phân tích định tính (sample reasoning, case study chéo) — đây mới là phần "khác biệt" của luận văn so với TH3

**Em mong thầy cho ý kiến**:
- Nếu thầy yêu cầu strict khớp TH3 paper → em sẽ làm Phương án 1 (30 episode)
- Nếu thầy ưu tiên chiều sâu phân tích hơn chiều rộng benchmark → em sẽ làm Phương án 2 (14 episode)

---

## 7. Rủi ro và phương án dự phòng

| Rủi ro | Khả năng | Phương án xử lý |
|---|---|---|
| Benchmark chạy vượt thời gian dự kiến (52-100 giờ) | Trung | Chạy nền 24/24 giờ + đã có cơ chế checkpoint resume an toàn |
| Phát hiện thêm bug khi chạy benchmark đầy đủ | Trung | Đã có 48 unit test + báo cáo lỗi chi tiết để truy nguồn nhanh |
| Claude API gặp rate-limit | Thấp | Premium seat có quota cao, có thể chia phiên |
| Máy local crash giữa benchmark | Thấp | Checkpoint mỗi 50 step + resume đã verified |
| Yêu cầu chỉnh sửa Tuần 3 | Trung | Có buffer sang Tuần 4 |

---

## 8. Cam kết

Em cam kết:

1. **Tập trung liên tục 3 tuần** với lịch trên — không gián đoạn vì việc khác
2. **Báo cáo định kỳ cuối tuần** qua email cho thầy
3. **Đáp ứng deadline cuối Tuần 3** — nộp bản báo cáo luận văn hoàn chỉnh
4. **Tiếp nhận góp ý của thầy** — sửa theo feedback trong vòng 24 giờ

Em xin gửi thầy báo cáo này để xin ý kiến phê duyệt. Nếu thầy thấy phân bổ chưa hợp lý hoặc cần ưu tiên khía cạnh khác, em sẽ điều chỉnh ngay trong vòng 24 giờ.

Em cảm ơn thầy.

---

**Học viên**: Trần Minh Vương