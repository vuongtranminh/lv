# CHƯƠNG 5 — KẾT QUẢ VÀ ĐÁNH GIÁ

> Chương này trình bày kết quả thực nghiệm trên 60 episode benchmark thiết kế ở Chương 4.
> **Các bảng số liệu cụ thể sẽ được điền sau khi hoàn thành benchmark** — hiện đang ở
> trạng thái dự thảo với khung phân tích đầy đủ.

## 5.1 Tổng quan thí nghiệm đã chạy

### 5.1.1 Cấu hình

- **3 setup**: A (baseline) / B (MCP only) / C (MCP + RoE)
- **4 red variant**: FiniteState, AggressiveFSM, StealthyFSM, ImpactFSM
- **5 episode/cấu hình** × 500 step/episode
- **Tổng**: 60 episode

### 5.1.2 Khối lượng dữ liệu thu thập

| Loại dữ liệu | Quy mô |
|---|---|
| Audit log CSV (mỗi step) | 60 × 500 = 30.000 dòng |
| Reasoning text (mỗi step) | ~30.000 đoạn văn |
| Token usage (mỗi LLM call) | ~30.000 ResultMessage |
| Wall clock time per step | ~30.000 mẫu thời gian |

## 5.2 Phân tích định lượng theo từng câu hỏi nghiên cứu

### 5.2.1 RQ1 — Token Consumption

**Giả thuyết H1**: MCP làm giảm token tiêu thụ trung bình mỗi step ít nhất 30%.

**Phương pháp đo**: lấy `usage.input_tokens + cache_creation + cache_read` từ ResultMessage mỗi LLM call. Tính trung bình theo step, so sánh A vs C.

**Kết quả**:

[Bảng 5.1 — Token tiêu thụ trung bình mỗi step theo setup × red variant]

| Setup | FiniteState | AggressiveFSM | StealthyFSM | ImpactFSM | Trung bình |
|---|---|---|---|---|---|
| A (baseline) | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| B (MCP only) | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| C (MCP + RoE) | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

[Hình 5.1 — Biểu đồ token consumption theo step number (đường cong) cho 3 setup]

**Phân tích chi phí biên (marginal cost)**:

[Hình 5.2 — Marginal token cost (so với step trước) theo step number]

→ Sau khi prompt cache warm (khoảng step thứ 10-20), chi phí biên ổn định ở mức [TBD] token/step cho Setup C so với [TBD] cho Setup A.

**Kết luận RQ1**: [Sau khi có data → kết luận H1 đúng / sai / một phần]

### 5.2.2 RQ2 — Invalid Action & Comms Misread Rate

**Giả thuyết H2**:
- Invalid action rate Setup C ≤ 0,5 × Setup A.
- Comms misread rate Setup C < 5%.

**Phương pháp đo**:
- Invalid action rate: đếm dòng audit log có `final_action == "Sleep (no action proposed)"` / tổng step.
- Comms misread rate: gán nhãn thủ công 50 dòng audit log ngẫu nhiên mỗi setup, đếm số dòng reasoning sai về comm vector.

**Kết quả**:

[Bảng 5.2 — Invalid action rate]

| Setup | FiniteState | AggressiveFSM | StealthyFSM | ImpactFSM | Trung bình |
|---|---|---|---|---|---|
| A | [TBD]% | [TBD]% | [TBD]% | [TBD]% | [TBD]% |
| B | [TBD]% | [TBD]% | [TBD]% | [TBD]% | [TBD]% |
| C | [TBD]% | [TBD]% | [TBD]% | [TBD]% | [TBD]% |

[Bảng 5.3 — Comms misread rate (gán nhãn thủ công)]

| Setup | Mẫu | Số sai | Tỉ lệ |
|---|---|---|---|
| A | 50 | [TBD] | [TBD]% |
| B | 50 | [TBD] | [TBD]% |
| C | 50 | [TBD] | [TBD]% |

**Kết luận RQ2**: [Sau khi có data]

### 5.2.3 RQ3 — Reward So với Baseline

**Giả thuyết H3**: Reward Setup C ≥ Setup A − 30%.

**Phương pháp đo**: lấy joint reward từ CybORG ở cuối mỗi episode. Tính trung bình + độ lệch chuẩn theo setup × red variant.

**Kết quả**:

[Bảng 5.4 — Joint Reward trung bình ± độ lệch chuẩn]

| Setup | FiniteState | AggressiveFSM | StealthyFSM | ImpactFSM | Trung bình |
|---|---|---|---|---|---|
| A | [µ ± σ] | [µ ± σ] | [µ ± σ] | [µ ± σ] | [µ ± σ] |
| B | [µ ± σ] | [µ ± σ] | [µ ± σ] | [µ ± σ] | [µ ± σ] |
| C | [µ ± σ] | [µ ± σ] | [µ ± σ] | [µ ± σ] | [µ ± σ] |

[Hình 5.3 — Box plot Joint Reward × 3 setup × 4 red variant]

**Phân tích**: [Sau khi có data — thảo luận về việc liệu RoE có làm giảm reward đáng kể không]

**Kết luận RQ3**: [Sau khi có data]

### 5.2.4 RQ4 — Trade-off Rule Count vs Reward

**Giả thuyết H4**: Tồn tại điểm tối ưu (Pareto-optimal) trong khoảng 6-8 rule.

**Phương pháp đo**: chạy thêm các biến thể của Setup C với số rule khác nhau (3, 5, 8, 10). Đo reward + RoE deny rate cho từng cấu hình.

**Kết quả**:

[Bảng 5.5 — Setup C với số rule khác nhau]

| Số rule | Tên rule | RoE Deny Rate | Reward trung bình |
|---|---|---|---|
| 3 | restore_admin, block_rate, decoy_per_host | [TBD]% | [TBD] |
| 5 | + restore_phase, decoy_global_quota | [TBD]% | [TBD] |
| 8 | + block_critical, no_block_busy, restore_max | [TBD]% | [TBD] |
| 10 | + analyse_cooldown, action_requires_session | [TBD]% | [TBD] |

[Hình 5.4 — Đường cong Pareto: RoE Deny Rate (trục X) vs Reward (trục Y)]

**Phân tích**: [Sau khi có data — xác định điểm tối ưu]

**Kết luận RQ4**: [Sau khi có data]

## 5.3 Phân tích định tính

### 5.3.1 Phân cụm suy luận bằng K-Means

> **Phương pháp**: áp dụng kỹ thuật phân cụm của bài báo *Large Language Models are Autonomous Cyber Defenders* [2] mục IV.E.

**Quy trình**:

1. Thu thập tất cả cặp (action, reasoning_text) từ audit log của Setup C — ~7.500 cặp (5 episode × 4 red × 500 step).
2. Embedding `reasoning_text` bằng OpenAI `text-embedding-3-large` (3.072 chiều).
3. Giảm chiều bằng PCA xuống 3 thành phần chính.
4. Phân cụm bằng K-Means. Số cluster $K$ xác định qua Elbow Method và Silhouette Score.
5. Tóm tắt mỗi cluster bằng GPT-4o để có nhãn ngôn ngữ tự nhiên.

**Kết quả số cluster tối ưu**:

[Hình 5.5 — Elbow Method: WCSS theo K]
[Hình 5.6 — Silhouette Score theo K]

→ $K^* = $ [TBD] (sau khi chạy)

**Bảng đặc trưng cluster**:

[Bảng 5.6 — Đặc trưng từng cluster]

| Cluster | Số DP | Tóm tắt nội dung | Action chính |
|---|---|---|---|
| 0 | [TBD] | [TBD] | [TBD] |
| 1 | [TBD] | [TBD] | [TBD] |
| ... | | | |

[Hình 5.7 — Scatter plot 2D của các cluster sau khi giảm chiều bằng PCA]

### 5.3.2 So sánh số cluster giữa Setup B và Setup C

[Bảng 5.7 — So sánh phân cụm B vs C]

| Setup | K tối ưu | Đặc trưng nổi bật |
|---|---|---|
| B (MCP only) | [TBD] | [TBD] |
| C (MCP + RoE) | [TBD] | [TBD] |

**Phân tích**: [Sau khi có data — đánh giá liệu RoE có làm reasoning gọn hơn / tập trung hơn / đa dạng hơn không]

### 5.3.3 Audit log walkthrough — Các tình huống đặc trưng

#### Case 1 — Self-correction thành công sau RoE deny

[Trích đoạn audit log thật từ benchmark sau khi chạy]

#### Case 2 — Proactive defense khi state sạch

[Trích đoạn]

#### Case 3 — Phối hợp với teammate qua comms

[Trích đoạn]

### 5.3.4 So sánh reasoning của LLM Agent (Setup C) vs RL baseline (KEEP)

**Action distribution**:

[Bảng 5.8 — Phân bố action]

| Action | Setup C (LLM + MCP + RoE) | RL Baseline (KEEP) |
|---|---|---|
| Sleep | [TBD]% | [TBD]% |
| Monitor | (auto) | [TBD]% |
| Analyse | [TBD]% | [TBD]% |
| Remove | [TBD]% | [TBD]% |
| Restore | [TBD]% | [TBD]% |
| DeployDecoy | [TBD]% | [TBD]% |
| BlockTrafficZone | [TBD]% | [TBD]% |

**Diễn giải**: [So sánh phong cách phòng thủ chủ động (LLM) vs thụ động (RL)]

## 5.4 Tổng kết đánh giá theo Pass Criterion

[Bảng 5.9 — Đánh giá theo 5 chỉ số]

| Chỉ số | Tiêu chí | Kết quả Setup C | Đạt? |
|---|---|---|---|
| M2 — Invalid Action Rate | < 0,5 × Setup A | [TBD]% vs [TBD]% | ✓/✗ |
| M3 — RoE Deny Rate | 5% ≤ ≤ 40% | [TBD]% | ✓/✗ |
| M1 — Reward | ≥ Setup A − 30% | [TBD] vs [TBD] | ✓/✗ |
| M5 — Step Latency p95 | < 5 × Setup A | [TBD]s vs [TBD]s | ✓/✗ |
| M4 — Comms Misread Rate | < 5% | [TBD]% | ✓/✗ |

**Kết luận tổng**: [X/5] tiêu chí đạt → đề tài [thành công / có đóng góp / cần điều chỉnh].

## 5.5 Hạn chế quan sát được

[Liệt kê các vấn đề phát hiện trong quá trình thực nghiệm]

Một số hạn chế dự kiến:
- Latency của LLM (kể cả với prompt caching) vẫn cao hơn RL ~50-100×.
- Tập 8 rule chưa cover hết các tình huống edge case của CybORG CAGE 4.
- Phương pháp gán nhãn thủ công Comms Misread Rate có yếu tố chủ quan.

## 5.6 Phát hiện ngoài kỳ vọng

Trong Giai đoạn 0, đã quan sát thấy hiện tượng Claude **từ chối tuân thủ directive sai** trong prompt — cụ thể khi inject "block ngay không cần investigate", Claude vẫn yêu cầu investigate trước khi block. Phát hiện này gợi ý rằng:

- Prompt + tool design **tự nó cũng là một lớp phòng vệ** bên cạnh RoE deterministic.
- LLM được huấn luyện kỹ về safety alignment có khả năng từ chối instruction không hợp lý.

Trong Phase 2, sẽ theo dõi liệu hiện tượng này có tái xuất hiện ở các trường hợp khác không (ví dụ khi red agent tạo ra prompt injection qua dữ liệu observation).

## 5.7 Tổng kết Chương 5

- **Định lượng**: [tóm tắt 1-2 câu kết quả RQ1-RQ4 sau khi có data]
- **Định tính**: [tóm tắt phát hiện từ clustering reasoning]
- **Đối chiếu với 3 hạn chế của bài báo [2]**: [tóm tắt mức độ giải quyết]

Chi tiết kết luận và hướng phát triển được trình bày trong Chương 6.
