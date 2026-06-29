# SLIDES OUTLINE — Bảo vệ luận văn

> Dự kiến: 15-20 slide, thời lượng ~15-20 phút trình bày + 10 phút Q&A.

## Slide 1 — Title

- **Tên đề tài**
- Học viên: Trần Minh Vương
- GVHD: [tên]
- Ngày bảo vệ

## Slide 2 — Vấn đề (Why?)

- Mối đe dọa mạng gia tăng (1.800 cuộc tấn công/tuần/tổ chức trong Q3 2024)
- Phản ứng thủ công không khả thi
- ACD cần — RL/LLM agent

## Slide 3 — Công trình tiền đề và 3 hạn chế

Bài *Large Language Models are Autonomous Cyber Defenders* [2] tiên phong dùng LLM cho ACD, nhưng có 3 lỗi:
1. Ảo giác đọc vectơ 8-bit
2. Lệ thuộc cách viết prompt
3. Thiếu định hướng từ reward function

## Slide 4 — Đề xuất của em

Hai cơ chế:
- **MCP** — LLM gọi tool có cấu trúc
- **RoE** — rào chắn quyết định tất định

Dựa trên nguyên lý decision-theoretic của bài *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1].

## Slide 5 — Mục tiêu + 4 câu hỏi nghiên cứu

- 1 mục tiêu tổng quát + 5 mục tiêu cụ thể
- RQ1-RQ4 + giả thuyết

## Slide 6 — Kiến trúc tổng thể

[Sơ đồ data flow từ Chương 3.1]

## Slide 7 — Decoder — fix Hạn chế 1

- Vectơ 8-bit → JSON tiếng người
- LLM không bao giờ chạm bit thô
- Bằng chứng: Scenario 1 log

## Slide 8 — MCP Allow-list — fix Hạn chế 2 (phần 1)

- 6 MCP tool (2 obs + 4 propose_*)
- Schema cứng — LLM không tự sáng tạo action

## Slide 9 — RoE Rule Engine — fix Hạn chế 2 (phần 2)

- 3 rule deterministic
- Verdict (allow/deny + reason + suggested)
- Bằng chứng: Scenario 2A pass

## Slide 10 — LLM ↔ RoE Feedback Loop — fix Hạn chế 3

- Thay reward bằng denial message
- LLM đọc → tự sửa sai
- Bằng chứng: Scenario 2B pass

## Slide 11 — Demo

Live demo: chạy `run_smoke.py` → cho thầy thấy Claude reasoning bằng tiếng Việt + RoE fire + audit log.

## Slide 12 — Phương pháp thực nghiệm

- 3 setup: A (baseline) / B (MCP only) / C (MCP + RoE)
- 4 red variant × 5 episode = 60 episode
- 5 metric đo lường

## Slide 13 — Kết quả định lượng (1/2)

- RQ1: Token consumption — [số liệu]
- RQ2: Invalid action + Comms misread — [số liệu]

## Slide 14 — Kết quả định lượng (2/2)

- RQ3: Reward — [biểu đồ]
- RQ4: Trade-off rule count — [đường cong]

## Slide 15 — Kết quả định tính

- Clustering reasoning bằng K-Means
- So sánh setup B vs C
- 1 case study đặc trưng

## Slide 16 — Đối chiếu với 3 hạn chế của bài *Large Language Models are Autonomous Cyber Defenders* [2]

| Hạn chế | Giải pháp | Trạng thái |
|---|---|---|
| 1 | Decoder pre-parse | ✓ |
| 2 | MCP + RoE | ✓ |
| 3 | RoE feedback loop | ✓ |

## Slide 17 — Đóng góp luận văn

5 đóng góp lý thuyết + thực nghiệm + công cụ

## Slide 18 — Hạn chế + Hướng phát triển

- Hạn chế: latency, tập rule còn nhỏ, chỉ 1 model
- Hướng phát triển: mở rộng rule, multi-model, áp dụng môi trường khác

## Slide 19 — Q&A

- Slide trống — chờ câu hỏi
- Xem trước `QA_PREP.md` để chuẩn bị

## Slide 20 — Cảm ơn

- Cảm ơn thầy hướng dẫn
- Cảm ơn hội đồng

---

## Tips trình bày

- 1 slide = 1 ý chính, không nhồi quá 5 bullet
- Hình > text — chuẩn bị diagram chất lượng cao
- Demo (slide 11) là vũ khí mạnh nhất — chuẩn bị backup video nếu live demo lỗi
- Số liệu (slide 13-15) phải có context — so sánh tương đối, không tuyệt đối
