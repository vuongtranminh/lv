# DEMO SCRIPT — Live demo trong slide 11

## Setup trước khi bảo vệ

- [ ] Mở terminal full screen, font lớn (>=18pt)
- [ ] Pre-cd vào `feasibility-mcp-roe/`
- [ ] Verify Claude Code đã login (`claude /status`)
- [ ] Verify code chạy thử trước 1 giờ — không có lỗi
- [ ] Backup: chuẩn bị video screencast 2 phút phòng case live demo lỗi

## Kịch bản demo (~3-5 phút)

### Bước 1 — Show offline test (~30 giây)

```bash
python3 tests/test_offline.py
```

Nói: *"Đây là 11 unit test kiểm thử logic deterministic — decoder và RoE engine. Tất cả pass trong dưới 1 giây."*

### Bước 2 — Show scenario 1 (happy path) (~1 phút)

```bash
python3 run_smoke.py
```

Khi output chạy, chỉ vào:
1. **BƯỚC 1**: observation raw có 8-bit `[0,0,0,0,0,1,1,1]` — *"đây là cái LLM gốc trong bài báo phải đọc"*
2. **BƯỚC 2**: state đã decode JSON — *"đây là cái Claude của em thấy — không bao giờ chạm bit thô"*
3. **BƯỚC 4**: Claude reasoning tiếng Việt + tool calls — *"đây là chuỗi suy luận của AI"*
4. **BƯỚC 5**: Final action `Restore host_a` + audit log

### Bước 3 — Show scenario 2 (RoE deny + self-correct) (~1 phút)

```bash
python3 scenario_2_roe_deny.py
```

Chỉ vào:
1. **PART A**: gọi trực tiếp `_propose("Restore", ...)` với user-level → RoE DENIED với lý do tiếng Việt — *"RoE là rào chắn cứng, không phụ thuộc LLM"*
2. **PART B**: inject denial vào prompt → Claude reasoning: *"Tôi hiểu rồi. Block bị từ chối..." → chuyển DeployDecoy* — *"đây là vòng tự sửa sai"*

### Bước 4 — Show audit log (~30 giây)

```bash
less logs/scenario_2_roe_deny_20260611_133811.txt
```

Lướt qua nội dung, chỉ vào reasoning Claude bằng tiếng Việt: *"audit log của em đọc được ngay, không cần dịch — phù hợp môi trường nghiên cứu Việt Nam."*

### Bước 5 — Show kết quả benchmark đầy đủ (~1 phút)

```bash
cat benchmark/results/summary.md
```

Hoặc mở biểu đồ:

```bash
open benchmark/results/clustering.png
open benchmark/results/reward_comparison.png
```

Nói tóm tắt 3-4 con số chính: *"Setup C đạt X/5 tiêu chí. Reward Y. RoE deny rate Z%."*

## Plan B — Nếu live demo lỗi

1. Mở video screencast đã chuẩn bị sẵn (`demo_backup.mp4` ~2 phút)
2. Nói: *"Để tiết kiệm thời gian, em đã chuẩn bị sẵn video demo..."*
3. Nếu video cũng lỗi → mở log file static (`logs/scenario_1_happy_path_*.txt`) đọc qua các phần BƯỚC 1-5

## Câu chuyện chính khi demo

Sợi dây xuyên suốt:
1. Code Python decode bit → JSON (không phải prompt) — fix Hạn chế 1
2. MCP tool có schema cứng → LLM không tự sáng tạo action — fix Hạn chế 2 phần 1
3. RoE rule deterministic → chặn được action sai — fix Hạn chế 2 phần 2
4. RoE deny có lý do tiếng người → LLM tự sửa sai — fix Hạn chế 3

Demo phải làm thầy/hội đồng **thấy được** 4 điểm này trong code chạy thật, không chỉ trong slide.
