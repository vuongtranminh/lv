# Q&A PREP — Chuẩn bị câu hỏi thường gặp

## Câu hỏi về vấn đề và động lực

### Q1: Tại sao chọn LLM mà không phải RL?

**Trả lời**: RL có 3 hạn chế chính: khó giải thích, khó chuyển giao, huấn luyện tốn kém. LLM có ưu thế ở tính giải thích, tổng quát hóa, không cần dữ liệu huấn luyện. Bài báo *Large Language Models are Autonomous Cyber Defenders* [2] tiên phong chứng minh khả thi. Em mở rộng để fix 3 hạn chế LLM mà bài đó chỉ ra.

### Q2: Tại sao kết hợp MCP và RoE thay vì chỉ một trong hai?

**Trả lời**: 
- MCP một mình fix Hạn chế 1 (decoder JSON) nhưng không fix Hạn chế 2 và 3.
- RoE một mình thì LLM vẫn nhận observation lộn xộn (ảo giác).
- Kết hợp: MCP cho structure đầu vào, RoE cho structure đầu ra — đầu cuối.

### Q3: Bài *Large Language Models are Autonomous Cyber Defenders* [2] đã có những gì? Em làm gì khác?

**Trả lời**: Bài đó wrap LLM bằng custom adapter, nhồi observation text + raw 8-bit vào prompt. Em thay bằng MCP tool có schema cứng + decoder pre-parse + RoE rule engine + feedback loop. Khác về kiến trúc, không phải chỉ tweak prompt.

## Câu hỏi về kỹ thuật

### Q4: Vì sao chọn Claude Haiku 4.5 mà không phải GPT-4o-mini như bài báo *Large Language Models are Autonomous Cyber Defenders* [2]?

**Trả lời**: Hai lý do:
1. **Tier giá tương đương** — Haiku 4.5 nằm cùng phân khúc với GPT-4o-mini.
2. **Native MCP support** — Claude Agent SDK có sẵn MCP nội bộ; OpenAI cũng có function calling nhưng chưa chuẩn hóa thành protocol như MCP.

So sánh hoàn toàn công bằng vì chạy cùng môi trường CybORG, cùng red agent, cùng metric.

### Q5: RoE rule có bị cứng nhắc không? Khi attacker dùng kỹ thuật mới thì sao?

**Trả lời**: RoE rule cứng nhằm bảo đảm các invariant an toàn (vd Restore chỉ với admin compromise). Để xử lý kỹ thuật mới, em đề xuất 2 hướng:
1. **Tập rule mở rộng được** — thêm rule mới qua YAML/Python không cần retrain LLM.
2. **Default safe fallback** — khi state không match rule nào, fallback về Analyse (action an toàn) thay vì Sleep mù.

Phase 2 sẽ test với 4 red variant đa dạng để xác nhận robust.

### Q6: Latency 19-30 giây/step có khả thi real-time không?

**Trả lời**: Hiện tại **chưa** real-time strict. Nhưng:
- ACD không cần phản ứng <1s như IDS (SOC analyst thường có vài phút).
- Latency có thể giảm bằng prompt caching (đã đo cache_read tới 75K tokens) + giảm max_turns + chuyển sang Anthropic SDK direct (~2-3 lần nhanh hơn).
- Đây là cost cho **interpretability** + **safety** — trade-off có thể chấp nhận trong context human-on-the-loop.

### Q7: Tại sao chỉ 1 LLM agent + 4 RL? Tại sao không 5 LLM?

**Trả lời**: 
- Setup này khớp với scenario chính trong bài *Large Language Models are Autonomous Cyber Defenders* [2] — so sánh trực tiếp được.
- Test 5 LLM cũng đã thực hiện trong bài đó nhưng latency × 5 → không khả thi cho benchmark đầy đủ.
- Hướng phát triển tương lai: 5 LLM với RoE chung (multi-agent RoE).

## Câu hỏi về kết quả

### Q8: Reward Setup C thấp hơn baseline thì có nghĩa là kiến trúc em kém hơn?

**Trả lời**: Không. Vì:
1. RoE chặn một số action tối ưu nhưng nguy cơ → reward giảm là **trade-off có chủ ý**.
2. Quan trọng hơn: invalid action rate giảm 50%+, comms misread về <5% → AI **an toàn hơn**.
3. ACD ưu tiên **không gây thiệt hại** (não nguyên lý của bài *A Model-Based, Decision-Theoretic Perspective on Automated Cyber Response* [1]) hơn là tối ưu reward đơn thuần.

### Q9: Nếu pass criterion không đạt 3/5 thì sao?

**Trả lời**: Em có sẵn kế hoạch B trong Mục 7.3 của báo cáo kế hoạch: chuyển hướng sang **phân tích failure modes** — đây vẫn là contribution có giá trị vì rất ít paper viết về failure mode trong autonomous defense.

### Q10: Em có chạy thử với attacker đối kháng (adversarial) chưa?

**Trả lời**: Hiện chỉ test với red agent có sẵn trong bài *Large Language Models are Autonomous Cyber Defenders* [2] (FiniteState, Aggressive, Stealthy, Impact). Adversarial là hướng phát triển tương lai (đã đề cập trong Chương 6).

## Câu hỏi về phạm vi và đóng góp

### Q11: Đóng góp em mới ở đâu — khoảng trống nghiên cứu cụ thể là gì?

**Trả lời**: Theo bảng so sánh ở Chương 2.9:
- Không có công trình nào kết hợp **đủ** MCP + RoE + Decoder + đánh giá trên CybORG cho LLM agent.
- Llama Guard / NeMo Guardrails — chỉ guardrail đối thoại, không cho ACD.
- KEEP / Singh — RL, không phải LLM.
- TH3 — LLM nhưng không có RoE.

Đề tài em là công trình đầu tiên đặt 4 cấu phần này vào 1 kiến trúc đầu cuối cho ACD.

### Q12: Có thể áp dụng kiến trúc này vào hệ thống thực không?

**Trả lời**: Có, qua 3 bước:
1. Wrap CybORG MCP server thành plugin cho SIEM (Splunk, Sentinel).
2. Tích hợp với SOAR playbook hiện có (vd Phantom, XSOAR).
3. Triển khai theo mô hình human-on-the-loop — analyst review trước khi commit action.

Đây là hướng phát triển tương lai em đề cập trong Chương 6.

### Q13: Tại sao em chỉ chạy 60 episode? Có ít quá không?

**Trả lời**: 
- 60 episode đã cho thấy xu hướng rõ (3 setup × 4 red × 5 episode).
- Bài *Large Language Models are Autonomous Cyber Defenders* [2] cũng chỉ chạy 2 episode/setup vì cost — em đã chạy nhiều hơn.
- Cost: 60 episode × 500 step ≈ 30 giờ wall time + tiền token API.

### Q14: Vì sao em dùng K-Means + PCA mà không phải HDBSCAN / DBSCAN cho clustering reasoning?

**Trả lời**: K-Means + PCA là phương pháp được bài *Large Language Models are Autonomous Cyber Defenders* [2] dùng (§IV.E) — em kế thừa để **so sánh trực tiếp** với baseline của bài. Hướng phát triển: thử HDBSCAN trong tương lai.

## Câu hỏi về thực thi

### Q15: Code có open-source không?

**Trả lời**: Có. Sau khi bảo vệ, em sẽ public repo trên GitHub kèm:
- Code prototype + Phase 2 đầy đủ
- Test suite
- Audit log của 60 episode benchmark
- Hướng dẫn reproduce đầy đủ
- License: Apache 2.0 (tương thích với CybORG)

### Q16: Em mất bao lâu để thực hiện đề tài này?

**Trả lời**: 
- Giai đoạn 0 (feasibility) đã xong ~1,5 tháng.
- Phase 2 + viết luận văn ~3-4 tháng tập trung (em sắp xếp lịch làm việc liên tục).
- Tổng ~5 tháng.

### Q17: Nếu thầy yêu cầu thay đổi hướng, em có sẵn sàng không?

**Trả lời**: Có. Nếu thầy thấy hướng nào quan trọng hơn (vd: tăng số rule, áp dụng môi trường mới), em sẵn sàng điều chỉnh. Hiện kiến trúc đã sẵn extensible — thêm rule chỉ là update file `rules.py`.
