# Dataset — Ground Truth Tuần 1

## File

| File | Vai trò |
|---|---|
| `findings_v1.json` | **Frozen — ground truth chính thức, dùng đo accuracy suốt Tuần 2-6.** Không sửa trực tiếp. |
| `findings_labeled.json` | Bản build ra từ `findings_draft.json` + `labels/*.json`, luôn khớp với `findings_v1.json` tại thời điểm freeze. Có thể regenerate bằng script, không commit tay. |
| `findings_draft.json` | Finding thô đã chuẩn hoá + phân nhóm taxonomy, **chưa** gán nhãn TP/FP. |
| `labels/*.json` | Nhãn gán theo từng lô (theo nhóm taxonomy hoặc theo đợt bổ sung), khớp vào `findings_draft.json` theo `id`. Đây là nguồn "thật" của nhãn — sửa nhãn thì sửa ở đây, không sửa trực tiếp file build ra. |
| `scripts/normalize_findings.py` | Gộp `reports/week1/findings_raw*.json` → `findings_draft.json`. Giữ nguyên `id` cũ khi chạy lại (chỉ cấp id mới cho finding thực sự mới) — **không được đổi lại thành đánh số tuần tự từ đầu**, sẽ làm sai lệch mapping nhãn. |
| `scripts/apply_labels.py` | Gộp `labels/*.json` vào `findings_draft.json` → `findings_labeled.json`. Báo lỗi nếu nhóm nào chưa đạt ≥10 finding có cả TP và FP. |

## Số liệu (v1, freeze ngày 17/09/2026)

| Nhóm | TP | FP | Tổng | Tỷ lệ FP |
|---|---|---|---|---|
| `taint_flow` | 12 | 11 | 23 | 48% |
| `insecure_property` | 13 | 2 | 15 | 13% |
| `missing_control` | 2 | 24 | 26 | 92% |
| `broken_invariant` | 13 | 10 | 23 | 43% |
| **Tổng** | **40** | **47** | **87** | **54%** |

Nguồn: 60 finding từ OWASP Juice Shop (Express/TypeScript), 27 finding từ crAPI (Django/Python
+ Java/Spring). Chi tiết định nghĩa từng nhóm + ví dụ: `docs/taxonomy.md`.

## ⚠️ Lưu ý phương pháp luận — bắt buộc đọc trước khi dùng dataset này để đo agent

### 1. Quy trình gán ground truth KHÁC quy trình agent bị kiểm tra

Nhãn TP/FP trong dataset này được gán bằng cách để Claude đọc finding + code liên quan + tự
grep/trace context cần thiết, **tự do không giới hạn tool hay số lượt**, rồi kết luận. Đây
**không phải** kiến trúc agent sẽ dùng ở Tuần 2+ (bị giới hạn tool cụ thể, vòng lặp tool-calling
tường minh, có log từng bước). Hai quy trình phải khác nhau — nếu không, "agent Tuần 2+ cải
thiện nhờ tool" sẽ chỉ là so sánh LLM với chính nó, không có ý nghĩa. Khi báo cáo accuracy của
agent trên dataset này, luôn nói rõ đây là so với ground truth **do LLM gán (có kiểm tra chéo
nội bộ), không phải do chuyên gia con người độc lập gán**.

### 2. Dataset chỉ phản ánh RECALL của bộ rule đã dùng, không phải mọi lỗ hổng có thể có

Mọi finding trong dataset đến từ 1 trong 2 nguồn: rule registry (Semgrep/Opengrep) hoặc custom
rule tự viết (`harness/rules/`). Nếu một loại lỗ hổng không được rule NÀO bắt (registry lẫn
custom), nó **không xuất hiện trong dataset này**, bất kể có thật hay không. Ví dụ cụ thể đã
xác nhận: lỗ hổng kinh điển nhất của Juice Shop (guard `isAuthorized()` bị comment ở
`server.ts:389`) không có trong dataset vì route đó do thư viện `finale` sinh tự động, không
tồn tại như 1 câu lệnh tường minh để rule pattern-matching bắt được. Đây là giới hạn **recall**,
nằm ngoài phạm vi đề tài (đề bài không yêu cầu cải thiện recall, chỉ yêu cầu verify finding đã
có — xem `docs/lo-trinh-thuc-tap-6-tuan.pdf`). Số liệu accuracy đo trên dataset này chỉ có giá
trị cho **loại finding mà bộ rule Tuần 1 có khả năng sinh ra**, không suy rộng ra mọi pattern
lỗ hổng có thể tồn tại.

### 3. Custom rule chỉ được dùng thông tin cục bộ, không nhúng sẵn đáp án

Mọi custom rule trong `harness/rules/` chỉ match cú pháp trong phạm vi 1 file/1 lệnh gọi, không
bao giờ mã hoá tri thức cross-file mà chính agent phải tự tìm (ví dụ: không viết rule biết
trước route nào đã có guard ở `server.ts`). Nếu vi phạm nguyên tắc này, finding sẽ nhúng sẵn
ground truth, phá vỡ chính luận điểm "SAST thiếu context" của đề tài.

### 4. Về việc gán nhãn — chưa có review độc lập bởi người thứ hai

Toàn bộ 87 nhãn hiện tại do một mình Claude suy luận (dưới sự giám sát/thảo luận của người thực
tập). Chưa có mentor hoặc người thứ hai độc lập xác nhận lại. Nếu phát hiện nhãn sai sau này,
**không sửa trực tiếp `findings_v1.json`** — tạo `findings_v2.json` + ghi rõ trong
`CHANGELOG.md` (mục nào đổi, vì sao, ai phát hiện).

### 5. Rule tự viết cũng có bug — đã tìm ra và sửa 1 case cụ thể

`CRAPI-0021` là ví dụ: custom rule `django-get-without-trycatch` có pattern
`except $EXC:` không khớp cú pháp `except $EXC as $NAME:`, khiến 1 case đã được bảo vệ đúng
cách vẫn bị flag nhầm. Rule đã sửa trong `harness/rules/` (dùng cho Tuần 2+), nhưng **cố ý giữ
nguyên** file scan gốc (`reports/week1/findings_raw_crapi_broken_invariant.json`) và nhãn trong
dataset — rerun sẽ làm case này biến mất, mất đi bằng chứng cho việc rule tự viết cũng cần được
kiểm chứng, không chỉ code của app.

## Khi nào tạo v2?

Chỉ khi: (a) phát hiện nhãn sai sau review độc lập, hoặc (b) cần bổ sung finding cho một nhóm
cụ thể (ví dụ nếu benchmark Tuần 6 phát hiện `broken_invariant` vẫn cần thêm dữ liệu). **Không**
tạo v2 chỉ vì Tuần 3-5 phát hiện thêm pattern lỗ hổng ngoài dataset — những case đó dùng làm ví
dụ minh hoạ định tính trong báo cáo root-cause, không nhét ngược vào ground truth định lượng.
