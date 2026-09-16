# Tiến độ dự án

> **Cập nhật file này vào cuối mỗi phiên làm việc.** Phiên Claude mới đọc `CLAUDE.md` → rồi
> file này → biết ngay đang ở đâu, việc tiếp theo là gì.

**Tuần hiện tại:** Tuần 1 — Thu thập dữ liệu & Taxonomy
**Cập nhật lần cuối:** 16/09/2026

---

## Việc tiếp theo cần làm

1. Sửa nốt custom rule bị lỗi cú pháp (`harness/rules/broken-invariant-candidates.yaml` —
   pattern `try { ... } catch (...) { ... }` không hợp lệ với TypeScript parser của Opengrep;
   `missing-control-candidates.yaml` lỗi YAML ở dòng 14).
2. Chạy lại scan với custom rule → xem có đủ finding cho `missing_control` và
   `broken_invariant` không.
3. **Chốt quy ước TP/FP** cho app cố ý chứa lỗi (câu hỏi #1 Tuần 1 — chưa chốt) và hỏi mentor
   về việc review nhãn (câu hỏi #4 — chưa chốt).
4. Clone + dựng crAPI (cần bật Docker Desktop WSL integration), scan lấy finding
   `missing_control`.
5. Chốt schema dataset + viết script chuẩn hoá output Opengrep → dataset rows.
6. Gán nhãn TP/FP (được dùng Claude hỗ trợ đọc/trace, tiêu chuẩn nhãn không đổi — xem T1.6).
7. Sau khi Tuần 1 xong: khảo sát agent-harness repo có sẵn cho Tuần 2 (T2.0).

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
| T1.3 | Custom rule cho 2 nhóm còn thiếu | 🔶 | 4 rule nháp, 2 file đều còn lỗi cú pháp |
| T1.4 | Mở rộng nguồn finding (crAPI/WebGoat) | ⬜ | Chờ chốt câu hỏi #2 |
| T1.5 | Schema dataset + script chuẩn hoá | ⬜ | Schema đề xuất đã có trong kế hoạch |
| T1.6 | Gán nhãn TP/FP + lý do + `context_needed` | ⬜ | |
| T1.7 | Viết `docs/taxonomy.md` | ⬜ | Đã có sẵn ví dụ thật cho `missing_control` |
| T1.8 | Review: ≥10 finding/nhóm, không mơ hồ | ⬜ | |
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
| 🟡 Vừa | Registry rule pack gần như không có rule cho `missing_control` / `broken_invariant` | Khó đủ 10 finding/nhóm | Viết custom Opengrep rule (T1.3) + cân nhắc thêm app khác |
| 🟡 Vừa | Juice Shop ít bug kiểu null-deref / resource-leak | Nhóm `broken_invariant` có thể thiếu TP thật | Cân nhắc WebGoat (Java) làm nguồn bổ sung |
| 🟢 Thấp | Docker chưa bật WSL integration | Chỉ ảnh hưởng nếu cần chạy crAPI (crAPI chạy bằng docker-compose) | Bật trong Docker Desktop khi tới Tuần 4 |

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
