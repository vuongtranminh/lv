# CHƯƠNG 6 — KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

> Dự kiến: 3-5 trang. Material đã có sẵn nhiều — có thể viết được hơn 80% sau khi có Chương 5 kết quả.

## 6.1 Tóm tắt đóng góp

Luận văn này đã thực hiện được những đóng góp sau:

### 6.1.1 Đóng góp lý thuyết

1. **Kiến trúc tích hợp đầu cuối MCP + RoE cho LLM Agent trong ACD** — theo khảo sát ở Chương 2, đây là công trình đầu tiên kết hợp:
   - Decoder pre-parse (giải quyết Hạn chế 1)
   - MCP Tool Allow-list với schema cứng (giải quyết Hạn chế 2 — phần ngữ nghĩa)
   - RoE Rule Engine tất định (giải quyết Hạn chế 2 — phần ràng buộc)
   - LLM ↔ RoE Feedback Loop (giải quyết Hạn chế 3 — thay thế reward function)

2. **Framework đo lường tiêu chuẩn** — đề xuất 5 metric + pass criterion cho việc đánh giá LLM Agent an toàn trong ACD.

### 6.1.2 Đóng góp thực nghiệm

3. **Benchmark đối chiếu đầy đủ** giữa baseline trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] và kiến trúc đề xuất trên CybORG CAGE 4 (60 episode, 3 setup, 4 red variant).

4. **Phân tích định tính reasoning** của LLM trong môi trường có ràng buộc tất định — khía cạnh chưa được nghiên cứu trong các công trình trước.

### 6.1.3 Đóng góp công cụ

5. **Mã nguồn mở reproducible** — repo public bao gồm prototype, test suite, benchmark scripts, hướng dẫn reproduce.

## 6.2 Hạn chế của nghiên cứu

[Liệt kê các hạn chế thực sự gặp phải sau khi hoàn thành thực nghiệm]

Một số hạn chế có thể đề cập:
- Chỉ kiểm thử với một model LLM (Claude Haiku 4.5); chưa so sánh với GPT-4o, o3, Llama 3, etc.
- Tập RoE rule còn nhỏ (8-10 rule) — production-grade cần nhiều hơn
- Chưa kiểm thử trên kiến trúc mạng khác ngoài CybORG CAGE 4
- Latency vẫn cao hơn baseline RL — chưa phù hợp real-time strict
- Đo lường Comms Misread Rate dựa trên gán nhãn thủ công → có thể có bias

## 6.3 Hướng phát triển tương lai

### 6.3.1 Mở rộng tập RoE rule

- Thêm rule liên quan đến: legal compliance, tổn thất tài chính, quyền truy cập theo role
- Áp dụng learned rule (RL học rule từ feedback)

### 6.3.2 Mở rộng model

- So sánh với các model open-source: Llama, DeepSeek, Qwen
- Tinh chỉnh prompt cho từng model

### 6.3.3 Áp dụng cho môi trường ACD khác

- NetSecGame
- BRAWL (DARPA program)
- Real-world penetration testing simulator

### 6.3.4 Tích hợp với SOC thực

- Wrap MCP server thành plugin cho SIEM (vd Splunk, Sentinel)
- Thử nghiệm A/B với analyst thật

### 6.3.5 Học rule tự động

- Dùng LLM để **đề xuất rule mới** dựa trên audit log (rule synthesis)
- Đánh giá rule mới qua simulation trước khi áp dụng

## 6.4 Khuyến nghị cho cộng đồng nghiên cứu ACD

1. **Tích hợp guardrail vào benchmark**: các CAGE Challenge tiếp theo nên có metric an toàn (không chỉ reward).
2. **Chuẩn hóa framework đo lường**: 5 metric đề xuất có thể dùng làm baseline.
3. **Mở rộng test set red agent**: thêm các kẻ tấn công đa dạng + stealthy.
4. **Open-source hơn**: nhiều submission CAGE đang closed-source, hạn chế khả năng tái lập.

## 6.5 Kết luận chung

[Phát biểu cuối — 1 đoạn]

Đề tài đã chứng minh rằng việc kết hợp Model Context Protocol (cho tool calling có cấu trúc) với Rules of Engagement (cho rào chắn quyết định tất định) là một hướng tiếp cận khả thi để khắc phục các hạn chế của LLM Agent trong phòng thủ mạng tự động. Kết quả thực nghiệm trên CybORG CAGE 4 cho thấy [tóm tắt 1 câu kết quả chính sau khi có data]. Hướng tiếp cận này có thể mở rộng cho nhiều domain ACD khác và là nền tảng cho việc tích hợp LLM Agent vào quy trình vận hành SOC thực tế trong tương lai.
