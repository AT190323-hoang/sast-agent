# Tiến độ dự án

> **Cập nhật file này vào cuối mỗi phiên làm việc.** Phiên Claude mới đọc `CLAUDE.md` → rồi
> file này → biết ngay đang ở đâu, việc tiếp theo là gì.

**Tuần hiện tại:** Tuần 1 — Thu thập dữ liệu & Taxonomy
**Cập nhật lần cuối:** 16/09/2026

---

## ⭐ Phát hiện quan trọng khi gán nhãn `missing_control` (16/09)

Case kinh điển nhất của Juice Shop (guard `security.isAuthorized()` bị comment out ở
`server.ts:389` cho `PUT /api/Products/:id`) **không nằm trong dataset**, dù đã quét bằng cả
registry rule lẫn custom rule. Lý do: route đó không tồn tại như một câu lệnh `app.put(...)`
tường minh — nó được **sinh tự động** bởi `finale.initialize({ app, sequelize: seq })` +
mảng `autoModels` (server.ts:500-522, thư viện REST scaffolding cho Sequelize model). Đây là
loại blind-spot **hoàn toàn khác** với "guard nằm ở file khác": không phải agent thiếu context
để verify, mà là **không có finding nào để verify từ đầu** (vấn đề recall của rule, xảy ra
trước cả bước SAST chạy). Đáng đưa vào tài liệu root-cause Tuần 4 như một giới hạn cần nêu rõ,
nhưng **không đưa vào dataset** vì không có tool nào thực sự tạo ra finding này (giữ đúng
nguyên tắc "dataset gồm finding do tool sinh ra", không tự chèn case biết trước đáp án).

Ngoài ra, khi gán nhãn 26 candidate `missing_control`, chỉ 2 là TP thật — 24 còn lại là FP
nhưng tách được **5 nguyên nhân FP khác nhau** (guard qua path-prefix middleware trong cùng
file; guard qua ownership-filter với giá trị bị middleware ghi đè trước khi tới handler; guard
nằm inline trong handler ở file route riêng; endpoint public-by-design theo nghiệp vụ; endpoint
thao tác state toàn cục không gắn với user cụ thể). Chi tiết đầy đủ + dẫn chứng từng dòng code:
xem `dataset/labels/missing_control.json`.

## Việc tiếp theo cần làm

1. Gán nhãn nốt `taint_flow` (23 candidate) và `insecure_property` (15 candidate) — chạy
   `python3 dataset/scripts/apply_labels.py` sau khi thêm mỗi file `dataset/labels/<nhóm>.json`.
2. Xử lý khoảng trống `broken_invariant` (7 candidate, cần ≥10): cân nhắc quét thêm service
   `chatbot` (Python) của crAPI, hoặc viết thêm 1 custom rule (resource không đóng, Django
   `.get()` có thể raise `DoesNotExist` không bắt).
3. **Chốt quy ước TP/FP** cho app cố ý chứa lỗi (câu hỏi #1 Tuần 1 — chưa chốt) và hỏi mentor
   về việc review nhãn (câu hỏi #4 — chưa chốt).
4. Viết `docs/taxonomy.md` (T1.7) — đã có rất nhiều ví dụ thật + lý do cụ thể trong
   `dataset/labels/*.json`, chỉ cần tổng hợp lại.
5. Review toàn bộ dataset đã gán nhãn (T1.8), rồi freeze thành `dataset/findings_v1.json` +
   viết `reports/week1/bao-cao-tuan-1.md` (T1.9).
6. Sau khi Tuần 1 xong: khảo sát agent-harness repo có sẵn cho Tuần 2 (T2.0).

---

## Bảng tiến độ tổng

| Tuần | Chủ đề | Trạng thái |
|---|---|---|
| 1 | Thu thập dữ liệu & Taxonomy | 🔶 Đang làm (~30%) |
| 2 | Xây dựng harness | ⬜ Chưa bắt đầu |
| 3 | `taint_flow` root-cause | ⬜ Chưa bắt đầu |
| 4 | `missing_control` + `insecure_property` | ⬜ Chưa bắt đầu |
| 5 | `broken_invariant` | ⬜ Chưa bắt đầu |
| 6 | Tích hợp & benchmark | ⬜ Chưa bắt đầu |

## Chi tiết Tuần 1

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| T1.1 | Cài Opengrep + fix lỗi CA | ✅ | Opengrep v1.30.0 tại `~/.local/bin/opengrep` |
| T1.2 | Scan registry packs trên Juice Shop | ✅ | 18 + 25 finding ở `reports/week1/` (có trùng lặp) |
| T1.3 | Custom rule cho 2 nhóm còn thiếu | ✅ | 4 rule đã sửa lỗi + validate sạch. Scan Juice Shop: 25 candidate `missing_control` + 7 candidate `broken_invariant` |
| T1.4 | Mở rộng nguồn finding (crAPI) | ✅ | Clone xong. Scan `workshop` (Django, 7 finding) + `identity` (Java, 4 finding) bằng registry pack. Chưa viết custom rule riêng cho BOLA/BFLA của crAPI — để dành khi gán nhãn (T1.6) đọc trực tiếp `shop/views.py`/`mechanic/views.py`, đây là nơi có ví dụ BOLA kinh điển |
| T1.5 | Schema dataset + script chuẩn hoá | ✅ | `dataset/scripts/normalize_findings.py` gộp 6 file, dedupe theo (app, file, dòng, rule_id), map rule→nhóm qua bảng tường minh (rule lạ sẽ báo `UNCLASSIFIED` thay vì đoán). Script đã sửa để **giữ nguyên id cũ khi chạy lại** (chỉ cấp id mới cho finding thực sự mới) — quan trọng vì `dataset/labels/*.json` tham chiếu finding theo id. Output: `dataset/findings_draft.json` — **87 finding** (missing_control 26, taint_flow 23, insecure_property 15, broken_invariant 23) |
| T1.6 | Gán nhãn TP/FP + lý do + `context_needed` | ✅ | **87/87 xong, cả 4 nhóm đạt ngưỡng ≥10 với cả TP lẫn FP.** `taint_flow` 12 TP/11 FP. `insecure_property` 13 TP/2 FP. `missing_control` 2 TP/24 FP (đã tách 5 loại nguyên nhân FP). `broken_invariant` 13 TP/10 FP (bổ sung 16 candidate từ rule mới `custom.broken-invariant.django-get-without-trycatch` quét crAPI — Django `.get()` không try/except). Phát hiện phụ: tìm ra chính custom rule của mình có 1 false-negative (pattern `except $EXC:` không khớp `except $EXC as $NAME:`) khi gán nhãn `CRAPI-0021` — đã sửa rule trong `harness/rules/`, nhưng **giữ nguyên** file scan gốc + nhãn trong dataset (không rerun) để không làm mất case này, vốn là ví dụ tốt cho báo cáo |
| T1.7 | Viết `docs/taxonomy.md` | ✅ | Định nghĩa 4 nhóm + 3 quy tắc phân định ranh giới + ví dụ TP/FP thật (kèm code) cho từng nhóm, rút từ `dataset/labels/*.json` |
| T1.8 | Review: ≥10 finding/nhóm, không mơ hồ | ⬜ | ≥10 đã đạt cả 4 nhóm (T1.6). Còn cần: mentor/người thứ 2 review 1 mẫu nhỏ (câu hỏi #4 Tuần 1 — chưa chốt) |
| T1.9 | Freeze dataset v1 + báo cáo tuần 1 | ⬜ | |

---

## Quyết định đã chốt

| Ngày | Quyết định | Lý do |
|---|---|---|
| 14/09 | Dùng **Opengrep** làm SAST tool | Fork OSS của Semgrep, không bị giới hạn cross-file/interprocedural như Semgrep CE, vẫn chạy được rule từ Semgrep registry |
| 14/09 | **Juice Shop** là app mẫu chính cho Tuần 1 | Code Express/TypeScript thật, có middleware/ORM nên sinh FP thực tế, sát mục tiêu đề tài hơn WebGoat |
| 14/09 | ~~crAPI để dành cho Tuần 4~~ → **thay đổi 15/09** (xem dưới) | |
| 15/09 | **Scan crAPI ngay trong Tuần 1**, đưa vào dataset v1 luôn | Dataset Tuần 1 là ground truth dùng xuyên suốt 6 tuần. Thêm dữ liệu ở Tuần 4 sẽ làm ground truth đổi giữa chừng → số liệu trước/sau mất ý nghĩa. Freeze một lần, Tuần 4 chỉ phân tích sâu nhóm `missing_control` |
| 15/09 | **Phạm vi scan: chỉ backend Juice Shop**, loại `test/` và `data/` (seed) | Mọi finding đều nằm trong luồng chạy thật → tranh luận TP/FP mới có ý nghĩa. Tránh dataset loãng vì finding trong code test luôn là FP hiển nhiên |
| 15/09 | **Được dùng custom Opengrep rule**, nhưng phải ghi `rule_source: registry\|custom` trong dataset | Registry pack gần như không có rule cho `missing_control`/`broken_invariant` → không viết custom thì không đủ 10 finding/nhóm. Ghi rõ nguồn để minh bạch và để phân tích riêng "FP do rule registry" vs "FP do rule tự viết" |
| 16/09 | **Tuần 2 khảo sát agent-harness repo có sẵn** rồi build tiếp lên đó (T2.0), không viết vòng lặp tool-calling từ đầu | Chỉ đạo mentor — tool/MCP bổ sung ngoài 2 tool nền sẽ quyết theo root-cause từng tuần (Tuần 3-5), không cần thiết kế kiến trúc trước |
| 16/09 | Gán nhãn Tuần 1 (T1.6) được dùng Claude hỗ trợ đọc/trace code cho nhanh hơn, nhưng **tiêu chuẩn nhãn không đổi** | Mentor: "không cần làm bằng cơm" = đổi công cụ thực hiện, không phải hạ chuẩn — nhãn sai ở Tuần 1 ảnh hưởng dây chuyền cả 5 tuần sau |

> WebGoat vẫn giữ làm nguồn dự phòng nếu nhóm `broken_invariant` không đủ finding.
>
> **Lưu ý đã hiệu chỉnh (16/09):** ví dụ mentor đưa ra cho root-cause `taint_flow` (call-edge,
> custom sanitizer) là minh hoạ, không phải khung phân tích bắt buộc cho Tuần 3 — xem
> `docs/ke-hoach-6-tuan.md` mục Tuần 3.

## Blocker / rủi ro đang mở

| Mức độ | Vấn đề | Ảnh hưởng | Hướng xử lý |
|---|---|---|---|
| 🔴 Cao | `node`/`npm` chưa cài trên máy | Chặn codebase-memory-mcp (Tuần 2) và chạy Juice Shop thật | Cần cài trước Tuần 2, `sudo` cần mật khẩu nên user phải tự chạy |
| ✅ Đã xử lý (16/09) | Registry rule pack gần như không có rule cho `missing_control` / `broken_invariant` | — | Viết + sửa xong 4 custom Opengrep rule (T1.3), scan ra 25 candidate `missing_control` + 7 candidate `broken_invariant` |
| 🟡 Vừa | 7 candidate `broken_invariant` hơi ít, chưa chắc đủ cả TP lẫn FP sau khi gán nhãn | Có thể thiếu case cho nhóm này | Xem lại sau khi gán nhãn; cân nhắc WebGoat (Java) hoặc thêm custom rule nếu thiếu |
| ✅ Đã xử lý (16/09) | Docker chưa bật WSL integration | — | Thực ra đã bật sẵn từ trước; chỉ cần `sg docker -c "..."` do shell hiện tại chưa nạp lại group `docker` |

---

## Nhật ký phiên làm việc

### Phiên 3 — 16/09/2026
- User hỏi đánh giá giáo trình 6 tuần cho mentor: nêu rủi ro chính là cỡ mẫu nhỏ khó chứng
  minh "accuracy cải thiện rõ rệt" (không tách dev/test → nguy cơ overfit), taxonomy có thể
  mơ hồ giữa 2 nhóm, Tuần 2 nặng nhưng không có tuần đệm.
- Mentor phản hồi 5 ý (xem log quyết định 16/09). Lần đầu diễn giải quá tay: biến ví dụ minh
  hoạ (call-edge/custom sanitizer) thành khung root-cause bắt buộc cho Tuần 3, và biến "không
  cần làm bằng cơm" thành "làm nhanh, gán nhãn 1 lượt không điều tra sâu" — user chỉnh lại: đó
  chỉ là ví dụ, và tiêu chuẩn gán nhãn không được hạ thấp. Đã hoàn tác bản diễn giải sai, cập
  nhật lại đúng phạm vi thật (nhẹ hơn nhiều): thêm T2.0 (khảo sát harness có sẵn) ở Tuần 2, ghi
  chú T1.6 (được dùng Claude hỗ trợ, tiêu chuẩn không đổi), ghi chú ở Tuần 3 rằng ví dụ mentor
  không phải danh sách đóng.

### Phiên 2 — 15/09/2026
- Lập kế hoạch chi tiết 6 tuần → `docs/ke-hoach-6-tuan.md`.
- Viết `CLAUDE.md`, `docs/tien-do.md`, `docs/moi-truong-va-cong-cu.md` để phiên sau vào việc ngay.
- Chốt 3 nguyên tắc xuyên suốt: dataset freeze + versioning, bộ chỉ số đo lường thống nhất
  (FP-elimination rate / TP-retention rate thay vì chỉ accuracy), harness modular từ đầu.

### Phiên 1 — 14/09/2026
- Đọc PDF lộ trình, nắm mục tiêu/phạm vi/rubric.
- Bootstrap `pip` thủ công (máy không có `pip`/`ensurepip`), cài Opengrep v1.30.0.
- Gặp lỗi `CERTIFICATE_VERIFY_FAILED` khi Opengrep tải rule từ `semgrep.dev` → xác định nguyên
  nhân là Opengrep dùng CA bundle riêng, không dùng trust store hệ thống (nơi đã có CA
  Vingroup). Fix bằng `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`.
- Scan Juice Shop backend: 25 finding với `--config auto`, 18 finding với tổ hợp rule pack.
  Chủ yếu `taint_flow` + `insecure_property`.
- Đọc `server.ts` + `lib/insecurity.ts`, tìm được ví dụ ground truth rất tốt cho
  `missing_control`: TP = guard bị comment out ở `app.put('/api/Products/:id', ...)`;
  FP = route chỉ có `appendUserId()` nhưng hàm này tự trả 401 ⇒ vẫn có auth.
- Viết nháp 4 custom Opengrep rule cho `missing_control` + `broken_invariant` (chưa chạy được).
