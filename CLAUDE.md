# CLAUDE.md — Bối cảnh dự án cho phiên làm việc mới

> File này là điểm vào cho mọi phiên Claude Code mới. Đọc file này trước, sau đó đọc
> `docs/tien-do.md` để biết đang làm tới đâu, rồi mới bắt tay vào việc.

## 1. Đề tài

**AI Agent Verify Findings Để Giảm FP Của SAST Tool** — thực tập 6 tuần tại VinSOC.

Pipeline mục tiêu: **SAST tool sinh finding → AI agent tự thu thập context trong codebase bằng
tool → kết luận TP/FP + giải thích**, để loại bỏ false positive mà không cần người review tay
từng case.

Luận điểm cốt lõi: SAST tool báo sai **vì thiếu context**, không phải vì rule sai. Nên agent
phải có công cụ tự đào context còn thiếu trước khi kết luận. Mỗi nhóm finding thiếu một *loại*
context khác nhau → xử lý riêng từng nhóm.

Tài liệu gốc (bắt buộc đọc khi cần chi tiết/rubric): `docs/lo-trinh-thuc-tap-6-tuan.pdf`
Kế hoạch chi tiết 6 tuần: `docs/ke-hoach-6-tuan.md`
Tiến độ hiện tại: `docs/tien-do.md`  ← **luôn cập nhật file này cuối mỗi phiên**

## 2. Taxonomy 4 nhóm (xương sống của cả đề tài)

| Nhóm | Bản chất | Context mà SAST thiếu → gây FP |
|---|---|---|
| `taint_flow` | Luồng dữ liệu source → sink (SQLi, XSS, path traversal) | Sanitizer tự viết không được nhận diện; sink không thực sự reachable từ input ngoài |
| `insecure_property` | Cấu hình/thuộc tính không an toàn (crypto yếu, cookie thiếu flag, hardcoded secret) | Giá trị cấu hình **thực tế lúc chạy** (env var, override ở file config khác) |
| `missing_control` | Thiếu auth/validation/guard | Guard được bind ở **file khác** (global middleware, route table trong `server.ts`) |
| `broken_invariant` | Vi phạm bất biến (thiếu null-check, resource không đóng, sai state machine) | Bất biến đã được caller/hàm trước đó đảm bảo — vô hình với phân tích trong 1 hàm |

Định nghĩa đầy đủ + ví dụ: `docs/taxonomy.md` (deliverable Tuần 1).

## 3. Cấu trúc thư mục

```
~/projects/vinsoc-sast-agent/          # repo này
├── CLAUDE.md                          # file này
├── docs/
│   ├── lo-trinh-thuc-tap-6-tuan.pdf   # đề bài gốc + rubric
│   ├── ke-hoach-6-tuan.md             # kế hoạch chi tiết từng tuần
│   ├── tien-do.md                     # tracker tiến độ + nhật ký phiên
│   ├── moi-truong-va-cong-cu.md       # setup môi trường, lệnh chạy, troubleshoot
│   └── taxonomy.md                    # deliverable Tuần 1
├── dataset/                           # ground truth (deliverable Tuần 1, dùng xuyên suốt)
├── harness/                           # agent harness (deliverable Tuần 2+)
│   └── rules/                         # custom Opengrep rules
└── reports/                           # kết quả scan, log chạy agent, báo cáo tuần
    └── week1/

~/projects/targets/juice-shop/         # app mẫu chính (OWASP Juice Shop, Express/TS)
```

## 4. Môi trường — những thứ dễ vấp

Chi tiết đầy đủ ở `docs/moi-truong-va-cong-cu.md`. Tóm tắt những thứ hay làm hỏng việc:

**Mạng công ty có TLS inspection (Vingroup Web Gateway).** CA của Vingroup ĐÃ có trong trust
store hệ thống (`/etc/ssl/certs/ca-certificates.crt`) nên `curl`/`git` chạy bình thường. Nhưng
tool nào **tự bundle Python/OpenSSL riêng** (Opengrep là một ví dụ) sẽ không dùng store hệ
thống và báo `CERTIFICATE_VERIFY_FAILED`. Cách chạy Opengrep luôn phải kèm:

```bash
export PATH="$HOME/.local/bin:$PATH"
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
opengrep scan --config auto <target> --json --output <out>.json
```

Lỗi SSL kiểu này **không phải lỗi code** — đừng đi sửa code, chỉ cần trỏ đúng CA bundle.

**Các ràng buộc khác của máy này:**
- `sudo` **cần mật khẩu** → không tự chạy `apt install`. Cần cài gì thì đưa lệnh cho user chạy
  bằng cú pháp `! <lệnh>` trong prompt.
- `node`/`npm` **chưa có** → sẽ là blocker khi cần chạy Juice Shop thật hoặc chạy
  codebase-memory-mcp (Tuần 2). Cần xử lý trước Tuần 2.
- `docker` chưa bật WSL integration trong Docker Desktop.
- `pip` đã được bootstrap thủ công (`--user`), gọi bằng `python3 -m pip`.

**Bẫy của Opengrep:** một `--config p/<tên>` sai (vd `p/nodejsscantypescript` → 404) sẽ làm
**toàn bộ lần chạy trả về 0 finding**, không phải chạy một phần. Luôn kiểm tra mảng `errors`
trong JSON output, đừng chỉ nhìn số lượng results.

## 5. Quy ước làm việc

- **Ngôn ngữ:** trao đổi và viết tài liệu bằng **tiếng Việt** (deliverable nộp cho VinSOC).
  Code, tên field trong dataset, tên file giữ tiếng Anh.
- **Nhịp làm việc:** làm **từng chunk nhỏ rồi dừng lại báo cáo**, không dồn cả tuần vào một
  lượt chạy tool liên tục. User muốn cùng bàn bạc làm rõ yêu cầu ở mỗi phần việc.
- **Không tự ý `git commit`/`push`** khi user chưa yêu cầu.
- **Dữ liệu là tài sản chính:** `dataset/` là ground truth dùng cho cả 6 tuần. Không sửa nhãn
  TP/FP sau khi đã freeze mà không ghi lại lý do + version.
- **Mọi con số accuracy phải tái lập được:** mỗi lần chạy agent lưu vào
  `reports/runs/<ngày>_<biến-thể>/` kèm prompt/tool version đã dùng.

## 6. Đang làm tới đâu?

→ Xem `docs/tien-do.md`. Tóm tắt nhanh tại thời điểm viết file này: **Tuần 1 đã hoàn thành**
(dataset `dataset/findings_v1.json` — 87 finding, 4 nhóm đều ≥10 TP+FP — đã freeze;
`docs/taxonomy.md` + `reports/week1/bao-cao-tuan-1.md` đã viết xong). **Đang chuyển sang
Tuần 2** — xây dựng harness cho AI agent. Đọc `dataset/README.md` trước khi dùng dataset để đo
accuracy agent (có vài lưu ý phương pháp luận quan trọng, đặc biệt về giới hạn recall).
