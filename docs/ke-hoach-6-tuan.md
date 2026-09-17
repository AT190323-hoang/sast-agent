# Kế hoạch chi tiết 6 tuần

> Bám theo `lo-trinh-thuc-tap-6-tuan.pdf`. Mỗi tuần gồm: mục tiêu → task chia nhỏ →
> deliverable → tiêu chí hoàn thành (trích từ đề bài) → **câu hỏi cần chốt** (phần để hai
> bên bàn bạc trước khi làm) → rủi ro.
>
> Mốc thời gian dưới đây **tạm tính** theo ngày bắt đầu 14/09/2026 — cần user xác nhận lại.

| Tuần | Thời gian (tạm tính) | Chủ đề | Trọng số rubric |
|---|---|---|---|
| 1 | 14/09 – 20/09 | Thu thập dữ liệu & Taxonomy | 10% |
| 2 | 21/09 – 27/09 | Xây dựng harness cho agent | 15% |
| 3 | 28/09 – 04/10 | `taint_flow`: root-cause & giải pháp | 15% |
| 4 | 05/10 – 11/10 | `missing_control` + `insecure_property` | 15% |
| 5 | 12/10 – 18/10 | `broken_invariant` | 10% |
| 6 | 19/10 – 25/10 | Tích hợp & benchmark tổng thể | 20% |

Ngoài ra **15%** cho *tài liệu & quá trình làm việc* — rải đều cả 6 tuần: mỗi tuần phải có
`reports/weekN/bao-cao-tuan-N.md` và check-in đều đặn với mentor.

---

## Nguyên tắc xuyên suốt (quyết định 1 lần, dùng cho cả 6 tuần)

Ba thứ dưới đây nếu chốt sai từ đầu sẽ phải làm lại rất nhiều ở Tuần 6, nên cần thống nhất
ngay trong Tuần 1.

### N1. Dataset là ground truth bất biến

Dataset Tuần 1 được dùng để đo accuracy ở **cả Tuần 3, 4, 5, 6**. Vì vậy:

- Sau khi gán nhãn xong → **freeze** thành `dataset/findings_v1.json`, không sửa nhãn nữa.
- Nếu phát hiện nhãn sai ở tuần sau → **không sửa đè**. Tạo `findings_v2.json` + ghi
  `dataset/CHANGELOG.md` nêu rõ finding nào đổi nhãn và vì sao. Mọi số liệu báo cáo phải ghi
  rõ đo trên version nào.
- Lý do: nếu vừa sửa ground truth vừa cải tiến agent, con số "accuracy cải thiện" mất ý nghĩa
  và sẽ bị mentor bắt lỗi ngay ở rubric Tuần 6 ("benchmark không đáng tin cậy").

### N2. Bộ chỉ số đo lường (định nghĩa 1 lần, dùng thống nhất)

Không báo cáo mỗi "accuracy" — với dataset lệch tỷ lệ TP/FP thì accuracy dễ gây hiểu nhầm.
Coi **"phát hiện đúng FP" là lớp positive** (vì mục tiêu đề tài là loại FP):

| Chỉ số | Công thức | Ý nghĩa |
|---|---|---|
| **FP-elimination rate** | (số FP agent gọi đúng FP) / (tổng FP thật) | Agent loại được bao nhiêu % rác — giá trị chính của đề tài |
| **TP-retention rate** | (số TP agent giữ lại là TP) / (tổng TP thật) | Agent có làm mất lỗ hổng thật không — **chỉ số an toàn quan trọng nhất** |
| **Precision khi agent nói FP** | (FP đúng) / (tổng số case agent gọi là FP) | Mức tin cậy khi agent bảo "cái này bỏ đi được" |
| **Accuracy tổng** | (số kết luận đúng) / (tổng finding) | Chỉ số phụ, báo cáo kèm |

Luôn kèm **confusion matrix** và luôn tách **theo từng nhóm taxonomy**.

**Bất đối xứng về rủi ro:** loại nhầm 1 TP (bỏ sót lỗ hổng thật) nguy hiểm hơn giữ lại 1 FP
(tốn công review). Nên khi phải đánh đổi, ưu tiên TP-retention. Prompt của agent cũng nên
phản ánh nguyên tắc này: *không chắc chắn thì giữ lại là TP*.

### N3. Harness phải modular ngay từ Tuần 2

Tuần 3/4/5 mỗi tuần cải tiến prompt+tool cho một nhóm; Tuần 6 phải **gộp lại thành một agent
thống nhất**. Nếu mỗi tuần fork một bản riêng thì Tuần 6 sẽ rất khổ. Thiết kế từ đầu:

- Một prompt **lõi chung** + các **module prompt theo nhóm** (nạp thêm tuỳ `group` của finding).
- Tool dùng chung một registry; tool mới của tuần N vẫn phải dùng được ở các tuần khác.
- Mọi lần chạy lưu kèm version: `reports/runs/<ngày>_<biến-thể>/{config.json, results.json, traces/}`.
- Giữ nguyên một **baseline đóng băng** (harness Tuần 2, prompt v0) để mọi so sánh
  "trước/sau" đều quy về cùng một mốc.

---

## Tuần 1 — Thu thập dữ liệu & Xây dựng Taxonomy

**Mục tiêu:** có bộ ground truth đủ lớn, gán nhãn chắc tay, và tài liệu taxonomy không mơ hồ.

### Task

| ID | Việc | Trạng thái |
|---|---|---|
| T1.1 | Cài SAST tool (Opengrep) + xử lý lỗi CA của gateway công ty | ✅ xong |
| T1.2 | Chạy scan registry rule packs trên Juice Shop backend → findings thô | ✅ xong (~43 finding, có trùng lặp giữa 2 lần chạy) |
| T1.3 | Viết custom Opengrep rule cho `missing_control` + `broken_invariant` | 🔶 đang làm (4 rule nháp, 1 rule lỗi cú pháp) |
| T1.4 | Dựng crAPI (cần Docker) + scan lấy finding `missing_control`; WebGoat dự phòng nếu `broken_invariant` thiếu | ⬜ |
| T1.5 | Chốt schema dataset + script chuẩn hoá JSON Opengrep → dataset rows | ⬜ |
| T1.6 | Gán nhãn từng finding: nhóm + TP/FP + lý do + `context_needed`. Được dùng Claude hỗ trợ đọc/trace code cho nhanh hơn tự tay lần từng dòng — nhưng **tiêu chuẩn không đổi**: mỗi nhãn vẫn cần dẫn chứng code cụ thể; case không chắc thì đánh dấu `confidence: low` để review thêm, không đoán ẩu (mentor 16/09: "không cần làm bằng cơm" = đổi công cụ, không đổi độ cẩn trọng) | ⬜ |
| T1.7 | Viết `docs/taxonomy.md` (định nghĩa + ví dụ thật từ code) | ⬜ |
| T1.8 | Review lại: đủ ≥10 finding/nhóm, không finding nào mơ hồ giữa 2 nhóm | ⬜ |
| T1.9 | Freeze `dataset/findings_v1.json` + viết `reports/week1/bao-cao-tuan-1.md` | ⬜ |

### Deliverable
- Bộ dataset findings đã gán nhãn (nhóm + TP/FP + lý do).
- Tài liệu taxonomy: định nghĩa rõ ràng, có ví dụ, cho từng nhóm trong 4 nhóm.

### Tiêu chí hoàn thành (theo đề bài)
- Mỗi nhóm ≥ 10 findings đã gán nhãn, **có cả TP và FP**.
- Taxonomy được review, không có finding nào mơ hồ giữa 2 nhóm.
- Mục tiêu tổng: 100 findings.

### Schema dataset đề xuất

```jsonc
{
  "id": "JS-0001",                  // mã ổn định, dùng để tham chiếu suốt 6 tuần
  "source_app": "juice-shop",       // juice-shop | crapi | webgoat
  "tool": "opengrep-1.30.0",
  "rule_id": "javascript.express.security.audit.express-res-sendfile...",
  "rule_source": "registry",        // registry | custom  ← minh bạch nguồn rule
  "severity": "WARNING",
  "cwe": ["CWE-22"],
  "group": "taint_flow",            // 1 trong 4 nhóm
  "file": "routes/fileServer.ts",
  "start_line": 32, "end_line": 32,
  "code_snippet": "res.sendFile(path.resolve('ftp/', file))",
  "tool_message": "...",            // nguyên văn message của tool
  "label": "TP",                    // TP | FP  ← ground truth
  "reason": "...",                  // vì sao TP/FP, dẫn chứng cụ thể ở code
  "context_needed": "...",          // ⭐ loại context nào giúp phân biệt đúng/sai
  "confidence": "high",             // high | medium | low — case low cần mentor review
  "labeled_by": "hoang",
  "labeled_at": "2026-09-15"
}
```

Field `context_needed` là thứ **quý nhất** của Tuần 1: nó chính là "ghi chú sơ bộ" mà đề bài
yêu cầu, và là **đầu vào trực tiếp để thiết kế tool ở Tuần 2 và root-cause ở Tuần 3–5**. Đừng
ghi chung chung kiểu "cần thêm context" — phải ghi rõ dạng *"cần biết `server.ts` có bind
`isAuthorized()` cho path prefix này không"*.

### Câu hỏi cần chốt trước khi gán nhãn

> **Đã chốt ngày 15/09:**
> - ✅ **crAPI vào dataset ngay Tuần 1** (câu #2) — freeze ground truth một lần, Tuần 4 chỉ
>   phân tích sâu chứ không thêm dữ liệu.
> - ✅ **Phạm vi scan: chỉ backend Juice Shop**, loại `test/` và `data/` seed (bổ sung cho câu #1).
> - ✅ **Được dùng custom rule**, bắt buộc ghi `rule_source: registry|custom` (câu #3).
>
> **Đã chốt ngày 17/09 (xác nhận qua thực hành, không chỉ bàn lý thuyết):**
> - ✅ **Câu #1 — quy ước TP/FP** — định nghĩa đề xuất bên dưới đã được áp dụng nhất quán cho
>   toàn bộ 87 finding (xem `dataset/labels/*.json`), qua review T1.8 không phát hiện case nào
>   mơ hồ hay áp dụng sai lệch. Coi như đã kiểm chứng bằng thực hành thay vì chỉ thống nhất
>   bằng lời.
>
> Còn lại **chưa chốt**: câu #4 (ai review nhãn — mentor hay tự review chéo).

1. **Quy ước TP/FP cho app cố ý chứa lỗi.** Juice Shop cố tình nhúng lỗ hổng, nên cần định
   nghĩa rõ, đề xuất:
   - **TP** = finding chỉ đúng một rủi ro có thật trong ngữ cảnh app chạy thật (reachable từ
     input bên ngoài, chưa có biện pháp bảo vệ hiệu lực).
   - **FP** = finding đúng về mặt cú pháp nhưng không phải rủi ro thật: đã có sanitizer/guard
     ở nơi khác, không reachable, chỉ nằm trong code test/seed, hoặc giá trị cấu hình thực tế
     đã an toàn.
   - Cần thống nhất thêm: code trong `test/`, `data/static/` (seed data) → **loại khỏi dataset**
     hay **giữ và gán FP**? Đề xuất: loại khỏi phạm vi scan để dataset sạch, trừ vài case cố ý
     giữ lại làm ví dụ FP dạng "không reachable".
2. **Có đưa crAPI vào dataset ngay Tuần 1 không?** Đề bài nói dataset Tuần 1 dùng xuyên suốt
   6 tuần. Nếu Tuần 4 mới thêm finding crAPI thì ground truth bị thay đổi giữa chừng → khó so
   sánh trước/sau. **Đề xuất: scan crAPI ngay trong Tuần 1** để lấy đủ finding
   `missing_control`, freeze một lần; Tuần 4 chỉ phân tích sâu chứ không thêm dữ liệu mới.
3. **Custom rule có được coi là "SAST findings" hợp lệ không?** Đề xuất: **có** — viết custom
   rule cho Opengrep là việc làm bình thường của kỹ sư AppSec, và registry pack gần như không
   có rule cho `missing_control`/`broken_invariant`. Nhưng phải minh bạch: ghi
   `rule_source: custom` trong dataset, và giữ tỷ lệ custom ở mức hợp lý để dataset không bị
   coi là "tự nghĩ ra finding".
4. **Ai review nhãn?** Rubric yêu cầu "taxonomy được review". Cần hỏi mentor VinSOC review
   trực tiếp, hay tự review chéo + đánh dấu `confidence: low` cho case không chắc?

### Rủi ro
- **Không đủ 10 finding/nhóm cho `broken_invariant`** — Juice Shop thiết kế quanh OWASP Top 10
  (injection/access control/crypto), ít bug kiểu null-deref/resource-leak. Phương án: mở rộng
  sang WebGoat (Java, nhiều case resource/state hơn) hoặc viết thêm custom rule.
- Gán nhãn vội → sai ground truth → hỏng toàn bộ số liệu 5 tuần sau. Thà chậm mà chắc.

---

## Tuần 2 — Xây dựng Harness Cho AI Agent

**Mục tiêu:** agent chạy được vòng lặp verify với tool, và **chứng minh được tool là cần thiết**.

> **Mentor (16/09):** không cần viết harness từ đầu — khảo sát agent-harness repo có sẵn trên
> GitHub (ReAct-style tool-calling loop, Claude Agent SDK, ...) rồi build tiếp lên đó. 2 tool
> cbm-mcp + grep/read_file chỉ là bộ nền cơ bản; tool/MCP bổ sung sẽ quyết theo root-cause tìm
> được ở Tuần 3–5 — đó chính là phần "giải pháp" của từng tuần, không cần thiết kế trước.

### Task

| ID | Việc |
|---|---|
| T2.0 | Khảo sát agent-harness repo có sẵn, chọn 1 cái để build tiếp thay vì viết từ đầu |
| T2.1 | Cài `node`/`npm` (đang thiếu) — tiền đề cho codebase-memory-mcp |
| T2.2 | Dựng codebase-memory-mcp, index Juice Shop, kiểm tra truy vấn trả về gì |
| T2.3 | Viết `grep`/`read_file` tool (Python, tự viết, giới hạn trong thư mục target) |
| T2.4 | Vòng lặp verify: nhận 1 finding → LLM tool-calling → kết luận TP/FP + giải thích |
| T2.5 | Prompt lõi v0 (baseline, chưa tối ưu theo nhóm) |
| T2.6 | Cơ chế log đầy đủ: mọi tool call + tham số + kết quả + reasoning cuối |
| T2.7 | Chạy thử 10–15 finding, kiểm tra không lỗi kỹ thuật |
| T2.8 | **Thí nghiệm ablation**: chạy cùng bộ finding ở 2 chế độ *no-tool* vs *with-tool* |
| T2.9 | Chạy full baseline trên toàn dataset → đóng băng làm mốc so sánh cho Tuần 3–5 |

### Deliverable
- Harness hoạt động với 2 tool (cbm + grep) và vòng lặp verify cơ bản.
- Log kết quả chạy thử trên tập nhỏ.

### Tiêu chí hoàn thành (theo đề bài)
- Agent gọi tool thành công, không lỗi kỹ thuật, trên toàn bộ tập test nhỏ.
- **Có ít nhất 1 case agent tự sửa kết luận sau khi dùng tool bổ sung context.**

> Tiêu chí thứ hai là lý do **T2.8 phải thiết kế từ đầu, không phải đi tìm sau**: cách chắc
> chắn nhất để có bằng chứng là chạy song song *no-tool* (chỉ đưa finding + snippet, cấm gọi
> tool) và *with-tool*, rồi diff hai kết quả. Mọi case khác nhau chính là bằng chứng
> "harness thực sự cần thiết". Ứng viên sáng giá đã thấy ở Tuần 1: các route chỉ có
> `security.appendUserId()` — hỏi thẳng LLM sẽ nói "thiếu auth" (sai), nhưng nếu agent grep
> đọc `lib/insecurity.ts` sẽ thấy hàm này tự trả 401 → đổi kết luận thành FP.

### Câu hỏi cần chốt
1. **LLM nào?** Đề xuất Claude qua Anthropic API (tool-calling tốt, có prompt caching để giảm
   chi phí khi chạy lại nhiều lần). Cần: VinSOC cấp API key hay dùng key cá nhân? Ngân sách token?
2. **codebase-memory-mcp index được gì?** Cần khảo sát sớm: nó index symbol/định nghĩa hàm, hay
   cả quan hệ gọi hàm? Nếu **không** nắm được route↔middleware binding thì Tuần 4 sẽ phải tự
   viết tool "route table" riêng — biết sớm để chủ động.
3. **Agent được gọi tối đa bao nhiêu lượt tool/finding?** Cần giới hạn để kiểm soát chi phí và
   để so sánh công bằng giữa các tuần.
4. **Output format của agent?** Đề xuất JSON có cấu trúc: `{verdict, confidence, reasoning,
   evidence: [{file, lines, why}], tools_used}` — `evidence` bắt buộc trỏ tới vị trí code cụ
   thể, tránh agent "chém" không dẫn chứng.

### Rủi ro
- Thiếu `node` → chặn cứng codebase-memory-mcp. Xử lý ngay đầu tuần.
- Nếu index của cbm quá nghèo, agent sẽ chỉ dùng grep → rubric trừ điểm "agent ít khi thực sự
  cần đến tool". Cần chủ động làm giàu index.

---

## Tuần 3 — Nhóm `taint_flow`: Root-Cause & Giải Pháp

**Mục tiêu:** tìm nguyên nhân cụ thể agent sai ở nhóm taint_flow và sửa được, có số liệu.

### Task

| ID | Việc |
|---|---|
| T3.1 | Chạy baseline (prompt v0) trên toàn bộ finding `taint_flow` |
| T3.2 | Lập confusion matrix, lọc ra các case agent sai |
| T3.3 | Với mỗi case sai: đọc trace tool call → tìm agent đã thiếu **chính xác** context gì |
| T3.4 | Gom nhóm root-cause (vd: sanitizer tự viết không nhận ra; không biết sink có reachable từ route hay không; ORM đã parameterize nhưng agent tưởng là nối chuỗi) |
| T3.5 | Cải tiến: bổ sung prompt module + tool (vd tra cứu danh sách sanitizer đã biết của project) |
| T3.6 | Chạy lại → số liệu trước/sau |
| T3.7 | Viết `reports/week3/root-cause-taint-flow.md` |

### Tiêu chí hoàn thành
- Accuracy nhóm `taint_flow` cải thiện rõ rệt so với baseline Tuần 2.
- Root-cause **cụ thể**, không chung chung — "thiếu context" phải chỉ rõ *context nào*.

### Giả thuyết root-cause để kiểm chứng (dựa trên code Juice Shop đã đọc)
- Juice Shop có sanitizer **tự viết** trong `lib/insecurity.ts` (`sanitizeHtml`,
  `sanitizeLegacy`, `sanitizeSecure`, `cutOffPoisonNullByte`). Rule của tool không biết chúng
  → FP. Đáng chú ý: `sanitizeLegacy` là sanitizer **cố tình yếu** (regex thay thế 1 lần, bypass
  được) → agent phải phân biệt "có sanitizer" với "sanitizer thực sự hiệu lực" — đây là case
  rất tốt để chứng minh agent hiểu sâu chứ không chỉ khớp tên hàm.
- `models.sequelize.query()` nối chuỗi trực tiếp (route `login.ts`) = TP thật, trong khi các
  chỗ dùng `where: { id: ... }` của Sequelize đã parameterize = FP.

> Mentor (16/09) có nêu ví dụ 2 dạng giới hạn SAST hay gặp ở `taint_flow`: không resolve hết
> **call-edge** (giới hạn interprocedural/call-graph) và không phân biệt được **custom
> sanitizer/guard**. Đây là ví dụ minh hoạ, không phải danh sách đóng — root-cause thật của
> tuần này vẫn phải rút ra từ T3.2/T3.3 (đọc trace, phân tích case sai thực tế), có thể trùng,
> khác, hoặc nhiều hơn 2 hướng trên.

---

## Tuần 4 — Nhóm `missing_control` & `insecure_property`

**Mục tiêu:** xử lý hai nhóm mà nguyên nhân FP nằm ở **ngoài file đang xét**.

### Task

| ID | Việc |
|---|---|
| T4.1 | Chạy baseline trên toàn bộ finding `missing_control` (Juice Shop + crAPI) |
| T4.2 | Root-cause `missing_control`: agent có biết guard bind ở `server.ts`/global middleware không? |
| T4.3 | Giải pháp: dạy agent grep tìm guard + (nếu cần) tool dựng **route table**: path → chuỗi middleware → handler |
| T4.4 | Chạy baseline trên toàn bộ finding `insecure_property` |
| T4.5 | Root-cause `insecure_property`: agent có truy được **giá trị cấu hình thực tế** không (env var, file config override theo `NODE_ENV`) |
| T4.6 | Giải pháp: tool truy vết cấu hình — đọc `config/*.yml`, thứ tự override, `process.env` |
| T4.7 | Chạy lại cả 2 nhóm → số liệu trước/sau từng nhóm |
| T4.8 | Viết `reports/week4/root-cause-missing-control-va-insecure-property.md` |

### Tiêu chí hoàn thành
- Accuracy cả 2 nhóm cải thiện rõ rệt.
- **Có ít nhất 1 ví dụ cụ thể** agent verify đúng `missing_control` nhờ tìm ra guard nằm ở nơi
  khác (không cùng file/function với finding).
- Agent phân biệt được **cấu hình bị override an toàn** vs **thực sự insecure**.

### Vật liệu đã có sẵn (từ khảo sát Tuần 1)
- **TP mẫu:** `server.ts` dòng ~389 — `// app.put('/api/Products/:id', security.isAuthorized())`
  bị comment out → PUT không có guard. Đây là lỗ hổng thật, kinh điển của Juice Shop.
- **FP mẫu:** nhiều route chỉ có `security.appendUserId()`. Nhìn qua tưởng thiếu auth, nhưng
  `appendUserId()` trong `lib/insecurity.ts` sẽ ném lỗi → trả 401 nếu token không hợp lệ ⇒
  **vẫn có auth**. Đây đúng là case "guard nằm ở nơi khác, dưới một cái tên khác" mà tiêu chí
  hoàn thành yêu cầu.
- **Bẫy thứ tự middleware:** `app.use('/api/BasketItems', security.isAuthorized())` bảo vệ theo
  *path prefix* và chỉ áp dụng cho route đăng ký **sau** nó. Agent phải hiểu thứ tự đăng ký
  trong `server.ts`, không chỉ "có tồn tại một dòng isAuthorized nào đó".
- **Cho `insecure_property`:** Juice Shop dùng package `config` với nhiều file trong `config/`
  → môi trường khác nhau cho giá trị khác nhau. Đây chính xác là tình huống "SAST không biết
  giá trị cấu hình thực tế" mà đề bài mô tả.

---

## Tuần 5 — Nhóm `broken_invariant`

**Mục tiêu:** xử lý nhóm khó nhất — bất biến ngầm định, không nhìn thấy trong phạm vi 1 hàm.

### Task

| ID | Việc |
|---|---|
| T5.1 | Chạy baseline trên toàn bộ finding `broken_invariant` |
| T5.2 | Phân tích case sai từ trace |
| T5.3 | Root-cause: bất biến do caller đảm bảo? do middleware đã validate? resource được quản lý vòng đời ở nơi khác? đã bọc try/catch nên không crash? |
| T5.4 | Giải pháp: tool tra **caller** của hàm (ai gọi, đã kiểm tra gì trước khi gọi) |
| T5.5 | Chạy lại → số liệu trước/sau |
| T5.6 | Viết `reports/week5/root-cause-broken-invariant.md` |

### Tiêu chí hoàn thành
- Accuracy nhóm `broken_invariant` cải thiện rõ rệt.
- Root-cause cụ thể, không chung chung.

### Ghi chú
Đây là nhóm agent cần **phân tích ngược theo call graph** (tìm caller), khác hẳn 3 nhóm trước
(chủ yếu tra xuôi/tra ngang). Nếu codebase-memory-mcp không hỗ trợ tìm caller thì phải bổ sung
tool — nên kiểm tra khả năng này **ngay từ Tuần 2** (xem câu hỏi T2.2) chứ đừng đợi tới Tuần 5.

Ví dụ đã thấy: `appendUserId()` truy `tokenMap[...].data.id` không null-check, nhưng bọc trong
`try/catch` trả 401 ⇒ FP. Bất biến "token hợp lệ" được đảm bảo bằng exception handling chứ
không bằng null-check.

---

## Tuần 6 — Tổng Hợp Cuối Kỳ

**Mục tiêu:** một agent thống nhất + benchmark thuyết phục + tài liệu kỹ thuật hoàn chỉnh.

### Task

| ID | Việc |
|---|---|
| T6.1 | Gộp prompt module + tool của 4 nhóm thành **một agent thống nhất** |
| T6.2 | Xử lý edge case khi tích hợp (finding mơ hồ giữa 2 nhóm, agent chọn sai module) |
| T6.3 | Quyết định: agent **tự phân loại nhóm** rồi mới verify, hay nhận sẵn nhóm từ dataset? |
| T6.4 | Chạy benchmark tổng thể trên **toàn bộ** dataset Tuần 1 |
| T6.5 | Báo cáo: FP-elimination rate, TP-retention rate, so sánh trước/sau, tách theo nhóm |
| T6.6 | Chuẩn bị **demo 1 ví dụ thực tế cho mỗi nhóm** (4 demo) |
| T6.7 | Viết tài liệu tổng kết: kiến trúc harness, root-cause + giải pháp từng nhóm, giới hạn còn lại, hướng mở rộng |

### Tiêu chí hoàn thành
- Agent thống nhất chạy được trên toàn bộ dataset, không lỗi kỹ thuật.
- Benchmark cho thấy giảm rõ rệt tỷ lệ FP, **có số liệu cụ thể**.
- Demo được ít nhất 1 ví dụ thực tế cho mỗi nhóm trong 4 nhóm.

### Lưu ý về tính thuyết phục của benchmark
Rubric Tuần 6 chiếm 20% và mức "chưa đạt" ghi rõ *"benchmark không đáng tin cậy"*. Để tránh:
- So sánh trên **cùng dataset đã freeze**, ghi rõ version.
- Báo cáo cả trường hợp agent làm **tệ hơn** baseline nếu có — trung thực quan trọng hơn con
  số đẹp, và mentor sẽ đánh giá cao việc chỉ ra giới hạn.
- Nêu rõ giới hạn: dataset chỉ từ 1–2 app, một tool SAST, số lượng ~100 → không khẳng định
  tổng quát hoá cho mọi codebase.
- Nếu dataset nhỏ, cân nhắc chạy lặp lại nhiều lần để thấy độ dao động của LLM (không
  deterministic) thay vì báo cáo một con số duy nhất.

---

## Checklist tài liệu (15% rubric — đừng để mất điểm ở đây)

- [ ] `reports/week1/bao-cao-tuan-1.md` … `reports/week6/bao-cao-tuan-6.md`
- [ ] Cập nhật `docs/tien-do.md` cuối mỗi phiên làm việc
- [ ] Ghi lại **blocker** ngay khi gặp (rubric chấm "chủ động báo cáo blocker")
- [ ] Tài liệu kỹ thuật cuối kỳ (Tuần 6)
