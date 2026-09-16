# Taxonomy: 4 nhóm Finding SAST

> Deliverable Tuần 1. Toàn bộ ví dụ trong tài liệu này là **finding thật**, đã được gán nhãn
> trong `dataset/findings_labeled.json` (xem `dataset/labels/*.json` để đọc lý do đầy đủ,
> không rút gọn). Không có ví dụ hư cấu — mục tiêu là tài liệu này phản ánh đúng dữ liệu thật
> đã thu thập trên OWASP Juice Shop (Express/TypeScript) và crAPI (Django/Python + Java).

## Vì sao chia 4 nhóm?

Luận điểm cốt lõi của đề tài: **SAST tool báo sai vì thiếu context, không phải vì rule sai.**
Nhưng "context" không phải một thứ duy nhất — mỗi nhóm lỗ hổng thiếu một *loại* context khác
nhau, nên cần agent có chiến lược thu thập context khác nhau cho từng nhóm. Bảng dưới tóm tắt,
chi tiết + ví dụ ở các mục sau.

| Nhóm | Câu hỏi cốt lõi | Loại context quyết định TP/FP |
|---|---|---|
| `taint_flow` | Dữ liệu từ nguồn không tin cậy có chảy tới sink nguy hiểm mà không qua sanitize/validate đủ mạnh không? | Sanitizer tự viết có tồn tại & có thực sự hiệu lực không; sink có reachable từ input ngoài không |
| `insecure_property` | Một thuộc tính/cấu hình có đang được set giá trị không an toàn không? | Giá trị cấu hình **thực tế lúc chạy**; cơ chế xác thực thật của hệ thống (quyết định 1 config có thực sự cần thiết không) |
| `missing_control` | Một thao tác nhạy cảm có đang thiếu hẳn kiểm soát (auth/guard/rate-limit) không? | Guard có nằm ở **nơi khác** không (file khác, hàm khác, tên khác); thao tác có thực sự chạm dữ liệu nhạy cảm/per-user không |
| `broken_invariant` | Code có giả định một bất biến (non-null, resource đã mở, API trả None thay vì throw...) mà thực ra không được đảm bảo không? | Bất biến có được đảm bảo bởi caller/hàm trước đó không; hành vi THẬT của API/thư viện đang dùng |

## Nguyên tắc phân loại — tránh mơ hồ giữa các nhóm

Ba ranh giới dễ nhầm nhất, và quy tắc đã áp dụng nhất quán khi gán nhãn:

1. **`taint_flow` vs `missing_control`:** `taint_flow` đòi hỏi có một **chuỗi dữ liệu** từ input
   tới sink (SQLi, XSS, SSTI, path traversal, open redirect, prototype pollution, SSRF).
   `missing_control` là về **sự vắng mặt của một bước kiểm tra** (auth/ownership/rate-limit),
   không quan tâm dữ liệu chảy đi đâu. Ví dụ: prototype pollution qua `req.query.fields` xếp
   `taint_flow` (có source→sink rõ ràng: field name → object property read) chứ không xếp
   `missing_control`, dù hệ quả là lộ thông tin.

2. **`insecure_property` vs `missing_control`:** `insecure_property` là một **thuộc tính/config
   tồn tại nhưng bị set sai giá trị** (CSRF bị tắt, cert validation bị tắt, thuật toán yếu).
   `missing_control` là **hoàn toàn không có bước kiểm tra nào**. Ranh giới cụ thể đã áp dụng:
   - `csrf_exempt` / `csrf().disable()` → `insecure_property` (đây là 1 toggle có sẵn, có thể
     đúng hoặc sai tuỳ ngữ cảnh — xem `CRAPI-0001`, `CRAPI-0005` đều là FP vì tắt CSRF hợp lý
     cho API dùng JWT/endpoint public).
   - Thiếu cấu hình rate-limit hoàn toàn (`missing-throttle-config`) → `missing_control` (không
     có gì để "sửa giá trị", phải **thêm mới** một control chưa từng tồn tại — xem `CRAPI-0011`).

3. **`broken_invariant` vs `missing_control`:** Cả hai đều có thể "thiếu 1 bước kiểm tra", nhưng
   `missing_control` là thiếu kiểm tra **quyền/định danh** (ai được phép làm gì), còn
   `broken_invariant` là thiếu kiểm tra **tính hợp lệ của dữ liệu/trạng thái nội bộ** (record có
   tồn tại không, chuỗi có phải JSON hợp lệ không, resource đã đóng chưa). Test nhanh: nếu câu
   hỏi là "user này có được phép không?" → `missing_control`; nếu là "giá trị/trạng thái này có
   đúng như code giả định không?" → `broken_invariant`.

Áp dụng nhất quán 3 quy tắc trên, **không có finding nào trong 87 finding đã gán nhãn bị xếp mơ
hồ giữa 2 nhóm** — mỗi case đều có thể trả lời rành mạch câu hỏi phân định tương ứng.

---

## 1. `taint_flow` — Luồng dữ liệu source → sink

**Định nghĩa:** dữ liệu từ nguồn không tin cậy (request input, file, config bên ngoài) chảy tới
một sink nguy hiểm (query DB, `eval`, ghi file, redirect, render template) mà không qua bước
sanitize/validate đủ mạnh để trung hoà nguy cơ. Gồm SQLi, XSS/SSTI, path traversal, open
redirect, command/code injection, prototype pollution.

**Kết quả gán nhãn:** 23 finding — 12 TP / 11 FP (cân bằng nhất trong 4 nhóm).

### Loại context quyết định TP/FP

- **Sanitizer tự viết có tồn tại không, và có thực sự hiệu lực không** — SAST không biết
  `sanitizeLegacy()`/`isRedirectAllowed()` của riêng app.
- **Input có thực sự reachable từ bên ngoài không** — nhiều case "trông giống taint" nhưng biến
  chỉ đến từ config nội bộ hoặc code chạy lúc khởi động.
- **Rule đúng sink nhưng có thể sai loại lỗ hổng** — code có lỗ hổng thật nhưng không phải loại
  rule đang cảnh báo.

### Ví dụ TP

**`JS-0022`/`JS-0023` — Open redirect do allowlist cài sai** (`routes/redirect.ts:18`)
```ts
if (security.isRedirectAllowed(toUrl)) { res.redirect(toUrl) }
```
Nhìn qua tưởng đã có allowlist bảo vệ. Nhưng đọc định nghĩa `isRedirectAllowed()` trong
`lib/insecurity.ts` mới thấy:
```ts
allowed = allowed || url.includes(allowedUrl)  // .includes(), không phải so khớp chính xác!
```
Một URL như `https://evil.com/?x=https://github.com/juice-shop/juice-shop` vẫn "chứa" domain
hợp lệ làm substring nên qua được check. **Đây là ví dụ mẫu cho "có sanitizer nhưng sanitizer bị
cài sai"** — SAST không đọc được thân hàm `isRedirectAllowed` để biết nó dùng `.includes()`.

**`CRAPI-0009`/`CRAPI-0010` — SQL injection thật** (`shop/views.py:388`)
```python
cursor.execute(
    "SELECT coupon_code from applied_coupon WHERE user_id = " + str(user.id)
    + " AND coupon_code = '" + coupon_request_body["coupon_code"] + "'"
)
```
Nối chuỗi trực tiếp giá trị từ request body vào SQL thô, không tham số hoá. TP rõ ràng, không
cần context gì thêm — nguồn và sink nằm trọn trong 1 câu lệnh.

### Ví dụ FP

**`JS-0014` — "Đúng sink, sai loại lỗ hổng"** (`routes/fileServer.ts:32`)
```ts
if (!file.includes('/')) { verify(file, res, next) }
// ... verify(): res.sendFile(path.resolve('ftp/', file))
```
Rule cảnh báo *"attacker có thể đọc file tuỳ ý trên hệ thống"* (path traversal ra ngoài thư
mục). Nhưng dòng `!file.includes('/')` chặn hoàn toàn mọi ký tự `/`, nên không thể dùng `../`
để thoát khỏi `ftp/`. Claim cụ thể của rule sai → **FP**. Lưu ý: code này **vẫn có lỗ hổng thật**
(`cutOffPoisonNullByte()` cho phép bypass check đuôi file `.md`/`.pdf` bằng null byte), nhưng đó
là loại lỗ hổng khác (bypass allowlist đuôi file trong cùng thư mục), không phải path traversal
ra ngoài hệ thống. Đây là lý do gán nhãn TP/FP phải khớp **đúng claim của rule**, không chỉ hỏi
"code có lỗ hổng không".

**`JS-0002`/`JS-0003` — Biến "trông giống taint" nhưng không reachable từ request**
(`lib/codingChallenges.ts:76`)
```ts
new RegExp(`vuln-code-snippet vuln-line.*${challengeKey}`).exec(lines[i])
```
`challengeKey` trông như một tham số hàm bất kỳ, nhưng lần theo toàn bộ chuỗi gọi
(`getCodeChallengesFromFile` → `findFilesWithCodeChallenges`) cho thấy nó được sinh ra bằng
cách **quét chính file source code của app lúc khởi động server** — không hề đến từ request.
FP vì input không reachable, dù rule không sai về mặt kỹ thuật (đây đúng là `new RegExp` với
biến không phải literal).

---

## 2. `insecure_property` — Cấu hình/thuộc tính không an toàn

**Định nghĩa:** một thuộc tính/cấu hình cụ thể được set giá trị không an toàn: thuật toán mã
hoá yếu, secret hardcode, TLS/certificate validation bị tắt, CSRF bị tắt sai chỗ, thư mục cho
phép liệt kê công khai.

**Kết quả gán nhãn:** 15 finding — 13 TP / 2 FP (rule registry khá chính xác cho nhóm này).

### Loại context quyết định TP/FP

- **Giá trị cấu hình thực tế lúc chạy** — không chỉ đọc default trong code mà phải biết giá trị
  cuối cùng sau mọi override (env var, config theo môi trường).
- **Cơ chế xác thực thật của hệ thống** — quyết định một control (CSRF) có thực sự cần thiết
  hay việc "tắt" nó là hợp lý.

### Ví dụ TP

**`CRAPI-0002`/`CRAPI-0003` — TLS bị vô hiệu hoá hoàn toàn, kèm credential thật**
(`VehicleOwnershipServiceImpl.java:70-82`)
```java
TrustStrategy allTrustStrategy = new TrustAllStrategy();
SSLConnectionSocketFactory csf = new SSLConnectionSocketFactory(sslContext, NoopHostnameVerifier.INSTANCE);
...
builder = builder.basicAuthentication(apiGatewayUsername, apiGatewayPassword);
```
Tin mọi certificate + không kiểm tra hostname, dùng để gửi Basic Auth credential thật tới API
gateway. Không phải code test — service implementation thật. TP nghiêm trọng, có thể bị MITM
đánh cắp credential.

**`CRAPI-0004` — Private key thật bị commit vào repo**
(`services/identity/.../certs/server.key`)
File PEM private key thật, **và được dùng thật** (`keystore.sh` dùng chính file này build
keystore cho service identity). `.gitignore` có dòng `services/certs/` nhưng đường dẫn thật là
`services/identity/src/main/resources/certs/` — không khớp, không loại trừ được. Key đang lộ
công khai trong git history.

### Ví dụ FP

**`CRAPI-0001` — CSRF bị tắt, nhưng đúng vì API không dùng session**
(`WebSecurityConfig.java:98`)
```java
.sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
...
http.csrf().disable();
```
CSRF chỉ có ý nghĩa khi trình duyệt **tự động** đính kèm credential (cookie) vào request
cross-site. API này dùng JWT qua header `Authorization`, không dùng session cookie
(`STATELESS`) — trình duyệt không tự động gửi JWT như vậy nên CSRF không áp dụng được. Tắt CSRF
ở đây là thực hành đúng chuẩn, không phải lỗ hổng. **SAST không biết cơ chế xác thực thật đang
dùng gì nên không phân biệt được.**

---

## 3. `missing_control` — Thiếu auth/validation/guard

**Định nghĩa:** một endpoint/thao tác cần được bảo vệ (bởi auth, ownership check, hoặc
rate-limit) nhưng thiếu hẳn sự bảo vệ đó. Bao gồm BOLA/BFLA (Broken Object/Function Level
Authorization) và thiếu rate-limiting cho endpoint nhạy cảm.

**Kết quả gán nhãn:** 26 finding — 2 TP / 24 FP. Tỷ lệ lệch mạnh nhất trong 4 nhóm, nhưng **có
cấu trúc rõ ràng, không phải nhiễu ngẫu nhiên** — xem 5 loại nguyên nhân FP bên dưới.

> Đây là nhóm mà đề bài mô tả trực tiếp: *"liên quan tới vấn đề binding route/guard"*. Kết quả
> thật khớp chính xác giả thuyết đó.

### 5 nguyên nhân khiến rule báo sai (tách ra từ 24 FP thật)

| # | Nguyên nhân | Ví dụ |
|---|---|---|
| 1 | Guard nằm ở **path-prefix middleware** đăng ký sớm hơn trong cùng file | `JS-0047`: `/rest/basket/:id/checkout` được `app.use('/rest/basket/:id', security.isAuthorized())` che từ trước |
| 2 | Guard nằm trong **ownership-filter**, giá trị "tưởng attacker-controlled" thực ra bị middleware ghi đè trước khi tới handler | `JS-0010`: `where: {id, UserId: req.body.UserId}` — `UserId` bị `appendUserId()` ghi đè bằng giá trị JWT thật |
| 3 | Guard nằm **inline trong handler ở file route riêng**, không phải ở nơi đăng ký route | `JS-0058`: `updateUserProfile()` tự `if (!loggedInUser) { ... return }` |
| 4 | Endpoint **public-by-design theo nghiệp vụ** (login, đăng ký, feedback) | `JS-0045`, `JS-0041`–`JS-0044` |
| 5 | Endpoint chỉ thao tác **state toàn cục/game**, không gắn với user cụ thể nào để cần bảo vệ | `JS-0049`–`JS-0051` (continue-code), `JS-0054`–`JS-0056` (web3 challenge) |

### Ví dụ TP

**`JS-0052` — Forged review, thiếu kiểm tra thật sự** (`routes/createProductReviews.ts:16`)
```ts
const user = security.authenticatedUsers.from(req)
challengeUtils.solveIf(challenges.forgedReviewChallenge, () => user?.data?.email !== req.body.author)
// ... KHÔNG reject khi user === undefined
await reviewsCollection.insert({ author: req.body.author, ... })
```
Đọc dòng đầu tưởng đã "check auth", nhưng đọc hết cả hàm mới thấy `user` chỉ dùng để so sánh
cho một challenge, không hề có nhánh reject khi `undefined`. Bất kỳ ai (kể cả chưa đăng nhập)
đều post được review và **mạo danh tác giả bất kỳ** qua `req.body.author`. TP thật.

**`CRAPI-0011` — Thiếu rate-limit toàn hệ thống** (`crapi_site/settings.py:128`)
```python
REST_FRAMEWORK = { ... }  # không có DEFAULT_THROTTLE_CLASSES/RATES
```
`grep` toàn bộ `services/workshop/crapi/` không tìm thấy view nào override `throttle_classes`.
Không có rate-limit ở bất kỳ đâu, kể cả endpoint OTP nhạy cảm → brute-force được. Đây là control
**hoàn toàn không tồn tại**, không phải bị tắt.

### Ví dụ FP (đại diện cho nguyên nhân #2 — tinh vi nhất)

**`JS-0010`** (`routes/address.ts:29`)
```ts
const address = await AddressModel.destroy({ where: { id: req.params.id, UserId: req.body.UserId } })
```
Nhìn qua: `UserId` đọc từ `req.body`, tưởng attacker tự set được để xoá địa chỉ của người khác.
Nhưng route `DELETE /api/Addresss/:id` (server.ts:470) có `security.appendUserId()` chạy
**trước** handler này — middleware đó **ghi đè** `req.body.UserId` bằng ID thật lấy từ JWT của
người gọi. Giá trị lúc tới handler không còn là input của attacker nữa. Phải đọc middleware
chain trong `server.ts` VÀ định nghĩa `appendUserId()` mới kết luận được đây là FP.

### ⭐ Giới hạn ngoài phạm vi dataset (đáng ghi chú riêng)

Case kinh điển nhất của Juice Shop — guard `security.isAuthorized()` bị comment out ở
`server.ts:389` cho `PUT /api/Products/:id` — **không có trong dataset**. Route đó không tồn tại
như một câu lệnh `app.put(...)` tường minh; nó được **sinh tự động** bởi
`finale.initialize({ app, sequelize: seq })` (dòng 500) cho mọi model trong `autoModels`. Không
rule nào (registry lẫn custom) bắt được vì đây là **vấn đề recall** (rule chưa từng sinh ra
finding để verify), khác hẳn "agent thiếu context để verify 1 finding đã có". Ghi nhận ở đây
thay vì nhét vào dataset, để giữ đúng nguyên tắc "dataset chỉ gồm finding do tool thật sự sinh
ra" (xem `docs/tien-do.md`).

---

## 4. `broken_invariant` — Vi phạm bất biến ngầm định

**Định nghĩa:** code giả định một điều kiện luôn đúng (giá trị không null, resource đã mở,
record tồn tại, API trả về `None` khi không tìm thấy...) nhưng điều kiện đó không thực sự được
đảm bảo tại điểm code đang xét.

**Kết quả gán nhãn:** 23 finding — 13 TP / 10 FP.

### Loại context quyết định TP/FP

- **Bất biến có được đảm bảo bởi caller/hàm gọi trước đó không** — thường đòi hỏi lần theo
  ngược (tìm ai gọi hàm này, trong điều kiện nào), khác hẳn 3 nhóm trên (chủ yếu tra xuôi).
  Trong dataset này, case sâu nhất phải lần qua **2 microservice khác ngôn ngữ**.
- **Hành vi THẬT của API/thư viện đang dùng** — nhầm lẫn phổ biến: tưởng `.get()` trả `None`
  khi không tìm thấy (giống `.filter().first()`), nhưng Django ORM `.get()` **ném exception**.

### Ví dụ TP

**`CRAPI-0018` — Anti-pattern kinh điển của Django** (`merchant/views.py:141`)
```python
service_request = ServiceRequest.objects.get(id=service_request_id)
if not service_request:                      # ← dead code!
    return Response({"message": ...}, status=404)
```
`.get()` không bao giờ trả `None` — nó ném `DoesNotExist` khi không tìm thấy, khiến dòng
`if not service_request` **không bao giờ chạy tới được** cho trường hợp lỗi. Developer tưởng đã
xử lý lỗi nhưng thực chất chưa. `service_request_id` đến từ URL (client-controlled) → request
với ID không tồn tại crash bằng lỗi 500 thay vì 404 như code tưởng đã trả về.

**`JS-0037` — Middleware toàn cục thiếu try/catch** (`server.ts:342`)
```ts
if (req.body !== Object(req.body)) {
  req.body = JSON.parse(req.body)   // Expensive workaround for 500 errors... (see #640)
}
```
Middleware chạy cho **mọi request**. Chỉ cần `Content-Type: application/json` + body không hợp
lệ, ở bất kỳ endpoint nào, là lỗi. Comment ngay phía trên là bằng chứng chính dev đã biết vấn đề
này nhưng chưa xử lý triệt để.

### Ví dụ FP — case cần context sâu nhất trong toàn bộ dataset

**`CRAPI-0019`/`0023`/`0025`/`0027` — `UserDetails.objects.get(user=user)`**

Trông giống hệt `CRAPI-0018` (cùng pattern `.get()` không try/except), nhưng khác biệt mấu chốt:
`user` ở đây **không phải id từ client** mà là danh tính người dùng đã xác thực. Kết luận FP đòi
hỏi lần theo:

1. `jwt_auth_required` (Django, `utils/jwt.py`) tự làm `User.objects.get(email=...)` và bắt
   `User.DoesNotExist` **trước khi** gọi vào view — nên tới được view nghĩa là `User` chắc chắn
   tồn tại.
2. `docker-compose.yml`: service Django (`workshop`) và service Java (`identity`) trỏ **chung
   một** Postgres database — nên `User` do Java tạo, Django đọc thấy ngay.
3. `UserRegistrationServiceImpl.java` (service `identity`): `registerUser()` được đánh dấu
   `@Transactional`, bọc cả việc lưu `User` lẫn lưu `UserDetails` — nếu lưu `UserDetails` thất
   bại, cả giao dịch rollback, không để lại `User` mồ côi.

Ba bước trên đi qua **2 file, 2 service, 2 ngôn ngữ** — đây chính là kiểu context-gathering multi-hop
mà một AI agent (Tuần 2+) cần làm được, khác hẳn việc con người SAST rule tĩnh có thể làm.
Gán `confidence: medium` vì chưa xác minh hết mọi luồng tạo user khác (chỉ trace 1 luồng đăng ký
chuẩn).

### ⭐ Lưu ý phụ: chính custom rule cũng có bug

**`CRAPI-0021`** cùng pattern (`UserDetails.objects.get(user=user)`, dòng 129) nhưng **thực sự**
nằm trong `try: ... except Exception as e: ...` — được bảo vệ đúng cách. Rule tự viết
(`custom.broken-invariant.django-get-without-trycatch`) vẫn báo finding vì pattern gốc
`except $EXC:` không khớp cú pháp `except $EXC as $NAME:`. Đã sửa rule cho Tuần 2, nhưng **giữ
nguyên** finding này trong dataset — nó minh hoạ đúng một root-cause thật: đôi khi FP đến từ
**giới hạn của chính bộ máy phân tích tĩnh**, không chỉ từ thiếu context nghiệp vụ.

---

## Tóm tắt số liệu

| Nhóm | TP | FP | Tổng | Tỷ lệ FP |
|---|---|---|---|---|
| `taint_flow` | 12 | 11 | 23 | 48% |
| `insecure_property` | 13 | 2 | 15 | 13% |
| `missing_control` | 2 | 24 | 26 | 92% |
| `broken_invariant` | 13 | 10 | 23 | 43% |
| **Tổng** | **40** | **47** | **87** | **54%** |

Chênh lệch tỷ lệ FP giữa các nhóm (13% → 92%) tự nó là một phát hiện quan trọng: **rule registry
khá đáng tin cho `insecure_property`, nhưng gần như vô dụng để tự động phát hiện
`missing_control` mà không sinh FP tràn lan** — nguyên nhân chính xác đã liệt kê ở bảng 5 loại
FP phía trên, sẽ là điểm khởi đầu cho root-cause Tuần 4.
