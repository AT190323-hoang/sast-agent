# AI Agent Verify Findings Để Giảm FP Của SAST Tool

Thực tập 6 tuần tại VinSOC. Pipeline mục tiêu: **SAST tool sinh finding → AI agent tự thu thập
context trong codebase bằng tool → kết luận TP/FP + giải thích**, để loại bỏ false positive mà
không cần người review tay từng case.

Luận điểm cốt lõi: SAST tool báo sai **vì thiếu context**, không phải vì rule sai. Mỗi nhóm
finding thiếu một *loại* context khác nhau, nên được chia thành 4 nhóm để xử lý riêng.

## Trạng thái

| Tuần | Chủ đề | Trạng thái |
|---|---|---|
| 1 | Thu thập dữ liệu & Taxonomy | ✅ Hoàn thành |
| 2 | Xây dựng harness cho AI agent | 🔶 Đang làm |
| 3 | `taint_flow` — root-cause & giải pháp | ⬜ |
| 4 | `missing_control` + `insecure_property` — root-cause & giải pháp | ⬜ |
| 5 | `broken_invariant` — root-cause & giải pháp | ⬜ |
| 6 | Tích hợp & benchmark tổng thể | ⬜ |

Chi tiết tiến độ + nhật ký từng phiên làm việc: [`docs/tien-do.md`](docs/tien-do.md).

## Taxonomy 4 nhóm

| Nhóm | Bản chất | Context mà SAST thiếu → gây FP |
|---|---|---|
| `taint_flow` | Luồng dữ liệu source → sink (SQLi, XSS, path traversal) | Sanitizer tự viết không được nhận diện; sink không thực sự reachable từ input ngoài |
| `insecure_property` | Cấu hình/thuộc tính không an toàn (crypto yếu, cookie thiếu flag, hardcoded secret) | Giá trị cấu hình **thực tế lúc chạy**; cơ chế xác thực thật của hệ thống |
| `missing_control` | Thiếu auth/validation/guard | Guard được bind ở **nơi khác** (file khác, hàm khác, tên khác) |
| `broken_invariant` | Vi phạm bất biến (thiếu null-check, resource không đóng, sai giả định về API) | Bất biến đã được caller/hàm trước đó đảm bảo — vô hình với phân tích trong 1 hàm |

Định nghĩa đầy đủ, 3 quy tắc phân định ranh giới, và ví dụ TP/FP thật kèm code cho từng nhóm:
[`docs/taxonomy.md`](docs/taxonomy.md).

## Kết quả Tuần 1

Dataset ground truth đã freeze tại [`dataset/findings_v1.json`](dataset/findings_v1.json) —
**87 finding**, thu thập từ OWASP Juice Shop (Express/TypeScript) và crAPI
(Django/Python + Java/Spring) bằng Opengrep (registry rule pack + custom rule tự viết).

| Nhóm | TP | FP | Tổng |
|---|---|---|---|
| `taint_flow` | 12 | 11 | 23 |
| `insecure_property` | 13 | 2 | 15 |
| `missing_control` | 2 | 24 | 26 |
| `broken_invariant` | 13 | 10 | 23 |
| **Tổng** | **40** | **47** | **87** |

Báo cáo đầy đủ: [`reports/week1/bao-cao-tuan-1.md`](reports/week1/bao-cao-tuan-1.md).
Phương pháp luận + lưu ý quan trọng khi dùng dataset này để đo agent (giới hạn recall, quy
trình gán ground truth khác quy trình agent, versioning...):
[`dataset/README.md`](dataset/README.md).

## Cấu trúc thư mục

```
├── docs/
│   ├── lo-trinh-thuc-tap-6-tuan.pdf   # đề bài gốc + rubric chấm điểm
│   ├── ke-hoach-6-tuan.md             # kế hoạch chi tiết từng tuần
│   ├── tien-do.md                     # tracker tiến độ + nhật ký phiên làm việc
│   ├── moi-truong-va-cong-cu.md       # setup môi trường, lệnh chạy, troubleshoot
│   └── taxonomy.md                    # định nghĩa taxonomy + ví dụ (deliverable Tuần 1)
├── dataset/
│   ├── findings_v1.json               # ground truth đã freeze — KHÔNG sửa trực tiếp
│   ├── findings_draft.json            # finding thô đã chuẩn hoá, chưa gán nhãn
│   ├── labels/                        # nhãn TP/FP theo từng lô, khớp vào draft theo id
│   ├── scripts/                       # normalize_findings.py, apply_labels.py
│   └── README.md                      # phương pháp luận dataset
├── harness/
│   └── rules/                         # custom Opengrep rule (missing_control, broken_invariant)
└── reports/
    └── week1/                         # kết quả scan thô + báo cáo tuần
```

## Công cụ

- **SAST tool:** [Opengrep](https://github.com/opengrep/opengrep) (fork OSS của Semgrep, không
  giới hạn cross-file/interprocedural analysis như Semgrep Community).
- **App mẫu:** [OWASP Juice Shop](https://github.com/juice-shop/juice-shop) (Express/TypeScript)
  và [crAPI](https://github.com/OWASP/crAPI) (Django/Python + Java/Spring) — cả hai đều là ứng
  dụng cố ý chứa lỗ hổng, dùng cho mục đích học tập/nghiên cứu bảo mật.
- **LLM:** Claude (Anthropic), qua prompt + tool-calling — không tự huấn luyện/fine-tune model
  riêng (ngoài phạm vi đề tài).

Chạy lại pipeline dataset:
```bash
python3 dataset/scripts/normalize_findings.py   # gộp reports/week1/findings_raw*.json
python3 dataset/scripts/apply_labels.py         # gộp dataset/labels/*.json vào draft
```

Hướng dẫn cài Opengrep + xử lý lỗi TLS-inspection của mạng công ty:
[`docs/moi-truong-va-cong-cu.md`](docs/moi-truong-va-cong-cu.md).
