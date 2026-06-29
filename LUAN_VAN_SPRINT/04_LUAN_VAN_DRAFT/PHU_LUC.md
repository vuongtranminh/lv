# PHỤ LỤC

## Phụ lục A — Danh sách Rules of Engagement đầy đủ

[Liệt kê 8-10 rule sau khi mở rộng ở B1, mỗi rule có format:]

### Rule X — `<tên_rule>`

- **Loại**: Precondition / Rate-limit
- **Action áp dụng**: <Restore | BlockTrafficZone | DeployDecoy | ...>
- **Điều kiện check**: <pseudo-code>
- **Lý do khi deny**: <text>
- **Gợi ý thay thế**: <propose_xxx>

## Phụ lục B — Cấu trúc Audit Log CSV

| Cột | Kiểu | Mô tả |
|---|---|---|
| timestamp | ISO 8601 | Thời điểm log |
| step | int | Chỉ số step trong episode |
| agent | str | Tên blue agent |
| phase | str | MissionA / MissionB / Planning |
| threats_count | int | Số threat phát hiện |
| comms_count | int | Số comm vector nhận được |
| llm_reasoning | str | Text reasoning Claude |
| proposed_action | str | Action được LLM đề xuất |
| roe_rejections | str | Danh sách rejection (nếu có) |
| final_action | str | Action thực thi cuối cùng |

## Phụ lục C — Hướng dẫn Reproduce thí nghiệm

```bash
# 1. Clone repo
git clone https://github.com/<username>/feasibility-mcp-roe
cd feasibility-mcp-roe

# 2. Cài CybORG
cd ../llms-are-acd-main && ./install_unified.sh
source cage-env/bin/activate

# 3. Cài Python deps
cd ../feasibility-mcp-roe
pip install -r requirements.txt

# 4. Login Claude Code (1 lần)
/opt/homebrew/lib/python3.11/site-packages/claude_agent_sdk/_bundled/claude /login

# 5. Test offline
python tests/test_offline.py

# 6. 3 scenario nhanh
python run_all_scenarios.py

# 7. Full benchmark (chạy ~30h)
python benchmark/run_benchmark.py --all

# 8. Phân tích kết quả
python benchmark/analyze_clustering.py benchmark/results/
```

## Phụ lục D — Source code chính

### D.1 `state_extractor.py` (decoder)

```python
# Copy code từ feasibility/state_extractor.py
```

### D.2 `tools.py` (MCP tools)

```python
# Copy code từ feasibility/tools.py
```

### D.3 `rules.py` (RoE rules)

```python
# Copy code từ feasibility/roe/rules.py + rules_v2.py
```

### D.4 `claude_policy.py` (Ray RLlib policy)

```python
# Copy code từ feasibility/claude_policy.py
```

## Phụ lục E — Mẫu prompt tiếng Việt

```markdown
# Copy nội dung từ feasibility/prompt.md
```

## Phụ lục F — Bảng số liệu chi tiết

[Sau khi chạy benchmark, copy CSV summary vào đây]
