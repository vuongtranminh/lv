# KẾ HOẠCH SPRINT 3 — THEO GÓP Ý CỦA THẦY

**Học viên**: Trần Minh Vương
**Ngày lập**: 2026-06-30
**Phạm vi**: Tuần 1 của kế hoạch 3 tuần
**Nguồn yêu cầu**: Email góp ý của thầy sau khi đọc báo cáo tiến độ tại [BAO_CAO_GUI_THAY_3_TUAN.md](https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_GUI_THAY_3_TUAN.md)

---

## 1. Mục tiêu Sprint 3

**Mục tiêu chính**: Chứng minh được Setup C (MCP + RoE) **không thắng chỉ vì "ngủ"** — tức là khẳng định được giá trị phòng thủ chủ động chứ không phải né phạt bằng Sleep.

**Mục tiêu phụ**: Đưa kết quả benchmark từ "một điểm reward" lên **chuẩn khoa học** — báo cáo mean ± std qua nhiều episode và nhiều red agent.

---

## 2. Phân tích yêu cầu của thầy → việc cần làm

Thầy yêu cầu 5 điểm. Em ánh xạ từng điểm sang nhiệm vụ kỹ thuật cụ thể:

| Yêu cầu của thầy | Việc Sprint 3 phải làm |
|---|---|
| 1. Setup C không thắng chỉ vì ngủ | Bổ sung Setup **C-active** với prompt/RoE buộc hành động khi có threat — so sánh với C-passive hiện tại |
| 2. Bảng phân phối action, tỷ lệ Sleep, số host can thiệp | Viết script `analyse_action_distribution.py` trích từ log JSON Lines — báo cáo riêng cho từng Setup |
| 3. Biến thể prompt/policy buộc hành động khi có threat | Tạo `prompt_active.md` + RoE rule `rule_no_sleep_when_threat` |
| 4. A vs C trên 2–5 episode FiniteState + ≥1 red khác | Chạy benchmark mở rộng: A và C (cả passive + active) × {FiniteState, AggressiveFSM} × 2–3 ep |
| 5. Báo cáo mean ± std thay vì 1 điểm | Viết script `aggregate_stats.py` — tổng hợp μ ± σ |

---

## 3. Phân rã công việc

### 3.1 Nhánh A — Triển khai Setup C-active (mới)

**Mục tiêu**: tạo biến thể buộc agent hành động khi có IOC, để loại trừ giả thuyết "C thắng vì ngủ".

| Task | File / vị trí | Ước lượng |
|---|---|---|
| A1. Viết `prompt_active.md` — bản prompt buộc hành động (cấm Sleep khi `recommended_action.priority ∈ {critical, high}`) | `feasibility/prompt_active.md` | 2h |
| A2. Thêm RoE rule `rule_no_sleep_when_threat` vào `rules_v2.py` — deny Sleep nếu `state.threats` không rỗng | `feasibility/roe/rules_v2.py` | 1h |
| A3. Thêm cờ `active_mode` vào `StepContext` + branch chọn prompt | `feasibility/context.py`, `claude_policy.py` | 2h |
| A4. Thêm 3 unit test cho C-active: (1) Sleep bị deny khi có threat; (2) Sleep allowed khi mạng sạch; (3) prompt_active được load đúng khi `active_mode=True` | `tests/test_c_active.py` (mới) | 1h |

**Acceptance**: 51/51 unit test pass (48 cũ + 3 mới), chạy thử 50 step Setup C-active không crash.

### 3.2 Nhánh B — Script phân tích phân phối hành động

**Mục tiêu**: trích số liệu định lượng từ log để bác bỏ "C ngủ 100%".

| Task | File / vị trí | Ước lượng |
|---|---|---|
| B1. Viết `analyse_action_distribution.py` — đọc `detailed_*.jsonl`, đếm action theo loại, tính tỷ lệ %, đếm host can thiệp distinct | `benchmark/analyse_action_distribution.py` | 3h |
| B2. Output: bảng CSV cho mỗi run + bảng tổng hợp Markdown | `benchmark/results/action_distribution_*.csv` | 1h |

**Schema bảng output cần trích**:

```
Setup, Red, Ep, # Sleep, # Analyse, # Remove, # Restore, # DeployDecoy, # Block,
% Sleep, # host distinct can thiệp, reward
```

**Acceptance**: chạy script trên 4 log Sprint 1+2 hiện có, sinh ra bảng đúng với 8980–9774 event/log.

### 3.3 Nhánh C — Script tổng hợp thống kê

**Mục tiêu**: từ N episode → mean ± std cho từng (Setup, Red).

| Task | File / vị trí | Ước lượng |
|---|---|---|
| C1. Viết `aggregate_stats.py` — đọc tất cả `joint_reward_*.json`, group theo (Setup, Red), tính μ, σ, min, max, n | `benchmark/aggregate_stats.py` | 2h |
| C2. Output: bảng Markdown final `KET_QUA_SPRINT_3.md` | `LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/KET_QUA_SPRINT_3.md` | 1h |

**Acceptance**: bảng cuối có ít nhất 1 cell với n ≥ 2 và σ tính ra được (không NaN).

### 3.4 Nhánh D — Chạy benchmark mở rộng

**Mục tiêu**: bổ sung dữ liệu để đạt yêu cầu thầy (2–5 ep × ≥2 red, A vs C).

Lộ trình benchmark Sprint 3 — **chạy nền 24/24 trong nền checkpoint mỗi 50 step**:

| Lần | Setup | Red | Episode | Wall time ước lượng |
|---|---|---|---|---|
| 5 | A | FiniteState | ep1 (seed 1) | 2h |
| 6 | C-passive | FiniteState | ep1 (seed 1) | 4h |
| 7 | C-active | FiniteState | ep0 (seed 0) | 4h |
| 8 | C-active | FiniteState | ep1 (seed 1) | 4h |
| 9 | A | AggressiveFSM | ep0 (seed 0) | 2h |
| 10 | C-passive | AggressiveFSM | ep0 (seed 0) | 4h |
| 11 | C-active | AggressiveFSM | ep0 (seed 0) | 4h |
| 12 (nếu kịp) | A, C-passive, C-active | AggressiveFSM | ep1 | 10h |

**Tổng wall time tối thiểu (lần 5–11)**: ~24h
**Tổng wall time tối đa (gồm lần 12)**: ~34h

**Acceptance**: tối thiểu có (Setup × Red) cell với n=2 cho A và cả hai biến thể C trên ≥1 red.

### 3.5 Nhánh E — Báo cáo Sprint 3

| Task | File | Ước lượng |
|---|---|---|
| E1. Viết `BAO_CAO_SPRINT_3.md` — kết quả mean ± std, bảng action distribution, so sánh C-passive vs C-active, trả lời trực diện từng góp ý của thầy | `LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_SPRINT_3.md` | 4h |
| E2. Cập nhật Chương 5 luận văn với số liệu mới | `LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/CHUONG_5_KET_QUA.md` | 3h |

---

## 4. Tiêu chí thành công của Sprint 3

Sprint 3 được coi là **thành công** khi và chỉ khi báo cáo cuối sprint **trả lời được 5 câu hỏi**:

1. **Setup C có thắng A nhờ ngủ không?** → trả lời bằng bảng phân phối action. Cần một trong hai kết luận:
   - **(a)** C-passive ngủ nhiều nhưng vẫn Restore ≥ K host khi có IOC admin (K ≥ 3) — C đã phòng thủ chủ động.
   - **(b)** C-passive ngủ 100% → công nhận giả thuyết "C thắng vì ngủ" đúng, và **C-active mới là setup so sánh hợp lệ với A**.
2. **C-active có thắng A không?** — câu hỏi quyết định giá trị luận văn. Yêu cầu so sánh μ ± σ.
3. **Kết quả có generalize sang red khác không?** — kiểm chứng trên AggressiveFSM. Nếu C-active thắng A trên cả 2 red → MCP+RoE có giá trị thật.
4. **Số liệu có ý nghĩa thống kê không?** — yêu cầu n ≥ 2 và σ < |μ_C - μ_A| / 2 (ít nhất nửa khoảng cách trung bình lớn hơn 1 σ).
5. **Hành vi phòng thủ phân bố ra sao?** — bảng phân phối 6 action × 3 Setup × 2 Red.

---

## 5. Lịch dự kiến

Tuần 1 của kế hoạch 3 tuần — phân ngày:

| Ngày | Việc chính |
|---|---|
| Thứ 2 (2026-07-06) | Nhánh A (A1–A4) — Setup C-active + test, ~6h |
| Thứ 3 (2026-07-07) | Nhánh B + C (B1–B2, C1–C2) — script phân tích, ~6h |
| Thứ 4 (2026-07-08) | Khởi động benchmark lần 5–7 chạy nền, song song debug nếu lỗi |
| Thứ 5 (2026-07-09) | Benchmark lần 8–9 |
| Thứ 6 (2026-07-10) | Benchmark lần 10–11 |
| Thứ 7 (2026-07-11) | Benchmark lần 12 (nếu cần) + bắt đầu viết E1 |
| Chủ Nhật (2026-07-12) | Hoàn thành E1 + E2 + gửi thầy số liệu cuối tuần |

Tổng workload dev + viết: ~25h. Benchmark chạy nền: ~24–34h. Khả thi trong quota 54h/tuần.

---

## 6. Rủi ro và phương án xử lý

| Rủi ro | Khả năng | Phương án xử lý |
|---|---|---|
| C-active prompt vẫn không phòng thủ tốt (reward kém hơn A) | Trung bình | Báo cáo trung thực + thử variant prompt v2 (vd: cho phép Sleep khi quota Restore cạn) |
| AggressiveFSM phá nhanh, A và C đều thua nặng → khó so sánh | Trung bình | Báo cáo cả 2 red, chấp nhận có cell C < A, đó là dữ liệu thật |
| Wall time vượt 34h | Thấp | Giảm xuống n=2 × 1 red khác, không chạy lần 12 |
| Action distribution cho thấy C-active vẫn Sleep nhiều | Thấp | Tinh chỉnh `rule_no_sleep_when_threat` cứng hơn — chạy lại |
| Phát hiện bug mới khi mở rộng | Trung bình | Áp dụng quy trình như Sprint 1: log → fix → unit test → re-run |

---

## 7. Sản phẩm bàn giao cuối Sprint 3

1. **Mã nguồn mới**: `prompt_active.md`, `rule_no_sleep_when_threat`, cờ `active_mode`, 3 unit test mới.
2. **Script phân tích**: `analyse_action_distribution.py`, `aggregate_stats.py`.
3. **Dữ liệu benchmark**: tối thiểu 7 episode mới (5–11) → đẩy tổng episode lên 11.
4. **Báo cáo**: `BAO_CAO_SPRINT_3.md` trả lời trực diện 5 câu hỏi mục 4.
5. **Cập nhật luận văn**: Chương 5 với bảng μ ± σ và bảng phân phối hành động.

---

## 8. Liên hệ ngược với kế hoạch 3 tuần

| Sprint | Tuần | Mục tiêu |
|---|---|---|
| **Sprint 3 (kế hoạch này)** | Tuần 1 | Triển khai góp ý thầy + chạy benchmark mở rộng + báo cáo số liệu |
| Sprint 4 | Tuần 2 | Viết Chương 4 + Chương 5 + bản Word phiên bản 1 gửi thầy review |
| Sprint 5 | Tuần 3 | Sửa theo feedback + nộp bản hoàn chỉnh |

---

**Cam kết**: Em sẽ gửi thầy `BAO_CAO_SPRINT_3.md` cuối Chủ Nhật 2026-07-12, kèm bảng μ ± σ và bảng phân phối action — trả lời trực diện 5 câu hỏi thầy đã đặt.
