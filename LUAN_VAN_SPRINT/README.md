# LUẬN VĂN MCP + RoE — Sprint workspace

> Theo phản hồi của thầy: bỏ kế hoạch 30 tuần. Làm liên tục, không chia thời gian.
> Hot topic — chậm là người khác publish trước.

---

## File chính

**`ACTION_ITEMS.md`** — toàn bộ checklist việc cần làm (5 block A-E, ~30 item).

Mỗi item có file output cụ thể. Tick ✓ khi xong.

---

## Cấu trúc folder

```
LUAN_VAN_SPRINT/
├── README.md                      ← bạn đang đọc
├── ACTION_ITEMS.md                ← MASTER CHECKLIST — bắt đầu từ đây
│
├── 00_SPRINT_PLAN/
│   └── SPRINT_4_TUAN.md           ← (legacy, tham khảo)
│
├── 01_BAO_CAO_THAY/               ← Đã gửi thầy
│   ├── BAO_CAO_BUOC_1.md/.docx
│   └── KE_HOACH_DE_TAI.md/.docx
│
├── 02_TAI_LIEU_NEN_TANG/          ← Khảo sát related work (block A)
│   ├── A1_llama_guard.md
│   ├── A2_nemo_guardrails.md
│   ├── A3_opa.md
│   ├── A4_keep.md
│   ├── A5_singh_hierarchical.md
│   ├── A6_netsecgame.md
│   ├── A7_mcp_spec.md
│   ├── A8_cyborg.md
│   ├── A9_recent_papers.md
│   ├── A10_so_sanh_tinh_moi.md
│   ├── LT1_GHI_CHU.md
│   ├── TH3_GHI_CHU.md
│   └── DANH_SACH_PAPER.md
│
├── 03_CODE_THUC_NGHIEM/           ← link sang feasibility-mcp-roe/
│   └── README.md
│
├── 04_LUAN_VAN_DRAFT/             ← 6 chương + phụ lục (block D)
│   ├── CHUONG_1_MO_DAU.md
│   ├── CHUONG_2_TONG_QUAN.md
│   ├── CHUONG_3_THIET_KE.md
│   ├── CHUONG_4_TRIEN_KHAI.md
│   ├── CHUONG_5_KET_QUA.md
│   ├── CHUONG_6_KET_LUAN.md
│   └── PHU_LUC.md
│
└── 05_BAO_VE/                     ← Slides + demo (block E)
    ├── SLIDES_OUTLINE.md
    ├── DEMO_SCRIPT.md
    └── QA_PREP.md
```

---

## Cách dùng

1. Mở `ACTION_ITEMS.md`
2. Pick item nào không phụ thuộc cái khác — bắt đầu làm
3. Tick ✓ khi xong, update PROGRESS LOG
4. Làm song song nhiều item không liên quan nhau (vd: A1 đọc paper + B1 viết code)
5. CybORG install (C1) chạy nền

## Code

Code thực nghiệm vẫn ở `../feasibility-mcp-roe/`. Folder `03_CODE_THUC_NGHIEM/` chỉ là pointer/note.
