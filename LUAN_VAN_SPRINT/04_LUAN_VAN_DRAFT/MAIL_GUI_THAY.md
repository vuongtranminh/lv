**Tiêu đề email**: Báo cáo tiến độ luận văn + kế hoạch tập trung 3 tuần — xin ý kiến thầy

---

Kính gửi thầy,

Em xin gửi thầy báo cáo tiến độ luận văn và kế hoạch tập trung 3 tuần để xin ý kiến phê duyệt của thầy.

**Báo cáo chi tiết (đã đẩy lên GitHub)**:
<https://github.com/vuongtranminh/lv/blob/main/LUAN_VAN_SPRINT/04_LUAN_VAN_DRAFT/BAO_CAO_GUI_THAY_3_TUAN.md>

---

**Tóm tắt nội dung báo cáo**

Từ khi được thầy gợi ý đến nay, em đã thực hiện được ba pha công việc:

1. **Pha khảo sát và thiết kế**: đọc kỹ hai bài báo nền (TH3 và LT1), phân tích ba hạn chế của TH3 cần khắc phục (ảo giác đọc vectơ truyền thông 8 bit, lệ thuộc cách viết prompt, thiếu định hướng phần thưởng), thiết kế kiến trúc ba phương án thí nghiệm cô lập (Setup A — baseline TH3, Setup B — chỉ MCP, Setup C — MCP và RoE đầy đủ).

2. **Pha triển khai và chạy thử nghiệm đầu (Sprint 1)**: triển khai một bộ mã nguồn duy nhất với ba chế độ bật/tắt, chạy benchmark ba phương án trên red FiniteState (mỗi phương án một episode). Phát hiện 17 lỗi qua phân tích log chi tiết.

3. **Pha sửa lỗi và chạy lại (Sprint 2)**: sửa năm lỗi nghiêm trọng nhất, trong đó quan trọng nhất là lỗi LLM tự bịa tên hostname trong tool call. Chạy lại Setup C → reward đạt **−585**, **lần đầu vượt baseline TH3 +75 điểm** (Setup A: −660).

**Kết quả định lượng 4 lần chạy** (red FiniteState × 500 step):

| Phương án | Phiên bản | Reward |
|---|---|---|
| A (baseline TH3) | Sprint 1 | −660 |
| B (chỉ MCP) | Sprint 1 | −2110 |
| C (MCP + RoE) | Sprint 1 pre-fix | −1515 |
| **C (MCP + RoE)** | **Sprint 2 post-fix** | **−585** |

Reward −585 của Setup C nằm trong vùng tốt nhất TH3 báo cáo (gần với cấu hình 1 LLM o3-mini + 4 RL KEEP).

**Điểm mà MCP và RoE đã chứng minh được (có bằng chứng định lượng)**:
- Cấu trúc tool call chặt chẽ: 3938 tool call, 0 lần parse JSON thất bại.
- Cơ chế tự sửa lỗi: 322/323 lần (99.7%) LLM đề xuất hành động khác sau khi RoE từ chối.
- Khử ảo giác hostname: từ 100% bịa tên xuống 0%.
- Triệt tiêu vòng lặp hành động: 40 chuỗi Analyse lặp → 0 chuỗi.
- Khả năng giải thích: 8980–9774 sự kiện log mỗi episode, truy vết được từng quyết định — TH3 paper không có.

**Hạn chế còn lại em đã nêu rõ trong báo cáo**: mới có n=1 episode mỗi phương án, mới test 1 red duy nhất (FiniteState), Setup C phiên bản 2 đang quá thụ động (chọn Sleep nhiều).

**Sản phẩm hiện tại**: 1 bộ mã nguồn (đã commit 6 lần lên GitHub), 48 unit test pass, 10 báo cáo phân tích chi tiết (~3000 dòng), 7 chương luận văn draft.

---

**Kế hoạch tập trung 3 tuần**

- Thời gian: 54 giờ mỗi tuần (6 giờ ngoài giờ làm Thứ 2–6, 12 giờ Thứ 7 và Chủ Nhật) → tổng 162 giờ tập trung trong 3 tuần.
- **Tuần 1**: sửa prompt cân bằng Sleep và chủ động, chạy benchmark đầy đủ theo phương án thầy phê duyệt, trích metric M1–M5.
- **Tuần 2**: viết Chương 4 (Triển khai) và Chương 5 (Kết quả), merge 7 chương, gửi bản Word draft thầy review.
- **Tuần 3**: sửa theo feedback của thầy, dọn repository, nộp bản báo cáo hoàn chỉnh.
- Buffer dự phòng: có thể kéo sang đầu Tuần 4 nếu cần.

---

**Câu hỏi xin ý kiến thầy về phạm vi benchmark**

Bài báo TH3 báo cáo qua **5 red variant**. Em xin ý kiến thầy chọn giữa hai phương án:

| Phương án | Phạm vi | Số episode | Wall time |
|---|---|---|---|
| **1 — Đầy đủ** | 3 setup × 5 red × 2 episode | 30 episode | ~100 giờ |
| **2 — Tập trung Setup C** | A và B chỉ FiniteState × 2 ep + C đủ 5 red × 2 ep | 14 episode | ~52 giờ |

Em đề xuất **Phương án 2** vì Setup C là đóng góp khoa học chính cần verify đầy đủ 5 red, còn A và B chỉ là baseline tham chiếu. Tiết kiệm 50 giờ chạy để dành cho phân tích định tính (sample reasoning, case study chéo). Nếu thầy yêu cầu strict khớp TH3 thì em sẽ làm Phương án 1.

---

Em mong thầy xem báo cáo chi tiết tại đường dẫn GitHub ở trên và cho em ý kiến phê duyệt. Nếu thầy thấy phân bổ chưa hợp lý hoặc cần ưu tiên khía cạnh khác, em sẽ điều chỉnh ngay trong vòng 24 giờ.

Em cảm ơn thầy.

---

Trân trọng,
Trần Minh Vương
