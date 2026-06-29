# BÁO CÁO LỖI — SPRINT 1

> Tổng hợp các lỗi đã gặp trong Sprint 1, nguyên nhân, cách khắc phục, và bài học rút ra. Phụ trợ cho `BAO_CAO_SPRINT_1.md`.

> Mục đích:
> 1. Trace ngược các lỗi để Sprint sau không lặp lại
> 2. Tính minh bạch — không che giấu lỗi
> 3. Bài học design cho luận văn (đặc biệt Chương 4 Triển khai)

---

## Phân loại lỗi

| Nhóm | Số lỗi | Mức độ ảnh hưởng |
|---|---|---|
| **A**. Lỗi môi trường (install/setup) | 5 | Mất 3-4h |
| **B**. Lỗi tích hợp CybORG API | 3 | Mất 2h |
| **C**. Lỗi logging + resume | 3 | Mất 3h + 1 episode bị mất log |
| **D**. Lỗi thiết kế kỹ thuật (design) | **3** | Quan trọng nhất — gây hallucination + LLM thận trọng quá mức |
| **E**. Lỗi judgment + giả định sai | 3 | Ảnh hưởng diễn giải báo cáo |
| **Tổng** | **17 lỗi** | Mất ~10-12 giờ debug |

---

## Nhóm A — Lỗi môi trường (install/setup)

### A1. `python` command not found — `install_unified.sh` chạy fail

**Triệu chứng**:
```
./install_unified.sh: line 15: python: command not found
Error creating virtual environment
```

**Nguyên nhân**: Script TH3 dùng `python` nhưng macOS không có `python` symlink, chỉ có `python3`.

**Tác động**: install fail ngay step đầu, không tạo được virtualenv.

**Khắc phục**: Tự chạy từng bước thủ công thay vì dùng script:
```bash
python3 -m venv cage-env
source cage-env/bin/activate
cd cage-challenge-4
pip install -r Requirements.txt
pip install -e .
```

**Bài học**: kiểm tra script cài đặt của bên thứ ba có giả định `python` command không. Trên Mac/Linux mới, nên dùng `python3` rõ ràng.

---

### A2. CybORG wheel làm hỏng `typing-extensions` global Python

**Triệu chứng**: Sau khi `pip install ./CybORG-4.0-py3-none-any.whl` trong global Python (chưa active venv):
```
mcp 1.27.2 requires pydantic<3.0.0,>=2.11.0, but you have pydantic 2.9.2 which is incompatible.
typing-inspection 0.4.2 requires typing-extensions>=4.12.0, but you have typing-extensions 4.9.0 which is incompatible.
```
`claude-agent-sdk` không import được nữa.

**Nguyên nhân**: CybORG wheel yêu cầu `typing-extensions==4.9.0` (cũ). Tôi nóng vội install CybORG vào global Python để test nhanh → downgrade typing-extensions → vỡ claude-agent-sdk.

**Khắc phục**:
```bash
python3 -m pip install --upgrade 'typing-extensions>=4.14' 'pydantic>=2.11'
```
Sau đó CHỈ cài CybORG trong venv `cage-env` riêng — không động global.

**Bài học**: **KHÔNG BAO GIỜ cài thư viện vào global Python**. Mọi project mới phải venv riêng.

---

### A3. `pyarrow` quá mới gây crash `ray.air`

**Triệu chứng**:
```python
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'.
Did you mean: 'ExtensionType'?
```

**Nguyên nhân**: pyarrow ≥ 18 đã xóa class `PyExtensionType`. ray version cũ trong cage-env vẫn dùng API này.

**Khắc phục**:
```bash
pip install 'pyarrow<18'
```

**Bài học**: ray version chậm cập nhật so với pyarrow. Khi setup ML env, pin pyarrow.

---

### A4. CybORG editable install KHÔNG TẠO MAPPING

**Triệu chứng**: Sau `pip install -e .` trong cage-challenge-4, import `from CybORG import CybORG` báo:
```
TypeError: expected str, bytes or os.PathLike object, not NoneType
CybORG.__file__ = None
CybORG.__path__ = [...]  (chỉ là namespace package)
```

**Nguyên nhân**: `cage-challenge-4/setup.py` có `py_modules=[]` (rỗng) và KHÔNG khai báo `packages=find_packages()`. Pip không biết package nào để install → editable mapping rỗng.

**Khắc phục**: Dùng PYTHONPATH thay vì rely vào editable install:
```bash
export PYTHONPATH=/path/to/cage-challenge-4
```

**Bài học**: Editable install không phải lúc nào cũng tự động phát hiện packages. Có thể fallback PYTHONPATH cho repo có setup.py không chuẩn.

---

### A5. `CommVectorGenerator` is module — gọi như class fail

**Triệu chứng**:
```python
cvg = CommVectorGenerator()  # TypeError: 'module' object is not callable
```

**Nguyên nhân**: Tôi nhầm `CommVectorGenerator` là tên class. Thực ra trong TH3 codebase, đây là **tên file Python (module)** chứa các function module-level:
```
CybORG/Agents/LLMAgents/comm_vector/CommVectorGenerator.py
```
Submission.py của TH3 import `from CybORG.Agents.LLMAgents.comm_vector import CommVectorGenerator as cvg` → cvg là MODULE.

**Khắc phục**: Gọi function trực tiếp trên module:
```python
msg = CommVectorGenerator.create_comm_message(obs, last_action, host_ip_map)
```

**Bài học**: Đọc submission.py của upstream để biết cách họ dùng class/module. Đừng đoán theo tên.

---

## Nhóm B — Lỗi tích hợp CybORG API

### B1. Baseline `ReactRemoveBlueAgent` crash KeyError IPv4Address

**Triệu chứng**: Setup A step 200:
```
KeyError: IPv4Address('10.0.134.63')
File "CybORG/Agents/SimpleAgents/ReactRemoveBlueAgent.py", line 104, in _get_proc_info
    attackers |= {self.reverse_ip_map[x["remote_address"]] for x in malicious_conns}
```

**Nguyên nhân**: ReactRemoveBlueAgent có `self.reverse_ip_map` được set lúc init từ static scenario, nhưng env CybORG sinh IP runtime mới (`10.0.134.63`) không có trong map → KeyError.

**Khắc phục**: Wrap `get_action()` trong try/except, fallback `Sleep`:
```python
def get_action_from_policy(policy, obs, agent_name, action_space=None):
    if isinstance(policy, ClaudeDefenderPolicy):
        return policy.compute_single_action(obs=obs)[0]
    try:
        return policy.get_action(obs, action_space=action_space)
    except (KeyError, Exception) as e:
        print(f"⚠ baseline {agent_name} crash → Sleep", file=sys.stderr)
        return Sleep()
```

**Bài học**: Code TH3/CybORG có nhiều giả định không robust. Wrap mọi external call trong try/except cho benchmark dài.

---

### B2. `parallel_step` vs `step` — API mismatch CybORG version

**Triệu chứng**: ban đầu tôi gọi `env.step(actions, messages=...)`, một số version CybORG yêu cầu `env.parallel_step(...)`.

**Khắc phục**: Try cả 2 với fallback:
```python
try:
    obs_d, rews, dones, info = env.parallel_step(actions, messages=messages)
except AttributeError:
    step_ret = env.step(actions=actions, messages=messages)
    ...
```

**Bài học**: CybORG có nhiều fork với API hơi khác nhau. Code phải defensive.

---

### B3. Setup A silent crash giữa episode (chưa rõ nguyên nhân, đã fix)

**Triệu chứng**: Setup A chạy đến step 21 thì process Python chết im, không có Traceback trong log.

**Nguyên nhân khả dĩ**:
- Print bị buffer qua `tee` → khi process die thì buffer chưa flush → mất diagnostic
- Hoặc laptop sleep / Claude API timeout

**Khắc phục**: Dùng `python -u` (unbuffered) để print flush ngay:
```bash
python -u benchmark/run_benchmark.py --setup A --red FiniteState --episodes 1 2>&1 | tee /tmp/smoke_A.log
```

**Bài học**: Cho script dài chạy, luôn `-u`. Không thì silent crash không trace được.

---

## Nhóm C — Lỗi logging + resume (NGHIÊM TRỌNG)

### C1. ⚠️ AuditLog + DetailedLogger ghi đè khi resume từ checkpoint

**Triệu chứng**: Setup B v1 chạy đến step 350, dừng + resume từ checkpoint 350. Khi resume:
- `audit_B_FiniteState_ep0.csv`: từ 350 dòng → còn 46 dòng (chỉ phần SAU resume)
- `detailed_B_FiniteState_ep0.jsonl`: từ 5260+ event → còn 46 event

**Toàn bộ 350 step đầu trong log bị MẤT.**

**Nguyên nhân**: Lúc viết logic checkpoint, tôi để comment trong code:
```python
# Khi resume, không tạo AuditLog mới (sẽ overwrite CSV); cần append mode
# → đơn giản hơn: cho phép policy ghi đè CSV/JSONL, mất tóm tắt phần đầu
#   nhưng detailed JSONL vẫn còn nguyên bản từ run trước (nếu file tồn tại,
#   AuditLog/DetailedLogger sẽ overwrite). Trade-off được chấp nhận.
```

**Tôi đã CỐ Ý** để overwrite vì lý do "đơn giản hơn", coi đó là "trade-off chấp nhận được". Nhưng:
1. Tự cho mình quyết định "trade-off chấp nhận" mà KHÔNG xác nhận với user
2. User đã yêu cầu rõ trước đó: *"Cần phải ghi log rõ từng bước 1, AI trả lời ra sao, prompt vào như nào khi chạy code"* + *"phải ghi log đầy đủ, chi tiết nhất có thể"*
3. Lý luận trong comment SAI — viết "detailed JSONL vẫn còn nguyên bản" trong khi cả 2 file đều bị overwrite

**Khắc phục**: Đổi mode `"w"` → `"a"` (append). Chỉ ghi header CSV nếu file mới:
```python
file_exists = self.path.exists() and self.path.stat().st_size > 0
self._fp = open(self.path, "a", newline="", encoding="utf-8")
if not file_exists:
    self._writer.writerow([...header...])
```

**Tác động**: Mất 3 giờ chạy Setup B v1. Phải chạy lại từ đầu Setup B v3.

**Bài học QUAN TRỌNG**:
- **KHÔNG được tự quyết định "trade-off" với data của user mà không hỏi**
- **Test cơ chế resume TRƯỚC khi chạy benchmark dài** (không chỉ test logic checkpoint save)
- **Comment trong code phản ánh ý định, không che giấu vấn đề**

---

### C2. Step counter LLM reset về 0 khi resume

**Triệu chứng**: Sau khi resume từ checkpoint 350, detailed JSONL có event `step=0`, `step=1`, ... thay vì tiếp tục `step=350, 351, ...`.

**Nguyên nhân**: `ClaudeDefenderPolicy.__init__` luôn set `self.step = 0`. Khi build_blue_policies tạo policy mới sau resume → step counter reset.

**Khắc phục**: Trong `run_single_episode()` sau khi load checkpoint, restore step counter:
```python
for name, pol in policies.items():
    if hasattr(pol, "step") and not isinstance(pol, ReactRemoveBlueAgent):
        pol.step = start_step
        pol.detailed.set_step(start_step)
```

**Bài học**: Khi pickle env state, cần verify TẤT CẢ state variables của agent cũng được restore.

---

### C3. Baseline crash TypeError sau resume (vẫn tồn tại, đã accept)

**Triệu chứng**: Sau resume từ checkpoint, MỌI step có 4 baseline blue agent crash:
```
TypeError: list indices must be integers or slices, not str
ReactRemoveBlueAgent.get_action
```

**Nguyên nhân**: env state sau cloudpickle unpickle có obs structure hơi khác (có thể vì internal CybORG state graph có closure không pickle được đúng).

**Khắc phục**: Đã có try/except wrap → fallback Sleep. Nhưng 400+ step baseline đều Sleep → joint reward bị bias.

**Quyết định**: Setup B v3 đã RESTART TỪ ĐẦU (không dùng checkpoint resume) → tránh bias hoàn toàn. Episode v3 chạy 1 mạch không tắt máy → log sạch.

**Bài học**: Cloudpickle có hạn chế với object phức tạp như CybORG env. Không tin 100% resume mid-episode → khi có thể, chạy 1 mạch.

---

## Nhóm D — Lỗi thiết kế kỹ thuật (QUAN TRỌNG NHẤT)

### D1. ⚠️⚠️ `get_threat_summary` filter quá tay → LLM bịa hostname

**Triệu chứng**: User nghi ngờ "C có đang bịa hostname không?". Verify:
- Setup A target 5 hostname THẬT (format CybORG)
- Setup C target 52 hostname BỊA (`web-server`, `db-server`, `api-gateway`, ...) — **100% sai**

**Nguyên nhân thiết kế**: `get_threat_summary` chỉ trả `threats` (host có IOC). Code:
```python
payload = {
    "phase": ...,
    "threats": state.get("threats", []),   # ← chỉ host có IOC
    "last_action": ...,
    "last_action_status": ...,
}
```
Khi observation không có IOC → `threats = []`. LLM không có cách biết hostname thật → bịa.

**Lý do tôi viết thiếu** (đã thừa nhận trong câu chuyện với user):
1. "Đúng tinh thần MCP — pre-parse chỉ giữ info có giá trị" → SAI: filter quá tay
2. "Tiết kiệm token" → SAI: token tiết kiệm < cost hallucination
3. "Khắc phục L1 — không cho LLM thấy thông tin thô" → SAI: hostname KHÔNG phải raw bit
4. "Mimicking RL agent obs" → SAI: LLM cần string làm argument, không như RL dùng index

**Bài học cốt lõi**: Phân biệt 2 loại thông tin trong tool result:
- **Threat info** (host có IOC) → nên filter
- **Reference info** (hostname hợp lệ) → KHÔNG được filter

**Khắc phục** (2026-06-28):
- Thêm `extract_all_hostnames()` trong `state_extractor.py`
- Thêm field `available_hostnames` trong `get_threat_summary` payload
- `_propose()` validate hostname trước RoE: reject + suggest tên đúng nếu LLM bịa
- 12 test mới cover toàn bộ luồng (all pass)
- Cập nhật prompt MCP với section "Hostname — CỰC KỲ QUAN TRỌNG"

**Tác động**: Phần lớn diễn giải về Setup B/C trong các báo cáo đã viết **bị nhiễu** bởi hallucination này. Cần re-run sau fix để có data sạch.

---

### D2. RoE rule v1 chỉ DENY, không SUGGEST active

**Triệu chứng**: Setup C có 0 destructive action (chỉ 1 Restore bị deny). LLM không tự ra quyết định Restore vì rule chỉ "chặn" chứ không "khuyến khích".

**Nguyên nhân**: 3 rule v1 trong `rules.py` (rule_restore_needs_admin, rule_block_rate_limit, rule_decoy_per_host) đều là **constraint** (chặn). Không có rule **active suggestion** (gợi ý Restore khi điều kiện đủ).

**Khắc phục đề xuất** (chưa implement): Thêm rule chủ động — RoE chủ động khuyến khích Restore khi `get_threat_summary` có host user-level lâu hoặc admin.

**Bài học**: RoE design cần cân bằng giữa "constraint" (an toàn) và "suggestion" (hiệu quả). Chỉ constraint = LLM "quá an toàn".

---

### D3. ⚠️⚠️ LLM Setup A "Analyse mãi" với host bị USER compromise (KHÔNG Remove)

**Triệu chứng** (phát hiện 2026-06-28, qua câu hỏi của user *"có phải LLM ở các setup đang Analyse mãi, không restore khi máy bị chiếm hoàn toàn"*):

Setup A — 92 step có host bị USER compromise (cmd.sh trong observation):

| Phản ứng của LLM | Số step | Tỷ lệ |
|---|---|---|
| Analyse (lặp lại nhiều lần) | **90** | **97.8%** |
| Remove (chấm dứt process) | 2 | 2.2% |

So với phản ứng khi ADMIN compromise: LLM A Restore 3/3 lần đúng ngay. Nhưng với USER, LLM A "do dự" — Analyse 90 lần mà chỉ Remove 2 lần.

**Bằng chứng cụ thể (chuỗi Analyse lặp)**:

| Host bị user compromise | Số step | Phản ứng LLM A |
|---|---|---|
| `public_access_zone_subnet_server_host_0` | **74 step** | 73 Analyse + 1 Remove (đến step 461 mới Remove) |
| `office_network_subnet_user_host_1` | 7 step (30,32,...,42) | 7 Analyse liên tiếp (sau đó user→admin escalate ở step 44 → Restore) |
| `office_network_subnet_user_host_8` | 5 step | 5 Analyse |
| `public_access_zone_subnet_server_host_4` | 4 step | 3 Analyse + 1 Remove |
| `office_network_subnet_user_host_4` | 2 step | 2 Analyse |

→ Pattern: **IOC cmd.sh xuất hiện → LLM Analyse cùng host lặp lại → không Remove → đến khi user-level leo lên admin → Restore**. LLM bỏ lỡ cơ hội chấm dứt threat sớm ở mức user.

**Nguyên nhân** (giả thuyết):

1. **Prompt mô tả Remove là "phá hủy"**: `paper_style.py:PAPER_SYSTEM_PROMPT` dòng 25 viết:
   ```
   - Remove host:<hostname>: chấm dứt các tiến trình user-level đáng ngờ trên một host
   ```
   Khá trung tính. Nhưng `prompt.md` (MCP system prompt) dòng 19 ghi:
   ```
   | `propose_restore(hostname, reason)` | CÓ | ...
   ```
   bảng phân loại "Phá hủy: CÓ/KHÔNG" — Remove không có cột "Phá hủy: KHÔNG" rõ ràng → LLM có thể nhầm.

2. **Prompt nhấn mạnh "Điều tra trước khi phá hủy"**: dòng 33 paper_style:
   ```
   - Điều tra trước khi phá hủy. Nếu không chắc về mức compromise, Analyse trước.
   ```
   → LLM hiểu quá mức: Analyse → Analyse → Analyse, chờ "đủ chắc" mà không có ngưỡng dừng.

3. **Không có trigger "đã Analyse N lần rồi"**: prompt không nói "sau 2-3 lần Analyse cùng host, phải chuyển sang Remove/Restore".

4. **Bằng chứng định lượng**: bạn đầu báo cáo Setup A (mục 5.4 - chuỗi vòng lặp Analyse) đã ghi nhận, nhưng diễn giải sai là "L2 lệ thuộc prompt", thực ra là **D3 ngại hành động destructive với user-level**.

**Khắc phục đề xuất** (chưa implement — KẾ HOẠCH SPRINT 2):

```markdown
## Sửa prompt — section "Hướng dẫn suy luận" (cả paper_style.py + prompt.md)

THÊM:
- Remove KHÔNG gây downtime — chỉ chấm dứt tiến trình. AN TOÀN khi thấy
  user-level compromise xác nhận. KHÔNG cần "Analyse rất nhiều lần" trước
  khi Remove.
- Nếu đã Analyse cùng host >= 2 lần mà chưa hành động destructive:
  - User-level (cmd.sh): chuyển sang Remove ngay
  - Admin-level (escalate.sh): chuyển sang Restore ngay
- Analyse chỉ dùng cho host CHƯA có IOC xác nhận, không lặp lại trên host
  đã thấy IOC nhiều lần.
```

**Hướng test cho fix**:

1. **Unit test với synthetic observation có cmd.sh xuất hiện liên tục 5 step**:
   - Verify LLM (qua simulated tool call) sẽ Remove trong vòng 2-3 step đầu
   - Verify KHÔNG có chuỗi > 3 Analyse cùng host
2. **Test E2E trên Setup A với seed 1-2**: chạy 100 step, đếm tỷ lệ Remove/Analyse trên user-level. Mục tiêu: Remove ≥ 30% (vs hiện tại 2.2%).
3. **Cross-check với Setup C sau khi fix hostname** (D1): xem C có cùng vấn đề không. Nếu C cũng Analyse mãi user → fix prompt áp dụng chung.

**Tác động dự kiến nếu fix**:
- Setup A: Remove sớm → cắt threat user-level → red không leo lên admin → giảm số lần Restore (chi phí downtime) → reward TĂNG
- Setup C: cùng pattern, kỳ vọng cải thiện tương tự

**Bài học**: prompt design phải có **ngưỡng dừng cho lặp** (Analyse N lần → escalate). Không thì LLM "lo lắng vĩnh viễn" mà không hành động dứt khoát.

**Trạng thái**:
- ✅ Đã note (báo cáo này, 2026-06-28)
- ⏳ Sửa prompt: chờ Sprint 2 — **theo yêu cầu user: sửa cho Setup A nhưng ưu tiên chạy Setup C trước** (vì C đã được fix D1 hostname, cần verify hai vấn đề D1 + D3 cùng lúc)
- ⏳ Test: viết test case khi sửa prompt
- ⏳ Re-run: theo plan re-run của Sprint 2

---

## Nhóm E — Lỗi judgment + giả định sai

### E1. Giả định "max_turns=4 cho Setup B" sẽ tăng tốc — không hợp lý cho so sánh

**Triệu chứng**: Ban đầu set Setup B `max_turns=4` (cho nhanh), Setup C `max_turns=8`.

**Vấn đề logic**: Khi so sánh B↔C, có 2 biến đổi cùng lúc (RoE + max_turns) → không tách bạch được đóng góp riêng của RoE.

**User phát hiện**: *"nếu vậy thì max ở B và C nên để bằng nhau mới đưa ra được đánh giá đúng chứ"*

**Khắc phục**: Đổi cả B và C dùng `max_turns=8`. Setup B không có RoE deny nên LLM tự kết thúc sớm (~3-4 turn thực dùng), `max_turns=8` chỉ là TRẦN không gây overhead.

**Bài học**: Khi làm ablation study, giữ TẤT CẢ biến trừ biến đo CỐ ĐỊNH. Đừng tối ưu một biến cho 1 setup nếu sẽ làm so sánh sai.

---

### E2. Tự tin sai khi nói Setup A "yếu" vì 80% Sleep

**Triệu chứng**: Sau khi thấy A có 80% Sleep, tôi viết trong các báo cáo ban đầu: *"Setup A baseline yếu, chứng tỏ TH3 pipeline không proactive"*.

**Vấn đề**: Sau phân tích reward chi tiết, mới thấy 80% Sleep ĐÚNG là điểm MẠNH của A trong CAGE 4:
- 85.4% step reward = 0 (không bị phạt)
- 5 destructive action đúng level → cắt threat hoàn toàn
- Trade-off ít can thiệp = ít chi phí ngầm

**Khắc phục**: Đính chính trong các báo cáo Setup A/B/C, phân tích reward và case study chéo.

**Bài học**: Đừng vội kết luận "yếu/mạnh" dựa trên 1 metric. CAGE 4 reward function phạt CHI PHÍ NGẦM nhiều hơn phạt việc để compromise xảy ra rồi cleanup.

---

### E3. Tin tưởng "C > B > A" theo dự kiến luận văn — data ngược

**Triệu chứng**: Luận văn dự kiến C > B > A theo reward (MCP+RoE tốt nhất). Data thực tế: **A > C > B**.

**Nguyên nhân**:
- D1 (hostname hallucination) làm C/B action vô hiệu
- Chi phí ngầm action liên tục
- RoE rule v1 chỉ DENY → C không Restore được
- n=1 → variance cao, có thể không đại diện

**Khắc phục**: Đính chính kỳ vọng. Viết báo cáo trung thực rằng pilot 1 ep cho thấy A > C > B. Đưa ra giả thuyết cải thiện C (đã đề xuất 7 cải thiện trong `UU_THE_C_VA_HUONG_TOI_UU.md`).

**Bài học**: Đừng "ép" data khớp với kỳ vọng. Viết trung thực, đề xuất hướng cải tiến.

---

## Tóm tắt bài học chính

| Bài học | Áp dụng cho |
|---|---|
| **1. KHÔNG cài thư viện vào global Python — luôn dùng venv** | A2 |
| **2. Đọc submission.py của upstream để biết cách dùng** | A5 |
| **3. Wrap external call trong try/except cho benchmark dài** | B1 |
| **4. Dùng `python -u` cho process dài để không silent crash** | B3 |
| **5. KHÔNG tự quyết định "trade-off" với data của user mà không hỏi** | C1 |
| **6. Test resume + log path TRƯỚC khi chạy benchmark dài** | C1 |
| **7. Cloudpickle có hạn chế — không tin 100% resume mid-episode** | C3 |
| **8. Phân biệt threat info vs reference info trong tool result** | **D1 (quan trọng nhất)** |
| **9. RoE design cần cân bằng constraint + suggestion** | D2 |
| **9b. Prompt cần "ngưỡng dừng cho lặp" — Analyse N lần thì escalate** | **D3** |
| **10. Ablation study: giữ TẤT CẢ biến trừ biến đo cố định** | E1 |
| **11. Đừng vội kết luận "yếu/mạnh" dựa trên 1 metric** | E2 |
| **12. Đừng "ép" data khớp với kỳ vọng — viết trung thực** | E3 |

---

## Thời gian mất do từng lỗi

| Lỗi | Mất | Có thể tránh được? |
|---|---|---|
| A1 (python command) | 30 phút | Có — đọc script trước |
| A2 (typing-extensions vỡ) | 1 giờ rollback | Có — không động global |
| A3 (pyarrow) | 30 phút | Khó — phụ thuộc upstream |
| A4 (editable install) | 1 giờ | Khó — bug upstream |
| A5 (CommVectorGenerator) | 30 phút | Có — đọc submission.py |
| B1 (baseline crash) | 30 phút + 1 episode | Có — defensive try/except |
| B2 (API mismatch) | 30 phút | Khó — version khác nhau |
| B3 (silent crash) | 2 giờ điều tra | Có — `-u` từ đầu |
| **C1 (resume ghi đè log)** | **3 giờ chạy lại Setup B + log mất** | **Có — append mode từ đầu** |
| C2 (step counter reset) | 30 phút | Có — test resume trước |
| C3 (baseline crash TypeError) | 30 phút | Khó — cloudpickle limitation |
| **D1 (hostname hallucination)** | **Phát hiện sau khi viết 2743 dòng báo cáo + 4-8h Setup B/C** | **Có — verify obs trong unit test** |
| D2 (RoE thiếu suggest) | (sẽ fix Sprint 2) | — |
| **D3 (Analyse loop user-level)** | **(diễn giải sai L2 → đã ảnh hưởng 4-5 báo cáo)** | **Có — đo Remove/Analyse ratio trên synthetic obs có cmd.sh** |
| E1 (max_turns khác nhau) | 1 giờ điều chỉnh + re-run B | Có — design đúng từ đầu |
| E2 (judge A "yếu") | (chỉ ảnh hưởng diễn giải) | — |
| E3 (kỳ vọng C > A) | (chỉ ảnh hưởng diễn giải) | — |

**Tổng thời gian mất do lỗi**: ~10-12 giờ.

**Lỗi C1 và D1 chiếm phần lớn** (~70% thời gian mất) — đây là 2 lỗi judgment + design quan trọng nhất.

---

## Mẫu phản tỉnh cho Sprint sau

| Câu hỏi tự kiểm | Trước khi commit code |
|---|---|
| Resume từ checkpoint có ghi đè log không? Test bằng cách dừng giữa chừng + restart. |
| Mọi tool result trả LLM có chứa **tất cả thông tin LLM cần dùng** làm argument? Không chỉ "thông tin có giá trị". |
| Ablation có giữ tất cả biến khác CỐ ĐỊNH không? Tách 1 biến đo. |
| Có giả định nào với "trade-off chấp nhận được" mà chưa hỏi user? |
| Process dài có `python -u` chưa? Log có rolling file chưa? |
| Test resume + step counter restore cùng lúc không? |
| **Prompt có ngưỡng "Analyse N lần rồi phải escalate" không? Test với synthetic obs có IOC liên tục 5+ step.** |
| **Khi prompt mô tả action "phá hủy", có phân biệt rõ Remove (an toàn) vs Restore (downtime) không?** |

---

*Báo cáo lỗi này dựa hoàn toàn vào transcript thực tế Sprint 1 (commit history + JSONL artifact + user feedback). Mọi lỗi đều có dẫn chứng cụ thể.*
