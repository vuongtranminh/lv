# SPRINT 4 TUẦN — KẾ HOẠCH TỔNG THỂ

> Mục tiêu: hoàn thành toàn bộ luận văn + chuẩn bị bảo vệ trong 4 tuần tập trung.

---

## Giả định thời gian

- **Ngày thường (T2-T6)**: 3 giờ/ngày (sáng sớm hoặc tối) = **15 giờ/tuần**
- **Cuối tuần (T7, CN)**: 8-10 giờ/ngày = **16-20 giờ/tuần**
- **Tổng**: ~**30-35 giờ/tuần × 4 tuần = 120-140 giờ tập trung**

Nếu em không đảm bảo được 30 giờ/tuần → kéo sang 5-6 tuần, KHÔNG giãn sang 30 tuần.

---

## Bảng tổng thể 4 tuần

| Tuần | Mục tiêu chính | Sản phẩm cuối tuần |
|---|---|---|
| **1** | Khảo sát related work + tích hợp CybORG | Draft Chương 2 + code chạy full episode |
| **2** | Mở rộng RoE + chạy benchmark đầy đủ | Bảng số liệu raw + audit log 60 episode |
| **3** | Phân tích + viết Chương 3, 4, 5 | 3 chương draft xong |
| **4** | Viết Chương 1, 2, 6 + slides + bảo vệ | Bản nộp + slides + demo |

---

## Checkpoint cuối mỗi tuần

Mỗi Chủ Nhật, gửi thầy email ngắn (~10 dòng) báo:
1. Đã làm xong gì (checklist tuần đó)
2. Còn vướng gì
3. Tuần sau định làm gì
4. Có cần thầy hướng dẫn gì không

→ Tránh để thầy mất liên lạc, cũng tạo áp lực bản thân tiếp tục đúng tiến độ.

---

## Chi tiết từng tuần

### TUẦN 1 — Khảo sát + Tích hợp (đọc `TUAN_1.md`)

**Mục tiêu**:
- Khảo sát ~15-20 paper liên quan (Llama Guard, NeMo Guardrails, OPA, CAGE submissions, MCP agents, etc.)
- Tích hợp `claude_policy.py` vào CybORG submission đầy đủ 5 agent
- Draft Chương 2 (Tổng quan tình hình nghiên cứu)

**Phân bổ**:
- T2-T4 (9h): Khảo sát + đọc paper
- T5-T6 (6h): Wire CybORG integration
- T7-CN (16h): Hoàn thiện Chương 2 draft + verify pipeline 500 step

### TUẦN 2 — Benchmark (đọc `TUAN_2.md`)

**Mục tiêu**:
- Mở rộng RoE từ 3 lên 8 rule + unit test
- Chạy benchmark 60 episode (3 setup × 4 red × 5 ep)
- Thu thập audit log, CSV data

**Phân bổ**:
- T2-T3 (6h): Mở rộng RoE + viết unit test
- T4-T5 (6h): Chạy batch episode 1 (15-20 episode)
- T6-CN (24h): Chạy batch episode 2-3 (hết 60 episode) + xem log

### TUẦN 3 — Phân tích + Viết (đọc `TUAN_3.md`)

**Mục tiêu**:
- Phân tích định lượng theo 4 RQ
- Cluster reasoning bằng K-Means
- Viết Chương 3, 4, 5

**Phân bổ**:
- T2 (3h): Phân tích số liệu RQ1-RQ4
- T3 (3h): Cluster + figure
- T4-T5 (6h): Viết Chương 4 (Triển khai & Thực nghiệm)
- T6 (3h): Viết Chương 5 (Kết quả)
- T7-CN (16h): Viết Chương 3 (Thiết kế) — chương dài nhất

### TUẦN 4 — Hoàn thiện + Bảo vệ (đọc `TUAN_4.md`)

**Mục tiêu**:
- Viết Chương 1, 6
- Sửa Chương 2 theo những gì học thêm trong Tuần 1-3
- Format toàn bộ luận văn
- Slides bảo vệ + demo

**Phân bổ**:
- T2 (3h): Viết Chương 1 + 6
- T3 (3h): Sửa Chương 2 + abstract
- T4 (3h): Format full + citation
- T5 (3h): Slides
- T6 (3h): Demo video
- T7-CN (8h): Bảo vệ thử + sửa cuối

---

## Bảng phụ thuộc (dependency)

```
Tuần 1: Khảo sát ──┐
                   ├──> Tuần 3: Viết Chương 2 (cập nhật từ Tuần 1)
Tuần 1: CybORG int ┘
                   │
                   ├──> Tuần 2: Benchmark
                   │
                   ├──> Tuần 3: Phân tích → Viết Chương 3, 4, 5
                   │
                   └──> Tuần 4: Chương 1, 6 + Slides
```

**Block nguy hiểm nhất**: nếu Tuần 1 không tích hợp CybORG xong → Tuần 2 không chạy benchmark được → toàn bộ Tuần 3 trống.

→ **Phương án phòng**: nếu cuối Tuần 1 thấy CybORG khó tích hợp hơn dự kiến, **chuyển sang chạy benchmark trên scenario giả** (mở rộng scenario test có sẵn ở Bước 1). Số liệu sẽ yếu hơn nhưng vẫn có để viết Chương 5.

---

## Cắt scope nếu kẹt thời gian

Theo thứ tự **cắt trước**:

1. Demo video (Tuần 4) — không bắt buộc
2. Cluster reasoning (Tuần 3) — vẫn viết Chương 5 nhưng bỏ phần định tính
3. Red variants 4 → 2 (Tuần 2) — giảm 60 → 30 episode
4. Phụ lục — gộp vào Chương 4 nếu thiếu thời gian
5. Chương 6 → ngắn 1 trang thay vì 3-5

**KHÔNG cắt**:
- Chương 2 (literature review) — thầy đánh giá nặng phần này
- Chương 3 (thiết kế) — đóng góp chính của luận văn
- Bảng so sánh A/B/C — bằng chứng định lượng

---

## File hỗ trợ

| File | Nội dung |
|---|---|
| `TUAN_1.md` ... `TUAN_4.md` | Checklist chi tiết từng ngày |
| `NHAT_KY.md` | Log hàng ngày (tự update) |
| `04_LUAN_VAN_DRAFT/CHUONG_*.md` | Template chương — fill in khi viết |
| `02_TAI_LIEU_NEN_TANG/DANH_SACH_PAPER.md` | Danh sách paper Tuần 1 |
