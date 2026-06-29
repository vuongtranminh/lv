---
title: "KẾ HOẠCH THỰC HIỆN ĐỀ TÀI LUẬN VĂN"
subtitle: "Tác nhân Mô hình Ngôn ngữ Lớn Phòng thủ Mạng Tự động với Model Context Protocol và Rules of Engagement"
author: "Trần Minh Vương"
date: "Tháng 6, 2026"
---

# KẾ HOẠCH THỰC HIỆN ĐỀ TÀI LUẬN VĂN

## Đề tài

**Tác nhân Mô hình Ngôn ngữ Lớn Phòng thủ Mạng Tự động với Model Context Protocol và Rules of Engagement**

(*A Large Language Model Agent for Autonomous Cyber Defense with Model Context Protocol and Rules of Engagement*)

---

## TÓM TẮT

Báo cáo trình bày kế hoạch thực hiện đề tài luận văn về việc xây dựng tác nhân Mô hình Ngôn ngữ Lớn (Large Language Model — LLM) làm nhiệm vụ phòng thủ mạng tự động (Autonomous Cyber Defense — ACD) trong môi trường mô phỏng CybORG CAGE 4. Hướng tiếp cận đề xuất tích hợp hai cơ chế: **Model Context Protocol (MCP)** cho phép LLM truy xuất trạng thái mạng theo cấu trúc thông qua việc gọi công cụ (tool calling), và **Rules of Engagement (RoE)** — tập quy tắc kiểm soát tất định nhằm ngăn chặn các hành động vượt ranh giới an toàn, dựa trên nguyên lý decision-theoretic của bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1].

Mục tiêu của kiến trúc đề xuất là khắc phục ba hạn chế chính được chỉ ra trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2]: (i) hiện tượng ảo giác (hallucination) khi đọc vectơ truyền thông nhị phân, (ii) sự phụ thuộc của hành vi LLM vào cách diễn đạt prompt, và (iii) việc thiếu cơ chế phần thưởng (reward function) định hướng.

Giai đoạn nghiên cứu khả thi (feasibility) ở quy mô nhỏ đã được hoàn thành, bao gồm việc xây dựng bản mẫu tích hợp MCP + RoE, ba tình huống kiểm thử (test scenario) và mười một kiểm thử đơn vị (unit test). Kết quả ban đầu cho thấy kiến trúc đề xuất khả thi về mặt kỹ thuật. Báo cáo này trình bày kế hoạch chi tiết để hoàn thành đề tài, gồm bốn câu hỏi nghiên cứu, sáu chương luận văn, và lộ trình thực hiện dự kiến.

**Từ khóa**: Phòng thủ mạng tự động, Mô hình Ngôn ngữ Lớn, Model Context Protocol, Rules of Engagement, CybORG CAGE 4.

---

## MỤC LỤC

1. [Đặt vấn đề và động lực nghiên cứu](#1-đặt-vấn-đề-và-động-lực-nghiên-cứu)
2. [Mục tiêu nghiên cứu](#2-mục-tiêu-nghiên-cứu)
3. [Câu hỏi nghiên cứu](#3-câu-hỏi-nghiên-cứu)
4. [Kết quả nghiên cứu khả thi](#4-kết-quả-nghiên-cứu-khả-thi)
5. [Cấu trúc luận văn dự kiến](#5-cấu-trúc-luận-văn-dự-kiến)
6. [Lộ trình thực hiện](#6-lộ-trình-thực-hiện)
7. [Phương pháp luận và đo lường](#7-phương-pháp-luận-và-đo-lường)
8. [Phân tích rủi ro và phương án dự phòng](#8-phân-tích-rủi-ro-và-phương-án-dự-phòng)
9. [Đóng góp khoa học dự kiến](#9-đóng-góp-khoa-học-dự-kiến)
10. [Tài liệu tham khảo](#10-tài-liệu-tham-khảo)

---

## 1. ĐẶT VẤN ĐỀ VÀ ĐỘNG LỰC NGHIÊN CỨU

### 1.1 Bối cảnh phòng thủ mạng tự động

Các mối đe dọa an ninh mạng (cyber threats) đang phát triển nhanh chóng cả về quy mô lẫn mức độ tinh vi. Việc phản ứng thủ công đối với các cảnh báo xâm nhập (intrusion alert) đã trở nên không khả thi do tốc độ và quy mô của các cuộc tấn công hiện đại.

**Phòng thủ Mạng Tự động (Autonomous Cyber Defense — ACD)** là cách tiếp cận sử dụng các tác nhân Trí tuệ Nhân tạo (AI) để phát hiện và giảm thiểu (mitigate) các cuộc tấn công ở tốc độ máy móc. Các nghiên cứu ACD truyền thống chủ yếu dựa trên **Học tăng cường (Reinforcement Learning — RL)**. Tuy nhiên, theo phân tích trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], các tác nhân RL gặp ba hạn chế nghiêm trọng:

1. **Khả năng giải thích hạn chế** (limited explainability): khó hiểu vì sao tác nhân đưa ra một quyết định cụ thể.
2. **Khả năng chuyển giao hạn chế** (limited transferability): chính sách (policy) huấn luyện trên một mạng không áp dụng tốt cho mạng khác.
3. **Yêu cầu huấn luyện tốn kém**: cần dữ liệu mô phỏng lớn, kém hiệu quả về mẫu (sample inefficient).

### 1.2 Vai trò của Mô hình Ngôn ngữ Lớn trong ACD

Bài báo *Large Language Models are Autonomous Cyber Defenders* [2] là **nghiên cứu tiên phong** áp dụng LLM làm tác nhân phòng thủ trong môi trường CybORG CAGE 4. Ưu điểm của LLM so với RL bao gồm:

- **Tính giải thích cao**: LLM cung cấp lý do (reasoning) bằng ngôn ngữ tự nhiên cho mỗi quyết định.
- **Khả năng tổng quát hóa (generalization)**: có thể sử dụng mô hình đã huấn luyện trước (pre-trained), không cần xây dựng môi trường gym chuyên biệt.
- **Tri thức rộng**: đã được huấn luyện trên dữ liệu từ nhiều mô hình mối đe dọa (threat model) và kiến trúc mạng đa dạng.

Tuy nhiên, bài báo *Large Language Models are Autonomous Cyber Defenders* [2] cũng chỉ ra **ba hạn chế quan trọng** của tác nhân LLM trong môi trường ACD:

#### Hạn chế 1 — Ảo giác khi đọc vectơ truyền thông

CybORG CAGE 4 yêu cầu các tác nhân phòng thủ (blue agent) trao đổi **vectơ truyền thông 8-bit** mỗi lượt. LLM nhận vectơ này dưới dạng mảng nhị phân và phải tự diễn giải. Trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], quan sát thực nghiệm cho thấy LLM thường xuyên đọc nhầm — gán nhầm vectơ cho tác nhân gửi sai, hoặc đọc nhầm mức độ xâm phạm (compromise level) được mã hóa trong các bit.

#### Hạn chế 2 — Lệ thuộc vào cách diễn đạt Prompt

Khi định nghĩa các hành động trong prompt thay đổi (chỉ một vài từ), hành vi của LLM thay đổi đột ngột. Theo thực nghiệm trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], khi không định nghĩa rõ hành động `Remove`, LLM giả định ý nghĩa khác (ngắt kết nối máy chủ thay vì xóa tiến trình độc hại), dẫn đến chiến lược sai lệch.

#### Hạn chế 3 — Thiếu định hướng phần thưởng

LLM hành động dựa trên prompt nhưng không nắm được trực tiếp hàm phần thưởng (reward function) như các tác nhân RL. Theo phân tích trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], LLM thiên vị các hành động phân tích (Analyse) và đánh lừa (DeployDecoy) thay vì giải quyết triệt để vấn đề bằng Restore.

### 1.3 Cơ sở lý thuyết về Decision-Theoretic ACD

Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] đặt nền tảng quan trọng: để con người có thể tin tưởng (trust) giao quyền cho AI phản ứng ở tốc độ máy móc, hệ thống bắt buộc phải có cơ chế **human-on-the-loop** (con người giám sát có thể can thiệp khi cần) và **tuân thủ các đánh đổi rủi ro** do con người thiết lập. Đây chính là cơ sở lý luận để đề tài này áp dụng khái niệm **Rules of Engagement (RoE)** làm ranh giới kiểm soát an toàn cho tác nhân AI.

### 1.4 Khoảng trống nghiên cứu

Theo khảo sát sơ bộ dựa trên hai bài báo nền tảng [1] và [2]:

- Bài báo *Large Language Models are Autonomous Cyber Defenders* [2] đã chứng minh khả năng của LLM trong ACD nhưng chưa giải quyết được ba hạn chế đã nêu, đặc biệt là hiện tượng ảo giác và sự lệ thuộc prompt.
- Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] đề xuất nguyên lý human-on-the-loop nhưng chưa tích hợp với tác nhân LLM cụ thể.

**Khoảng trống**: Chưa có công trình tích hợp đầu cuối **MCP + RoE** cho tác nhân LLM phòng thủ mạng. Việc khảo sát các công trình liên quan ngoài hai bài báo nền tảng sẽ được thực hiện trong Giai đoạn 1 của lộ trình để xác nhận chính xác tính mới của đề tài.

---

## 2. MỤC TIÊU NGHIÊN CỨU

### 2.1 Mục tiêu tổng quát

Xây dựng và đánh giá một kiến trúc tác nhân LLM phòng thủ mạng tự động kết hợp **Model Context Protocol (MCP)** cho cơ chế gọi công cụ (tool calling) có cấu trúc và **Rules of Engagement (RoE)** cho rào chắn quyết định tất định (deterministic policy enforcement), nhằm khắc phục ba hạn chế chính của tác nhân LLM được chỉ ra trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2].

### 2.2 Mục tiêu cụ thể

| Mã | Mục tiêu cụ thể |
|---|---|
| MT1 | Thiết kế và triển khai kiến trúc MCP + RoE cho tác nhân LLM trong môi trường CybORG CAGE 4 |
| MT2 | Đánh giá định lượng hiệu quả của kiến trúc so với baseline (đường cơ sở) — kiến trúc gốc trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] — trên năm chỉ số đo lường (metric) |
| MT3 | Phân tích định tính chất lượng suy luận (reasoning) của LLM trong môi trường có ràng buộc tất định |
| MT4 | Đề xuất framework đo lường tiêu chuẩn cho việc đánh giá LLM Agent an toàn trong ACD |
| MT5 | Cung cấp mã nguồn mở (open-source code) có thể tái lập (reproducible) cho cộng đồng nghiên cứu |

---

## 3. CÂU HỎI NGHIÊN CỨU

Nghiên cứu trả lời **bốn câu hỏi (Research Question — RQ)** sau:

### RQ1 — Hiệu quả về Token Consumption

> *Việc sử dụng MCP cho phép LLM truy xuất trạng thái mạng có cấu trúc theo yêu cầu (on-demand) thay vì nhồi toàn bộ ngữ cảnh vào prompt như trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2]. Liệu cơ chế này có thực sự giảm số token (đơn vị từ vựng cơ bản model xử lý) tiêu thụ trên CybORG CAGE 4 hay không?*

**Giả thuyết H1**: MCP làm giảm token tiêu thụ trung bình mỗi step ít nhất 30% so với kiến trúc baseline trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], với chi phí biên (marginal cost) giảm dần khi bộ nhớ đệm prompt (prompt cache) hoạt động hiệu quả qua các step.

### RQ2 — Hiệu quả Giảm Hallucination và Invalid Action

> *Cơ chế MCP (bộ giải mã vectơ truyền thông + tool schema có cấu trúc) kết hợp với RoE (danh sách cho phép — allow-list) có làm giảm tỉ lệ invalid action và comms misread (đọc nhầm vectơ truyền thông) so với baseline trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] hay không?*

**Giả thuyết H2**: Kiến trúc đề xuất giảm tỉ lệ invalid action ít nhất 50% và đưa tỉ lệ comms misread về dưới 5%.

### RQ3 — Hiệu quả về Performance

> *Tác nhân LLM với MCP + RoE có đạt được điểm thưởng (joint reward — phần thưởng chung tích lũy của CybORG) tương đương hoặc tốt hơn kiến trúc baseline trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] hay không?*

**Giả thuyết H3**: Tác nhân MCP + RoE đạt reward không thấp hơn baseline trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] quá 30% (do RoE có thể chặn một số hành động tối ưu nhưng tiềm ẩn nguy cơ).

### RQ4 — Trade-off giữa An toàn và Hiệu năng

> *Khi mở rộng tập rule RoE (từ 3 lên 10 quy tắc), tỉ lệ RoE deny rate tăng nhưng reward thay đổi như thế nào? Tồn tại điểm tối ưu (Pareto-optimal point) không?*

**Giả thuyết H4**: Tồn tại đường cong trade-off rõ ràng giữa số lượng rule và reward, với điểm tối ưu nằm trong khoảng 6-8 rule.

---

## 4. KẾT QUẢ NGHIÊN CỨU KHẢ THI

Giai đoạn nghiên cứu khả thi (feasibility study) đã được hoàn thành theo hướng dẫn của giảng viên hướng dẫn. Chi tiết được trình bày trong báo cáo riêng (`BAO_CAO_BUOC_1.md`); tóm tắt kết quả chính dưới đây.

### 4.1 Sản phẩm đã hoàn thành

| Hạng mục | Mô tả | Quy mô |
|---|---|---|
| Mã nguồn prototype | Triển khai MCP + RoE cho một tác nhân blue agent, kế thừa môi trường mô phỏng từ repo của bài báo *Large Language Models are Autonomous Cyber Defenders* [2] | ~1.230 dòng code Python |
| Decoder pre-parse | Bộ giải mã vectơ truyền thông 8-bit thành JSON | `feasibility/state_extractor.py` |
| Tập MCP tool | 6 công cụ (2 quan sát + 4 đề xuất hành động) | `feasibility/tools.py` |
| Tập RoE rule | 3 quy tắc tất định | `feasibility/roe/rules.py` |
| Kiểm thử đơn vị | 11 unit test cho decoder + RoE | `tests/test_offline.py` |
| Tình huống thực nghiệm | 3 scenario test với LLM thực | `run_smoke.py`, `scenario_2_*.py`, `scenario_3_*.py` |

### 4.2 Kết quả thực nghiệm chính

**Bảng 4.1** — Kết quả ba tình huống kiểm thử (timestamp logs: 20260611_133751-133841)

| Tình huống | Mục đích | Kết quả | Wall time |
|---|---|---|---|
| 1 (Happy path) | Verify pipeline đầu cuối | ✓ Pass — LLM chọn `Restore host_a` đúng | 19,36s |
| 2A (RoE deny trực tiếp) | Verify RoE tất định | ✓ Pass — RoE từ chối với reason + suggested | <0,01s |
| 2B (LLM tự sửa sai) | Verify LLM phản ứng denial | ✓ Pass — LLM chuyển sang `DeployDecoy` | 29,27s |
| 3 (Token compare) | So sánh prompt size | Hỗn hợp — prompt giảm 22,1%, tổng token tăng 333% | 14-29s |

**Bảng 4.2** — Đánh giá đối chiếu với ba hạn chế chỉ ra trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2]

| Hạn chế trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] | Giải pháp đề xuất | Trạng thái xác nhận |
|---|---|---|
| Ảo giác đọc vectơ 8-bit | Pre-decode bằng Python tất định, expose qua MCP tool | Đã giải quyết bằng kiến trúc |
| Lệ thuộc prompt cho định nghĩa action | RoE rule tất định, không qua LLM | Đã xác minh ở quy mô nhỏ |
| Thiếu reward direction | Thay thế bằng RoE feedback (allow/deny + reason) | Bằng chứng sơ bộ, cần Phase 2 |

### 4.3 Hạn chế của giai đoạn khả thi

Những điều chưa được kiểm chứng ở giai đoạn này, sẽ được giải quyết ở Phase 2:

1. Chưa kiểm thử trên observation thực tế của CybORG CAGE 4 (mới dùng 1 host giả).
2. Chưa chạy full episode 500 step.
3. Chưa đo chi phí biên (marginal cost) sau khi prompt cache đạt trạng thái ổn định.
4. RoE denial trong Scenario 2 Part B được inject thủ công vào prompt thay vì fire tại runtime.
5. Chưa benchmark với 4 biến thể red agent trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2].
6. Tập RoE rule mới có 3, cần mở rộng.

---

## 5. CẤU TRÚC LUẬN VĂN DỰ KIẾN

Luận văn dự kiến có **6 chương chính** với độ dài 60-80 trang. Mỗi mục được mô tả ngắn nội dung sẽ trình bày.

### Chương 1 — Mở đầu (5-8 trang)

| Mục | Nội dung |
|---|---|
| 1.1 Bối cảnh và động lực | Trình bày thực trạng tấn công mạng gia tăng, giới hạn của phản ứng thủ công, sự cần thiết của phòng thủ mạng tự động (ACD). |
| 1.2 Mục tiêu nghiên cứu | Phát biểu mục tiêu tổng quát (xây dựng kiến trúc MCP+RoE) và năm mục tiêu cụ thể (MT1-MT5). |
| 1.3 Câu hỏi nghiên cứu | Trình bày bốn câu hỏi nghiên cứu RQ1-RQ4 cùng giả thuyết H1-H4. |
| 1.4 Đóng góp dự kiến | Liệt kê 5 đóng góp về lý thuyết, thực nghiệm, công cụ. |
| 1.5 Bố cục luận văn | Tóm tắt nội dung từng chương trong luận văn. |

### Chương 2 — Cơ sở lý thuyết và Tổng quan tình hình nghiên cứu (15-20 trang)

| Mục | Nội dung |
|---|---|
| 2.1 Bài toán quyết định Markov có quan sát một phần (POMDP) trong ACD | Giới thiệu mô hình POMDP, nguyên lý decision-theoretic, vai trò của human-on-the-loop trong bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1]. |
| 2.2 Mô hình Ngôn ngữ Lớn và LLM Agent | Giới thiệu kiến trúc transformer, khái niệm LLM Agent, cơ chế gọi công cụ (function calling), so sánh với tác nhân RL. |
| 2.3 Mô phỏng phòng thủ mạng CybORG CAGE 4 | Mô tả kiến trúc môi trường mô phỏng: 3 mạng, 5 zone, blue/red/green agents, 3 pha nhiệm vụ. Nội dung được trích từ tài liệu của bài báo *Large Language Models are Autonomous Cyber Defenders* [2]. |
| 2.4 Công trình tiền đề | Phân tích chi tiết bài báo *Large Language Models are Autonomous Cyber Defenders* [2]: kiến trúc, cách prompt, đánh giá hiệu năng, ba hạn chế đã chỉ ra. |
| 2.5 Model Context Protocol | Đặc tả của MCP: cấu trúc tool schema, cơ chế gọi công cụ, in-process MCP server. |
| 2.6 Guardrail và Policy-as-code Frameworks | Tổng quan các framework kiểm soát an toàn LLM và policy-as-code hiện có. Nội dung này sẽ được khảo sát trong Giai đoạn 1 của lộ trình thực hiện. |
| 2.7 Khảo sát các CAGE Challenge submissions | Tổng hợp các approach gần đây cho CybORG. Nội dung này sẽ được khảo sát trong Giai đoạn 1 của lộ trình thực hiện. |
| 2.8 Xác định khoảng trống nghiên cứu | Bảng so sánh kiến trúc đề xuất với các công trình liên quan (sau khi khảo sát ở Giai đoạn 1), định vị tính mới của đề tài. |

### Chương 3 — Thiết kế hệ thống đề xuất (10-12 trang)

| Mục | Nội dung |
|---|---|
| 3.1 Kiến trúc tổng thể | Sơ đồ tổng thể: CybORG observation → Decoder → MCP Tool → LLM → RoE → Action. Mô tả vai trò từng thành phần. |
| 3.2 Decoder Pre-parse — Giải quyết Hạn chế 1 | Mô tả giải pháp tiền xử lý vectơ truyền thông 8-bit thành JSON cấu trúc. |
| 3.2.1 Định dạng vectơ truyền thông 8-bit | Mô tả chi tiết quy ước 8 bit theo CybORG CAGE 4 (bit 0-4 phát hiện malice, bit 5-6 compromise level, bit 7 busy). |
| 3.2.2 Thuật toán decode | Pseudo-code thuật toán deterministic chuyển 8-bit thành dict JSON. |
| 3.2.3 Cấu trúc JSON đầu ra | Ví dụ JSON đầu ra mà LLM sẽ thấy thay cho raw bit. |
| 3.3 MCP Tool Allow-list — Giải quyết Hạn chế 2 (phần 1) | Mô tả việc đóng gói tất cả hành động khả dụng thành tập tool cứng. |
| 3.3.1 Hai loại tool: quan sát và đề xuất hành động | Phân loại 2 observation tool + 4 proposal tool, vai trò và signature. |
| 3.3.2 Schema MCP cho tool | Mô tả schema cứng cho từng tool — name, description, input_schema. |
| 3.3.3 In-process MCP server | Cách dùng `create_sdk_mcp_server` để chạy MCP nội bộ, không cần spawn process riêng. |
| 3.4 RoE Rule Engine — Giải quyết Hạn chế 2 (phần 2) | Mô tả cơ chế thẩm định mỗi hành động trước khi thực thi. |
| 3.4.1 Cấu trúc Verdict (allow / deny + reason + suggested) | Định nghĩa kết quả thẩm định và ý nghĩa từng trường. |
| 3.4.2 EpisodeCounter cho ràng buộc trạng thái | Bộ đếm theo episode cho các rule liên quan đến lịch sử (rate-limit). |
| 3.4.3 Phân loại rule: precondition và rate-limit | Hai loại rule chính, ví dụ cụ thể từng loại. |
| 3.5 LLM ↔ RoE Feedback Loop — Giải quyết Hạn chế 3 | Mô tả cơ chế thay thế hàm phần thưởng bằng phản hồi RoE. |
| 3.5.1 Cơ chế deny + reason + suggested | Cấu trúc thông điệp deny được gửi ngược cho LLM bằng ngôn ngữ tự nhiên. |
| 3.5.2 Vòng lặp tự sửa sai (self-correction loop) của LLM | Cách LLM đọc denial và chuyển sang hành động thay thế. |
| 3.6 Audit log và Reproducibility | Cấu trúc CSV log mỗi step (state, llm_reason, proposed, verdict, final) và cách reproduce thí nghiệm. |

### Chương 4 — Triển khai và Thực nghiệm (10-15 trang)

| Mục | Nội dung |
|---|---|
| 4.1 Môi trường thực nghiệm | Mô tả setup phần cứng/phần mềm. |
| 4.1.1 CybORG CAGE 4 setup | Mô tả version, cách cài đặt từ repo gốc của bài báo *Large Language Models are Autonomous Cyber Defenders* [2], cấu hình mạng (5 zone, 5 blue agent). |
| 4.1.2 Mô hình LLM (Claude Haiku 4.5) | Lý do chọn model — tương đương GPT-4o-mini sử dụng trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] — và cấu hình. |
| 4.1.3 SDK và stack kỹ thuật | `claude-agent-sdk`, anyio, Python 3.11, Ray RLlib. |
| 4.2 Triển khai Prototype (Giai đoạn 0) | Mô tả cấu trúc module, dòng code, các điểm tích hợp với CybORG. |
| 4.3 Thực nghiệm khả thi (Giai đoạn 0) | Mô tả 3 scenario test + 11 unit test, kết quả tóm tắt. |
| 4.4 Thực nghiệm Full Benchmark (Phase 2) | Thiết kế thí nghiệm A/B/C × red variant × episode, quy trình chạy, cách thu thập log. |

### Chương 5 — Kết quả và Đánh giá (12-15 trang)

| Mục | Nội dung |
|---|---|
| 5.1 Phân tích định lượng theo từng câu hỏi nghiên cứu | Trình bày kết quả cho RQ1-RQ4 với bảng số liệu, biểu đồ. |
| 5.1.1 RQ1 — Token consumption | So sánh token tiêu thụ giữa Setup A và Setup C qua các step. |
| 5.1.2 RQ2 — Invalid action & comms misread rate | Bảng so sánh tỉ lệ hallucination giữa các setup. |
| 5.1.3 RQ3 — Reward so với baseline | Biểu đồ reward theo episode, so sánh A vs B vs C. |
| 5.1.4 RQ4 — Trade-off rule count vs reward | Đường cong Pareto khi mở rộng tập rule. |
| 5.2 Phân tích định tính | Mô tả chất lượng suy luận của LLM. |
| 5.2.1 Phân cụm suy luận (reasoning clustering) bằng K-Means | Áp dụng phương pháp của bài báo *Large Language Models are Autonomous Cyber Defenders* [2] mục IV.E, so sánh số cluster và đặc trưng giữa các setup. |
| 5.2.2 Audit log walkthrough — các tình huống đặc trưng | Phân tích chi tiết 3-5 trường hợp đại diện từ audit log. |
| 5.2.3 So sánh với reasoning của tác nhân RL | Đối chiếu cách ra quyết định LLM vs RL (kiến trúc baseline RL được khảo sát ở Giai đoạn 1). |
| 5.3 Hạn chế quan sát được | Liệt kê những điều thực nghiệm chưa giải quyết được. |

### Chương 6 — Kết luận và Hướng phát triển (3-5 trang)

| Mục | Nội dung |
|---|---|
| 6.1 Tóm tắt đóng góp | Tổng kết 5 đóng góp đã đạt được. |
| 6.2 Hạn chế của nghiên cứu | Liệt kê hạn chế còn lại sau khi hoàn thành luận văn. |
| 6.3 Hướng mở rộng tương lai | Đề xuất hướng: thêm rule, thử model khác, áp dụng cho môi trường ACD khác. |
| 6.4 Khuyến nghị cho cộng đồng nghiên cứu ACD | Khuyến nghị về framework đo lường + open-source code. |

### Phụ lục

- Danh sách RoE rule đầy đủ (sau khi mở rộng ở Phase 2B).
- Cấu trúc audit log CSV.
- Hướng dẫn tái lập thí nghiệm.
- Mã nguồn các thành phần chính.

---

## 6. LỘ TRÌNH THỰC HIỆN

Kế hoạch được chia thành **5 giai đoạn**, mỗi giai đoạn có sản phẩm bàn giao (deliverable) rõ ràng.

**Lưu ý về tốc độ thực hiện**: Lộ trình được dự trù cho hình thức học thạc sĩ vừa làm vừa học. Khối lượng làm việc dành cho luận văn ước tính khoảng **15-20 giờ/tuần** (so với toàn thời gian khoảng 40 giờ/tuần), tương ứng hệ số giãn thời gian khoảng 2 lần so với người làm luận văn toàn thời gian.

### Giai đoạn 0 — Nghiên cứu khả thi (ĐÃ HOÀN THÀNH, ~1,5 tháng)

| Nhiệm vụ | Trạng thái | Sản phẩm |
|---|---|---|
| Đọc và phân tích bài báo lý thuyết *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] và bài báo thực nghiệm *Large Language Models are Autonomous Cyber Defenders* [2] | ✓ Hoàn thành | Ghi chú nghiên cứu |
| Triển khai prototype MCP + RoE | ✓ Hoàn thành | `feasibility-mcp-roe/` |
| Ba scenario test với LLM thực | ✓ Hoàn thành | 4 file log trong `logs/` |
| 11 unit test pure logic | ✓ Hoàn thành | `tests/test_offline.py` |
| Báo cáo Giai đoạn 0 | ✓ Hoàn thành | `BAO_CAO_BUOC_1.md` |

### Giai đoạn 1 — Khảo sát tình hình nghiên cứu (4-6 tuần)

**Mục tiêu**: mở rộng phạm vi đọc tài liệu ngoài hai bài báo nền tảng [1] và [2] để xác định khoảng trống nghiên cứu (research gap) và tính mới (novelty) của đề tài.

**Phạm vi khảo sát dự kiến** (chi tiết các paper sẽ được xác định trong quá trình khảo sát; sẽ tổng hợp thành Chương 2 luận văn):

| Nhóm | Phạm vi khảo sát |
|---|---|
| LLM Agent cho cybersecurity (ngoài bài báo [2]) | Các paper 2024-2025 trên arXiv về function calling / tool use cho phòng thủ mạng |
| Guardrail frameworks cho LLM | Các framework hiện có như Llama Guard, NeMo Guardrails, Guardrails AI |
| Policy-as-code | Open Policy Agent (OPA), Cedar (AWS), AWS Verified Permissions |
| Human-on-the-loop trong autonomous defense | Các báo cáo của CMU SEI, MIT Lincoln Lab, DARPA CASTLE program |
| CAGE Challenge submissions | Các approach RL/GNN cho CAGE Challenge các năm trước |
| LLM tool use và function calling | Các paper từ OpenAI, Anthropic, Google về tool calling |

**Phương pháp khảo sát**:

1. Tra cứu các database: Google Scholar, IEEE Xplore, arXiv, ACM Digital Library.
2. Snowball sampling (lan truyền tham chiếu) từ danh sách tham khảo của bài báo *Large Language Models are Autonomous Cyber Defenders* [2].
3. Tra cứu các venue chuyên ngành: USENIX Security, IEEE S&P, ACSAC, NDSS, CAMLIS.

**Sản phẩm**:
- Draft Chương 2 luận văn (~15-20 trang).
- Bảng so sánh tính mới của đề tài với 10-15 công trình liên quan.
- Cập nhật phần "Đóng góp dự kiến" trong báo cáo này.
- Cập nhật danh sách tài liệu tham khảo (mở rộng từ 2 bài báo nền tảng hiện tại).

### Giai đoạn 2 — Thực nghiệm full benchmark (8-12 tuần)

#### 2A. Tích hợp Prototype vào CybORG (2-3 tuần)

Hiện tại `claude_policy.py` mới chạy độc lập trên một step giả. Cần thực hiện:

1. Đăng ký policy theo interface của Ray RLlib trong CybORG submission.
2. Tích hợp với 4 tác nhân RL baseline (sẽ chọn từ các submission được khảo sát ở Giai đoạn 1) — giữ làm baseline — cho 4 blue agent còn lại.
3. Cập nhật `EnterpriseObsWrapper` (đã có trong repo của bài báo *Large Language Models are Autonomous Cyber Defenders* [2]) để forward observation đúng cách.
4. Verify pipeline chạy được 500 step không gặp lỗi.

**Sản phẩm**: Code submission tương thích với `python -m CybORG.Evaluation.evaluation`.

#### 2B. Mở rộng RoE Rule (1-2 tuần)

Mở rộng từ 3 lên 8-10 rule:

| Rule mới | Loại | Mô tả |
|---|---|---|
| `rule_restore_phase_constraint` | Precondition | Restore bị hạn chế trong phase MissionA/B với một số zone |
| `rule_block_critical_zone_forbidden` | Precondition | Không cho block traffic giữa các zone trọng yếu |
| `rule_decoy_global_quota` | Rate-limit | Giới hạn tổng số decoy toàn episode |
| `rule_analyse_minimum_cooldown` | Rate-limit | Không Analyse cùng host trong 5 step liên tiếp |
| `rule_action_requires_active_session` | Precondition | Action chỉ được thực hiện trên session đang hoạt động |
| `rule_no_block_when_busy` | Precondition | Không block khi agent đang ở trạng thái busy |
| `rule_restore_max_per_episode` | Rate-limit | Tối đa N lần Restore mỗi episode |

**Sản phẩm**: `rules.py` mở rộng + unit test phủ hết các rule mới.

#### 2C. Chạy Benchmark Đầy đủ (3-4 tuần)

**Thiết kế thí nghiệm**:

| Yếu tố | Giá trị |
|---|---|
| Setup | A (baseline — kiến trúc trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2]) / B (MCP only) / C (MCP + RoE) |
| Số episode mỗi setup mỗi red variant | 5 |
| Red variants | FiniteState (default), AggressiveFSM, StealthyFSM, ImpactFSM — bốn biến thể có sẵn trong môi trường mô phỏng và được dùng trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] |
| Step mỗi episode | 500 |
| Tổng số episode | 3 setup × 4 red × 5 episode = 60 episode |

**Wall time ước tính**: ~30 giờ chạy mô phỏng. Vì làm part-time, chia thành 8-10 phiên (mỗi phiên 3-4 giờ vào cuối tuần hoặc buổi tối).

**Sản phẩm**:
- File CSV raw data của 60 episode.
- Audit log JSON cho mỗi episode.
- Bảng số liệu tổng hợp 5 metric (RQ1-RQ4).

#### 2D. Phân tích Định tính (2 tuần)

- Phân cụm reasoning bằng K-Means trên các cặp (action, reasoning) trong audit log — áp dụng phương pháp của bài báo *Large Language Models are Autonomous Cyber Defenders* [2] (mục IV.E).
- Vẽ biểu đồ scatter 2D bằng PCA.
- So sánh số cluster, đặc trưng cluster giữa setup B (MCP only) và C (MCP + RoE).
- Audit log walkthrough — chọn 3-5 trường hợp đặc trưng.

**Sản phẩm**: Hình ảnh + bảng cho Chương 5 luận văn.

### Giai đoạn 3 — Viết luận văn (6-8 tuần)

| Chương | Thời gian | Sản phẩm |
|---|---|---|
| Chương 1 | 1 tuần | Mở đầu |
| Chương 2 | (đã có draft từ Giai đoạn 1, chỉnh sửa 1 tuần) | Cơ sở lý thuyết |
| Chương 3 | 1,5 tuần | Thiết kế hệ thống |
| Chương 4 | 1,5 tuần | Triển khai và Thực nghiệm |
| Chương 5 | 1,5 tuần | Kết quả và Đánh giá |
| Chương 6 | 0,5 tuần | Kết luận |
| Phụ lục | 0,5 tuần | Code, log, hướng dẫn |

**Sản phẩm**: Draft luận văn 60-80 trang.

### Giai đoạn 4 — Hoàn thiện và bảo vệ (3-4 tuần)

| Nhiệm vụ | Thời gian |
|---|---|
| Sửa theo góp ý của giảng viên | 1-1,5 tuần |
| Hiệu chỉnh format, citation, ngữ pháp | 0,5-1 tuần |
| Chuẩn bị slides bảo vệ | 0,5-1 tuần |
| Demo video (tùy chọn) | 3-5 ngày |
| Bảo vệ thử | 2-3 ngày |

**Sản phẩm**: Bản nộp + slides + demo video.

### Tổng thời gian dự kiến

**Khoảng 7,5 - 9,5 tháng** từ thời điểm phê duyệt kế hoạch này.

Trong đó:
- Giai đoạn 1 (Khảo sát): 4-6 tuần.
- Giai đoạn 2 (Thực nghiệm): 8-12 tuần.
- Giai đoạn 3 (Viết): 6-8 tuần.
- Giai đoạn 4 (Hoàn thiện): 3-4 tuần.

Lộ trình này có dự trữ thời gian (buffer) cho các rủi ro được nêu trong Mục 8 và những gián đoạn do công việc chính ngoài luận văn.

---

## 7. PHƯƠNG PHÁP LUẬN VÀ ĐO LƯỜNG

### 7.1 Phương pháp nghiên cứu

Đề tài sử dụng **phương pháp thực nghiệm so sánh (comparative experimental method)** với ba cấu hình:

- **Setup A (Baseline)**: tái triển khai LLM Agent theo bài báo *Large Language Models are Autonomous Cyber Defenders* [2], không có MCP và RoE.
- **Setup B (MCP only)**: thêm MCP nhưng không có RoE rule.
- **Setup C (MCP + RoE)**: kiến trúc đề xuất đầy đủ.

Mỗi setup được chạy độc lập trên cùng môi trường, cùng red agent, cùng seed, đảm bảo điều kiện so sánh công bằng.

### 7.2 Tập chỉ số đo lường

**Bảng 7.1** — Năm chỉ số đo lường chính

| ID | Chỉ số | Định nghĩa | Cách đo | Mục đích |
|---|---|---|---|---|
| M1 | Reward | Phần thưởng chung tích lũy của 5 blue agent qua một episode | CybORG built-in joint reward | Đo hiệu năng phòng thủ tổng thể |
| M2 | Invalid Action Rate | Tỉ lệ step mà LLM không đưa ra hành động hợp lệ | (số step `final_action == Sleep`) / (tổng step) | Đo hallucination về hành động |
| M3 | RoE Deny Rate | Tỉ lệ step có ít nhất một đề xuất bị RoE từ chối | (số step có `rejected_attempts != []`) / (tổng step) | Đo mức độ RoE phải fire |
| M4 | Comms Misread Rate | Tỉ lệ step LLM diễn giải sai vectơ truyền thông | Gán nhãn thủ công 50 audit row mỗi setup | Đo hallucination về comms |
| M5 | Step Latency p50, p95 | Phân vị thứ 50 và 95 của thời gian xử lý mỗi step | Wall clock time | Đo chi phí thời gian |

### 7.3 Tiêu chí đạt

**Bảng 7.2** — Tiêu chí đánh giá thành công của đề tài

| Chỉ số | Tiêu chí | Diễn giải |
|---|---|---|
| M2 (Invalid Action Rate) | Setup C < 0,5 × Setup A | RoE giảm tỉ lệ action sai ít nhất 50% |
| M3 (RoE Deny Rate) | 5% ≤ Setup C ≤ 40% | RoE fire hợp lý: không quá ít (vô dụng), không quá nhiều (rule sai) |
| M1 (Reward) | Setup C ≥ Setup A − 30% | RoE không khiến reward giảm quá mức chấp nhận được |
| M5 (Step Latency p95) | Setup C < 5 × Setup A | Chi phí thời gian chấp nhận được |
| M4 (Comms Misread Rate) | Setup C < 5% | Decoder loại bỏ hallucination về comms |

**Quy ước**:
- **Đạt 5/5** → đề tài thành công xuất sắc.
- **Đạt 3/5 hoặc 4/5** → đề tài thành công, có đóng góp khả thi.
- **Dưới 3/5** → đề tài chuyển hướng sang phân tích thất bại (failure modes), vẫn có giá trị khoa học.

### 7.4 Phương pháp phân tích định tính

Áp dụng phương pháp **clustering reasoning** đã được sử dụng trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] (mục IV.E):

1. Thu thập tất cả `(action, reasoning_text)` từ audit log.
2. Embedding `reasoning_text` bằng OpenAI `text-embedding-3-large` (model 3.072 chiều).
3. Giảm chiều bằng PCA xuống 3 thành phần chính.
4. Phân cụm bằng K-Means với K xác định qua Elbow Method và Silhouette Score.
5. Tóm tắt mỗi cluster bằng LLM (GPT-4o hoặc Claude Opus).
6. So sánh số cluster, kích thước cluster, đặc trưng cluster giữa các setup.

---

## 8. PHÂN TÍCH RỦI RO VÀ PHƯƠNG ÁN DỰ PHÒNG

Ba rủi ro chính được xác định cùng phương án xử lý:

### Rủi ro 1 — Tích hợp CybORG phức tạp hơn dự kiến

**Mô tả**: Giai đoạn 2A có thể kéo dài hơn 1 tuần do CybORG có API phức tạp.

**Phương án**:
- Nếu sau 2 tuần chưa tích hợp xong đầy đủ 5 agent, giảm xuống chỉ chạy 1-2 episode để có số liệu sơ bộ.
- Nếu CybORG không tương thích Claude Agent SDK, chuyển sang anthropic SDK trực tiếp (cần API key) qua module `model_manager` đã có sẵn trong repo của bài báo *Large Language Models are Autonomous Cyber Defenders* [2].

### Rủi ro 2 — RoE Deny Rate quá cao gây giảm Reward mạnh

**Mô tả**: Nếu RoE deny rate vượt 40% (chặn quá nhiều), reward có thể giảm mạnh dưới ngưỡng chấp nhận.

**Phương án**:
- Tune lại rule: giảm rule strict (cứng), thêm rule soft (mềm) với threshold tham số hóa.
- So sánh từng cấu hình rule — dữ liệu này phục vụ trực tiếp RQ4 (trade-off curve), nên không phải rủi ro mà còn là cơ hội phân tích.

### Rủi ro 3 — Latency quá chậm

**Mô tả**: Giai đoạn 0 đo wall time ~20 giây/step với Claude Haiku 4.5 qua claude-agent-sdk. Ngoại suy 60 episode × 500 step × 20s ≈ **167 giờ** — không khả thi.

**Phương án**:
- Sử dụng prompt caching aggressive (đã đo cache_read tới 75K token, hiệu quả tốt).
- Giảm `max_turns` từ 8 xuống 4-5.
- Nếu vẫn chậm, chuyển sang `anthropic` SDK trực tiếp (yêu cầu API key) — latency ước tính thấp hơn 2-3 lần do bỏ qua Claude Code CLI overhead.
- Phương án cuối: giảm số episode mỗi setup từ 5 xuống 2-3 — vẫn đủ cho thống kê sơ bộ.

---

## 9. ĐÓNG GÓP KHOA HỌC DỰ KIẾN

(Sẽ chốt lại sau khi hoàn thành Giai đoạn 1 — khảo sát tình hình nghiên cứu.)

### 9.1 Đóng góp lý thuyết

1. **Đề xuất kiến trúc tích hợp MCP + RoE cho LLM Agent trong ACD** — theo khảo sát sơ bộ dựa trên hai bài báo nền tảng [1] và [2], chưa có công trình tương tự. Tính mới sẽ được xác nhận chính thức sau Giai đoạn 1.
2. **Framework đo lường tiêu chuẩn** với 5 metric + pass criterion cho việc đánh giá LLM Agent an toàn — đóng góp cho cộng đồng đánh giá ACD.

### 9.2 Đóng góp thực nghiệm

3. **Benchmark đối chiếu** giữa baseline — bài báo *Large Language Models are Autonomous Cyber Defenders* [2] — và kiến trúc đề xuất trên CybORG CAGE 4. Cung cấp số liệu định lượng cho cộng đồng nghiên cứu ACD.
4. **Phân tích định tính** chất lượng suy luận của LLM khi bị ràng buộc bởi rule tất định — khía cạnh chưa được nghiên cứu trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2].

### 9.3 Đóng góp công cụ

5. **Mã nguồn mở reproducible** — repo public trên GitHub (sau khi hoàn thành), bao gồm:
   - Code prototype MCP + RoE.
   - Test suite (unit test + scenario test).
   - Audit log của các thí nghiệm.
   - Hướng dẫn reproduce đầy đủ.

---

## 10. TÀI LIỆU THAM KHẢO

[1] [Tác giả bài LT1], "A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response," (thông tin trích dẫn đầy đủ sẽ được cập nhật sau khi xác nhận lại với giảng viên hướng dẫn).

[2] S. R. Castro, R. Campbell, N. Lau, O. Villalobos, J. Duan, và A. A. Cárdenas, "Large Language Models are Autonomous Cyber Defenders," in *Proc. IEEE Conf. on Artificial Intelligence (CAI) — Adaptive Cyber Defense Workshop*, 2025. arXiv:2505.04843.

---

*Ghi chú*: Hai bài báo trên là tài liệu nền tảng được giảng viên hướng dẫn cung cấp và đã được nghiên cứu kỹ trong Giai đoạn 0. Danh sách tài liệu tham khảo sẽ được mở rộng sau Giai đoạn 1 (khảo sát tình hình nghiên cứu) để phục vụ Chương 2 luận văn.
