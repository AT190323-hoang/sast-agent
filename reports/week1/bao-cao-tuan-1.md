# Báo cáo Tuần 1 — Thu thập dữ liệu & Xây dựng Taxonomy

**Thời gian:** 14/09 – 17/09/2026
**Trạng thái:** Hoàn thành

## 1. Mục tiêu

Thu thập một bộ dataset findings từ SAST tool, phân loại vào 4 nhóm taxonomy
(`taint_flow`, `insecure_property`, `missing_control`, `broken_invariant`), gán nhãn TP/FP kèm
lý do cụ thể, và viết tài liệu taxonomy làm nền tảng cho 5 tuần tiếp theo.

## 2. Công việc đã thực hiện

### 2.1. Môi trường & công cụ

- Cài Opengrep v1.30.0 (fork OSS của Semgrep) làm SAST tool. Gặp và xử lý lỗi
  `CERTIFICATE_VERIFY_FAILED` do gateway TLS-inspection của công ty (Opengrep bundle CA riêng,
  không dùng trust store hệ thống) — fix bằng `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`.
- Xác nhận Docker Desktop WSL integration thực ra đã bật sẵn (vấn đề ban đầu chỉ là shell chưa
  nạp lại group `docker`).
- Clone 2 app mẫu: OWASP Juice Shop (Express/TypeScript, đã có sẵn) và crAPI (Django/Python +
  Java/Spring, clone mới trong tuần này).

### 2.2. Thu thập finding thô

- Quét Juice Shop backend (`routes/`, `lib/`, `models/`, `config/`, `server.ts`, `app.ts`) bằng
  rule pack registry (`auto`, `p/javascript`, `p/typescript`, `p/security-audit`,
  `p/owasp-top-ten`, `p/secrets`) — chủ yếu ra finding `taint_flow` và `insecure_property`.
- Quét crAPI (`workshop` — Django, `identity` — Java) bằng rule pack tương ứng ngôn ngữ.
- **Phát hiện quan trọng:** rule pack registry gần như không có rule nào cho `missing_control`
  và `broken_invariant` — bản thân đây là dữ liệu đáng ghi nhận (những nhóm này đòi hỏi hiểu
  ngữ nghĩa app-specific, vượt quá khả năng pattern-matching thuần cú pháp của rule chung).
- Viết 3 custom rule để bù khoảng trống: 2 rule cho `missing_control` (mutation theo
  request-id, route thiếu guard tường minh) và 2 rule cho `broken_invariant` ban đầu
  (`JSON.parse` không try/catch, chained access không null-check), sau đó bổ sung thêm 1 rule
  Django (`.get()` không try/except) khi phát hiện nhóm `broken_invariant` còn thiếu dữ liệu.
- Nguyên tắc bắt buộc cho mọi custom rule: chỉ match cú pháp **cục bộ** (1 file/1 lệnh gọi),
  không nhúng tri thức cross-file mà agent phải tự tìm — tránh phá vỡ chính luận điểm "SAST
  thiếu context" của đề tài.

### 2.3. Xây dựng dataset

- Viết script `dataset/scripts/normalize_findings.py`: gộp 6 file JSON output thô, khử trùng
  lặp theo (app, file, dòng, rule_id), map mỗi rule về 1 trong 4 nhóm qua bảng tường minh (rule
  lạ báo `UNCLASSIFIED` thay vì đoán). Script được thiết kế để **giữ nguyên id cũ** khi chạy
  lại — quan trọng vì nhãn tham chiếu finding theo id, tránh corrupt dữ liệu khi bổ sung finding
  mới.
- Viết script `dataset/scripts/apply_labels.py`: gộp nhãn từ `dataset/labels/*.json` (chia theo
  lô) vào dataset, cảnh báo nhóm nào chưa đạt ngưỡng ≥10 finding có cả TP và FP.

### 2.4. Gán nhãn

Đọc trực tiếp code liên quan cho từng finding (không chỉ dựa vào message của rule) để kết luận
TP/FP + lý do cụ thể + loại context cần thiết. Với case cần cross-reference (vd guard nằm ở file
khác), lần theo đến tận nơi thay vì suy đoán.

### 2.5. Tài liệu

- `docs/taxonomy.md`: định nghĩa 4 nhóm, 3 quy tắc phân định ranh giới (tránh mơ hồ giữa các
  nhóm), ví dụ TP/FP thật cho từng nhóm kèm code.
- `dataset/README.md`: phương pháp luận đầy đủ, các lưu ý quan trọng khi dùng dataset để đo
  agent ở tuần sau.

## 3. Kết quả

**87 finding**, cả 4 nhóm đều đạt ngưỡng ≥10 finding có cả TP và FP:

| Nhóm | TP | FP | Tổng | Tỷ lệ FP |
|---|---|---|---|---|
| `taint_flow` | 12 | 11 | 23 | 48% |
| `insecure_property` | 13 | 2 | 15 | 13% |
| `missing_control` | 2 | 24 | 26 | 92% |
| `broken_invariant` | 13 | 10 | 23 | 43% |
| **Tổng** | **40** | **47** | **87** | **54%** |

60 finding từ Juice Shop, 27 từ crAPI. Dataset đã freeze tại `dataset/findings_v1.json`.

## 4. Phát hiện đáng chú ý

Đây là phần tôi cho là giá trị nhất của Tuần 1 — không chỉ là số liệu mà là các **root-cause cụ
thể**, đặt nền cho Tuần 3-5:

1. **`missing_control` có 5 nguyên nhân FP khác nhau, không phải nhiễu ngẫu nhiên:** guard qua
   path-prefix middleware đăng ký sớm hơn; guard qua ownership-filter mà giá trị "tưởng
   attacker-controlled" thực ra bị middleware ghi đè; guard nằm inline ở file route khác; endpoint
   public-by-design; endpoint chỉ thao tác state toàn cục không gắn user cụ thể. Đây gần như là
   bản nháp cho báo cáo root-cause Tuần 4.

2. **Case cross-service sâu nhất:** để xác định `UserDetails.objects.get(user=user)` (crAPI) có
   phải bug thật không, phải lần qua 3 file, 2 microservice (Django + Java), và cả cấu hình
   `docker-compose.yml` (2 service dùng chung 1 database) mới kết luận được FP. Đây là ví dụ
   thực tế cho loại context-gathering đa bước mà AI agent Tuần 2+ cần làm được.

3. **Rule tự viết cũng có bug:** phát hiện chính custom rule của mình có 1 false-negative
   (pattern `except $EXC:` không khớp `except $EXC as $NAME:`), khiến 1 case đã được bảo vệ
   đúng cách vẫn bị flag nhầm (`CRAPI-0021`). Đã sửa rule cho Tuần 2, cố ý giữ nguyên case cũ
   trong dataset làm bằng chứng.

4. **Giới hạn về recall (ngoài phạm vi dataset):** lỗ hổng kinh điển nhất của Juice Shop (guard
   bị comment ở `server.ts:389`) không nằm trong dataset vì route đó do thư viện `finale` sinh
   tự động — không rule nào (registry lẫn custom) từng sinh ra finding để verify. Đây là vấn đề
   **recall**, khác với vấn đề **precision** mà đề tài tập trung giải quyết. Ghi nhận đầy đủ ở
   `docs/tien-do.md` và `dataset/README.md`.

## 5. Đối chiếu tiêu chí hoàn thành (theo đề bài)

| Tiêu chí | Trạng thái |
|---|---|
| Mỗi nhóm ≥10 finding đã gán nhãn, có cả TP và FP | ✅ Đạt cả 4 nhóm |
| Taxonomy được review, không có finding mơ hồ giữa 2 nhóm | 🔶 Tự review xong (không phát hiện case mơ hồ); **chưa có review độc lập bởi người thứ hai** |
| Mục tiêu 100 finding | 🔶 87 finding — theo trao đổi với mentor, 100 là "vừa đủ" chứ không phải ngưỡng cứng; ưu tiên chất lượng nhãn hơn số lượng |

## 6. Vấn đề còn mở

**Ai review nhãn độc lập?** Toàn bộ 87 nhãn hiện do một mình AI (Claude) suy luận, dưới sự giám
sát của người thực tập qua trao đổi trực tiếp trong quá trình làm, nhưng chưa có người thứ hai
đọc lại độc lập theo đúng nghĩa cross-review. Đề xuất: mentor dành thời gian xem qua 1 mẫu nhỏ
(~5-15 finding), ưu tiên các case `confidence: medium` (12/87 case) và các case root-cause phức
tạp.

## 7. Hướng Tuần 2

Theo chỉ đạo mentor: khảo sát agent-harness repo có sẵn để build tiếp (không viết vòng lặp
tool-calling từ đầu); dựng `codebase-memory-mcp` + tool grep/read_file; thiết kế thí nghiệm
no-tool vs with-tool để chứng minh harness thực sự cần thiết (không chỉ hỏi thẳng LLM). Chi tiết
task: `docs/ke-hoach-6-tuan.md` mục Tuần 2.
