# CHƯƠNG 1 — MỞ ĐẦU

## 1.1 Bối cảnh và động lực

### 1.1.1 Sự gia tăng các cuộc tấn công mạng

Trong những năm gần đây, các mối đe dọa an ninh mạng (cyber threats) phát triển nhanh chóng cả về quy mô lẫn mức độ tinh vi. Tổ chức Trí tuệ Đe dọa Checkpoint báo cáo rằng số lượng cuộc tấn công trung bình hàng tuần trên mỗi tổ chức đã đạt mức 1.800 trong quý III năm 2024, tăng hơn gấp đôi so với cùng kỳ năm trước. Các cuộc tấn công này ngày càng tự động hóa, sử dụng các công cụ khai thác lỗ hổng được điều khiển bằng máy với tốc độ cao, khiến cho việc phản ứng thủ công bởi các nhà phân tích an ninh (security analyst) trong Trung tâm Vận hành An ninh (Security Operations Center — SOC) trở nên không khả thi.

### 1.1.2 Phòng thủ Mạng Tự động (ACD) và vai trò của AI

**Phòng thủ Mạng Tự động (Autonomous Cyber Defense — ACD)** là hướng tiếp cận sử dụng các tác nhân Trí tuệ Nhân tạo (AI) để phát hiện và giảm thiểu (mitigate) các cuộc tấn công ở tốc độ máy móc, không cần can thiệp thủ công của con người ở mỗi quyết định. Các nghiên cứu ACD truyền thống chủ yếu dựa trên **Học tăng cường (Reinforcement Learning — RL)**: huấn luyện tác nhân học từ phần thưởng/hình phạt (reward/penalty) trong môi trường mô phỏng cho đến khi đạt chính sách (policy) tối ưu.

Tuy nhiên, các tác nhân RL trong ACD gặp ba hạn chế nghiêm trọng được nêu rõ trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2]:

1. **Khả năng giải thích hạn chế** (limited explainability) — khó hiểu vì sao tác nhân RL đưa ra một quyết định cụ thể, gây khó khăn cho việc kiểm toán và tin cậy.
2. **Khả năng chuyển giao hạn chế** (limited transferability) — chính sách huấn luyện trên một mạng không áp dụng tốt cho mạng khác do sự khác biệt về kiến trúc.
3. **Yêu cầu huấn luyện tốn kém** — cần xây dựng môi trường mô phỏng phức tạp và tiêu tốn nhiều mẫu dữ liệu (sample inefficient).

### 1.1.3 Mô hình Ngôn ngữ Lớn (LLM) — hướng tiếp cận mới

Bài báo *Large Language Models are Autonomous Cyber Defenders* [2] là **nghiên cứu tiên phong** áp dụng Mô hình Ngôn ngữ Lớn (Large Language Model — LLM) làm tác nhân phòng thủ trong môi trường mô phỏng đa tác nhân CybORG CAGE 4. LLM có ba ưu điểm so với RL:

- **Tính giải thích cao**: LLM cung cấp lý do (reasoning) bằng ngôn ngữ tự nhiên cho mỗi quyết định, có thể được kiểm tra trực tiếp bởi nhà phân tích.
- **Khả năng tổng quát hóa (generalization)**: có thể sử dụng các mô hình đã huấn luyện trước (pre-trained), không cần xây dựng môi trường gym chuyên biệt cho mỗi bài toán mới.
- **Tri thức rộng**: đã được huấn luyện trên dữ liệu từ nhiều mô hình mối đe dọa (threat model) và kiến trúc mạng đa dạng.

Tuy nhiên, cũng trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], các tác giả đã chỉ ra **ba hạn chế quan trọng** của tác nhân LLM trong môi trường ACD, mà đề tài này hướng đến giải quyết:

#### Hạn chế 1 — Ảo giác (hallucination) khi đọc vectơ truyền thông

CybORG CAGE 4 yêu cầu các tác nhân phòng thủ (blue agent) trao đổi vectơ truyền thông nhị phân 8 bit mỗi lượt. LLM nhận vectơ này dưới dạng mảng nhị phân thô (ví dụ `[0,0,0,0,0,1,1,1]`) và phải tự diễn giải ý nghĩa của từng bit. Trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], quan sát thực nghiệm cho thấy LLM thường xuyên đọc nhầm — gán nhầm vectơ cho tác nhân gửi sai, hoặc đọc nhầm mức độ xâm phạm (compromise level) được mã hóa trong các bit cuối.

#### Hạn chế 2 — Lệ thuộc vào cách diễn đạt prompt

Khi định nghĩa các hành động trong prompt thay đổi chỉ một vài từ, hành vi của LLM thay đổi đột ngột. Theo thực nghiệm trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], khi không định nghĩa rõ hành động `Remove`, LLM giả định ý nghĩa khác hoàn toàn (ngắt kết nối máy chủ thay vì xóa tiến trình độc hại), dẫn đến chiến lược sai lệch trong toàn bộ episode.

#### Hạn chế 3 — Thiếu định hướng phần thưởng (reward direction)

Khác với tác nhân RL được huấn luyện trực tiếp với hàm phần thưởng (reward function), LLM hành động dựa trên prompt và không nắm được mục tiêu tối ưu hóa định lượng. Theo phân tích trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2], LLM thiên vị các hành động phân tích (Analyse) và đánh lừa (DeployDecoy) thay vì giải quyết triệt để vấn đề bằng Restore — dẫn đến tổng phần thưởng (joint reward) thấp hơn baseline RL khoảng 5 lần.

### 1.1.4 Cơ sở lý thuyết về Decision-Theoretic ACD

Bài báo *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1] đặt nền tảng lý thuyết quan trọng cho hướng nghiên cứu của đề tài: để con người có thể tin tưởng (trust) giao quyền cho AI phản ứng ở tốc độ máy móc trong an ninh mạng, hệ thống bắt buộc phải có cơ chế **human-on-the-loop** (con người giám sát có thể can thiệp khi cần) và **tuân thủ các đánh đổi rủi ro** do con người thiết lập sẵn. Đây chính là cơ sở lý luận để đề tài này áp dụng khái niệm **Rules of Engagement (RoE)** làm ranh giới kiểm soát an toàn cho tác nhân AI.

## 1.2 Mục tiêu nghiên cứu

### 1.2.1 Mục tiêu tổng quát

Xây dựng và đánh giá một kiến trúc tác nhân LLM phòng thủ mạng tự động kết hợp **Model Context Protocol (MCP)** cho cơ chế gọi công cụ (tool calling) có cấu trúc và **Rules of Engagement (RoE)** cho rào chắn quyết định tất định (deterministic policy enforcement), nhằm khắc phục ba hạn chế chính của tác nhân LLM được chỉ ra trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2].

### 1.2.2 Mục tiêu cụ thể

| Mã | Mục tiêu cụ thể |
|---|---|
| MT1 | Thiết kế và triển khai kiến trúc MCP + RoE cho tác nhân LLM trong môi trường CybORG CAGE 4 |
| MT2 | Đánh giá định lượng hiệu quả của kiến trúc đề xuất so với baseline trên năm chỉ số đo lường |
| MT3 | Phân tích định tính chất lượng suy luận (reasoning) của LLM trong môi trường có ràng buộc tất định |
| MT4 | Đề xuất framework đo lường tiêu chuẩn cho việc đánh giá LLM Agent an toàn trong ACD |
| MT5 | Cung cấp mã nguồn mở (open-source) có thể tái lập (reproducible) cho cộng đồng nghiên cứu |

## 1.3 Câu hỏi nghiên cứu

Nghiên cứu này trả lời **bốn câu hỏi (Research Question — RQ)** chính:

### RQ1 — Hiệu quả về tiêu thụ token

> *Việc sử dụng MCP cho phép LLM truy xuất trạng thái mạng có cấu trúc theo yêu cầu (on-demand) thay vì nhồi toàn bộ ngữ cảnh vào prompt như trong bài báo Large Language Models are Autonomous Cyber Defenders [2]. Liệu cơ chế này có thực sự giảm số token (đơn vị từ vựng cơ bản model xử lý) tiêu thụ trên CybORG CAGE 4 hay không?*

**Giả thuyết H1**: MCP làm giảm token tiêu thụ trung bình mỗi step ít nhất 30% so với kiến trúc baseline, với chi phí biên (marginal cost) giảm dần khi bộ nhớ đệm prompt (prompt cache) hoạt động hiệu quả qua các step.

### RQ2 — Hiệu quả giảm hallucination và invalid action

> *Cơ chế MCP (bộ giải mã vectơ truyền thông + tool schema có cấu trúc) kết hợp với RoE (danh sách cho phép — allow-list) có làm giảm tỉ lệ invalid action và comms misread so với baseline trong bài báo Large Language Models are Autonomous Cyber Defenders [2] hay không?*

**Giả thuyết H2**: Kiến trúc đề xuất giảm tỉ lệ invalid action ít nhất 50% và đưa tỉ lệ comms misread về dưới 5%.

### RQ3 — Hiệu quả về hiệu năng (reward)

> *Tác nhân LLM với MCP + RoE có đạt được điểm thưởng (joint reward — phần thưởng chung tích lũy của CybORG) tương đương hoặc tốt hơn kiến trúc baseline hay không?*

**Giả thuyết H3**: Tác nhân MCP + RoE đạt reward không thấp hơn baseline quá 30% (do RoE có thể chặn một số hành động tối ưu nhưng tiềm ẩn nguy cơ).

### RQ4 — Trade-off giữa an toàn và hiệu năng

> *Khi mở rộng tập rule RoE từ 3 lên 8-10 quy tắc, tỉ lệ RoE deny rate tăng nhưng reward thay đổi như thế nào? Tồn tại điểm tối ưu (Pareto-optimal point) không?*

**Giả thuyết H4**: Tồn tại đường cong trade-off rõ ràng giữa số lượng rule và reward, với điểm tối ưu nằm trong khoảng 6-8 rule.

## 1.4 Đóng góp dự kiến

### 1.4.1 Đóng góp lý thuyết

1. **Đề xuất kiến trúc tích hợp đầu cuối MCP + RoE cho LLM Agent trong ACD** — kết hợp:
   - Decoder pre-parse (giải quyết Hạn chế 1)
   - MCP Tool Allow-list với schema cứng (giải quyết Hạn chế 2 — phần ngữ nghĩa)
   - RoE Rule Engine tất định (giải quyết Hạn chế 2 — phần ràng buộc)
   - LLM ↔ RoE Feedback Loop (giải quyết Hạn chế 3)

2. **Framework đo lường tiêu chuẩn** — đề xuất 5 chỉ số đo lường + pass criterion để đánh giá LLM Agent an toàn trong ACD.

### 1.4.2 Đóng góp thực nghiệm

3. **Benchmark đối chiếu đầy đủ** giữa baseline trong bài báo *Large Language Models are Autonomous Cyber Defenders* [2] và kiến trúc đề xuất trên CybORG CAGE 4 với 60 episode (3 setup × 4 red variant × 5 episode).

4. **Phân tích định tính reasoning** của LLM khi bị ràng buộc bởi rule tất định — khía cạnh chưa được nghiên cứu trong bài báo gốc.

### 1.4.3 Đóng góp công cụ

5. **Mã nguồn mở reproducible** — repo public bao gồm prototype, test suite, benchmark scripts, hướng dẫn tái lập đầy đủ.

## 1.5 Phạm vi nghiên cứu

### 1.5.1 Trong phạm vi

- Môi trường mô phỏng: **CybORG CAGE 4** — kế thừa từ bài báo *Large Language Models are Autonomous Cyber Defenders* [2].
- Tác nhân: 1 blue agent điều khiển bởi LLM (với MCP + RoE), 4 blue agent còn lại dùng baseline RL có sẵn.
- Mô hình LLM: **Claude Haiku 4.5** — tương đương GPT-4o-mini về tier giá/tốc độ.
- Red agent: 4 biến thể (FiniteState, AggressiveFSM, StealthyFSM, ImpactFSM) — kế thừa từ môi trường mô phỏng.

### 1.5.2 Ngoài phạm vi

- Không so sánh với các framework guardrail / policy-as-code khác (Llama Guard, NeMo Guardrails, OPA, v.v.) — đề tài chỉ phát triển trên cơ sở 2 bài báo nền tảng.
- Không thử nhiều mô hình LLM khác nhau (GPT-4o, o3-mini, DeepSeek-V3) — chỉ tập trung vào Claude Haiku 4.5.
- Không kiểm thử trên hệ thống mạng thực — chỉ trong mô phỏng CybORG.

## 1.6 Bố cục luận văn

Luận văn gồm **6 chương** và **phụ lục**:

- **Chương 1 — Mở đầu** (chương hiện tại): trình bày bối cảnh, mục tiêu, câu hỏi nghiên cứu, đóng góp, phạm vi.
- **Chương 2 — Cơ sở lý thuyết**: phân tích chi tiết hai bài báo nền tảng [1] và [2], giới thiệu Model Context Protocol và khái niệm Rules of Engagement.
- **Chương 3 — Thiết kế hệ thống đề xuất**: trình bày kiến trúc tổng thể, decoder, MCP tool allow-list, RoE rule engine, feedback loop.
- **Chương 4 — Triển khai và Thực nghiệm**: mô tả môi trường thực nghiệm, triển khai prototype, ba kịch bản kiểm thử khả thi, thiết kế benchmark đầy đủ.
- **Chương 5 — Kết quả và Đánh giá**: phân tích định lượng theo 4 câu hỏi nghiên cứu, phân tích định tính reasoning, đối chiếu với pass criterion.
- **Chương 6 — Kết luận và Hướng phát triển**: tóm tắt đóng góp, hạn chế, đề xuất hướng nghiên cứu tương lai.
- **Phụ lục**: danh sách RoE rule đầy đủ, cấu trúc audit log, hướng dẫn tái lập thí nghiệm, mã nguồn chính.
